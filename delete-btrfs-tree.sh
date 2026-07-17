#!/usr/bin/env bash

# Delete every Btrfs subvolume below a destination, then remove ordinary
# leftover files/directories. The destination directory itself is preserved.
#
# Uses "subvolume delete --recursive" when available (btrfs-progs 6.12+).
# Older versions use an explicit deepest-first Btrfs deletion fallback.

set -Eeuo pipefail

PROGRAM_NAME="${0##*/}"
MODE="dry-run"
DESTINATION=""

usage() {
    cat <<EOF
Usage:
  sudo ./$PROGRAM_NAME --dry-run DESTINATION
  sudo ./$PROGRAM_NAME --yes-delete DESTINATION

Modes:
  --dry-run      Show and validate what Btrfs would delete. This is the default.
  --yes-delete   Permanently delete all contents below DESTINATION.

The DESTINATION directory itself is never deleted.
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

while (($#)); do
    case "$1" in
        --dry-run)
            MODE="dry-run"
            ;;
        --yes-delete)
            MODE="delete"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --*)
            die "Unknown option: $1"
            ;;
        *)
            [[ -z "$DESTINATION" ]] || die "Only one destination may be supplied"
            DESTINATION="$1"
            ;;
    esac
    shift
done

[[ -n "$DESTINATION" ]] || {
    usage >&2
    exit 2
}

for command_name in btrfs find findmnt grep realpath rm; do
    require_command "$command_name"
done

((EUID == 0)) || die "Run this script with sudo"

DESTINATION="$(realpath -e -- "$DESTINATION")"
[[ -d "$DESTINATION" ]] || die "Destination is not a directory: $DESTINATION"
[[ "$DESTINATION" != "/" ]] || die "Refusing to operate on /"

filesystem_type="$(findmnt -rn -o FSTYPE -T "$DESTINATION")"
[[ "$filesystem_type" == "btrfs" ]] || \
    die "Destination is not on Btrfs: $DESTINATION (found: ${filesystem_type:-unknown})"

mount_options="$(findmnt -rn -o VFS-OPTIONS -T "$DESTINATION")"
[[ ",$mount_options," == *,rw,* ]] || \
    die "The Btrfs filesystem containing the destination is not mounted read-write"

delete_help="$(btrfs subvolume delete --help 2>&1 || true)"
if [[ "$delete_help" == *"--recursive"* ]]; then
    HAS_RECURSIVE_DELETE=true
else
    HAS_RECURSIVE_DELETE=false
fi

# Refuse separately mounted filesystems below the destination. This guarantees
# that the final ordinary-file cleanup cannot cross into another mount.
nested_mounts=()
while IFS= read -r mount_target; do
    [[ -n "$mount_target" ]] || continue
    mount_target="$(realpath -m -- "$mount_target")"
    if [[ "$mount_target" == "$DESTINATION/"* ]]; then
        nested_mounts+=("$mount_target")
    fi
done < <(findmnt -Rrn -o TARGET -T "$DESTINATION")

if ((${#nested_mounts[@]})); then
    printf 'ERROR: Refusing to operate while filesystems are mounted below the destination:\n' >&2
    printf '  %s\n' "${nested_mounts[@]}" >&2
    exit 1
fi

# Find only outermost subvolumes. A Btrfs subvolume root has inode 256.
# -prune is essential: find reports the subvolume path but never traverses its
# contents. btrfs itself performs the recursive child-subvolume deletion.
discover_outermost_subvolumes() {
    find "$DESTINATION" \
        -mindepth 1 \
        -type d \
        -inum 256 \
        -prune \
        -print0
}

# Compatibility path for btrfs-progs older than 6.12. This only reads the
# directory tree. It collects all subvolumes before any deletion and -depth
# guarantees that nested subvolumes appear before their containing subvolume.
# No ordinary file is removed or changed during discovery.
discover_all_subvolumes_deepest_first() {
    find "$DESTINATION" \
        -mindepth 1 \
        -depth \
        -type d \
        -inum 256 \
        -print0
}

subvolumes=()
if [[ "$HAS_RECURSIVE_DELETE" == true ]]; then
    DELETE_STRATEGY="Btrfs native recursive deletion"
    mapfile -d '' -t subvolumes < <(discover_outermost_subvolumes)
else
    DELETE_STRATEGY="explicit deepest-first Btrfs deletion (compatibility mode)"
    mapfile -d '' -t subvolumes < <(discover_all_subvolumes_deepest_first)
fi

# Confirm every inode-256 candidate through Btrfs before allowing deletion.
for subvolume in "${subvolumes[@]}"; do
    btrfs subvolume show "$subvolume" >/dev/null 2>&1 || \
        die "Inode 256 was found but Btrfs did not confirm it as a subvolume: $subvolume"
done

printf 'Destination: %s\n' "$DESTINATION"
printf 'Mode:        %s\n' "$MODE"
printf 'Strategy:    %s\n' "$DELETE_STRATEGY"

if [[ "$HAS_RECURSIVE_DELETE" == true ]]; then
    printf 'Outermost Btrfs subvolumes found: %d\n' "${#subvolumes[@]}"
else
    printf 'Btrfs subvolumes found, deepest first: %d\n' "${#subvolumes[@]}"
fi

if ((${#subvolumes[@]})); then
    printf '  %s\n' "${subvolumes[@]}"
else
    printf '  (none)\n'
fi

if [[ "$MODE" == "dry-run" ]]; then
    if ((${#subvolumes[@]})); then
        printf '\nBTRFS DELETE PREVIEW\n'
        if [[ "$HAS_RECURSIVE_DELETE" == true ]]; then
            for subvolume in "${subvolumes[@]}"; do
                printf '\nRecursive target: %s\n' "$subvolume"
                btrfs --dry-run subvolume delete --recursive "$subvolume"
            done
        else
            printf 'Compatibility mode will run btrfs subvolume delete in exactly the order shown above.\n'
        fi
    fi

    printf '\nDry run only; nothing was deleted.\n'
    printf 'After successful Btrfs deletion, ordinary leftovers below the destination would also be removed.\n'
    printf 'Run with --yes-delete to perform the deletion.\n'
    exit 0
fi

printf '\nPHASE 1: DELETE BTRFS SUBVOLUMES\n'

if [[ "$HAS_RECURSIVE_DELETE" == true ]]; then
    for subvolume in "${subvolumes[@]}"; do
        printf '\nDeleting recursively with Btrfs: %s\n' "$subvolume"
        if ! btrfs subvolume delete --recursive --commit-after "$subvolume"; then
            die "Btrfs deletion failed. Ordinary files and directories were not cleaned up."
        fi
    done
else
    for subvolume in "${subvolumes[@]}"; do
        printf '\nDeleting with Btrfs: %s\n' "$subvolume"
        if ! btrfs subvolume delete --commit-after "$subvolume"; then
            die "Btrfs deletion failed. Ordinary files and directories were not cleaned up."
        fi
    done
fi

printf '\nPHASE 2: VERIFY THAT NO SUBVOLUMES REMAIN\n'

remaining_subvolumes=()
mapfile -d '' -t remaining_subvolumes < <(discover_outermost_subvolumes)

if ((${#remaining_subvolumes[@]})); then
    printf 'ERROR: Btrfs subvolumes still remain; ordinary cleanup has been cancelled:\n' >&2
    printf '  %s\n' "${remaining_subvolumes[@]}" >&2
    exit 1
fi

printf 'No Btrfs subvolumes remain below the destination.\n'

printf '\nPHASE 3: REMOVE ORDINARY LEFTOVERS\n'

leftovers=()
mapfile -d '' -t leftovers < <(
    find "$DESTINATION" -mindepth 1 -maxdepth 1 -print0
)

if ((${#leftovers[@]})); then
    for leftover in "${leftovers[@]}"; do
        printf 'Removing ordinary leftover: %s\n' "$leftover"
        if ! rm -rf -- "$leftover"; then
            die "Could not remove ordinary leftover: $leftover"
        fi
    done
else
    printf 'No ordinary leftovers found.\n'
fi

if find "$DESTINATION" -mindepth 1 -print -quit | grep -q .; then
    die "Deletion finished with unexpected content still below the destination"
fi

printf '\nDeletion complete.\n'
printf 'Preserved destination: %s\n' "$DESTINATION"
