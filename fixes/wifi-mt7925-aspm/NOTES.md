# wifi-mt7925-aspm — stop MediaTek MT7925 Wi-Fi drop-outs

**Status: fixed (verified live).**

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
