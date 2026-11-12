# folio-keyboard-wakeup — keep the folio keyboard able to wake the machine

**Status: fixed (armed).**

## Symptom

The detachable folio keyboard stops being able to wake the machine from
suspend: USB wakeup for the keyboard gets reset across the suspend/resume
cycle, so after the first sleep the keyboard is dead as a wake source.

## Cause

Nothing re-asserts `power/wakeup = enabled` for the folio keyboard's USB
device across suspend. The setting does not reliably survive the cycle on
this machine (ASUS ROG Flow Z13, GZ302EA).

## Fix

A systemd system-sleep hook, `50-folio-keyboard-wakeup`, runs on both the
`pre` (going to sleep) and `post` (resume) phases. It walks
`/sys/bus/usb/devices/*`, matches the ASUS folio keyboard USB IDs —
vendor `0b05`, product `1a30` (folio keyboard) or `18c6` (N-KEY variant) —
and writes `enabled` to each match's `power/wakeup`.

## Apply

```sh
sudo install -m 0755 50-folio-keyboard-wakeup /lib/systemd/system-sleep/
```

No service to enable: systemd runs everything in
`/lib/systemd/system-sleep/` around suspend automatically.

## Verify

```sh
for d in /sys/bus/usb/devices/*; do
  [ "$(cat $d/idVendor 2>/dev/null)" = "0b05" ] && \
  grep -H . $d/idProduct $d/power/wakeup 2>/dev/null
done
```

The folio keyboard's `power/wakeup` should read `enabled`. Final proof is
one real sleep: suspend, then wake the machine from the folio keyboard.

## Caveats

- The hook matches by USB ID, so it also does the right thing if the
  keyboard is re-enumerated on a different USB port.
- It deliberately enables wake for this keyboard; if you *don't* want the
  keyboard to wake the machine, don't install it.
