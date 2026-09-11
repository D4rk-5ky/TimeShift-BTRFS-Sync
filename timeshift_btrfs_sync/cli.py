"""Command-line interface for timeshift-btrfs-sync."""

from __future__ import annotations

from pathlib import Path
from .paths import is_local_same_or_under as _path_is_same_or_under
from importlib.resources import files
import argparse
import json
import sys
import time
from . import __version__, timeshift
from .commands import CommandError
from .btrfs_ops import BtrfsOps
from .endpoint import CommandEndpoint
from .config import ConfigError, load_config
from .lock import FileLock
from .log import active_logger, create_run_logger, emit_final_terminal_summary, stage_final_run_summary
from .mail import send_status as send_mail_status
from .mqtt import publish_status
from .models import SnapshotMeta
from .notify import build_notification_payload
from .retention import PruneResult, prune
from .restore import restore_backups
from .destroy import destroy_leftovers
from .maintenance import clear_state_file, delete_lock_file
from .source import SourceRunner
from .state import load_state, refresh_state_metadata_and_report
from .sync import SyncRunSummary, confirm_source_identity_before_manual_snapshot, format_sync_summary, format_transferred_snapshots, list_source_snapshots, print_snapshot_table, source_snapshot_index, sync_once
from .preflight import check_required_sync_paths, prepare_destination_helper_paths, prepare_lock_path
from .timeshift import create_source_manual_snapshot
from .topology import describe_sync_topology, reject_pull_restore_profile_for_sync


CLI_FORMATTER = argparse.RawTextHelpFormatter


def add_version_arg(parser: argparse.ArgumentParser) -> None:
    """Expose the installed package version from the top level and every subcommand."""

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the installed TimeShift-BTRFS-Sync version and exit; valid before or after a subcommand",
    )


def new_subparser(
    sub,
    name: str,
    help_text: str,
    description: str,
    func,
    *,
    epilog: str = "",
):
    """Create one self-contained command parser with version and troubleshooting help."""

    parser = sub.add_parser(
        name,
        help=help_text,
        description=f"TimeShift-BTRFS-Sync {__version__}\n\n{description}",
        epilog=epilog or None,
        formatter_class=CLI_FORMATTER,
    )
    add_version_arg(parser)
    parser.set_defaults(func=func)
    return parser


def add_config_arg(parser) -> None:
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        metavar="FILE",
        help=(
            "required TOML configuration file. It selects the job name, source/restore topology, "
            "source and destination paths, SSH/sudo settings, retention, logging/notifications, "
            "and default_dry_run behavior. The CLI does not auto-discover a config file."
        ),
    )


def add_run_mode_args(parser, *, dry_run_help: str, run_help: str) -> None:
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help=dry_run_help)
    mode.add_argument("--run", action="store_true", help=run_help)


def add_yes_delete_arg(parser, help_text: str) -> None:
    parser.add_argument("--yes-delete", action="store_true", help=help_text)


def _load_config_state(config):
    """Load state and resolve all root-relative paths against this config."""

    return load_state(config.state_file)


def _failure_exit_code(exc: BaseException) -> int:
    """Return a stable CLI exit code for failure notifications.

    CommandError carries the real return code from the failed external command,
    such as btrfs send/receive or ssh. Other Python-side safety errors use 1.
    Keeping this helper defined avoids masking the real error with a secondary
    NameError during MQTT/mail failure handling.
    """

    if isinstance(exc, CommandError):
        try:
            return int(exc.returncode)
        except Exception:
            return 1
    return 1

def _stderr_tail_for_exception(exc: BaseException, logger) -> str:
    """Return the best available recent stderr text for failure notifications."""

    if isinstance(exc, CommandError) and exc.stderr:
        return exc.stderr[-4000:]
    if logger:
        return logger.last_stderr_tail()
    return ""


def _send_notifications(
    config,
    command_name: str,
    *,
    success: bool,
    exit_code: int,
    error: str = "",
    stderr_tail: str = "",
    attachment_paths: list[Path] | None = None,
) -> None:
    """Send optional MQTT/email status without changing the command exit code."""

    payload = build_notification_payload(
        job_name=config.name,
        command=command_name,
        state="success" if success else "failure",
        success=success,
        exit_code=exit_code,
        stderr_tail=stderr_tail,
        error=error,
        version=__version__,
    )

    mqtt_config = config.mqtt
    if mqtt_config and mqtt_config.enabled:
        if (success and mqtt_config.notify_on_success) or (not success and mqtt_config.notify_on_failure):
            try:
                publish_status(mqtt_config, payload)
            except Exception as mqtt_exc:
                print(f"WARNING: MQTT notification failed: {mqtt_exc}", file=sys.stderr)

    mail_config = config.mail
    if mail_config and mail_config.enabled:
        if (success and mail_config.notify_on_success) or (not success and mail_config.notify_on_failure):
            try:
                send_mail_status(mail_config, payload, attachments=attachment_paths)
            except Exception as mail_exc:
                print(f"WARNING: mail notification failed: {mail_exc}", file=sys.stderr)


def _mail_attachment_paths(logger) -> list[Path] | None:
    """Return current run log paths for optional email attachment."""

    if not logger:
        return None
    try:
        return logger.attachment_paths()
    except Exception:
        return None

def _safe_destroy_log_dir(config, selected_delete_roots: list[Path]) -> Path | None:
    """Return a log directory that will survive a destructive cleanup.

    Normal commands use the configured ``log_dir``.  destroy-leftovers is
    different: the configured log directory may live inside destination.target_root,
    and that target may be deleted by the same command.  If so, use a stable
    fallback under the current working directory or the user's cache directory so
    the destructive-run logs remain available after cleanup.
    """

    configured = config.log_dir
    if configured is None:
        return None
    selected = [Path(root).expanduser() for root in selected_delete_roots]
    if not any(_path_is_same_or_under(configured, root) for root in selected):
        return configured

    candidates = [
        Path.cwd() / "logs",
        Path.home() / ".cache" / "timeshift-btrfs-sync" / "logs",
    ]
    for candidate in candidates:
        if any(_path_is_same_or_under(candidate, root) for root in selected):
            continue
        try:
            candidate.mkdir(mode=0o755, parents=True, exist_ok=True)
            print(
                "WARNING: configured log_dir is inside a destroy-leftovers target; "
                f"using survivor log_dir instead: {candidate}",
                file=sys.stderr,
            )
            return candidate
        except OSError:
            continue
    print(
        "WARNING: configured log_dir is inside a destroy-leftovers target and no survivor log_dir could be prepared; "
        "file logging is disabled for this command.",
        file=sys.stderr,
    )
    return None

def _with_logging(
    config,
    command_name: str,
    callback,
    *,
    log_dir_override: Path | None = None,
    finalizer=None,
    mail_finalizer=None,
):
    """Run a command with optional logging, notifications, and final summary.

    If config.log_dir is None, this is a direct callback call plus optional
    notifications. With logging, split run files are created before command work.
    When ``finalizer`` is supplied it returns the final terminal/.log summary.
    ``mail_finalizer`` may provide a differently ordered .succes/mail body. Both
    are staged before notifications, then the terminal form is printed only after
    notifications so its final three blocks remain the last normal output.
    """

    logger = create_run_logger(config.log_dir if log_dir_override is None else log_dir_override, config.name)

    def _summary_text(exc: BaseException | None) -> str:
        if finalizer is None:
            return ""
        try:
            return str(finalizer(exc) or "")
        except Exception as summary_exc:
            print(f"WARNING: final run summary could not be prepared: {summary_exc}", file=sys.stderr)
            return ""

    def _mail_summary_text(exc: BaseException | None, normal_text: str) -> str:
        if mail_finalizer is None:
            return normal_text
        try:
            return str(mail_finalizer(exc) or normal_text)
        except Exception as summary_exc:
            print(f"WARNING: mail run summary could not be prepared: {summary_exc}", file=sys.stderr)
            return normal_text

    def _stage(text: str, *, mail_text: str) -> None:
        if text:
            stage_final_run_summary(text, success_text=mail_text)

    def _emit_terminal(text: str) -> None:
        if text:
            emit_final_terminal_summary(text)

    with active_logger(logger):
        if logger:
            logger.info(f"CLI COMMAND: {command_name}")
            logger.info("Logging is active before command work begins")
        try:
            result = int(callback() or 0)
            summary_text = _summary_text(None)
            mail_summary_text = _mail_summary_text(None, summary_text)
            _stage(summary_text, mail_text=mail_summary_text)
            _send_notifications(
                config,
                command_name,
                success=(result == 0),
                exit_code=result,
                attachment_paths=_mail_attachment_paths(logger),
            )
            _emit_terminal(summary_text)
            return result
        except KeyboardInterrupt as exc:
            if logger:
                logger.err("ERROR: Interrupted by user")
            summary_text = _summary_text(exc)
            mail_summary_text = _mail_summary_text(exc, summary_text)
            _stage(summary_text, mail_text=mail_summary_text)
            stderr_tail = _stderr_tail_for_exception(exc, logger)
            _send_notifications(
                config,
                command_name,
                success=False,
                exit_code=130,
                error="Interrupted by user",
                stderr_tail=stderr_tail,
                attachment_paths=_mail_attachment_paths(logger),
            )
            _emit_terminal(summary_text)
            raise
        except Exception as exc:
            if logger:
                logger.err(f"ERROR: {exc}")
            summary_text = _summary_text(exc)
            mail_summary_text = _mail_summary_text(exc, summary_text)
            _stage(summary_text, mail_text=mail_summary_text)
            stderr_tail = _stderr_tail_for_exception(exc, logger)
            exit_code = _failure_exit_code(exc)
            _send_notifications(
                config,
                command_name,
                success=False,
                exit_code=exit_code,
                error=str(exc),
                stderr_tail=stderr_tail,
                attachment_paths=_mail_attachment_paths(logger),
            )
            _emit_terminal(summary_text)
            raise


def _resolve_dry_run(args, config) -> bool:
    if getattr(args, "dry_run", False):
        return True
    if getattr(args, "run", False):
        return False
    return config.default_dry_run


def cmd_init_config(args) -> int:
    path = Path(args.path).expanduser()
    if path.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {path}", file=sys.stderr)
        return 2
    template_name = {
        "sync": "config.example.toml",
        "restore-pull": "config.restore-pull.example.toml",
        "remote-roundtrip": "config.remote-roundtrip.example.toml",
    }[args.profile]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        files("timeshift_btrfs_sync").joinpath(f"data/{template_name}").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    print(f"Wrote {args.profile} config: {path}")
    return 0


def cmd_test_source(args) -> int:
    config = load_config(args.config)

    def _run() -> int:
        source = SourceRunner.from_config(config)
        if source.uses_ssh:
            source.test()
        else:
            print("Source mode: local; SSH test skipped.")
        source.run(timeshift.timeshift_cmd(config.source.sudo, config.source.timeshift_command, ["--list"]))
        source_btrfs = BtrfsOps(
            CommandEndpoint.for_source(source), config.source.sudo, config.source.btrfs_command
        )
        source_btrfs.run(["--version"])
        print("Source command endpoint works. Source sudo for timeshift/btrfs works.")
        return 0

    return _with_logging(config, "test-source", _run)



def _refresh_state_metadata_from_timeshift(config, state: dict, *, dry_run: bool) -> dict[str, SnapshotMeta]:
    """Refresh mutable state metadata and return the same current Timeshift index."""

    source = SourceRunner.from_config(config)
    print("Refreshing state metadata from source Timeshift --list...")
    source_by_name = source_snapshot_index(list_source_snapshots(config, source, include_btrfs_info=False))
    refresh_state_metadata_and_report(state, source_by_name.values(), config.state_file, dry_run=dry_run)
    return source_by_name

def cmd_list_source(args) -> int:
    """List snapshots on the source machine.

    Default is fast listing: parse Timeshift names/tags and construct expected
    subvolume paths without probing every subvolume with Btrfs. Use
    --verify-btrfs when you explicitly want the slower full verification.
    """

    config = load_config(args.config)

    def _run() -> int:
        print_snapshot_table(
            list_source_snapshots(
                config,
                SourceRunner.from_config(config),
                include_btrfs_info=args.verify_btrfs,
            )
        )
        return 0

    return _with_logging(config, "list-source", _run)


def _format_cleanup_summary(
    result: PruneResult | None,
    *,
    requested: bool,
    dry_run: bool,
    error: BaseException | None = None,
) -> str:
    """Return the mandatory final cleanup summary for a sync command."""

    lines = [
        "CLEANUP SUMMARY",
        "===============",
    ]

    if not requested:
        lines += [
            "  requested:          no",
            "  status:             not requested",
            "  cleaned snapshots:  0",
            "  reason:             neither --prune nor prune_after_sync=true requested retention",
            "  result:             SUCCESS - cleanup skipped; cleaned 0 snapshots",
        ]
        return "\n".join(lines)

    lines.append("  requested:          yes")
    lines.append(f"  mode:               {'dry-run' if dry_run else 'real run'}")

    if result is None:
        reason = str(error) if error else "cleanup did not return a result"
        lines += [
            "  status:             failed/not completed",
            "  cleaned snapshots:  unknown",
            f"  reason:             {reason}",
            "  result:             FAILED",
        ]
        return "\n".join(lines)

    lines += [
        f"  retention candidates:{len(result.plan.delete):>5}",
        f"  source candidates:   {result.source_delete_candidates:>5}",
        f"  source authorized:   {result.source_delete_authorized:>5}",
        f"  cleaned snapshots:   {result.cleaned_snapshots:>5}",
        f"  retry paired items:  {result.retry_destination_state_items:>5}",
        f"  blocked source:      {result.blocked_source_candidates:>5}",
        f"  remaining in state:  {result.remaining_state:>5}",
    ]
    if result.dry_run:
        lines += [
            "  status:             dry-run only; no snapshots deleted",
            "  result:             SUCCESS - cleaned 0 snapshots (dry-run)",
        ]
    elif result.retry_destination_state_items or result.blocked_source_candidates:
        lines += [
            "  status:             completed with protected/retry items",
            f"  result:             SUCCESS - cleaned {result.cleaned_snapshots} snapshot(s); some candidates were retained safely",
        ]
    else:
        lines += [
            "  status:             completed",
            f"  result:             SUCCESS - cleaned {result.cleaned_snapshots} snapshot(s)",
        ]
    return "\n".join(lines)


def _format_failed_sync_summary(exc: BaseException, *, elapsed_seconds: float | None = None) -> str:
    """Return a final sync block when sync failed before a normal summary existed."""

    lines = [
        "SYNC SUMMARY",
        "============",
        "  status:             FAILED",
        "  transferred:        incomplete/unknown",
        f"  reason:             {exc}",
    ]
    if elapsed_seconds is not None:
        from .sync import format_duration

        lines.append(f"  total backup time: {format_duration(elapsed_seconds)}")
    return "\n".join(lines)


def cmd_sync(args) -> int:
    backup_started = time.monotonic()
    config = load_config(args.config)
    reject_pull_restore_profile_for_sync(config)
    topology = describe_sync_topology(config)
    print("SYNC TOPOLOGY")
    print("=============")
    print(f"  Timeshift source: {topology.source_label}")
    print(f"  backup target:    {topology.destination_label}")
    print(f"  source path:      {config.source.snapshot_root}")
    print(f"  backup root:      {config.destination.target_root}")
    print(f"  effective rule:   {topology.detail}")
    print()
    dry_run = _resolve_dry_run(args, config)
    cleanup_requested = bool(args.prune or config.prune_after_sync)
    final_state: dict[str, object] = {
        "sync": None,
        "cleanup": None,
        "elapsed_seconds": None,
    }

    def _final_blocks(exc: BaseException | None) -> tuple[str, str, str]:
        elapsed_seconds = final_state.get("elapsed_seconds")
        if not isinstance(elapsed_seconds, (int, float)):
            elapsed_seconds = time.monotonic() - backup_started
            final_state["elapsed_seconds"] = elapsed_seconds
        sync_result = final_state.get("sync")
        cleanup_result = final_state.get("cleanup")
        if isinstance(sync_result, SyncRunSummary):
            transfer_text = format_transferred_snapshots(sync_result)
            sync_text = format_sync_summary(sync_result, elapsed_seconds=elapsed_seconds)
        else:
            transfer_text = "TRANSFERRED SNAPSHOTS\n=====================\nNo completed transfer list is available because sync did not complete.\n\n  none/unknown"
            sync_text = _format_failed_sync_summary(
                exc or RuntimeError("sync did not complete"),
                elapsed_seconds=elapsed_seconds,
            )

        cleanup_error = exc if cleanup_requested and not isinstance(cleanup_result, PruneResult) else None
        cleanup_text = _format_cleanup_summary(
            cleanup_result if isinstance(cleanup_result, PruneResult) else None,
            requested=cleanup_requested,
            dry_run=dry_run,
            error=cleanup_error,
        )
        return transfer_text, sync_text, cleanup_text

    def _finalize(exc: BaseException | None) -> str:
        transfer_text, sync_text, cleanup_text = _final_blocks(exc)
        return transfer_text + "\n\n" + sync_text + "\n\n" + cleanup_text + "\n"

    def _mail_finalize(exc: BaseException | None) -> str:
        transfer_text, sync_text, cleanup_text = _final_blocks(exc)
        return (
            "BACKUP RUN\n"
            "==========\n"
            f"  name: {config.name}\n\n"
            + sync_text
            + "\n\n"
            + cleanup_text
            + "\n\n"
            + transfer_text
            + "\n"
        )

    def _run_dry() -> int:
        print("Run mode: dry-run")
        print("Strict dry-run: no destination preparation, no lock file, no receive, and no prune deletion will be performed.")
        state = _load_config_state(config)
        final_state["sync"] = sync_once(
            config,
            state,
            dry_run=True,
            limit=args.limit,
            only_snapshot=args.snapshot,
            only_missing=not args.resend,
        )
        if cleanup_requested:
            final_state["cleanup"] = prune(config, state, dry_run=True, yes_delete=False)
        return 0

    def _run_locked() -> int:
        state = _load_config_state(config)
        final_state["sync"] = sync_once(
            config,
            state,
            dry_run=False,
            limit=args.limit,
            only_snapshot=args.snapshot,
            only_missing=not args.resend,
        )
        if cleanup_requested:
            final_state["cleanup"] = prune(
                config,
                state,
                dry_run=False,
                yes_delete=args.yes_delete,
            )
        return 0

    if dry_run:
        return _with_logging(config, "sync", _run_dry, finalizer=_finalize, mail_finalizer=_mail_finalize)

    print("Run mode: real run")
    prepare_lock_path(config, dry_run=False)
    print(f"Acquiring lock: {config.lock_file}")
    with FileLock(config.lock_file):
        return _with_logging(config, "sync", _run_locked, finalizer=_finalize, mail_finalizer=_mail_finalize)


def cmd_prune(args) -> int:
    config = load_config(args.config)
    dry_run = _resolve_dry_run(args, config)

    def _run_dry() -> int:
        print("Run mode: dry-run")
        print("Strict dry-run: no lock file and no destination deletion will be performed.")
        state = _load_config_state(config)
        source_timeshift_index = _refresh_state_metadata_from_timeshift(config, state, dry_run=True)
        prune(
            config,
            state,
            dry_run=True,
            yes_delete=False,
            source_timeshift_index=source_timeshift_index,
        )
        return 0

    def _run_locked() -> int:
        prepare_destination_helper_paths(config, dry_run=False)
        state = _load_config_state(config)
        source_timeshift_index = _refresh_state_metadata_from_timeshift(config, state, dry_run=False)
        prune(
            config,
            state,
            dry_run=False,
            yes_delete=args.yes_delete,
            source_timeshift_index=source_timeshift_index,
        )
        return 0

    if dry_run:
        return _with_logging(config, "prune", _run_dry)

    print("Run mode: real run")
    prepare_lock_path(config, dry_run=False)
    print(f"Acquiring lock: {config.lock_file}")
    with FileLock(config.lock_file):
        return _with_logging(config, "prune", _run_locked)


def cmd_restore(args) -> int:
    """Restore one snapshot or the complete post-common backup chain into Timeshift."""

    config = load_config(args.config)
    dry_run = _resolve_dry_run(args, config)

    def _run() -> int:
        restore_backups(
            config,
            snapshot_name=args.snapshot,
            restore_all=args.restore_all,
            dry_run=dry_run,
            danger_confirmed=args.i_understand_this_modifies_timeshift,
            allow_no_common_parent=args.allow_no_common_parent,
            allow_os_identity_mismatch=args.allow_os_identity_mismatch,
            create_pre_restore_snapshot=args.create_pre_restore_snapshot,
        )
        return 0

    if dry_run:
        print("Run mode: dry-run restore")
        print(f"Restore mode: {config.restore.mode}")
        return _with_logging(config, "restore", _run)

    print("Run mode: real restore")
    print(f"Restore mode: {config.restore.mode}")
    if not config.lock_file.parent.is_dir():
        raise RuntimeError(
            "Restore requires the configured local lock directory to already exist on the machine "
            f"running the command: {config.lock_file.parent}"
        )
    print(f"Acquiring local restore lock: {config.lock_file}")
    with FileLock(config.lock_file):
        return _with_logging(config, "restore", _run)


def cmd_create_manual(args) -> int:
    config = load_config(args.config)

    def _run() -> int:
        source = SourceRunner.from_config(config)
        if source.uses_ssh:
            source.test()
        else:
            print("Source mode: local; SSH setup/test skipped.")
        check_required_sync_paths(config, source, dry_run=False)
        confirm_source_identity_before_manual_snapshot(
            config,
            source,
            _load_config_state(config),
            load_source_index=lambda: source_snapshot_index(
                list_source_snapshots(config, source, include_btrfs_info=config.source.verify_subvolumes_at_discovery)
            ),
        )
        print()
        create_source_manual_snapshot(source, sudo=config.source.sudo, timeshift_command=config.source.timeshift_command, comment=args.comment)
        print("Requested source Timeshift on-demand snapshot.")
        return 0

    return _with_logging(config, "create-manual", _run)





def cmd_clear_state(args) -> int:
    """Guardedly remove the configured state_file with normal run logging."""

    config = load_config(args.config)
    dry_run = not args.run

    def _run() -> int:
        if dry_run:
            clear_state_file(config, dry_run=True, danger_confirmed=False)
            return 0

        # Acquire the existing app lock for real state clearing so sync/prune cannot
        # update state.json at the same time. This maintenance command deliberately
        # does not create destination/helper paths; it only touches configured
        # metadata files. If the lock directory is missing, FileLock raises a clear
        # error instead of creating backup folders as a side effect.
        print(f"Acquiring lock: {config.lock_file}")
        with FileLock(config.lock_file):
            clear_state_file(
                config,
                dry_run=False,
                danger_confirmed=args.i_understand_this_clears_state,
            )
        return 0

    return _with_logging(config, "clear-state", _run)


def cmd_delete_lock(args) -> int:
    """Guardedly remove the configured lock_file if it is stale, with logging."""

    config = load_config(args.config)
    dry_run = not args.run

    def _run() -> int:
        delete_lock_file(
            config,
            dry_run=dry_run,
            danger_confirmed=args.i_understand_this_deletes_lock,
        )
        return 0

    return _with_logging(config, "delete-lock", _run)


def cmd_destroy_leftovers(args) -> int:
    """Destroy configured leftovers with normal run logging enabled."""

    config = load_config(args.config)
    dry_run = not args.run
    delete_source = args.delete_source or args.delete_both
    delete_destination = args.delete_destination or args.delete_both
    selected_delete_roots: list[Path] = []
    if delete_source and config.source.cache_root:
        selected_delete_roots.append(Path(config.source.cache_root))
    if delete_destination:
        selected_delete_roots.append(Path(config.destination.target_root))
    log_dir = _safe_destroy_log_dir(config, selected_delete_roots)

    def _run() -> int:
        destroy_leftovers(
            config,
            delete_source=delete_source,
            delete_destination=delete_destination,
            dry_run=dry_run,
            danger_confirmed=args.i_understand_this_destroys_data,
        )
        return 0

    return _with_logging(config, "destroy-leftovers", _run, log_dir_override=log_dir)

def cmd_show_state(args) -> int:
    config = load_config(args.config)

    def _run() -> int:
        state = _load_config_state(config)
        if args.json:
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0
        snapshots = state.get("snapshots", {})
        if not snapshots:
            print("State is empty.")
            return 0
        print(f"{'SNAPSHOT':<22} {'TAGS':<8} SUBVOLUMES")
        for name in sorted(snapshots):
            item = snapshots[name]
            print(f"{name:<22} {''.join(item.get('tags', [])) or '-':<8} {','.join(sorted(item.get('subvolumes', {}).keys())) or '-'}")
        return 0

    return _with_logging(config, "show-state", _run)


TOP_LEVEL_HELP = f"""
Version: {__version__}

How to get complete help:
  ts-btrfs --help
  ts-btrfs COMMAND --help
  ts-btrfs --version
  ts-btrfs COMMAND --version

Every subcommand help page documents its flags, required combinations, config interaction,
and examples. All CLI flag requirements and combinations are documented in these help pages.

Run-mode rules:
  sync / prune / restore:
    --dry-run forces preview mode.
    --run forces real mode.
    If neither is supplied, config.default_dry_run decides.

  clear-state / delete-lock / destroy-leftovers:
    dry-run is the command default; --run is required for real changes.

Deletion / danger rules:
  sync --prune and prune:
    real deletion requires both real-run mode and --yes-delete.
  restore:
    real restore requires --run and --i-understand-this-modifies-timeshift,
    then typed confirmations may still be required.
  clear-state / delete-lock / destroy-leftovers:
    real execution requires --run plus that command's explicit danger flag,
    and guarded typed confirmations where documented by the command help.

Exit codes:
  0    success
  1    runtime/safety failure
  2    configuration/argument-style refusal such as init-config overwrite refusal
  3    another process holds the configured lock
  130  interrupted by user (Ctrl-C)

Typical diagnosis flow:
  ts-btrfs --version
  ts-btrfs test-source --config ./config.toml
  ts-btrfs list-source --config ./config.toml
  ts-btrfs sync --config ./config.toml --dry-run
  ts-btrfs sync --config ./config.toml --run --limit 1
"""


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser and complete command-specific flag help."""

    parser = argparse.ArgumentParser(
        prog="ts-btrfs",
        description=(
            f"TimeShift-BTRFS-Sync {__version__}\n\n"
            "Safely back up and restore Timeshift Btrfs snapshots locally or over SSH.\n"
            "Normal sync always writes destination.target_root on the machine running sync;\n"
            "restore direction is controlled separately by [restore].mode."
        ),
        epilog=TOP_LEVEL_HELP,
        formatter_class=CLI_FORMATTER,
    )
    add_version_arg(parser)
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
        metavar="COMMAND",
        description="Run 'ts-btrfs COMMAND --help' for the complete flags, dependencies, examples, and troubleshooting for that command.",
    )

    p = new_subparser(
        sub,
        "init-config",
        "write a complete commented TOML config",
        (
            "Write one packaged complete TOML profile. This command does not need --config.\n"
            "The generated file contains every supported configuration key with comments."
        ),
        cmd_init_config,
        epilog=(
            "Profiles:\n"
            "  sync              Normal local/SSH Timeshift source -> local backup profile.\n"
            "                    Restore mode defaults to local.\n"
            "  restore-pull      SSH backup repository -> local Timeshift restore profile.\n"
            "                    This is restore-oriented and normal sync refuses it.\n"
            "  remote-roundtrip  SSH Timeshift source -> local backup -> SSH Timeshift restore target.\n\n"
            "Examples:\n"
            "  ts-btrfs init-config --profile sync --path ./config.toml\n"
            "  ts-btrfs init-config --profile remote-roundtrip --path ./config.toml\n"
            "  ts-btrfs init-config --profile sync --path ./config.toml --force\n\n"
            "If the destination file already exists, init-config refuses to overwrite it unless --force is supplied."
        ),
    )
    p.add_argument(
        "--path",
        default="./ts-btrfs.toml",
        metavar="FILE",
        help="output TOML path; parent directories are created as needed; default: ./ts-btrfs.toml",
    )
    p.add_argument(
        "--profile",
        choices=("sync", "restore-pull", "remote-roundtrip"),
        default="sync",
        metavar="PROFILE",
        help=(
            "profile to write; default: sync.\n"
            "  sync             = normal local/SSH source backup profile\n"
            "  restore-pull     = SSH backup -> local Timeshift restore profile\n"
            "  remote-roundtrip = SSH Timeshift source -> local backup -> SSH-target restore profile"
        ),
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="overwrite FILE if it already exists; without this flag an existing file is left untouched and the command exits with code 2",
    )

    p = new_subparser(
        sub,
        "test-source",
        "test source endpoint and source sudo permissions",
        (
            "Test the configured source command endpoint without sending or deleting snapshots.\n"
            "SSH mode first verifies the SSH connection; local mode skips SSH. The command then\n"
            "runs Timeshift --list and Btrfs --version through the configured source sudo/commands."
        ),
        cmd_test_source,
        epilog=(
            "Example:\n"
            "  ts-btrfs test-source --config ./config.toml\n\n"
            "If it fails, the failing SSH/Timeshift/Btrfs command is the item to repair. This command does not test destination capacity or perform a backup."
        ),
    )
    add_config_arg(p)

    p = new_subparser(
        sub,
        "list-source",
        "list source Timeshift snapshots",
        (
            "List Timeshift snapshots found on the configured source.\n"
            "Fast mode is the default: Timeshift metadata is parsed and expected payload paths are constructed.\n"
            "Add --verify-btrfs when you need slower per-payload Btrfs verification."
        ),
        cmd_list_source,
        epilog=(
            "Examples:\n"
            "  ts-btrfs list-source --config ./config.toml\n"
            "  ts-btrfs list-source --config ./config.toml --verify-btrfs\n\n"
            "Use --verify-btrfs when diagnosing a wrong snapshot_root, missing @/@home payload, or unexpected Btrfs layout. Omit it for normal quick inventory."
        ),
    )
    add_config_arg(p)
    p.add_argument(
        "--verify-btrfs",
        action="store_true",
        help="slow verification mode: probe every configured source payload with Btrfs instead of only trusting the fast Timeshift inventory/expected paths",
    )

    p = new_subparser(
        sub,
        "sync",
        "pull missing snapshots",
        (
            "Back up Timeshift snapshot payloads from the configured source into the local destination.target_root.\n"
            "source.mode selects local versus SSH source. Normal sync never writes a remote backup destination.\n"
            "Without --run or --dry-run, config.default_dry_run selects preview versus real execution."
        ),
        cmd_sync,
        epilog=(
            "Flag relationships:\n"
            "  --dry-run and --run are mutually exclusive. If neither is used, default_dry_run from FILE decides.\n"
            "  --snapshot DATE restricts discovery/transfer to that Timeshift timestamp and skips automatic manual-snapshot creation for other dates.\n"
            "  --resend bypasses only the state.json 'already synced' skip; it does not bypass UUID lineage, existing-path, topology, or receive safety checks.\n"
            "  --prune enables retention after sync even when prune_after_sync=false. prune_after_sync=true enables it without --prune.\n"
            "  --yes-delete authorizes deletion only when pruning is actually requested and the command is in real-run mode.\n\n"
            "Examples:\n"
            "  ts-btrfs sync --config ./config.toml --dry-run\n"
            "  ts-btrfs sync --config ./config.toml --run --limit 1\n"
            "  ts-btrfs sync --config ./config.toml --snapshot 2026-08-14_16-33-59 --run\n"
            "  ts-btrfs sync --config ./config.toml --run --prune --yes-delete\n\n"
            "Troubleshooting:\n"
            "  If a pull-restore profile is refused, normal remote-source backup needs source.mode=ssh and a local destination; do not use restore.mode=ssh for the same sync profile.\n"
            "  If transfer-size preflight refuses space, adjust destination capacity or the [stream] transfer-size settings in FILE; --resend does not override capacity safety."
        ),
    )
    add_config_arg(p)
    add_run_mode_args(
        p,
        dry_run_help=(
            "force strict preview mode even when default_dry_run=false: no destination preparation, lock creation, receive, state write, automatic manual snapshot, or deletion"
        ),
        run_help=(
            "force real backup mode even when default_dry_run=true: prepare paths/lock and perform send/receive; pruning still cannot delete without --yes-delete"
        ),
    )
    p.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="transfer at most N individual configured subvolume payloads in this run (for example one @ or @home); useful for a first real test; does not mean N snapshot dates",
    )
    p.add_argument(
        "--snapshot",
        metavar="DATE",
        help="consider only this Timeshift timestamp (for example 2026-08-14_16-33-59); useful for a targeted retry/test; does not bypass normal safety checks",
    )
    p.add_argument(
        "--resend",
        action="store_true",
        help="do not skip a payload merely because state.json marks it complete; all UUID/lineage/path/conflict checks still apply, so this is not a force-overwrite option",
    )
    p.add_argument(
        "--prune",
        action="store_true",
        help="run retention after sync regardless of prune_after_sync=false; if prune_after_sync=true, pruning runs even without this flag; actual deletion also requires real-run mode and --yes-delete",
    )
    add_yes_delete_arg(
        p,
        "authorize actual retention deletion during a real sync when --prune or prune_after_sync=true requests pruning; has no force/override effect on non-retention safety checks",
    )

    p = new_subparser(
        sub,
        "prune",
        "apply retention rules",
        (
            "Apply retention without transferring new snapshots. Destination retention follows [retention].\n"
            "App-created tag O snapshots can also be retired from Timeshift only when they still match\n"
            "manual_snapshot.marker and their required backup payloads are proven complete."
        ),
        cmd_prune,
        epilog=(
            "Flag relationships:\n"
            "  --dry-run and --run are mutually exclusive. If neither is supplied, config.default_dry_run decides.\n"
            "  A real run may calculate a delete plan, but no retention delete is allowed without --yes-delete.\n"
            "  --yes-delete does not bypass protected snapshots, keep_latest/common-parent rules, backup proof, or Timeshift marker checks.\n\n"
            "Examples:\n"
            "  ts-btrfs prune --config ./config.toml --dry-run\n"
            "  ts-btrfs prune --config ./config.toml --run --yes-delete\n\n"
            "If the command says 'Refusing to delete without --yes-delete', review the printed plan and rerun with both --run and --yes-delete only if the plan is correct."
        ),
    )
    add_config_arg(p)
    add_run_mode_args(
        p,
        dry_run_help="force preview mode: refresh/read metadata and show retention decisions, but do not create a lock, save state changes, or delete anything",
        run_help="force real prune mode: acquire the lock and apply retention; actual deletion still requires --yes-delete",
    )
    add_yes_delete_arg(
        p,
        "explicit authorization for real retention deletes; required in addition to real-run mode whenever the plan contains destination/source deletions",
    )

    p = new_subparser(
        sub,
        "restore",
        "restore one backup or a complete chain into Timeshift",
        (
            "Restore backup payloads into source.snapshot_root in Timeshift's native layout.\n"
            "[restore].mode selects transport: local = local backup -> local Timeshift; ssh = SSH backup -> local Timeshift;\n"
            "ssh-target = local backup -> SSH Timeshift. source.mode does not select restore direction.\n"
            "Exactly one of --snapshot DATE or --all is required."
        ),
        cmd_restore,
        epilog=(
            "Flag relationships and safety:\n"
            "  --snapshot DATE performs one full restore and is mutually exclusive with --all.\n"
            "  --all restores the proven chain newer than the newest safely confirmed shared timestamp.\n"
            "  --allow-no-common-parent is valid only with --all and is needed only when --all cannot prove a common timestamp; real execution adds stronger typed confirmations.\n"
            "  --allow-os-identity-mismatch is needed only when identity cannot be proven; real execution requires an additional exact typed acknowledgement.\n"
            "  --create-pre-restore-snapshot creates one tag O safety snapshot on the Timeshift restore target, never on the backup repository.\n"
            "  --run requires --i-understand-this-modifies-timeshift; the command still asks for the documented typed retention-risk confirmation before receive.\n"
            "  --dry-run and --run are mutually exclusive; if neither is supplied, config.default_dry_run decides.\n\n"
            "Examples:\n"
            "  ts-btrfs restore --config ./config.toml --snapshot 2026-08-14_16-33-59 --dry-run\n"
            "  ts-btrfs restore --config ./config.toml --all --dry-run\n"
            "  ts-btrfs restore --config ./config.toml --all --run --i-understand-this-modifies-timeshift\n"
            "  ts-btrfs restore --config ./config.toml --all --allow-no-common-parent --allow-os-identity-mismatch --run --i-understand-this-modifies-timeshift\n\n"
            "When a guard refuses a real restore, read the refusal literally: add a danger override only after independently verifying the condition named by that refusal."
        ),
    )
    add_config_arg(p)
    add_run_mode_args(
        p,
        dry_run_help="force restore preview: validate physical overlap, Btrfs/state/cache lineage, same-date info.json identity fallback, target collisions, and the receive plan without modifying Timeshift",
        run_help="force real restore: acquire the local configured lock and execute receive/commit work; also requires --i-understand-this-modifies-timeshift and typed confirmations",
    )
    restore_selection = p.add_mutually_exclusive_group(required=True)
    restore_selection.add_argument(
        "--snapshot",
        metavar="DATE",
        help="restore exactly one backup timestamp with a full receive; mutually exclusive with --all; example DATE: 2026-08-14_16-33-59",
    )
    restore_selection.add_argument(
        "--all",
        dest="restore_all",
        action="store_true",
        help="restore the complete safe chain newer than the newest confirmed timestamp physically present in both repositories; mutually exclusive with --snapshot",
    )
    p.add_argument(
        "--create-pre-restore-snapshot",
        action="store_true",
        help="before any receive in a real run, create and verify one on-demand/tag O Timeshift safety snapshot on the restore target; dry-run reports the action; never snapshots the backup repository",
    )
    p.add_argument(
        "--allow-no-common-parent",
        action="store_true",
        help="danger override valid only with --all: permit a full oldest-to-newest chain when no shared timestamp can be proven; real execution requires stronger typed confirmations and does not bypass OS-identity checks",
    )
    p.add_argument(
        "--allow-os-identity-mismatch",
        action="store_true",
        help="danger override when backup identity cannot be matched to the current Timeshift repository and exact Btrfs proof does not resolve it; real execution requires an additional exact typed acknowledgement",
    )
    p.add_argument(
        "--i-understand-this-modifies-timeshift",
        action="store_true",
        help="mandatory acknowledgement for --run; permits direct Timeshift modification but does not replace the later typed retention-risk confirmation or any no-common-parent/OS-identity confirmations",
    )

    p = new_subparser(
        sub,
        "create-manual",
        "create source Timeshift tag O snapshot",
        (
            "Ask the configured source Timeshift endpoint to create one on-demand snapshot (tag O).\n"
            "Before creation the command validates source/destination paths and, when backups already exist,\n"
            "requires UUID-confirmed source/destination continuity so a stray manual snapshot is not created on the wrong source."
        ),
        cmd_create_manual,
        epilog=(
            "Example:\n"
            "  ts-btrfs create-manual --config ./config.toml --comment 'before kernel upgrade'\n\n"
            "This command is always real; it has no --dry-run/--run pair. The supplied comment is passed to Timeshift. Automatic app-created snapshot recognition during retention additionally depends on your configured manual_snapshot.marker."
        ),
    )
    add_config_arg(p)
    p.add_argument(
        "--comment",
        required=True,
        metavar="TEXT",
        help="required Timeshift comment passed to `timeshift --create --comments`; quote TEXT when it contains spaces; this does not automatically append manual_snapshot.marker",
    )

    p = new_subparser(
        sub,
        "destroy-leftovers",
        "destroy app-created leftovers",
        (
            "Permanently destroy selected app-owned Btrfs trees. This ignores state.json and retention rules.\n"
            "source.snapshot_root is never a target. Dry-run is the default for this maintenance command."
        ),
        cmd_destroy_leftovers,
        epilog=(
            "Selection (exactly one is required):\n"
            "  --delete-source       source.cache_root only\n"
            "  --delete-destination  destination.target_root only\n"
            "  --delete-both         both of the above; still never source.snapshot_root\n\n"
            "Real deletion requires ALL of: a delete selection, --run, --i-understand-this-destroys-data, and the command's typed confirmations.\n"
            "--dry-run is optional because preview is already the default when --run is absent. Ordinary non-empty roots are refused; the app does not fall back to rm -rf.\n\n"
            "Examples:\n"
            "  ts-btrfs destroy-leftovers --config ./config.toml --delete-destination --dry-run\n"
            "  ts-btrfs destroy-leftovers --config ./config.toml --delete-both --run --i-understand-this-destroys-data"
        ),
    )
    add_config_arg(p)
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--delete-source",
        action="store_true",
        help="select source.cache_root for recursive Btrfs-subvolume cleanup; never selects or deletes source.snapshot_root",
    )
    target.add_argument(
        "--delete-destination",
        action="store_true",
        help="select destination.target_root for destructive cleanup, including its received snapshots and app metadata; does not select source.cache_root",
    )
    target.add_argument(
        "--delete-both",
        action="store_true",
        help="select both source.cache_root and destination.target_root for cleanup; equivalent target set to the two individual selections together; source.snapshot_root remains protected",
    )
    add_run_mode_args(
        p,
        dry_run_help="force/express preview mode; show the selected destructive tree plan and validation results without deleting anything (also the default when --run is absent)",
        run_help="perform the selected destructive cleanup; also requires --i-understand-this-destroys-data and the command's typed confirmations",
    )
    p.add_argument(
        "--i-understand-this-destroys-data",
        action="store_true",
        help="mandatory acknowledgement for --run; confirms that selected configured app-owned trees will be permanently destroyed; does not bypass path/layout safety checks or typed confirmations",
    )

    p = new_subparser(
        sub,
        "clear-state",
        "remove configured state.json with guardrails",
        (
            "Remove only the configured state_file; snapshots are not deleted. Dry-run is the default.\n"
            "A real run acquires the existing app lock so state cannot be cleared while sync/prune is active.\n"
            "After clearing, later sync can recover only entries it can prove again from exact live Btrfs UUID relationships."
        ),
        cmd_clear_state,
        epilog=(
            "Real removal requires BOTH --run and --i-understand-this-clears-state, followed by guarded typed confirmations.\n"
            "--dry-run is optional because preview is already the default when --run is absent. The command does not create missing destination/helper folders merely to clear state.\n\n"
            "Examples:\n"
            "  ts-btrfs clear-state --config ./config.toml --dry-run\n"
            "  ts-btrfs clear-state --config ./config.toml --run --i-understand-this-clears-state"
        ),
    )
    add_config_arg(p)
    add_run_mode_args(
        p,
        dry_run_help="force/express preview mode; show the exact configured state_file that would be removed without changing it (also the default when --run is absent)",
        run_help="remove the configured state_file after acquiring the existing app lock; also requires --i-understand-this-clears-state and typed confirmations",
    )
    p.add_argument(
        "--i-understand-this-clears-state",
        action="store_true",
        help="mandatory acknowledgement for --run; confirms that removing state may break incremental continuity unless later recovery can prove exact UUID matches; does not delete any snapshot",
    )

    p = new_subparser(
        sub,
        "delete-lock",
        "remove stale configured lock file with guardrails",
        (
            "Remove only the configured lock_file when it is stale. Dry-run is the default.\n"
            "This command is not a way to stop or bypass a running ts-btrfs process; if the lock is held, stop the process normally instead."
        ),
        cmd_delete_lock,
        epilog=(
            "Real removal requires BOTH --run and --i-understand-this-deletes-lock, followed by guarded typed confirmations.\n"
            "--dry-run is optional because preview is already the default when --run is absent.\n\n"
            "Examples:\n"
            "  ts-btrfs delete-lock --config ./config.toml --dry-run\n"
            "  ts-btrfs delete-lock --config ./config.toml --run --i-understand-this-deletes-lock"
        ),
    )
    add_config_arg(p)
    add_run_mode_args(
        p,
        dry_run_help="force/express preview mode; show the exact configured lock_file that would be removed without changing it (also the default when --run is absent)",
        run_help="remove the configured lock_file only if it is stale/not held; also requires --i-understand-this-deletes-lock and typed confirmations",
    )
    p.add_argument(
        "--i-understand-this-deletes-lock",
        action="store_true",
        help="mandatory acknowledgement for --run; confirms that deleting a stale file must never be used to bypass a currently running process or held lock",
    )

    p = new_subparser(
        sub,
        "show-state",
        "show local sync state",
        (
            "Read the configured local state.json that records completed payloads, source/send UUID identity,\n"
            "destination Received UUID relationships, and incremental-parent metadata. This command does not modify state."
        ),
        cmd_show_state,
        epilog=(
            "Examples:\n"
            "  ts-btrfs show-state --config ./config.toml\n"
            "  ts-btrfs show-state --config ./config.toml --json\n\n"
            "Use --json when you need the complete stored structure for diagnosis or automation. The default table is a compact human-readable summary."
        ),
    )
    add_config_arg(p)
    p.add_argument(
        "--json",
        action="store_true",
        help="print the complete parsed state.json as formatted JSON instead of the compact snapshot/tag/subvolume table; useful for UUID/parent-path diagnosis and machine parsing",
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    except BlockingIOError:
        print("Another ts-btrfs process is already running for this config.", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
