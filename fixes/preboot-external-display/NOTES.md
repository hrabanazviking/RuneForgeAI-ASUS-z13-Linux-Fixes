# preboot-external-display — KNOWN LIMITATION

**Status: known limitation (investigated, no fix known).**

## What doesn't work

On the ASUS ROG Flow Z13 (GZ302EA), **external monitors stay blank
until Linux loads**. Before that — firmware splash, GRUB menu, early
boot — only the internal panel lights up. There is no mirroring of the
built-in screen to an external display in the pre-boot environment.

## What was tried

- `GRUB_GFXMODE=auto` (and GRUB's gfxterm output) so the bootloader
  draws through the firmware graphics path. GRUB renders fine on the
  internal panel; the external display still stays dark until the
  Linux amdgpu driver takes over.
- Verified by direct observation on a reboot with an external monitor
  attached: blank pre-boot, normal behaviour the moment Linux is up.

## Conclusion

This is firmware behaviour, not a Linux setting: the GZ302 firmware
does not drive external displays before an OS display driver loads.
Nothing in GRUB or the kernel command line changes it.

## Roads not yet tried (for the next owner who wants to dig)

- Digging through the BIOS/UEFI setup for a display-output option.
- Trying the other USB-C port for the external display.
- Booting with the lid closed.

These are unverified ideas, listed so nobody repeats the GRUB work
expecting a different result.

## Once Linux is up

Displays behave completely normally (the desktop handles the external
monitor as expected). This note is only about the pre-boot window.
