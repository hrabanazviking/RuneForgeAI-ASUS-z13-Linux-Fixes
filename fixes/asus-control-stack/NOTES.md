# asus-control-stack — asusctl + supergfxctl on Ubuntu/Kubuntu 26.10

**Status: fixed (built from source, services running).**

## Symptom

Out of the box there is no working ASUS control layer on this machine
under a current Ubuntu: no fan/performance profiles, no charge limit
control, no graphics-mode switching — and the asus-linux PPA has **no
build for Ubuntu 26.10** ("stonking"), so the usual install road is a
dead end.

## Fix

Build the stack from the asus-linux project's own sources:

- **asusctl 6.3.8** (upstream commit `321b111`) —
  https://gitlab.com/asus-linux/asusctl — MPL-2.0
- **supergfxctl** (same era) —
  https://gitlab.com/asus-linux/supergfxctl — MPL-2.0

## Build

Build dependencies (compiler toolchain, cmake, and the libclang the
bindgen step needs) come from the Ubuntu archive. Then, in each source
tree:

```sh
make build
sudo make install
```

## Services — read this before "fixing" them

- **asusd is udev-activated by design.** Its unit has no `[Install]`
  section, so `systemctl enable asusd` is meaningless and its
  "disabled" look is normal. It starts on demand via udev/systemd when
  the hardware is present. Don't chase it.
- **supergfxd** is a normal unit: `sudo systemctl enable --now
  supergfxd.service`.

## Verify

```sh
asusctl info
asusctl profile get
supergfxctl -g
```

On the reference machine this yields profiles working (set:
**Performance on AC / Quiet on battery**) and graphics mode **Hybrid**.

## Caveats

- Battery charge limit: the reference machine reports 100% and it was
  **left as-is** — set yours deliberately (`asusctl` exposes it), don't
  copy a number blind.
- A source build means distro kernel/driver updates can occasionally
  need a rebuild; re-running `make build && sudo make install` after a
  major kernel jump is the whole maintenance story.
- Upstream is actively developed and has reorganised since 6.3.8 (the
  project has since moved homes and supergfxctl's role has changed in
  newer releases). These notes describe the 6.3.8-era build that is
  verified on this machine; for newer versions, upstream's own docs
  govern.
