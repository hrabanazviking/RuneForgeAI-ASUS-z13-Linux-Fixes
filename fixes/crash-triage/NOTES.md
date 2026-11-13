# crash-triage — teach the crash reporter to tell experiment crashes from real ones

**Status: applied and proven on this unit (2026-11-12). Five
deliberate sandbox test crashes were quarantined by the watcher;
one deliberate real-parentage test crash was left in place for
normal reporting. Three bugs the tests exposed in the watcher
itself were fixed and re-proven the same evening.**

## Symptom

Crash dialogs (apport/KDE) for desktop components —
`plasmashell`, `kactivitymanagerd` — that had **not** crashed.
The session's real copies were verified alive and untouched in
the process list and in `coredumpctl`; the dying copies were
short-lived test instances wearing the same names.

## What actually produces these dialogs (evidence first)

Reading the installed apport (2.36.0) source and the evening's
coredump records before building anything:

1. **Unpackaged binaries never reach the dialog at all.**
   `process_crash()` drops any report whose executable does not
   belong to a package ("executable does not belong to a
   package, ignoring"). Proven live: deliberate segfaults of a
   test binary in `/tmp` and of one in a build tree produced a
   stored coredump and **no** `/var/crash` file. Foreground
   experiment binaries were never the problem — and their cores
   stay in systemd-coredump storage as evidence; this fix does
   not touch coredump collection.
2. **The offenders were package-owned KDE binaries spawned as
   throwaway test instances** through an agent tooling channel:
   their coredumps sit in the tooling channel's cgroup
   (`/system.slice/musegadget.service`) instead of the user
   session's, they had the offscreen Qt platform plugin loaded
   (a headless test instance), and they died in the same seconds
   as `timeout` wrappers from the test harness. The real session
   copies live under the user manager's session/background
   slices and never crashed.
3. **The native denylist is the wrong tool here.** apport's
   `/etc/apport/report-ignore/` suppresses reports by exact
   executable path only (no globbing — verified in the installed
   `README.denylist` and `check_ignored()`), and the mechanism
   was proven live with a temporary entry. But the offenders'
   paths are the *real* desktop binaries' paths: denylisting
   them would also suppress a genuine desktop crash. The proof
   entry was removed the same evening; **no denylist entry is
   left in place.**

So the distinguishing information is context — who spawned it,
from where, headless or not — never the executable path.

## The fix: a classifying watcher (user service)

`crash-triage.py` runs as a systemd **user** service and watches
`/var/crash`. It acts only on *settled* files (size and mtime
unchanged across two 1-second polls — apport writes, then
closes; nothing is judged mid-write) and classifies each report,
corroborating context from `coredumpctl` (the report's
executable + date matched to the closest dump within 120 s):

- **Hard REAL override (checked first):** the coredump's control
  group is under the user manager's `session.slice/` or
  `background.slice/` — the real desktop's own services. Such a
  report is left exactly in place, no matter what else matches.
- **Sandbox (any one strong signal):** the control group is the
  agent tooling channel (`musegadget.service`); the command line
  references `/tmp` or a forge/build tree; the working directory
  is under `/tmp` or a forge/build tree; the report carries
  `QT_QPA_PLATFORM=offscreen`; or the executable itself lives
  under `/tmp` or a forge/build tree.
- **Sandbox reports are moved — never deleted** — to
  `~/.local/state/crash-triage/quarantine/`, with one digest
  line (time, file, executable, signal, reasons) in
  `~/.local/state/crash-triage/digest.log`. Every decision,
  including REAL leaves, is also written to `watcher.log` in the
  same directory for audit.
- **Fail-safe: any doubt classifies REAL.** A missing field, a
  parse error, a failed `coredumpctl` lookup, an unknown control
  group — the report is left untouched for normal
  apport/whoopsie handling. A crash spawned from a plain
  interactive shell in the real session, with no experiment
  markers, is REAL by design: real reports must never be hidden.

One identity lesson is baked in: apport reuses **one filename
per executable** for repeat crashes, so the watcher keys
"already handled" on a (name, size, mtime) fingerprint — never
the name alone — and quarantined files get a timestamp suffix
on collision so a repeat crash can never overwrite an earlier
quarantine.

Install (user level, no root):

```sh
install -m 0755 crash-triage.py ~/.local/bin/crash-triage.py
install -m 0644 crash-triage.service ~/.config/systemd/user/
# the shipped unit uses %h for the script path; point ExecStart
# at your copy if you installed it elsewhere, then:
systemctl --user daemon-reload
systemctl --user enable --now crash-triage.service
```

## Proof on this unit (2026-11-12)

- **Sandbox, `/tmp` context:** a packaged shell run from a
  `/tmp` test script, self-segfaulted — quarantined (tooling
  cgroup + experiment-path signals). Repeated after the
  fingerprint fix: quarantined again, under a unique name.
- **Sandbox, build tree:** the same test from a forge tree —
  quarantined.
- **Real, session parentage:** the same shell run via
  `systemd-run --user` with ordinary parentage and no experiment
  markers — verdict REAL, the report stayed in `/var/crash` for
  normal handling. (The test report was removed by hand
  afterwards, and that removal is recorded in the test log.)
- **Totals:** 5 sandbox test crashes quarantined (all deliberate
  shell segfaults in experiment contexts), 1 real test left in
  place, 0 real reports harmed, 0 unpackaged binaries
  quarantined (apport never writes reports for them — see
  finding 1).
- **Three bugs found by the tests and fixed in-slice:** repeat
  crashes skipped because "done" was keyed by filename alone;
  a second quarantine overwriting the first (5 digest events,
  4 files — the first overwrite predates the fix and is
  recorded, not hidden); and a report-Date parse bug that made
  the cgroup matcher pick a wrong dump and mis-quarantine the
  first real-parentage attempt (a test file only — fixed, and
  the re-run passed).
- The service survived three restarts during testing and is
  enabled and active. apport and whoopsie configuration are
  untouched, and the real session was never disturbed.

## Caveats

- **Reaction time:** the watcher polls at 1 s and acts ~2–3 s
  after a report settles. The KDE notifier watches `/var/crash`
  too, so in the worst case a sandbox popup could flash briefly
  and then vanish as its file is quarantined. The flood pattern
  that prompted this work — paired test crashes under the
  tooling channel — is caught by the cgroup signal within
  seconds.
- **Runs while logged in:** linger is off on this unit, so the
  user service runs while the user is logged in. That is the
  intended shape here; enable linger if you want it watching
  outside a login.
- **A different warning class is not covered:** a test probe
  killed inside its own small `systemd-run` memory cgroup
  produces a generic "low memory" system warning. That is
  systemd/KDE memory-cgroup OOM reporting, not the apport
  report path — this fix honestly does not reach it.
- On this unit the crash *uploader* (whoopsie) was found
  already failed — start-limit hit in the same minute as the
  crash flood that prompted this work — and was left exactly
  as found. Restarting it is a separate, deliberate decision;
  this fix changes nothing about how real reports are uploaded.
- The forge-tree markers in the script (`aesir-`, `-forge`,
  `/build/`, …) are this unit's build-tree names; adjust them
  to your own experiment trees before trusting the sandbox
  verdicts.
- Rollback is one command:
  `systemctl --user disable --now crash-triage.service`, remove
  the unit and script, `daemon-reload`, and move any
  quarantined `*.crash` files back to `/var/crash`. No
  `/etc/apport` changes were made, so there is nothing to
  restore there.
