"""Btrfs send-stream size measurement and destination-capacity checks.

Exact mode generates the same full or incremental Btrfs send stream that the
real transfer will use, but counts it on the source endpoint instead of sending
it over the network or storing it. Estimate mode uses ``btrfs send --no-data``
with the same selected parent, validates it with ``btrfs receive --dump`` on
the source endpoint, and reduces the dump there to one ASCII changed-byte total.
File payload is not read or transferred and the full dump is never captured by Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import shlex

from .btrfs_ops import BtrfsOps

_SIZE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([KMGTPE]?)(?:I?B)?\s*$", re.IGNORECASE)
_SEND_RC_MARKER = "TSBTRFS_SEND_SIZE_RC="
_ESTIMATE_SEND_RC_MARKER = "TSBTRFS_ESTIMATE_SEND_RC="
_ESTIMATE_DUMP_RC_MARKER = "TSBTRFS_ESTIMATE_DUMP_RC="
_ESTIMATE_BYTES_MARKER = "TSBTRFS_ESTIMATE_CHANGED_BYTES="


class TransferSizeError(RuntimeError):
    """Raised when send-size measurement or destination-space probing fails."""


@dataclass(slots=True, frozen=True)
class TransferSizeMeasurement:
    """One measured or estimated Btrfs send-stream size."""

    size_bytes: int
    mode: str
    basis: str


def parse_size_bytes(value: str) -> int:
    """Parse a binary K/M/G/T/P/E size string into bytes.

    Bare numbers are bytes. ``1G`` and ``1GiB`` both mean 1 GiB (1024**3),
    matching the binary size convention used by Btrfs tools.
    """

    match = _SIZE_RE.fullmatch(str(value))
    if match is None:
        raise ValueError(
            "size must be a number optionally followed by K, M, G, T, P, or E "
            "(for example '1G' or '512M')"
        )
    try:
        number = Decimal(match.group(1))
    except InvalidOperation as exc:  # pragma: no cover - regex already constrains this
        raise ValueError(f"invalid size: {value}") from exc
    suffix = match.group(2).upper()
    power = "KMGTPE".find(suffix) + 1 if suffix else 0
    result = number * (Decimal(1024) ** power)
    if result < 0 or result != result.to_integral_value():
        raise ValueError(f"size does not resolve to a whole number of bytes: {value}")
    return int(result)


def format_bytes(value: int) -> str:
    """Format bytes as a compact IEC value plus the exact byte count."""

    value = int(value)
    if value < 1024:
        return f"{value} B"
    units = ("KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    amount = float(value)
    for unit in units:
        amount /= 1024.0
        if amount < 1024.0 or unit == units[-1]:
            return f"{amount:.2f} {unit} ({value} bytes)"
    return f"{value} B"


def parse_btrfs_usage_free_bytes(output: str) -> int:
    """Return the conservative ``Free (estimated)`` value from raw Btrfs usage."""

    match = re.search(
        r"^\s*Free \(estimated\):\s*(\d+)\s*(?:\(min:\s*(\d+)\s*\))?",
        output,
        re.MULTILINE,
    )
    if match is None:
        raise TransferSizeError("could not parse 'Free (estimated)' from `btrfs filesystem usage -b`")
    estimate = int(match.group(1))
    minimum = int(match.group(2)) if match.group(2) is not None else None
    return minimum if minimum is not None else estimate


def parse_estimate_changed_bytes(output: str) -> int:
    """Parse the source-side ASCII estimate summary into bytes.

    Estimate mode deliberately reduces the potentially huge ``btrfs receive
    --dump`` output on the source endpoint. Only this ASCII marker is returned
    through SSH/local command capture, avoiding binary/text decoding hazards and
    large in-memory dump capture.
    """

    matches = re.findall(
        rf"^{re.escape(_ESTIMATE_BYTES_MARKER)}(\d+)\s*$",
        output,
        re.MULTILINE,
    )
    if not matches:
        raise TransferSizeError("metadata-only send estimate returned no changed-byte summary marker")
    return int(matches[-1])


def exact_send_stream_size(
    source_btrfs: BtrfsOps,
    current_path: str,
    *,
    parent_path: str | None = None,
    compressed_data: bool = False,
    proto: int | None = None,
) -> TransferSizeMeasurement:
    """Generate and count the real send stream entirely on the source endpoint.

    The Btrfs stream is piped into ``wc -c`` on the same endpoint. Only the
    decimal byte count returns through SSH. A producer-status marker is emitted
    on stderr so POSIX shell pipeline semantics cannot hide a failed
    ``btrfs send`` behind a successful ``wc``.
    """

    send_argv = source_btrfs.send_argv(
        current_path,
        parent_path=parent_path,
        compressed_data=compressed_data,
        proto=proto,
        verbose=False,
    )
    send_text = shlex.join(send_argv)
    script = (
        "{ "
        + send_text
        + "; tsbtrfs_send_rc=$?; "
        + f"printf '{_SEND_RC_MARKER}%s\\n' \"$tsbtrfs_send_rc\" >&2; "
        + "} | wc -c"
    )
    result = source_btrfs.endpoint.run_shell(
        script,
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )

    markers = re.findall(rf"^{re.escape(_SEND_RC_MARKER)}(\d+)\s*$", result.stderr, re.MULTILINE)
    if not markers:
        detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
        raise TransferSizeError(f"exact send-size measurement returned no producer status marker: {detail}")
    send_returncode = int(markers[-1])
    cleaned_stderr = re.sub(
        rf"^{re.escape(_SEND_RC_MARKER)}\d+\s*$",
        "",
        result.stderr,
        flags=re.MULTILINE,
    ).strip()
    if send_returncode != 0:
        detail = cleaned_stderr or f"btrfs send return code {send_returncode}"
        raise TransferSizeError(f"exact send-size measurement failed: {detail}")
    if result.returncode != 0:
        detail = cleaned_stderr or result.stdout.strip() or f"return code {result.returncode}"
        raise TransferSizeError(f"send-stream byte counter failed: {detail}")
    try:
        size_bytes = int(result.stdout.strip())
    except ValueError as exc:
        raise TransferSizeError(
            f"send-stream byte counter returned an invalid value: {result.stdout.strip()!r}"
        ) from exc
    if size_bytes < 0:
        raise TransferSizeError("send-stream byte counter returned a negative size")
    return TransferSizeMeasurement(
        size_bytes=size_bytes,
        mode="exact",
        basis="real Btrfs send stream generated and counted on the source endpoint",
    )


def estimated_send_stream_size(
    source_btrfs: BtrfsOps,
    current_path: str,
    *,
    parent_path: str | None = None,
    compressed_data: bool = False,
    proto: int | None = None,
) -> TransferSizeMeasurement:
    """Return a fast parent-specific changed-data estimate without file payload.

    ``btrfs send --no-data`` performs the same full/incremental metadata walk,
    including the selected ``-p`` parent, but replaces changed file payload with
    ``UPDATE_EXTENT`` records. ``btrfs receive --dump`` validates and prints that
    metadata-only stream. The dump is reduced by source-side POSIX ``awk`` under
    ``LC_ALL=C`` so Python receives only an ASCII byte total and stage-status
    markers instead of capturing the complete dump text.
    """

    send_argv = source_btrfs.send_argv(
        current_path,
        parent_path=parent_path,
        compressed_data=compressed_data,
        proto=proto,
        verbose=False,
    )
    # Add --no-data immediately after the send subcommand. This preserves all
    # real-send protocol/parent/compressed-data choices while suppressing file
    # payload from the measurement stream.
    try:
        send_index = send_argv.index("send")
    except ValueError as exc:  # defensive: BtrfsOps owns this argv shape
        raise TransferSizeError("could not construct metadata-only btrfs send command") from exc
    send_argv.insert(send_index + 1, "--no-data")
    send_text = shlex.join(send_argv)
    dump_text = shlex.join(source_btrfs.argv(["receive", "--dump"]))

    # btrfs receive --dump can be very large on change-heavy snapshots. Keep it
    # entirely on the source endpoint and reduce it as a byte-oriented C-locale
    # stream. This also avoids asking Python's generic UTF-8 command runner to
    # decode arbitrary bytes from a real-world dump path.
    awk_program = (
        "BEGIN { total=0; parse_error=0 } "
        "/^[[:space:]]*update_extent([[:space:]]|$)/ { "
        "found=0; "
        "for (i=1; i<=NF; i++) { "
        "token=$i; gsub(/[,;]/, \"\", token); "
        "if (token ~ /^(size|len)=[0-9]+$/) { "
        "split(token, parts, \"=\"); total += parts[2]; found=1; break "
        "} "
        "} "
        "if (!found) { parse_error=1; "
        "print \"TSBTRFS_ESTIMATE_PARSE_ERROR=unparseable_update_extent\" > \"/dev/stderr\"; exit 42 } "
        "} "
        f"END {{ if (!parse_error) printf \"{_ESTIMATE_BYTES_MARKER}%.0f\\n\", total }}"
    )
    script = (
        "{ "
        + send_text
        + "; tsbtrfs_send_rc=$?; "
        + f"printf '{_ESTIMATE_SEND_RC_MARKER}%s\\n' \"$tsbtrfs_send_rc\" >&2; "
        + "} | { LC_ALL=C "
        + dump_text
        + "; tsbtrfs_dump_rc=$?; "
        + f"printf '{_ESTIMATE_DUMP_RC_MARKER}%s\\n' \"$tsbtrfs_dump_rc\" >&2; "
        + "} | LC_ALL=C awk "
        + shlex.quote(awk_program)
    )
    result = source_btrfs.endpoint.run_shell(
        script,
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )

    send_markers = re.findall(
        rf"^{re.escape(_ESTIMATE_SEND_RC_MARKER)}(\d+)\s*$",
        result.stderr,
        re.MULTILINE,
    )
    dump_markers = re.findall(
        rf"^{re.escape(_ESTIMATE_DUMP_RC_MARKER)}(\d+)\s*$",
        result.stderr,
        re.MULTILINE,
    )
    cleaned_stderr = re.sub(
        rf"^(?:{re.escape(_ESTIMATE_SEND_RC_MARKER)}|{re.escape(_ESTIMATE_DUMP_RC_MARKER)})\d+\s*$",
        "",
        result.stderr,
        flags=re.MULTILINE,
    ).strip()
    if not send_markers:
        detail = cleaned_stderr or result.stdout.strip() or f"return code {result.returncode}"
        raise TransferSizeError(f"metadata-only send estimate returned no producer status marker: {detail}")
    if not dump_markers:
        detail = cleaned_stderr or result.stdout.strip() or f"return code {result.returncode}"
        raise TransferSizeError(f"metadata-only send estimate returned no dump status marker: {detail}")

    send_returncode = int(send_markers[-1])
    dump_returncode = int(dump_markers[-1])
    if send_returncode != 0:
        detail = cleaned_stderr or f"btrfs send return code {send_returncode}"
        raise TransferSizeError(f"metadata-only send estimate failed: {detail}")
    if dump_returncode != 0:
        detail = cleaned_stderr or f"btrfs receive --dump return code {dump_returncode}"
        raise TransferSizeError(f"metadata-only send-stream dump failed: {detail}")
    if result.returncode != 0:
        detail = cleaned_stderr or result.stdout.strip() or f"return code {result.returncode}"
        raise TransferSizeError(f"metadata-only changed-extent summarizer failed: {detail}")

    changed_bytes = parse_estimate_changed_bytes(result.stdout)
    return TransferSizeMeasurement(
        size_bytes=changed_bytes,
        mode="estimate",
        basis=(
            "parent-specific changed extent bytes from source-side `btrfs send --no-data` + "
            "`btrfs receive --dump` + streaming C-locale summarization"
        ),
    )


def destination_free_bytes(destination_btrfs: BtrfsOps, path: str | Path) -> int:
    """Return conservative Btrfs estimated free bytes for the destination filesystem."""

    result = destination_btrfs.run(
        ["filesystem", "usage", "-b", str(path)],
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
        raise TransferSizeError(f"destination Btrfs free-space check failed: {detail}")
    return parse_btrfs_usage_free_bytes(result.stdout)
