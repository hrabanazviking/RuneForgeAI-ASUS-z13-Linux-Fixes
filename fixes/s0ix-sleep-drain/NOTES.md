# s0ix-sleep-drain — suspend-then-hibernate

**Status: configured.**

## Symptom

Modern-standby (S0ix) sleep on this machine keeps sipping power: left
asleep unplugged, the battery drains far faster than a real hibernate
would, and the machine can be found warm or flat after a day or two in a
bag.

## Cause

Plain `suspend` keeps the SoC in a low-power idle rather than powering
off. On Strix Halo the draw is small but not negligible, and it never
reaches zero.

## Fix

Use systemd's **suspend-then-hibernate**: sleep normally, then
automatically hibernate (full power-off, state on disk) after a delay.
The drop-in `10-suspend-then-hibernate.conf` sets:

```ini
[Sleep]
HibernateDelaySec=2h
```

Short naps keep the instant resume of suspend; anything longer than two
hours becomes a true hibernate.

## Apply

```sh
sudo install -m 0644 10-suspend-then-hibernate.conf /etc/systemd/sleep.conf.d/
```

Then suspend as usual (`systemctl suspend` now routes through
suspend-then-hibernate when the setting is picked up — check with
`systemd-analyze cat-config systemd/sleep.conf`).

## Verify

Suspend the machine, leave it for just over the delay, and wake it: the
resume will come from the hibernation image (slower, from disk) instead
of instant-on. Battery drain while "asleep" past the delay should be
effectively zero.

## Caveats

- **You need a working resume device** (swap big enough for the RAM you
  want to hibernate, and a `resume=` kernel parameter / resume hook set
  up) before hibernate can work at all. Fix that first; on this machine
  it was already in place from the distro install.
- Hibernation writes RAM to swap: on a 128 GB machine that needs swap
  sized accordingly, or hibernate will fail and the machine stays in
  suspend.
- Adjust `HibernateDelaySec` to taste (`30min`, `1h`, …).
