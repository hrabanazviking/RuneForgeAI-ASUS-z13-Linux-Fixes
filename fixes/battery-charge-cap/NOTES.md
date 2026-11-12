# battery-charge-cap — hold the battery at 80% on a desk machine

**Status: applied and verified on this unit (2026-11-12). The
charge end threshold is 80% in the kernel sysfs, in the vendor
daemon config (so it survives reboots), and in UPower's view —
all three agree, which they did not before.**

## Why

This machine lives on AC power as a desktop with the battery as
a backup. A lithium cell held at 100% ages fastest; capping the
charge at 80% is the standard longevity trade for a machine
that rarely needs the last fifth of the battery on the move.

## The discrepancy this fix also closed

Before the change, the three places that report the charge
limit disagreed: the kernel sysfs threshold and the vendor
daemon (asusd) config both said 100, while UPower reported an
end threshold of 80 / start 75. It was not clear which value
actually governed charging. Setting one deliberate value in
every authoritative place resolved the question by making
them agree.

## The fix

1. In `/etc/asusd/asusd.ron`, set both fields to 80:
   - `charge_control_end_threshold: 80`
   - `base_charge_control_end_threshold: 80`

   (Back up the file first; the pre-change copy is kept beside
   the fix team's notes on the machine.)
2. Set the live kernel value to match:
   `echo 80 | sudo tee /sys/class/power_supply/BAT0/charge_control_end_threshold`

## Verify

- `cat /sys/class/power_supply/BAT0/charge_control_end_threshold`
  reads back `80`.
- Both fields in `/etc/asusd/asusd.ron` read `80` (persistence
  across reboots).
- `upower -i $(upower -e | grep BAT)` reports the end threshold
  as 80 and the start threshold as 75 — UPower now agrees with
  sysfs instead of contradicting it.

## Caveats

- The battery was at 100% and fully charged when the cap was
  applied. A charge cap governs *charging*; it does not drain
  the cell. The cap takes visible effect as the battery next
  cycles below 80%.
- No power/TDP limit was changed at the same time: there was
  no evidence for one, and this repo does not apply fixes
  without evidence.
