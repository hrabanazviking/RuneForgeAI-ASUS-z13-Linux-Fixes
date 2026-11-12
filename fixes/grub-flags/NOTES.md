# grub-flags — display wake glitches + backlight keys

**Status: fixed (applied and verified in `/proc/cmdline`).**

Three boot-time settings, all merged into `GRUB_CMDLINE_LINUX_DEFAULT`
in `/etc/default/grub`. The example file `grub-cmdline-example.txt`
shows them together.

## 1. `amdgpu.dcdebugmask=0x610` — PSR/VRR wake glitches

- **Symptom:** after waking from sleep, the internal panel can glitch or
  misbehave around Panel Self Refresh (PSR) and Variable Refresh Rate
  (VRR) on the Radeon 8060S (gfx1151).
- **Fix:** the flag disables the PSR / PSR-SU / Replay paths in the
  amdgpu display core (bits 0x10 + 0x200 + 0x400), which are the ones
  implicated in the wake glitches, while leaving the rest of the display
  stack alone.

## 2. `acpi_backlight=native` — backlight keys

- **Symptom:** the keyboard's brightness keys don't drive the internal
  panel backlight.
- **Fix:** prefer the native (GPU) backlight interface over the ACPI
  one, which is the interface the desktop's brightness controls actually
  work through on this machine.

## 3. `GRUB_GFXMODE=auto` — GRUB rendering

- Lets the bootloader use the firmware graphics mode instead of falling
  back to text/low-res on the internal panel.
- **Honest limit:** this only affects what GRUB itself draws. It does
  **not** light external monitors before Linux loads — see
  `../preboot-external-display/`.

## Apply

1. Edit `/etc/default/grub`: add the two flags to your existing
   `GRUB_CMDLINE_LINUX_DEFAULT` (keep your own `resume=UUID=…` — it is
   **machine-specific**, it points at your swap; the example file uses a
   placeholder on purpose), and set `GRUB_GFXMODE=auto`.
2. Back up first: `sudo cp /etc/default/grub /root/grub.bak`
3. `sudo update-grub`
4. Reboot.

## Verify

```sh
cat /proc/cmdline
```

Both flags should appear in the running kernel's command line. Checking
`/etc/default/grub` alone is not proof — the generated
`/boot/grub/grub.cfg` and the live `/proc/cmdline` are the truth.

## Caveats

- Quoting matters: distro files may use single *or* double quotes around
  the value; match what's there and confirm the flags actually landed in
  `grub.cfg` after `update-grub`.
- `dcdebugmask` trades a little idle power (PSR off) for wake
  reliability.
