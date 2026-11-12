# no-fingerprint — OPTIONAL: remove fingerprint authentication entirely

**Status: done on the reference machine (privacy choice, not a defect fix).**

> This is a deliberate privacy/ownership choice: no fingerprint
> enrollment and no fingerprint authentication, on any login path. Only
> follow it if that's your policy too.

## What was on the machine

A stock Ubuntu 26.10 install **does** ship the fingerprint stack —
`fprintd`, `libpam-fprintd` and `libfprint` — even on a machine where no
fingerprint reader driver is present. Check yours before assuming:

```sh
dpkg -l | grep -i fprint
```

## Removal

1. **Purge the PAM module and the daemon:**

   ```sh
   sudo apt purge fprintd libpam-fprintd
   ```

2. **Mask the service** (covers anything that might reinstall or
   socket-activate it later):

   ```sh
   sudo systemctl mask fprintd.service
   ```

   After purging, this leaves `fprintd.service` as a symlink to
   `/dev/null`; `systemctl is-enabled fprintd.service` reports
   `masked`.

3. **Neutralise the leftover PAM file.** `/etc/pam.d/kde-fingerprint`
   is owned by the KDE screen locker package (on the reference machine,
   `libkscreenlocker6`), so it can't simply be deleted with the purge.
   Comment out its two `pam_fprintd.so` lines instead — the shipped
   `kde-fingerprint.example` shows the exact pattern:

   ```
   # disabled: fingerprint authentication removed (see NOTES.md): auth	required	pam_fprintd.so
   # disabled: fingerprint authentication removed (see NOTES.md): password required       pam_fprintd.so
   ```

   Back the file up first (`sudo cp /etc/pam.d/kde-fingerprint
   /root/kde-fingerprint.pam.bak`).

## Verify

- `dpkg -l | grep -i fprint` → no installed (`ii`) fingerprint packages.
- `systemctl is-enabled fprintd.service` → `masked`.
- No active `pam_fprintd.so` lines remain in `/etc/pam.d/` (only
  commented ones):
  `grep -rn pam_fprintd /etc/pam.d/ | grep -v '^\s*#'`

## Caveats

- If your machine genuinely has a supported reader and you *want*
  fingerprint login, this whole folder is not for you.
- Package updates to the screen locker could restore the PAM file;
  re-check after major upgrades.
