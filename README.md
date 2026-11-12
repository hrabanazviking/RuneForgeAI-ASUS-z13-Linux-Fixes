# RuneForgeAI ASUS z13 Linux Fixes

The ASUS z13 is a powerful small supercomputer for AI development, but has a massive string of issues that need fixing under Linux. Linux is the only OS any serious developer is going to use, so these issues are an oversight by ASUS and AMD. I own one and this repo is my own fixes for it.The bits are opensource under whatever liscense they have.

## Free — made to help fellow owners

**Everything in this repo is free, and non-commercial.** These fixes were
made to get one owner's own ASUS ROG Flow Z13 working properly under
Linux, and they are shared for one reason: to help other owners of the
same machine. If you have a Z13, take what you need — no charge, no
catch, no product, nothing for sale. They are offered honestly and
as-is: no warranty, no support obligation, no promise they fit your
exact setup. Check each fix's notes before applying it, and back up
before you change system files.

## What this is

A collection of working fixes, configs and hard-won notes for the
**ASUS ROG Flow Z13 (2025, model GZ302EA)** — AMD Strix Halo
(Ryzen AI Max, Radeon 8060S iGPU, gfx1151) — running **Kubuntu / Ubuntu
26.10**. Every fix here was applied and verified on a real machine;
anything that could not be fixed is written up honestly as a known
limitation instead of being left for the next owner to rediscover the
hard way.

Each fix lives in its own folder under `fixes/` with the real artifact
(config, hook, script) plus a `NOTES.md` covering symptom, cause, fix,
how to apply, how to verify, and caveats.

## The fixes

| Fix | Symptom | Status |
|---|---|---|
| [folio-keyboard-wakeup](fixes/folio-keyboard-wakeup/) | Folio keyboard can no longer wake the machine after the first suspend | **Fixed** |
| [s0ix-sleep-drain](fixes/s0ix-sleep-drain/) | S0ix "sleep" keeps draining the battery | **Configured** — suspend-then-hibernate after 2 h |
| [wifi-mt7925-aspm](fixes/wifi-mt7925-aspm/) | MediaTek MT7925 Wi-Fi drops out | **Resolved on kernels ≥ 6.17** — A/B-verified: the disable_aspm workaround is not needed there and is withdrawn on this machine; on older kernels the original note applies |
| [ethernet-r8152](fixes/ethernet-r8152/) | USB-C Ethernet (Realtek r8152) link flapping; adapter dead after idle | **Fixed** — software readiness: working udev power rule (the popular modprobe option is a dead parameter — see the notes) and the NetworkManager profile-pinning pitfall both documented |
| [grub-flags](fixes/grub-flags/) | Panel glitches on wake (PSR/VRR); backlight keys don't work | **Fixed** — kernel flags + GRUB gfx mode |
| [unified-memory-params](fixes/unified-memory-params/) | ROCm caps GPU allocations at ~61 GB of the unified memory | **Fixed** — GTT pool 60.75 → 121.5 GiB; an 80 GB single allocation verified (and: the `amd_iommu=off` variant kills the NPU — use `iommu=pt`) |
| [asus-control-stack](fixes/asus-control-stack/) | No ASUS profiles/control under Linux; PPA has no 26.10 build | **Fixed** — asusctl 6.3.8 + supergfxctl built from source |
| [speaker-gain](fixes/speaker-gain/) | Internal speakers quiet — the CS35L41 amps boot on the low-gain firmware profile | **Fixed** — 19.5 dB bincfg profile selected; "Gain: 19" read back at probe, twice (loudness itself judged by ear) |
| [pytorch-gfx1151](fixes/pytorch-gfx1151/) | Stock PyTorch ROCm wheel segfaults on gfx1151 | **Fixed** — AMD TheRock arch-matched wheels (+ honest fp32 caveats) |
| [tensile-fp32-tables](fixes/tensile-fp32-tables/) | fp32 GEMM fallback: rocBLAS ships exactly one placeholder SGEMM solution for gfx1151 — fp32 crawls at ~2.5 TFLOPS | **Fixed** — self-tuned Tensile tables built from a retargeted mature pool: 3.2–6.9× (4096³ 2.37 → 7.95 TFLOPS), true IEEE fp32, wheel files untouched, one-file rollback ⚠ one pool kernel hangs the GPU — blacklisted in the notes |
| [npu-userland](fixes/npu-userland/) | XDNA 2 NPU unusable from Linux userland; the documented EP road is Windows-only | **Working** — XRT from Ubuntu universe + memlock drop-in; FastFlowLM serves an LLM on the NPU (81.96 tok/s decode, NPU-lock log proof) |
| [server-power-on-ac](fixes/server-power-on-ac/) | Machine sleeps on AC power | **Optional** — a preference, not a defect fix |
| [no-fingerprint](fixes/no-fingerprint/) | Fingerprint auth stack installed by default | **Optional** — privacy choice: full removal |
| [preboot-external-display](fixes/preboot-external-display/) | External monitors stay dark until Linux loads | **Known limitation** — firmware behaviour, no fix known |
| [greeter-gpu-wedge](fixes/greeter-gpu-wedge/) | Login screen (SDDM) flashes black/white continuously — the greeter wedges the GPU in a reset loop | **Known issue** — verified workaround: restart the display manager (trigger chain identified; if the first login after it collapses, restart once more — see notes) |

Plus one recipe file: [recipes/vulkan-llama-whisper.md](recipes/vulkan-llama-whisper.md)
— building llama.cpp / whisper.cpp with Vulkan on gfx1151 (including the
SPIRV/glslang packages everyone misses), and the uv interpreter-pin
lesson for AI front-end tools.

## Using a fix

1. Open the fix's folder and read its `NOTES.md` first — several fixes
   have a verify step and caveats that matter.
2. Back up the file you're replacing (the notes say where).
3. Copy the artifact into place with the `install` command given in the
   notes, then run the verify step. Don't trust that an edit "took" —
   check the live state the notes point at (`/proc/cmdline`, the sysfs
   parameter, the health script's verdict, …).

Nothing in this repo is machine-specific: no serial numbers, no UUIDs,
no network names, no personal paths. Where a value genuinely differs
per machine (the GRUB `resume=` UUID), the file ships a clearly marked
placeholder — use your own.

## Verified on

- ASUS ROG Flow Z13 **GZ302EA** (AMD Ryzen AI Max / Strix Halo)
- GPU: AMD Radeon 8060S, **gfx1151** (RDNA 3.5)
- OS: **Kubuntu 26.10**, kernel **7.3.0-10-generic**
- PyTorch fix verified end-to-end up to a real GPU image generation
  through ComfyUI; numbers are in the fix's notes.

## Licenses & credits

True to the purpose above — free help for fellow owners — this repo
mostly stands on other people's open-source work. Credit and licenses:

### This repo's own material

The scripts, configs and notes written for this repo are covered by the
**MIT License** in the [LICENSE](LICENSE) file at the repo root. They
were written for the repo owner's own machine and are shared freely and
non-commercially, to help other Z13 owners — see the purpose statement
at the top of this README.

### Upstream programs these fixes build on

| Program | License | Credit / upstream |
|---|---|---|
| asusctl | MPL-2.0 | asus-linux project (Luke Jones et al.) — https://gitlab.com/asus-linux/asusctl |
| supergfxctl | MPL-2.0 | asus-linux project — https://gitlab.com/asus-linux/supergfxctl |
| PyTorch | BSD-3-Clause | PyTorch contributors — https://github.com/pytorch/pytorch |
| ROCm | MIT (component licenses vary; AMD's table governs) | AMD — https://rocm.docs.amd.com/en/latest/about/license.html |
| TheRock (gfx1151 nightly wheels) | MIT | AMD ROCm — https://github.com/ROCm/TheRock |
| rocBLAS / Tensile | MIT (AMD component table; some distro records also note bundled BSD-3-Clause bits) | AMD ROCm — https://github.com/ROCm/rocm-libraries |
| llama.cpp | MIT | Georgi Gerganov and the ggml-org contributors — https://github.com/ggml-org/llama.cpp |
| whisper.cpp | MIT | Georgi Gerganov and contributors — https://github.com/ggml-org/whisper.cpp |
| Ollama | MIT | Ollama — https://github.com/ollama/ollama |
| ComfyUI | GPL-3.0 | Comfy Org / comfyanonymous — https://github.com/Comfy-Org/ComfyUI |
| Linux kernel drivers (amdgpu, mt7925e, hid) | GPL-2.0-only with Linux-syscall-note | The Linux kernel project — https://docs.kernel.org/6.0/process/license-rules.html |

License identifiers above are the SPDX identifiers from each project's
own LICENSE file / official license listing, checked against the
upstream sources. Where a fix modifies behaviour of an upstream program
(kernel flags, module options, a PAM example), the upstream program
keeps its own license — this repo only contributes the small configs
and notes around it.
