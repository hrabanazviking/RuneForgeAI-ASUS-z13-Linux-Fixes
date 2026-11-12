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
