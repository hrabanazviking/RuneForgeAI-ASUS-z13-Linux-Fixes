# greeter-gpu-wedge — KNOWN ISSUE (workaround verified)

**Status: known issue. Workaround verified on this unit;
trigger chain identified (see the campaign finding at the end);
root cause not isolated.**

## Symptom

At the SDDM login screen — before any user session exists — the
display flashes black/white continuously, every few seconds. Both
the internal panel and any external display flash, because it is
not a display problem: the GPU itself is resetting in a loop.

## Evidence

Kernel log during an episode (Kubuntu 26.10, kernel
7.3.0-10-generic, amdgpu / gfx1151), repeating every few seconds:

```
amdgpu: ring gfx_0.0.0 timeout, signaled seq=…, emitted seq=…
amdgpu:   Process sddm-greeter-qt … thread sddm-greet:cs0 …
amdgpu: Starting gfx_0.0.0 ring reset
amdgpu: Ring gfx_0.0.0 reset succeeded
amdgpu: [drm] device wedged, but no recovery needed
amdgpu: [drm] AMDGPU device coredump file has been created
```

The faulting process is named in the log: `sddm-greeter-qt` — the
login greeter's Qt Quick graphics path stalls the graphics ring,
the driver resets the ring, the screen flashes, and the cycle
repeats.

## Workaround (verified)

Restart the display manager so a fresh greeter starts:

```
sudo systemctl restart sddm
```

On the unit where this was observed, that broke the loop
immediately: no further `ring gfx_0.0.0 timeout` lines afterwards,
and the machine stayed clean through a subsequent full desktop
login.

**Warning:** restarting the display manager ends any user session
that is already running. This workaround is for the
stuck-at-the-login-screen case, where no session exists yet. If
you are already logged in and happy, you do not have this problem.

## Honest status

- The workaround is verified **once**, on one machine, on the
  environment above. It has not recurred since on that unit.
- The root cause is **not** isolated. The leading candidate is the
  greeter's GL scene-graph path against this kernel's amdgpu
  driver, but that is a candidate, not a finding.
- The episode appeared on a boot that also carried newly added
  unified-memory kernel parameters (`iommu=pt`, enlarged GTT
  sizing). That is a correlation worth recording, **not** a proven
  cause — the greeter normally starts fine on the same parameters,
  and the stall did not return after the greeter restart.
- If it recurs on your machine, the kernel log is the place to
  confirm it is the same fault (look for the greeter named as the
  process in a `ring gfx_0.0.0 timeout`) before assuming this note
  applies.

## Deeper finding — the trigger chain (campaign analysis, added later)

A later robustness campaign re-read that boot's full journal and
found the chain that led into the wedge — plus one correction to
the tidy story above.

**The trigger:** on that boot, SDDM's **autologin attempt failed
inside sddm's first second** — the autologin helper crashed with
exit code 1 and the session never started — leaving the machine
stranded on the greeter. The greeter's graphics stack then
wedged the graphics ring **41 times over ~12 minutes** (a
timeout roughly every 2 s at the peak), flashing the displays
the whole while. The identical autologin path had succeeded on
the previous boot; the one-second exit did not reproduce and its
inner cause was **not isolated** — it is recorded as a start-up
race, not a configuration defect. So the chain is: failed
autologin → stranded greeter → greeter wedges the ring. *Why*
the greeter's graphics wedge the ring, and why the helper
exited, both remain open.

**The workaround, re-affirmed — with a caveat.** Restarting sddm
broke the reset loop instantly, and no ring timeout has occurred
since. But the first session started immediately after that
restart **collapsed after ~5 seconds**: the journal shows the
session's workspace targets being *stopped* as the dying
greeter's teardown raced the new session's start — plasmashell
itself started cleanly and was stopped; it did not crash. A
**second** `systemctl restart sddm` brought the session up
cleanly, and it stayed up.

Practical version: if the first login right after the fix
collapses, don't debug the desktop — restart sddm once more.
The greeter you are looking at may be a fresh process sitting on
a half-torn-down VT.

## Fix-campaign verdict update (later; supersedes the framing above)

A dedicated fix-campaign team re-did the archaeology across
**every boot in the journal (8 boots)** and the picture changed
in three ways. The trigger-chain section above stays as the
record of the earlier reading; this section is the current
verdict.

**The census.** Ring timeouts appear in exactly two boots — and
both coincide with heavy AI GPU stress running on the machine:

- Six boots: zero ring timeouts, zero GPU resets, zero wedges.
- One boot: 21 timeouts whose faulting processes were a **live
  user session's** compositor and shell (not the greeter at
  all), escalating to full GPU resets, during an AI
  stress-testing window.
- The greeter boot: 52 timeouts, all inside ~100 seconds
  (01:51:40–01:53:20) — 41 on the main graphics ring faulting
  the greeter app, 11 on the second graphics ring faulting the
  greeter's own compositor. (The "~12 minutes" in the section
  above measures the whole stranded-greeter episode from boot;
  the timeout loop itself spans ~100 s. Zero timeouts since the
  display-manager restart, including through a full login.)

**The verdict.** This is not a greeter defect, and it is not
the unified-memory kernel parameters:

1. The victim is whichever graphics client is submitting when
   the episode strikes — in the other wedged boot that was the
   live session, and it fared worse. The greeter was simply the
   only graphics client present that night (which is where the
   failed-autologin chain above still matters: it explains why
   a greeter was on screen to be hit).
2. The unified-memory parameters are **exonerated**: the
   session boot wedged *without* them, another boot carried
   them and was completely clean, and the greeter boot was
   clean for its first ten minutes on them and ever since.
   Neither necessary nor sufficient.
3. The greeter's configuration is identical across its clean
   and wedged starts; the only changed variable was concurrent
   GPU load.

The strong candidate (named as a candidate, not kernel-proven):
an intermittent amdgpu graphics-ring lockup on gfx1151 when a
particular sustained heavy compute-load shape coincides with
graphics submissions — graphics jobs exceed the ring lockup
timeout, the driver resets the ring, clients lose their GL
contexts, and a continuously re-rendering client re-queues into
the still-saturated GPU, producing the flashing loop.
Restarting the display manager broke it by dropping the wedged
client contexts while the compute burst passed.

**Prevention: staged, NOT applied — stated plainly.**

- Rejected on evidence: forcing the greeter to software
  rendering. It treats the greeter as the culprit; the census
  proves it is not, and it would leave the session exactly as
  exposed.
- Staged, ready to prove: raising `amdgpu.lockup_timeout` in
  the boot flags, decided by a named discriminating test — sit
  at the greeter with nobody logged in, reproduce the heavy
  compute-load shape, and watch: episodes vanishing under a
  longer timeout with identical load proves a timeout-margin
  mechanism; episodes persisting means a hard hang and the
  proposal is dead. The test needs a window when the owner is
  not using the machine, and has not run yet.
- A greeter-wedge watchdog (restart the display manager only
  when a greeter-faulting timeout loop is in progress **and no
  user session is active** — a session wedge is a different
  incident and must never be "helped" by killing the session)
  has been built to the detection stage and is in a log-only
  dry run: its detector replayed against this episode's journal
  fires on the signature, refuses when a session is assumed
  active, and stays silent on the clean boots. The restart
  action is **not** enabled; the spec requires a full day of
  clean log-only running first.

**Status line, honestly:** root cause narrowed to one strong
candidate; prevention staged, nothing applied; the verified
workaround above remains the cure if it recurs.
