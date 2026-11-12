# pytorch-gfx1151 — make PyTorch actually run on the Radeon 8060S

**Status: fixed (arch-matched TheRock nightly wheels), with honest
performance caveats below.**

Target hardware: AMD Strix Halo iGPU, **gfx1151** ("Radeon 8060S
Graphics", RDNA 3.5, 40 CUs), on Ubuntu/Kubuntu 26.10. This is the fix
that takes PyTorch on this machine from *segfault on first use* to a
fully proven GPU stack (a real ComfyUI image generation included).

## Symptom

Install PyTorch the obvious way — the `rocm7.1` wheel from
download.pytorch.org — and it *looks* installed, then **segfaults** the
first time a kernel actually runs on the GPU.

## Diagnosis (measured, not guessed)

The crash is a **null-pointer dereference inside the wheel's own bundled
`libhsa-runtime64.so`**, on the first kernel dispatch. It is not a
permissions problem and not a driver problem:

- The user had full read/write access to `/dev/kfd` (ACL-verified), and
  `rocminfo` enumerated the gfx1151 agent cleanly.
- Vulkan compute on the same driver was flawless throughout.
- The wheel's private HSA runtime is simply arch/kernel-mismatched for
  gfx1151. This is a tracked upstream issue (**issue #2991**); AMD's
  published remedy for gfx1151 is their **TheRock** arch-matched builds.

No environment variable fixes the stock wheel. In particular do **not**
reach for `HSA_OVERRIDE_GFX_VERSION` — with the correct build below the
arch matches natively and the override would *break* that match.

## The cure: TheRock nightly wheels for gfx1151

Install torch/torchvision/torchaudio from AMD's gfx1151 nightly index,
at these exact pins (the build verified end-to-end on the Z13):

```
torch       2.12.0a0+rocm7.13.0a20260411
torchvision 0.27.0a0+rocm7.13.0a20260411
torchaudio  2.11.0a0+rocm7.13.0a20260411
index: https://rocm.nightlies.amd.com/v2/gfx1151/
```

`install-pytorch-gfx1151.sh` in this folder does exactly this into a
venv you name, e.g.:

```sh
./install-pytorch-gfx1151.sh "$HOME/ai/venvs/ai-dev"
```

The ROCm runtime arrives as pip packages (`rocm`,
`rocm-sdk-libraries-gfx1151`, …) — **no system ROCm install is needed**.

Two install gotchas, both learned the hard way:

- **The fix carries a lower version number than the broken wheel**
  (2.12.0a0 vs 2.13). A plain `uv pip install --upgrade` will silently
  keep the broken one. Pin the exact versions.
- **AMD pins must always come from the gfx1151 index**, never from PyPI
  or download.pytorch.org, or the broken build comes back.

## Proof (reference machine)

- `torch.cuda.get_arch_list()` → `['gfx1151']` — native, no overrides.
- Correctness: 1024² matmul vs CPU, allclose (max diff 1.9e-4).
- Training loop: cross-entropy loss 2.333 → 0.0 over 20 steps.
- Stress: 1,000 mixed iterations, peak 1.91 GB, no crash.
- Throughput @8192³: **fp16 20.3 TFLOPS, bf16 20.7 TFLOPS** (CPU fp32
  comparison: 1.11 TFLOPS).
- Ecosystem intact afterwards: transformers, accelerate, peft,
  trl, sentence-transformers, faster-whisper all import and run.
- Crown proof: ComfyUI generated a real 512×512 image from an SD 1.5
  checkpoint on the GPU (prompt executed in 6.65 s).
- Sustained load: 3 minutes of fp16 8192³ GEMM at ~70 W, peak 72 °C,
  no throttling.

`torch-health.py` in this folder is the one-command re-check: device
identity, a 2048² correctness probe, fp32/fp16 TFLOPS, a 50-iteration
stress, and a single `TORCH-HEALTH OK / DEGRADED / FAIL` verdict. Run it
with the venv's Python after any install or upgrade.

## Maturity warnings — read before "optimising"

The seated build is the best configuration AMD currently ships for
gfx1151, but it is a nightly and fp32 is its weak side:

- **fp32 GEMM is ~2.5 TFLOPS** (2.55 @4096, 1.60 @8192) — roughly 8% of
  the silicon's ~30 TFLOPS fp32 peak. Root cause is proven: the
  rocBLAS/hipBLASLt Tensile logic shipped for gfx1151 is
  **fallback-grade** (the gfx1151 solution tables exist; they are just
  not tuned). TF32 backend flags are no-ops in this build and there is
  no bf16x9 mode. This is a tuning gap in AMD's tables, not a missing
  kernel and not something a source rebuild fixes.
- **A newer nightly (20260513 libs) is a trap as a default:** it passes
  basic checks and slightly improves fp16 @8192, but its *default* fp32
  dispatch is broken — hipBLASLt returns
  `HIPBLAS_STATUS_NOT_SUPPORTED` and fp32 falls back to 0.23–1.23
  TFLOPS. Workarounds exist (TF32 flag, or
  `TORCH_BLAS_PREFER_HIPBLASLT=0` restores 2.45–2.70 TFLOPS), but a
  build whose defaults are broken does not replace the seated pins.
- **`TORCH_BLAS_PREFER_HIPBLASLT=1`** on the seated build lifts fp16
  @8192 by ~+29% but *craters* fp32. fp16-only, per-process opt-in —
  never set it globally.
- **Never mix library builds.** A rocBLAS-only swap changed nothing; a
  rocBLAS + hipBLASLt hybrid from two different builds **hung the GPU**
  (HW exception, core dump). Library surgery across builds is a dead
  end on this arch.
- `torch.compile` on fp32: no gain measured. bf16-split fp32 emulation:
  either bf16-accurate (not fp32) or slower than native. Dead ends,
  recorded so nobody re-walks them.

Re-check AMD's gfx1151 nightly index every month or so: the day they
ship tuned gfx1151 SGEMM logic, fp32 should jump — until then, ~2.5
TFLOPS fp32 with excellent fp16/bf16 is the honest state of the art.

## Credits

- PyTorch — BSD-3-Clause — https://github.com/pytorch/pytorch
- ROCm / TheRock / rocBLAS / Tensile — AMD, MIT —
  https://github.com/ROCm/TheRock ,
  https://rocm.docs.amd.com/en/latest/about/license.html
