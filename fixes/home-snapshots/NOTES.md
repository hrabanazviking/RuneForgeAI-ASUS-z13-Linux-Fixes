# home-snapshots — a Btrfs @home snapshot regimen that actually runs

**Status: applied and proven on this unit (2026-11-12). A system
timer fires daily at 03:30; the scheduled run itself created a
snapshot (exit 0), on top of two earlier manual proofs. Three
read-only snapshots held at proof time.**

## Why

The install lays the system out as Btrfs subvolumes (`@`, `@home`)
but ships no snapshot regimen — the safety net exists as a
filesystem feature and nothing else. One bad update or one bad
afternoon in `$HOME` has no way back.

## The fix

- `snapshot-home.sh` (installed as `/usr/local/sbin/z13-snapshot-home`,
  root-owned) mounts the Btrfs top level, takes a **read-only**
  snapshot of `@home` under `@snapshots/home-<date>-<time>`, and
  prunes older campaign snapshots, keeping the **newest 11**.
  (Design intent was 7 daily + 4 weekly tiers; for now they are
  held as one newest-11 pool — recorded honestly rather than
  dressed up as tiering that is not implemented.)
- `z13-snapshot-home.timer` — `OnCalendar=*-*-* 03:30:00`,
  `Persistent=true` (a missed night catches up at next boot).
- `z13-snapshot-home.service` — a oneshot running the script.

Install:

```sh
sudo install -m 0755 snapshot-home.sh /usr/local/sbin/z13-snapshot-home
sudo install -m 0644 z13-snapshot-home.service z13-snapshot-home.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now z13-snapshot-home.timer
```

Check the device path in the script first: it mounts the Btrfs
device directly (`/dev/nvme0n1p3` on this unit — yours may differ).

## Proof on this unit

- Manual proof runs created the first two snapshots.
- The **armed timer then fired on schedule at 03:30** and created
  the third, service exit 0/SUCCESS — the regimen is proven as a
  schedule, not just as a script.
- Snapshots are read-only and list cleanly under `@snapshots/`.

## Caveats

- Snapshots are not backups: they live on the same device. They
  protect against bad changes, not against a dead drive.
- Retention pruning only ever deletes this regimen's own
  `home-*` snapshots, newest-11 kept; it touches nothing else.
