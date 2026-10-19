"""Shared optional MQTT notification and live-monitor batch publishing.

Legacy completion notifications use publish_status; the asynchronous monitor
uses publish_messages with independent enablement/topics. Paho imports remain
lazy, so installing the optional module is unnecessary when both are disabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import json
import socket


@dataclass(slots=True)
class MQTTConfig:
    """MQTT broker and publish settings.

    username/password are optional. If username is blank, anonymous MQTT is used.
    password_file is supported so passwords do not have to be stored directly in
    config.toml. Use either password or password_file, not both.
    """

    enabled: bool = False
    host: str = ""
    port: int = 1883
    topic: str = "timeshift-btrfs-sync/status"
    username: str | None = None
    password: str | None = None
    password_file: str | None = None
    client_id: str | None = None
    qos: int = 0
    retain: bool = False
    timeout: int = 10
    notify_on_success: bool = True
    notify_on_failure: bool = True

    def resolved_password(self) -> str | None:
        """Return password from config value or password_file."""

        if self.password_file:
            with open(self.password_file, "r", encoding="utf-8") as fh:
                return fh.read().strip()
        return self.password



def publish_status(config: MQTTConfig, payload: dict[str, Any]) -> None:
    """Publish one JSON MQTT status message.

    Publishing errors are raised to the caller. CLI code catches them and prints
    a warning because notification failure should not hide the real backup exit
    code.
    """

    if not config.enabled:
        return
    publish_messages(config, [(config.topic, payload, config.retain)])


def publish_messages(
    config: MQTTConfig,
    messages: list[tuple[str, dict[str, Any], bool]],
    *,
    client_suffix: str = "",
    cancelled: Callable[[], bool] | None = None,
) -> None:
    """Publish a batch through one broker connection with its network loop active.

    Both legacy notifications and independent live monitoring reuse credentials,
    serialization and QoS handling. The caller decides enablement. Monitoring
    calls this only on a daemon worker so DNS/socket timeouts cannot stall sends.
    """

    if cancelled is not None and cancelled():
        return
    if not config.host:
        raise RuntimeError("mqtt.host is required for MQTT publishing")

    try:
        import paho.mqtt.client as mqtt_client
    except ImportError as exc:
        raise RuntimeError(
            "paho-mqtt is required for MQTT publishing. Install with: "
            "python3 -m pip install -e '.[mqtt]'"
        ) from exc

    client_id = (config.client_id or f"timeshift-btrfs-sync-{socket.gethostname()}") + client_suffix

    # paho-mqtt 2.x supports callback_api_version. paho-mqtt 1.x does not.
    try:
        client = mqtt_client.Client(
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
    except (AttributeError, TypeError):
        client = mqtt_client.Client(client_id=client_id)

    if config.username:
        client.username_pw_set(config.username, config.resolved_password())

    # paho 2.x bounds TCP connection setup; older releases may not expose it.
    if hasattr(client, "connect_timeout"):
        client.connect_timeout = config.timeout
    started = False
    try:
        client.connect(config.host, config.port, keepalive=max(config.timeout, 5))
        client.loop_start()
        started = True
        for topic, payload, retain in messages:
            if cancelled is not None and cancelled():
                return
            info = client.publish(
                topic, payload=json.dumps(payload, sort_keys=True, separators=(",", ":")),
                qos=config.qos, retain=retain,
            )
            info.wait_for_publish(timeout=config.timeout)
            if not info.is_published():
                raise RuntimeError("MQTT publish did not finish before timeout")
    finally:
        try:
            client.disconnect()
        finally:
            if started:
                client.loop_stop()
