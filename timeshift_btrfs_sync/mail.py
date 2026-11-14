"""Optional email notifications for timeshift-btrfs-sync.

Email formatting is shared by Python SMTP and the optional local mailx utility.
No Python dependency beyond the standard library is required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Iterable
import json
import mimetypes
import re
import shutil
import smtplib
import subprocess


@dataclass(slots=True)
class MailConfig:
    """SMTP or local mailx settings for optional email notifications.

    username/password are optional. If username is blank, the SMTP connection
    is made without login. password_file is supported so passwords do not have
    to be stored directly in config.toml. Use either password or password_file,
    not both.

    attach_logs attaches the run's split log files when file logging is enabled:
    .log, .err, .btrfs, .mbuffer, and .succes. Empty files are not attached.
    max_attachment_bytes can optionally prevent very large verbose logs from
    being attached. Set it to 0 for no cap.
    """

    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_ssl: bool = False
    starttls: bool = True
    username: str | None = None
    password: str | None = None
    password_file: str | None = None
    from_addr: str = ""
    to_addrs: list[str] = field(default_factory=list)
    subject_prefix: str = "[timeshift-btrfs-sync]"
    timeout: int = 10
    notify_on_success: bool = True
    notify_on_failure: bool = True
    include_json: bool = True
    attach_logs: bool = True
    max_attachment_bytes: int = 0
    use_mailx_util: bool = False
    to_addr: str = ""

    def recipients(self) -> list[str]:
        """Use an explicit single recipient, otherwise preserve the existing recipient list."""
        return [self.to_addr] if self.to_addr else list(self.to_addrs)

    def resolved_password(self) -> str | None:
        """Return password from config value or password_file."""

        if self.password_file:
            return Path(self.password_file).expanduser().read_text(encoding="utf-8").strip()
        return self.password



def _subject(config: MailConfig, payload: dict[str, Any]) -> str:
    """Create a short readable subject line."""

    state = "SUCCESS" if payload.get("success") else "FAILURE"
    job = payload.get("name") or payload.get("job") or "timeshift-btrfs-sync"
    prefix = config.subject_prefix.strip()
    if prefix:
        return f"{prefix} {state}: {job}"
    return f"{state}: {job}"


def _body(config: MailConfig, payload: dict[str, Any], *, attached: list[Path], skipped: list[str]) -> str:
    """Create a fallback plain-text email body from the status payload."""

    lines = [
        f"timeshift-btrfs-sync {payload.get('state', 'unknown')}",
        "",
        f"Job:       {payload.get('name', payload.get('job', 'timeshift-btrfs-sync'))}",
        f"Command:   {payload.get('command', 'unknown')}",
        f"Exit code: {payload.get('exit_code', 'unknown')}",
        f"Host:      {payload.get('host', 'unknown')}",
        f"Time UTC:  {payload.get('timestamp', '')}",
        f"Version:   {payload.get('version', '')}",
    ]
    if payload.get("error"):
        lines += ["", "Error:", str(payload.get("error"))]
    if payload.get("stderr"):
        lines += ["", "Last stderr:", str(payload.get("stderr"))]
    if attached:
        lines += ["", "Attached log files:"]
        lines += [f"- {path.name}" for path in attached]
    if skipped:
        lines += ["", "Log files not attached:"]
        lines += [f"- {item}" for item in skipped]
    if config.include_json:
        lines += ["", "JSON payload:", json.dumps(payload, indent=2, sort_keys=True)]
    return "\n".join(lines).rstrip() + "\n"



def _success_body_from_paths(paths: Iterable[str | Path] | None) -> str | None:
    """Return the text content of the non-empty .succes file, if present."""

    if not paths:
        return None
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if path.suffix != ".succes":
            continue
        try:
            if path.is_file() and path.stat().st_size > 0:
                text = path.read_text(encoding="utf-8", errors="replace")
                return text if text.endswith("\n") else text + "\n"
        except OSError:
            continue
    return None

def _filter_attachments(config: MailConfig, paths: Iterable[str | Path] | None) -> tuple[list[Path], list[str]]:
    """Return existing attachment paths and human-readable skipped reasons."""

    attached: list[Path] = []
    skipped: list[str] = []
    if not config.attach_logs or not paths:
        return attached, skipped

    seen: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if path in seen:
            continue
        seen.add(path)
        if not path.exists():
            continue
        if not path.is_file():
            skipped.append(f"{path.name}: not a regular file")
            continue
        size = path.stat().st_size
        if size == 0:
            skipped.append(f"{path.name}: empty file, not attached")
            continue
        if config.max_attachment_bytes > 0 and size > config.max_attachment_bytes:
            skipped.append(f"{path.name}: {size} bytes exceeds mail.max_attachment_bytes={config.max_attachment_bytes}")
            continue
        attached.append(path)
    return attached, skipped


def _attach_file(msg: EmailMessage, path: Path) -> None:
    """Attach one file to an EmailMessage."""

    content_type, _encoding = mimetypes.guess_type(path.name)
    if content_type is None:
        content_type = "text/plain"
    maintype, subtype = content_type.split("/", 1)
    data = path.read_bytes()
    msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)


def validate_mailx_address(address: str, label: str) -> None:
    """Accept plain mailboxes/local users, excluding mailx file, pipe and option syntax."""
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.+%-]*(?:@[A-Za-z0-9][A-Za-z0-9.-]*)?", address):
        raise ValueError(f"{label} must be a plain email address or local username in mailx mode; display names, lists, file/pipe destinations and options are not supported")


def _mailx_flavor(command: str, timeout: int) -> str:
    """Identify attachment syntax without sending a message or opening a mailbox."""
    result = subprocess.run([command, "--version"], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=min(timeout, 5), check=False)
    version = (result.stdout + result.stderr).lower()
    if result.returncode == 0 and "gnu mailutils" in version:
        return "gnu"
    if result.returncode == 0 and "s-nail" in version:
        return "s-nail"
    return "posix"


def _send_mailx(config: MailConfig, subject: str, body: str, attached: list[Path]) -> None:
    """Submit one notification through local mailx/mail; never retry via another transport."""
    recipients = config.recipients()
    for address in recipients:
        validate_mailx_address(address, "mail recipient")
    if config.from_addr:
        validate_mailx_address(config.from_addr, "mail.from_addr")
    if any(ord(char) < 32 or ord(char) == 127 for char in subject):
        raise ValueError("mail subject must not contain control characters")
    command = shutil.which("mailx") or shutil.which("mail") or shutil.which("s-nail")
    if command is None:
        raise RuntimeError("mail.use_mailx_util=true requires mailx/mail (GNU Mailutils or s-nail for attachments) on PATH and a configured local mail system such as Postfix")
    try:
        flavor = _mailx_flavor(command, config.timeout)
        args = [command, "-s", subject]
        if config.from_addr:
            args += ["-r", config.from_addr]
        if flavor == "s-nail":
            # Wait for the MTA's result instead of silently launching it asynchronously.
            args += ["-S", "sendwait"]
        if attached and flavor == "posix":
            raise RuntimeError("This mailx variant has no supported attachment syntax; install GNU Mailutils or s-nail, or set mail.attach_logs=false. No message was submitted")
        for path in attached:
            # Absolute paths cannot become options; GNU -a is a header, not an attachment.
            args += ["--attach" if flavor == "gnu" else "-a", str(path.absolute())]
        # Every recipient is validated above; in s-nail '--' starts MTA options.
        args += recipients
        result = subprocess.run(args, input=body, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=config.timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"mailx timed out (limit {config.timeout}s per submission, at most 5s for detection); delivery is unknown and was not retried") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not run local mailx utility: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip()[-2000:] or "no diagnostic output"
        raise RuntimeError(f"mailx exited {result.returncode}: {detail}; delivery was not retried")


def send_status(config: MailConfig, payload: dict[str, Any], *, attachments: Iterable[str | Path] | None = None) -> None:
    """Send one optional status email through the selected SMTP or mailx transport.

    Sending errors are raised to the caller. CLI code catches them and prints a
    warning because notification failure should not hide the real backup exit
    code.
    """

    if not config.enabled:
        return
    if not config.use_mailx_util and not config.smtp_host:
        raise RuntimeError("mail.smtp_host is required when mail.enabled = true")
    if not config.use_mailx_util and not config.from_addr:
        raise RuntimeError("mail.from_addr is required when mail.enabled = true")
    if not config.recipients():
        raise RuntimeError("mail.to_addrs must contain at least one address or mail.to_addr must be set when mail.enabled = true")

    attachments = list(attachments) if attachments is not None else None
    success_body = _success_body_from_paths(attachments)
    attached, skipped = _filter_attachments(config, attachments)
    subject = _subject(config, payload)
    body = success_body or _body(config, payload, attached=attached, skipped=skipped)
    if config.use_mailx_util:
        _send_mailx(config, subject, body, attached)
        return

    msg = EmailMessage()
    msg["From"] = config.from_addr
    msg["To"] = ", ".join(config.recipients())
    msg["Subject"] = subject
    msg.set_content(body)

    for path in attached:
        _attach_file(msg, path)

    if config.smtp_ssl:
        smtp_cls = smtplib.SMTP_SSL
    else:
        smtp_cls = smtplib.SMTP

    with smtp_cls(config.smtp_host, config.smtp_port, timeout=config.timeout) as smtp:
        if config.starttls and not config.smtp_ssl:
            smtp.starttls()
        if config.username:
            smtp.login(config.username, config.resolved_password() or "")
        smtp.send_message(msg)
