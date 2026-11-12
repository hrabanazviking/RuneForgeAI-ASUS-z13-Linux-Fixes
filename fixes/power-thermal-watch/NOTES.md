# power-thermal-watch — a plain log of heat, watts and fans, with a 95 °C alert

**Status: applied and proven on this unit (2026-11-12). A user
timer samples every 5 minutes; continuous samples with real
temperature, package-power and fan fields have been logged since
arming, idle through load.**

## Why

Community reports for this model include a sudden power-cut
pattern under sustained load. Without a local record, a cut like
that leaves nothing to reason from afterwards — no temperatures,
no wattage, no fan behaviour in the minutes before it died.

## The fix

- `power-thermal-watch.sh` takes **one sample per run** and
  appends one line: CPU Tctl, GPU edge temperature, GPU package
  power (PPT), both fan speeds, battery state/charge, and the
  ACPI platform profile.
- Sensors are resolved **by hwmon name at runtime** (`k10temp`,
  `amdgpu`) — never by `hwmonN` number, which renumbers between
  boots. (The first version of this watch read fixed nodes and
  produced a broken Tctl field; the name-based fix is the version
  published here, and the lesson is the point.)
- If Tctl or GPU edge reaches **95 °C**, a plain-language alert
  line goes to a separate `.alerts` log next to the main log.
- `z13-power-thermal-watch.timer` — user timer, every 5 minutes
  (`OnBootSec=2min`, `OnUnitActiveSec=5min`).

Install:

```sh
install -m 0755 power-thermal-watch.sh ~/bin/power-thermal-watch.sh
install -m 0644 z13-power-thermal-watch.service z13-power-thermal-watch.timer ~/.config/systemd/user/
# point the service's ExecStart at your copy of the script, then:
systemctl --user daemon-reload
systemctl --user enable --now z13-power-thermal-watch.timer
```

## Proof on this unit

Samples land every 5 minutes with all fields real — from idle
(≈29 °C, ≈6 W, fans stopped) to working load (≈72 °C, ≈52 W,
fans at 3,200–3,800 RPM). No alert has fired; the alert path was
proven by test lines when the watch was built.

## Caveats

- This is a watch, not a guard: it changes no power or thermal
  setting. A TDP/charge-cap proposal for this machine exists as
  a draft only and is deliberately not published as a fix.
- The `sensors`-based fallbacks in the script carry this unit's
  sensor names (and one PCI bus address for the PPT fallback);
  check them against `sensors` output on your machine.
