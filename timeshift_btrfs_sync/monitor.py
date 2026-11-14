"""Optional per-config MQTT monitoring and honest snapshot-date progress."""
from __future__ import annotations

from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable
import hashlib
import os
import re
import socket
import sys
import time
import uuid

from . import __version__
from .mqtt import MQTTConfig, publish_messages


@dataclass(slots=True)
class MonitorConfig:
    """Independent live status options; broker/auth/QoS come from [mqtt]."""
    enabled: bool = False
    topic_prefix: str = "timeshift-btrfs-sync"
    heartbeat_interval: int = 60
    expire_after: int = 180
    discovery: bool = True
    discovery_prefix: str = "homeassistant"
    events: bool = True
    measure_transfers: bool = True
    progress_interval: int = 1
    manufacturer: str = "TimeShift-BTRFS-Sync"


_ACTIVE: ContextVar[LiveMonitor | None] = ContextVar("timeshift_live_monitor", default=None)


def utc_now() -> str:
    """Return an offset-aware UTC timestamp for consumers in any timezone."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def backup_identity(config_path: str | Path, hostname: str) -> str:
    """Hash hostname plus canonical config path so equal filenames stay distinct."""
    digest = hashlib.sha256((hostname + "\0" + str(Path(config_path).expanduser().resolve())).encode()).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9_]", "_", hostname.lower())[:32].strip("_") or "host"
    return f"ts_btrfs_{slug}_{digest}"


class SnapshotProgress:
    """Track completed dates plus the current remaining plan, without byte probes."""

    def __init__(self, observer: Callable[[dict], None] | None = None):
        """Start with an unknown total until the existing inventory/plan is ready."""
        self.completed: set[str] = set()
        self.pending: set[str] = set()
        self.skipped: set[str] = set()
        self.payload_bytes: dict[tuple[str, str], int | None] = {}
        self.planned = False
        self.current_snapshot: str | None = None
        self.current_subvolume: str | None = None
        self.observer = observer or report_progress

    def replan(self, names) -> None:
        """Replace only remaining work; changed tags cannot erase completed dates."""
        self.planned = True
        self.pending = set(names) - self.completed
        self._emit()

    def current(self, name: str, subvolume: str | None = None) -> None:
        """Expose the active date/payload while a long send is running."""
        self.current_snapshot, self.current_subvolume = name, subvolume
        self._emit()

    def payload_done(self, name: str, subvolume: str, size: int | None) -> None:
        """Count confirmed payload bytes once; a partial date is not completed."""
        self.payload_bytes[name, subvolume] = size
        self._emit()

    def complete(self, name: str) -> None:
        """Count a date only after all configured payloads and info.json succeed."""
        self.completed.add(name)
        self.pending.discard(name)
        self.current_snapshot = self.current_subvolume = None
        self._emit()

    def drop(self, name: str) -> None:
        """Record a source-unavailable/skipped date without pretending it transferred."""
        self.pending.discard(name)
        self.skipped.add(name)
        if self.current_snapshot == name:
            self.current_snapshot = self.current_subvolume = None
        self._emit()

    def invalidate(self, name: str) -> None:
        """Remove a failed whole-date version before existing recovery retries it."""
        self.completed.discard(name)
        self.payload_bytes = {key: size for key, size in self.payload_bytes.items() if key[0] != name}
        self._emit()

    def view(self) -> dict:
        """Build the same immutable counter view for CLI, heartbeat and last result."""
        total = len(self.completed) + len(self.pending) if self.planned else None
        return {
            "total_snapshots": total, "completed_snapshots": len(self.completed),
            "remaining_snapshots": len(self.pending) if self.planned else None,
            "skipped_snapshots": len(self.skipped),
            "progress": f"{len(self.completed)} / {total}" if total is not None else "planning",
            "current_snapshot": self.current_snapshot, "current_subvolume": self.current_subvolume,
            "data_transferred_bytes": sum(size for size in self.payload_bytes.values() if size is not None),
            "bytes_complete": all(size is not None for size in self.payload_bytes.values()),
            "progress_basis": "snapshot dates; all configured payloads and info.json complete",
        }

    def _emit(self) -> None:
        """Observers cannot turn monitoring problems into failed backup operations."""
        try:
            self.observer(self.view())
        except Exception:
            pass


class CleanupProgress:
    """Count confirmed date cleanup jobs; paired sides together form one job."""

    GROUPS = ("paired", "source", "cache", "destination")

    def __init__(self, observer: Callable[[dict], None] | None = None):
        """Keep unknown groups unknown until inventory supplies their candidates."""
        self.observer = observer or report_progress
        self.enabled = False
        self.pending: dict[str, set[str] | None] = {group: set() for group in self.GROUPS}
        self.completed: set[tuple[str, str]] = set()
        self.blocked: set[tuple[str, str]] = set()
        self.estimated: set[str] = set()
        self.current_group: str | None = None
        self.current_name: str | None = None
        self.finished = False
        self.initial_total: int | None = None
        self.initial_estimated = False

    def configure(self, enabled: bool) -> None:
        """Declare requested cleanup before transfers, without authorizing deletion."""
        self.enabled = enabled
        self.pending = {group: None if enabled else set() for group in self.GROUPS}
        self._emit()

    def plan(self, group: str, names, *, estimated: bool = False) -> None:
        """Replace one remaining group while retaining confirmed completed history."""
        self.pending[group] = None if names is None else set(names) - {name for kind, name in self.completed if kind == group}
        self.blocked = {key for key in self.blocked if key[0] != group or self.pending[group] is None or key[1] in self.pending[group]}
        if estimated:
            self.estimated.add(group)
        else:
            self.estimated.discard(group)
        self._emit()

    def current(self, group: str, name: str) -> None:
        """Expose the currently evaluated date even when a guard refuses deletion."""
        self.current_group, self.current_name = group, name
        self._emit()

    def complete(self, group: str, name: str, success: bool) -> None:
        """Advance only after all required actions are confirmed; retain blocked work."""
        key = (group, name)
        if success:
            self.completed.add(key)
            self.blocked.discard(key)
            if self.pending[group] is not None:
                self.pending[group].discard(name)
        elif key not in self.completed:
            self.blocked.add(key)
        self.current_group = self.current_name = None
        self._emit()

    def finish(self) -> None:
        """Finish reporting without converting remaining or unknown work into success."""
        self.finished = True
        self.current_group = self.current_name = None
        self._emit()

    def view(self) -> dict:
        """Return aggregate and per-group counters without claiming physical subvolume counts."""
        remaining = sum(len(names) for names in self.pending.values() if names is not None)
        known = all(names is not None for names in self.pending.values())
        total = len(self.completed) + remaining if known else None
        status = ("disabled" if not self.enabled else "unverified" if self.finished and (not known or self.estimated)
                  else "incomplete" if self.finished and remaining else "complete" if self.finished
                  else "estimated" if self.estimated else "running" if known else "planning")
        return {
            "cleanup_enabled": self.enabled, "cleanup_status": status,
            "cleanup_total": total, "cleanup_completed": len(self.completed),
            "cleanup_remaining": remaining if known else None,
            "cleanup_blocked": len(self.blocked),
            "cleanup_processed": len(self.completed | self.blocked),
            "cleanup_initial_total": self.initial_total,
            "cleanup_initial_plan_estimated": self.initial_estimated,
            "cleanup_current_number": len((self.completed | self.blocked) - {(self.current_group, self.current_name)}) + 1 if self.current_name else None,
            "cleanup_plan_estimated": bool(self.estimated),
            "cleanup_current_snapshot": self.current_name, "cleanup_current_group": self.current_group,
            "cleanup_progress_basis": "date cleanup jobs; all required sides confirmed; not individual Btrfs subvolumes",
            "cleanup_groups": {group: {
                "total": len(names) + sum(kind == group for kind, _ in self.completed) if names is not None else None,
                "completed": sum(kind == group for kind, _ in self.completed),
                "blocked": sum(kind == group for kind, _ in self.blocked),
                "estimated": group in self.estimated,
            } for group, names in self.pending.items()},
        }

    def _emit(self) -> None:
        """Keep optional observers outside the backup's success and safety decisions."""
        try:
            metrics = self.view()
            if self.enabled and self.initial_total is None and metrics["cleanup_total"] is not None:
                self.initial_total = metrics["cleanup_total"]
                self.initial_estimated = bool(self.estimated)
                metrics.update(cleanup_initial_total=self.initial_total,
                               cleanup_initial_plan_estimated=self.initial_estimated)
            self.observer(metrics)
        except Exception:
            pass


def cleanup_progress() -> CleanupProgress | None:
    """Return this run's optional main-thread tracker, with no MQTT or inventory I/O."""
    active = _ACTIVE.get()
    return active.cleanup if active is not None else None


def configure_run(*, cleanup: bool, operation: str = "sync") -> None:
    """Initialize work metrics after the existing real-run lock is held."""
    active = _ACTIVE.get()
    if active is not None:
        active.cleanup.configure(cleanup)
        active.update({"operation": operation})
        if operation == "prune":
            active.update(SnapshotProgress(observer=lambda _: None).view() | {
                "total_snapshots": 0, "remaining_snapshots": 0, "progress": "0 / 0"})


def report_progress(payload: dict) -> None:
    """Forward main-thread progress to its active per-run monitor, when enabled."""
    active = _ACTIVE.get()
    if active is not None:
        active.update(payload)


def report_phase(phase: str) -> None:
    """Keep heartbeats alive during inventory, Timeshift waiting and cleanup."""
    report_progress({"phase": phase})


def transfer_reporter():
    """Bind this run's byte observer before relaying one real send stream."""
    active = _ACTIVE.get()
    if active is None or not active.options.measure_transfers:
        return None
    return active.begin_transfer()


def discovery_messages(options: MonitorConfig, identity: str, name: str, status_topic: str, result_topic: str) -> list[tuple[str, dict, bool]]:
    """Describe one HA device per backup, with expiring live and durable result sensors."""
    device = {"identifiers": [identity], "name": name, "manufacturer": options.manufacturer, "model": "Snapshot backup", "sw_version": __version__}
    fields = {
        "status": ("Live status", None, None), "progress": ("Snapshot progress", None, None),
        "completed_snapshots": ("Completed snapshots", None, None), "total_snapshots": ("Expected snapshots", None, None),
        "remaining_snapshots": ("Remaining snapshots", None, None), "failed_snapshots": ("Failed snapshots", None, None),
        "data_transferred_bytes": ("Confirmed transferred bytes", "B", "data_size"),
        "runtime_seconds": ("Runtime", "s", "duration"), "current_snapshot": ("Current snapshot", None, None),
        "started_at": ("Started at", None, "timestamp"), "last_heartbeat": ("Last heartbeat", None, "timestamp"),
        "last_result": ("Last result", None, None),
        "last_success": ("Last successful run", None, "timestamp"),
        "average_speed_bytes_per_second": ("Run average speed", "B/s", "data_rate"),
    }
    messages = []
    for field, (label, unit, device_class) in fields.items():
        result = field in {"last_result", "last_success"}
        topic = result_topic.rsplit("/", 1)[0] + "/last_success" if field == "last_success" else result_topic if result else status_topic
        template = "{{ value_json.status }}" if result else "{{ value_json." + field + " }}"
        if field == "last_success":
            template = "{{ value_json.ended_at }}"
        if field == "current_snapshot":
            template = "{{ value_json.current_snapshot or '-' }}"
        payload = {
            "name": label, "unique_id": identity + "_" + field,
            "default_entity_id": "sensor." + identity + "_" + field,
            "device": device, "state_topic": topic, "value_template": template,
            "json_attributes_topic": topic if field in {"status", "last_result", "last_success"} else None,
        }
        if payload["json_attributes_topic"] is None:
            del payload["json_attributes_topic"]
        else:
            # Stable roles are independent of entity IDs and user-facing labels.
            payload["json_attributes_template"] = (
                "{{ dict(value_json, live_preview_role=" + repr(field) + ") | tojson }}"
            )
        if not result:
            payload["expire_after"] = options.expire_after
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        messages.append((f"{options.discovery_prefix}/sensor/{identity}/{field}/config", payload, True))
    return messages


class LiveMonitor:
    """Publish status asynchronously; flock and backup success never depend on MQTT."""

    def __init__(self, config, config_path: str | Path, *, event_only: bool = False, started_monotonic=None, started_at=None):
        """Capture public identity and metrics without connecting on the backup thread."""
        self.options = config.mqtt_monitor
        self.broker: MQTTConfig = config.mqtt
        self.hostname = socket.gethostname()
        self.identity = backup_identity(config_path, self.hostname)
        self.name = config.name or Path(config_path).stem
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + f"-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self.started_at = started_at or utc_now()
        self.started_monotonic = time.monotonic() if started_monotonic is None else started_monotonic
        self.ended_monotonic = None
        self._stream_bytes = 0
        self._stream_attempt = 0
        self.base = self.options.topic_prefix.rstrip("/") + "/" + self.identity
        self.event_only = event_only
        self._lock = Lock()
        self._wake = Event()
        self._cancelled = Event()
        self._finished = False
        self._events: deque[dict] = deque(maxlen=64)
        self._result: dict | None = None
        self._metrics = {**SnapshotProgress(observer=lambda _: None).view(), "status": "running", "phase": "starting", "failed_snapshots": 0}
        self.cleanup = CleanupProgress(observer=self.update)
        self._metrics.update(self.cleanup.view())
        self._thread: Thread | None = None
        self._token = None

    def payload(self) -> dict:
        """Snapshot public metrics under the lock without including config secrets/paths."""
        with self._lock:
            elapsed = max(0, (self.ended_monotonic if self.ended_monotonic is not None else time.monotonic()) - self.started_monotonic)
            metrics = dict(self._metrics)
            if self.options.measure_transfers:
                metrics.update(data_transferred_bytes=self._stream_bytes, bytes_complete=True,
                               byte_measurement="actual send stream forwarded to receive; includes retries and active payload")
            transfer_total, cleanup_total = metrics.get("total_snapshots"), metrics.get("cleanup_total")
            overall_total = transfer_total + cleanup_total if transfer_total is not None and cleanup_total is not None else None
            overall_done = metrics.get("completed_snapshots", 0) + metrics.get("cleanup_completed", 0)
            metrics.update(overall_total_steps=overall_total, overall_completed_steps=overall_done,
                           overall_remaining_steps=overall_total - overall_done if overall_total is not None else None,
                           overall_plan_estimated=metrics.get("cleanup_plan_estimated", False),
                           overall_progress_basis="one complete transferred date or one confirmed date cleanup job per step")
            total = metrics.get("data_transferred_bytes")
            metrics["average_speed_bytes_per_second"] = total / elapsed if isinstance(total, (int, float)) and elapsed > 0 else None
            return {"backup_id": self.identity, "backup_name": self.name, "hostname": self.hostname,
                    "run_id": self.run_id, "version": __version__, "started_at": self.started_at,
                    "runtime_seconds": round(elapsed, 3),
                    "last_heartbeat": utc_now(), **metrics}

    def begin_transfer(self):
        """Count every actual attempted byte once, including failed/retried streams."""
        with self._lock:
            base = self._stream_bytes
            self._stream_attempt += 1
            attempt = self._stream_attempt
        def observe(total):
            """Coalesce cumulative per-attempt measurements without resetting prior traffic."""
            with self._lock:
                if attempt != self._stream_attempt:
                    return
                self._stream_bytes = max(self._stream_bytes, base + max(0, int(total)))
            self._wake.set()
        return observe

    def update(self, metrics: dict) -> None:
        """Coalesce progress immediately; socket work stays on one bounded worker."""
        with self._lock:
            self._metrics.update(metrics)
        self._wake.set()

    def event(self, kind: str, **details) -> None:
        """Queue a non-retained lifecycle event, independently from notifications."""
        if self.options.events:
            with self._lock:
                self._events.append({"backup_id": self.identity, "backup_name": self.name,
                                     "hostname": self.hostname, "run_id": self.run_id,
                                     "event": kind, "timestamp": utc_now(), **details})
            self._wake.set()

    def __enter__(self):
        """Activate only after the real sync lock has been acquired."""
        self._token = _ACTIVE.set(self)
        self.event("started")
        self._start_worker()
        return self

    def _start_worker(self) -> None:
        """Launch at most one daemon; missing paho/broker access cannot block sync."""
        try:
            self._thread = Thread(target=self._worker, name="ts-btrfs-mqtt-monitor", daemon=True)
            self._thread.start()
        except Exception as exc:
            self._thread = None
            print(f"WARNING: live MQTT worker could not start: {exc}", file=sys.stderr)

    def __exit__(self, exc_type, exc, tb):
        """Publish the truthful terminal result and bound final drain to one second."""
        try:
            self.ended_monotonic = time.monotonic()
            status = "success" if exc is None else "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            if exc is not None and self.cleanup.current_name:
                self.cleanup.complete(self.cleanup.current_group, self.cleanup.current_name, False)
            self.cleanup.finish()
            if exc is None and (self._metrics.get("remaining_snapshots") or
                                self._metrics.get("cleanup_status") in {"incomplete", "unverified"}):
                status = "incomplete"
            self.update({"status": status, "phase": "finished", "ended_at": utc_now(),
                         "failed_snapshots": int(exc is not None and bool(self._metrics.get("current_snapshot"))),
                         "error": str(exc)[-2000:] if exc is not None else "",
                         "exit_code": 130 if isinstance(exc, KeyboardInterrupt) else getattr(exc, "returncode", 1) if exc else 0})
            result = self.payload()
            with self._lock:
                self._result = result
            self.event("completed" if status == "success" else "failed", status=status)
            self._finished = True
            self._wake.set()
            if self._thread:
                self._thread.join(timeout=1.0)
                if self._thread.is_alive():
                    self._cancelled.set()
        except Exception as monitor_error:
            print(f"WARNING: live MQTT finalization failed: {monitor_error}", file=sys.stderr)
        finally:
            self._cancelled.set()
            if self._token is not None:
                _ACTIVE.reset(self._token)
        return False

    def _worker(self) -> None:
        """Emit heartbeat/changes with retryable, rate-limited broker failures."""
        discovery_sent = False
        warned = False
        while not self._cancelled.is_set():
            self._wake.clear()
            with self._lock:
                events = list(self._events)
                self._events.clear()
                result = self._result
                finished = self._finished
            payload = self.payload()
            messages = []
            if self.options.discovery and not discovery_sent and not self.event_only:
                messages.extend(discovery_messages(self.options, self.identity, self.name, self.base + "/status", self.base + "/last_result"))
            messages.extend((self.base + "/events", event, False) for event in events)
            if not self.event_only:
                messages.append((self.base + "/status", payload, False))
                if result is not None:
                    messages.append((self.base + "/last_result", result, True))
                    if result.get("status") == "success":
                        messages.append((self.base + "/last_success", result, True))
            try:
                publish_messages(self.broker, messages, client_suffix="-live-" + self.identity[-16:] + "-" + self.run_id,
                                 cancelled=self._cancelled.is_set)
                discovery_sent = True
                warned = False
            except Exception as exc:
                if not warned and not self._cancelled.is_set():
                    print(f"WARNING: live MQTT monitoring unavailable for {self.name} ({self.identity}): {exc}", file=sys.stderr)
                    warned = True
            if finished or self.event_only:
                return
            self._wake.wait(timeout=self.options.heartbeat_interval)


def duplicate_event(config, config_path: str | Path) -> None:
    """Report a refused launch on events only; never overwrite its live owner/result."""
    if not config.mqtt_monitor.enabled or not config.mqtt_monitor.events:
        return
    try:
        monitor = LiveMonitor(config, config_path, event_only=True)
        monitor.event("duplicate_run", reason="backup lock already held")
        monitor._start_worker()
        if monitor._thread:
            monitor._thread.join(timeout=1.0)
            if monitor._thread.is_alive():
                monitor._cancelled.set()
    except Exception:
        pass
