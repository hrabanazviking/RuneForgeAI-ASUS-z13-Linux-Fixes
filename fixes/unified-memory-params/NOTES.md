# unified-memory-params — remove the ~61 GB ROCm allocation ceiling

**Status: fixed (pool size and a >61 GB allocation both measured
after the change).**

## Symptom

Strix Halo is a unified-memory machine — CPU and GPU share one big
pool (128 GB on the reference machine) — but under stock settings
ROCm caps GPU allocations at roughly **61 GB**. Anything that wants
a bigger single GPU allocation (a large model, a big tensor) hits
a wall that the hardware does not actually have.

## Fix

Three kernel parameters, merged into `GRUB_CMDLINE_LINUX_DEFAULT`
in `/etc/default/grub` (example file shipped alongside):

```
iommu=pt amdgpu.gttsize=126976 ttm.pages_limit=32505856
```

What each one does:

- **`iommu=pt`** — puts the IOMMU in pass-through mode: devices
  that don't need address translation get identity mapping, which
  removes the translation overhead on the GPU's path. Crucially,
  the IOMMU stays *present* — see the warning below.
- **`amdgpu.gttsize=126976`** — the size, in MiB, of the GTT
  (Graphics Translation Table) pool the amdgpu driver may use for
  GPU allocations: 126976 MiB = 124 GiB requested.
- **`ttm.pages_limit=32505856`** — TTM's own page ceiling,
  32505856 pages × 4096 = the same 124 GiB, so the memory manager
  doesn't quietly cap below what `gttsize` asked for. The two
  numbers must move together.

## Measured result (reference machine)

- GTT pool (`mem_info_gtt_total`): **60.75 GiB → 121.5 GiB**
  (65,227,026,432 → 130,454,048,768 bytes). The driver grants
  slightly less than the raw 126976 MiB request — what matters is
  the ~61 GB cap is gone, doubled.
- Allocation proof: PyTorch allocated a single **80.0 GB fp32
  tensor on the Radeon 8060S** — impossible under the old pool —
  filled it with 1.5, and a 1024-element sample summed exactly
  (1024 × 1.5 = 1536.0). Released cleanly.
- Cross-check: the NPU is still enumerated by `xrt-smi` under the
  new parameters — `iommu=pt` did not hurt it (see
  `../npu-userland/`).

## ⚠ Do NOT use the `amd_iommu=off` variant

Community guides for this platform sometimes suggest turning the
IOMMU off entirely (`amd_iommu=off`) to reach the same place.
**It kills the NPU** — XDNA needs the IOMMU. `iommu=pt` is the
variant that removes the ceiling and keeps the NPU alive.

## Held back, on purpose

`amdgpu.no_system_mem_limit=1` circulates as a companion flag. It
was **deliberately not applied** on the reference machine: the
GTT/TTM change alone removed the cap that mattered, so the extra
lever stays staged and unproven rather than stacked in. If you
hit a ceiling this fix doesn't lift, that flag is the next thing
to test — on its own, so you know what did it.

## Apply

1. **Back up first:** `sudo cp /etc/default/grub /root/grub.bak`
   (date it). Keep your own `resume=UUID=…` — it is
   machine-specific; the shipped example uses a placeholder.
2. Add the three parameters to your existing
   `GRUB_CMDLINE_LINUX_DEFAULT`.
3. `sudo update-grub`, then reboot.
4. A previous kernel with its own GRUB entries is your fallback if
   a boot goes wrong — check one exists before you reboot.

## Verify

```sh
cat /proc/cmdline   # all three parameters present
```

and the pool itself, via the driver's debugfs
(`mem_info_gtt_total`) or by simply allocating more than 61 GB
from your framework and watching it succeed.

## Rollback

Restore the `/etc/default/grub` backup, `sudo update-grub`,
reboot. Nothing else on the system is touched.
