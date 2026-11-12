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
