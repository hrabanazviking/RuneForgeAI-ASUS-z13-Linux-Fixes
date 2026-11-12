#!/bin/bash
# @home btrfs snapshot regimen. Runs as root (system timer).
# Creates a read-only snapshot of @home under @snapshots, keeps the
# newest 11, prunes only this regimen's own older snapshots.
# Check the device on the mount line: /dev/nvme0n1p3 on the
# proving unit; yours may differ.
set -u
TOP=/mnt/btrfs-top; MOUNTED=0
cleanup(){ [ "$MOUNTED" = 1 ] && umount "$TOP"; }
trap cleanup EXIT
if ! mountpoint -q "$TOP"; then mkdir -p "$TOP"; mount -o subvolid=5 /dev/nvme0n1p3 "$TOP" || exit 1; MOUNTED=1; fi
mkdir -p "$TOP/@snapshots"
NAME="home-$(date +%F-%H%M)"
[ -e "$TOP/@snapshots/$NAME" ] && NAME="home-$(date +%F-%H%M%S)"
btrfs subvolume snapshot -r "$TOP/@home" "$TOP/@snapshots/$NAME" || exit 1
echo "created $NAME"
ls -1 "$TOP/@snapshots" | grep '^home-' | sort -r | tail -n +12 | while read -r old; do
  echo "pruning $old"; btrfs subvolume delete "$TOP/@snapshots/$old"
done
btrfs subvolume list "$TOP" | grep '@snapshots/home-' || true
