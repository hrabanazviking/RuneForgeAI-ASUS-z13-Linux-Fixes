# ethernet-r8152 — USB-C Ethernet that flaps, and the fix that silently wasn't

**Status: fixed — software readiness (autosuspend trap removed, NetworkManager pitfalls cleared).**

## Symptom

USB-C Ethernet through a Realtek-based dongle (RTL8152/8153/8155/8156/
8157, driver `r8152`) is unreliable: the link drops and comes back over
and over, or the adapter is simply dead after sitting idle.

In the logs it looks like this — a carrier flap storm:

```
r8152 … enx…: carrier on
r8152 … enx…: carrier off
```

On the reference machine's earlier boots the journal held **148
carrier-on and 146 carrier-off events** for one dongle — roughly 147
link flaps — plus a blizzard of mDNS address add/remove churn riding on
top of them.

## Cause — and the trap

The underlying cause is USB autosuspend on these chips: the adapter is
power-managed to sleep, and the link dies with it.

The trap is that **the fix everyone copies does nothing at all.** The
internet is full of this one-liner:

```
options r8152 autosuspend=0
```

(included in this folder as `r8152-noautosuspend.conf.anti-example` —
do not use it). It looks plausible and is completely dead:

- `r8152` has **no module parameters at all** — `modinfo -p r8152`
  prints nothing.
- Load the module with that file in place and the kernel says so,
  quietly, once:

  ```
  r8152: unknown parameter 'autosuspend' ignored
  ```

- Nothing else complains. The file sits there, the owner believes
  autosuspend is off, and the flapping continues.

## Fix

Set the power policy per-device with udev, the mechanism that actually
exists. `50-r8152-no-autosuspend.rules` sets `power/control="on"` for
the Realtek vendor ID `0bda` and the five common product IDs
(8152/8153/8155/8156/8157), so the adapter stays powered while plugged
in.

The replacement `r8152-noautosuspend.conf` (comment-only) goes where
the dead option used to live, so the next person to open the file
learns why there is no `options` line in it.

## Apply

Back up anything you're replacing first, then:

```sh
sudo install -m 0644 50-r8152-no-autosuspend.rules /etc/udev/rules.d/
sudo install -m 0644 r8152-noautosuspend.conf /etc/modprobe.d/
sudo udevadm control --reload-rules
```

Unplug/replug the dongle (or reboot) so the rule takes effect on it.

## Verify

- Reload the driver and watch the journal: post-fix, loading `r8152`
  produces a clean registration line and **no** new "unknown parameter"
  warning.
- With a dongle attached, confirm it stays powered:

  ```sh
  cat /sys/bus/usb/devices/*/power/control   # the adapter's entry should read: on
  ```

  (or find the device by vendor: `grep -l 0bda /sys/bus/usb/devices/*/idVendor`)
- Then watch `journalctl -f` while the adapter idles: the carrier
  on/off pairs should be gone.

## Pitfall 1 — a NetworkManager profile pinned to one dongle

A wired profile created while a specific dongle was plugged in records
that adapter's interface name (`connection.interface-name` = its
`enx…` name, which is derived from the dongle's MAC address). From then
on the profile **silently never matches any other adapter** — plug in a
different dongle and nothing happens, no error, no connection.

Check and clear the binding:

```sh
nmcli connection show "<your wired profile>" | grep interface-name
sudo nmcli connection modify "<your wired profile>" connection.interface-name ""
```

An empty `interface-name` means the profile applies to any ethernet
device. (On the reference machine this was the second real defect: the
only wired profile could only ever have matched the one dongle it was
created with.)

## Pitfall 2 — is ethernet even managed by NetworkManager?

Stock Ubuntu ships
`/usr/lib/NetworkManager/conf.d/10-globally-managed-devices.conf`,
which marks wired devices *unmanaged*. On Kubuntu with netplan
rendering to NetworkManager, that file happens to be masked by a
0-byte namesake netplan generates at
`/run/NetworkManager/conf.d/10-globally-managed-devices.conf` — so
ethernet **is** managed, but by accident of a mask, and only for as
long as the netplan renderer stays as it is.

Don't trust the contents of either file — ask NetworkManager for its
**effective merged configuration**:

```sh
NetworkManager --print-config | grep -A3 unmanaged
```

On a healthy setup the merged output contains no `unmanaged-devices`
entry. If it ever does (renderer change, distro re-spin), ethernet
will silently stop being managed and no dongle will ever get a
connection, whatever the drivers are doing.

## Caveats

- What is proven here is the software side: the dead parameter is gone,
  the working power rule is in, module loads are clean, and both
  NetworkManager pitfalls are checked and corrected. The final
  end-to-end proof — carrier, DHCP, throughput through a real cable —
  needs a dongle plugged in once; on the reference machine none was
  attached when the fix was made, so that last step is honestly still
  open.
- The udev rule covers the Realtek IDs listed above. Other USB
  ethernet chipsets (ASIX, etc.) need their own vendor/product lines.
- An embedded-controller latch-up is sometimes blamed for dead USB-C
  networking on this machine family. It was checked and **not
  indicated** on the reference machine: the adapter enumerated and
  carried link repeatedly whenever attached (a latched controller
  presents as a dead, invisible device, which never occurred). No
  power-drain ritual is prescribed here.
