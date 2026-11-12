# self-healing-reporting — verdicts and reports, not second restarters

**Status: applied and proven on this unit (2026-11-12). Health
summary, daily failed-unit report and boot-health summary are
armed and test-proven. The greeter-wedge detector runs LOG-ONLY
on a 60-second timer in a 24-hour dry-run that started
2026-11-12 03:08 local time; its restart action does not exist
yet, on purpose.**

## The finding that shaped this

Auditing this unit's services before building anything showed
systemd already restarts the two services a naive "self-healing"
pass would target: the local AI server ships `Restart=always`
and the web server `Restart=on-failure`, and both answer HTTP
health checks. The autostart census found exactly one
owner-custom autostart item (a desktop gauges widget), already
covered by an existing 2-minute respawn-guard timer; everything
else is distro/KDE session machinery.

So the missing layer was never restarting — it was **honest
reporting**: knowing, each day, what failed, and having a boot
health record to read after something goes wrong.

## What was built (all read-only; nothing restarts anything)

- `service-health-summary.sh` — one-screen verdict: key services
  active or not, both HTTP health probes, system and user failed
  units, the respawn-guard's state, and the last self-check line.
- `failed-unit-report.sh` + timer (daily 00:05) — appends a
  failed-unit report to a daily health log, filtering the
  known-noise crash-uploader template instances by name.
- Boot health (timer at +130 s after the user manager starts) —
  writes a boot-health log line set; test-proven by a manual
  start, verdict OK.
- `greeter-wedge-watch.sh` — implements the greeter-wedge
  signature from the greeter fix's notes (at least 5
  `ring gfx_0.0.0 timeout` kernel lines with the greeter
  faulting, inside 120 s) on a 60-second user timer. **Log-only:**
  on signature it writes a line; if a user session is active it
  writes REFUSE. Replay proofs against recorded boots all pass
  (the incident boot FIREs 40/40, a session-active window
  REFUSEs, clean windows NO-FIRE). The restart action will only
  be considered after a clean 24-hour dry-run, as a separate,
  root-armed step.

Install (user level, no root):

```sh
install -m 0755 service-health-summary.sh failed-unit-report.sh greeter-wedge-watch.sh ~/bin/
install -m 0644 failed-unit-report.service failed-unit-report.timer \
  greeter-wedge-watch.service greeter-wedge-watch.timer ~/.config/systemd/user/
# point each service's ExecStart at your copies, then:
systemctl --user daemon-reload
systemctl --user enable --now failed-unit-report.timer greeter-wedge-watch.timer
```

## Caveats

- The whoopsie-template filter and the service list are this
  unit's; adjust both to your own census before trusting the
  report.
- Log-only means log-only: if you want the wedge detector to act,
  that is a deliberate later decision with its own proof bar —
  do not just add a restart line.
