# wifi-mt7925-aspm — stop MediaTek MT7925 Wi-Fi drop-outs

**Status: RESOLVED on kernels ≥ 6.17 — the workaround below is
not needed there (A/B-verified; withdrawn on the reference
machine). On older kernels the original note applies.** The
sections below are the original record, kept as history; the
verdict from the attended A/B test is at the end.

## Symptom

The built-in Wi-Fi (MediaTek MT7925, driver `mt7925e`) drops out under
Linux: connections stall or fall over, especially around power-state
transitions, even though signal strength is fine.

## Cause

ASPM (Active State Power Management) on the PCIe link interacts badly
with this card/driver combination: the link power-saving states are
where the drop-outs come from.

## Fix

Disable ASPM for the driver via modprobe options, in
`mt7925e-noaspm.conf`:

```
options mt7925e disable_aspm=1
options mt7925_common disable_aspm=1
```

## Apply

```sh
sudo install -m 0644 mt7925e-noaspm.conf /etc/modprobe.d/
sudo reboot   # module options load at boot
```

## Verify

After reboot:

```sh
cat /sys/module/mt7925e/parameters/disable_aspm
```

It should print `Y`. On the reference machine the fix was confirmed in
the live kernel command state after the reboot that loaded it, and the
drop-outs stopped.

## Caveats

- Costs a little battery: the PCIe link no longer enters its deepest
  power-saving states for the Wi-Fi card. On a machine that lives on AC
  this is a non-issue; road warriors can weigh it.
- Driver parameters can change name between kernel versions; if the
  verify command fails, check `modinfo mt7925e` for the current name.

## Community warning — contested on kernels ≥ 6.17 (added later)

Both sides of this one, honestly:

- **Our evidence:** on the reference machine (kernel
  7.3.0-10-generic) this fix was applied on install day, the drop-outs
  stopped, and the boot journal since shows no Wi-Fi disconnects or
  errors with `disable_aspm` reading `Y`. That is a real observation,
  not a guess.
- **The dispute:** a careful kernel-by-kernel analysis of this exact
  machine (th3cavalry's *strix-halo-linux-setup* obsolescence analysis)
  argues the packet-loss/jitter fault this workaround targets was
  repaired natively in **kernel 6.17**, and that forcing
  `disable_aspm=1` on 6.17+ kernels is therefore obsolete — and, if
  applied where it isn't needed, a needless battery cost. Source:
  https://github.com/th3cavalry/strix-halo-linux-setup/blob/HEAD/docs/technical/obsolescence-analysis.md

We cannot fully separate, from one machine, how much of the cure was
this option and how much was the kernel's own state — so the honest
advice for anyone on a current kernel is: **check behaviour first.**
Run without this fix and see whether drop-outs actually happen on your
kernel; apply it only if they do, and A/B it (a boot with, a boot
without) rather than cargo-culting it because it worked here. The fix
stays on the reference machine because the harm demonstrably stopped
with it there — but don't let this page talk you into a power cost
your kernel may already have made unnecessary.

## A/B verdict — tested, and the fix is withdrawn (kernels ≥ 6.17)

The dispute above has now been settled the way the warning itself
prescribed: an attended A/B on the reference machine (kernel
7.3.0-10-generic), run with a safety net because Wi-Fi was the
machine's only remote lifeline at the time.

**Method — a rehearsed dead-man's switch.** Before anything was
changed, a boot timer was installed: at boot + 10 minutes it
checks whether Wi-Fi is associated. If it is, it logs the fact,
stands down, and disarms itself; if it is not, it restores the
backed-up modprobe config and reboots the machine back to the
known-good state. The full trigger → check → verdict → disarm
path was **live-rehearsed before the change** (it fired, found
the association, stood down, and disarmed itself), then re-armed
for the real run.

**Change.** Both `options … disable_aspm=1` lines in
`/etc/modprobe.d/mt7925e-noaspm.conf` were commented out (file
kept; a backup of the pre-change config kept alongside), and the
machine rebooted.

**Result — clean for the full watch window.**

- Wi-Fi associated within seconds of boot; the dead-man's real
  post-boot check found the association, stood down, and disarmed
  itself, exactly as rehearsed.
- Full 20-minute window: **0 mt7925 errors, 0 post-association
  deauth/disconnect events, tx failed 0**, at the full
  **2401.9 Mbit/s** link rate throughout, with
  `disable_aspm = N` confirmed live in
  `/sys/module/mt7925e/parameters/disable_aspm`.

**Verdict.** On this kernel the community position held: the
fault this workaround targets was repaired natively in 6.17, and
forcing `disable_aspm=1` on ≥ 6.17 is obsolete. The fix **stays
off** on the reference machine (the conf remains on disk with
both lines commented; re-enabling is literally uncommenting
them), and a daily self-check watches the ASPM state so any drift
is caught. The shipped `mt7925e-noaspm.conf` in this folder is
the original fix as applied — on an **older kernel (< 6.17)**,
where the fault was real, the original note above still applies
as written.

**Honest bound:** one clean 20-minute window, on one unit, in
one RF environment. If drop-outs ever return, the one-line revert
and the backup both stand ready.
