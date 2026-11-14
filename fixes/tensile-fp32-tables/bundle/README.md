# Tuned fp32 (SGEMM) Tensile Tables for gfx1151 — a donation

**What this is.** A drop-in rocBLAS Tensile library for AMD **gfx1151**
(Strix Halo — Ryzen AI Max+ 395, Radeon 8060S) whose fp32 (SGEMM,
`Type_SS`) tables are tuned instead of placeholder. AMD ships exactly
**one** SGEMM solution per transpose combination for gfx1151 in the
ROCm 7.13 TheRock wheels — a 32×32-tile placeholder — so true fp32 GEMM
crawls at ~2.4 TFLOPS on silicon that does fp16 at ~27 TFLOPS. This
library replaces only the four Type_SS gfx1151 `.dat`/`.co` pairs with
measured winners; every other file is byte-identical to the shipped
stock library. Result: **fp32 GEMM 3.2–6.9× faster** across the
measured grid (4096³ NN: 2.374 → **7.946 TFLOPS**), true IEEE fp32 —
no TF32, no split-precision emulation — with correctness in the same
family as stock.

**Provenance — read this before citing.** These tables are
**RETARGETED**, not native and not AMD's own tuning: the solution pool
is navi31's (gfx1100) mature SGEMM logic from the rocBLAS source tree,
retargeted to gfx1151 (ISA `[11,0,0]` → `[11,5,1]`, device `1586`),
built with Tensile v4.44.0 using the toolchain bundled in the wheel
itself (HIP 7.13.60980, AMD clang 23, V5 code objects), then tuned
**on real gfx1151 hardware**: 361 candidates benched through PyTorch's
own dispatch path with a float64 correctness check in every run; the
final table keeps the 20 measured winners per transpose combination
(14 grid shapes + 6 small/decode shapes). A from-scratch native
gfx1151 search is a separate, later campaign; this donation does not
pretend to be it.

**Stack it was tuned and proven on.** TheRock nightly ROCm
**7.13.0a20260411**, torch `2.12.0a0+rocm7.13.0a20260411`, on an ASUS
ROG Flow Z13 (40 CUs, LPDDR5X unified memory). gfx1151 only.

## Install

The wheel's own files are never touched. Unpack, and point rocBLAS at
the included `lib/` directory:

```sh
export ROCBLAS_TENSILE_LIBPATH=/path/to/tensile-gfx1151-fp32-tables/lib
```

For Python venvs, the durable pattern is a `sitecustomize.py` in the
venv's `site-packages` calling
`os.environ.setdefault("ROCBLAS_TENSILE_LIBPATH", ...)`. Rollback =
remove the wiring; stock behaviour returns exactly. Verify by benching
fp32 GEMM at 4096³ before/after: expect roughly **2.4 → 7.9 TFLOPS**.
(`ROCBLAS_TENSILE_LIBPATH` is authoritative in this build — an
incomplete library directory segfaults rather than silently falling
back. That was proven during the campaign and cuts both ways: keep
`lib/` complete.)

## Measured evidence (stock vs tuned, back-to-back, same session)

| Case (fp32) | Stock TFLOPS | Tuned TFLOPS | Ratio |
|---|---|---|---|
| NN 1024³ | 1.442 | 9.028 | 6.3× |
| NT 1024³ | 1.240 | 8.592 | 6.9× |
| TN 1024³ | 1.718 | 9.767 | 5.7× |
| TT 1024³ | 1.455 | 9.226 | 6.3× |
| NN 2048³ | 1.471 | 7.660 | 5.2× |
| NN 4096³ | 2.374 | 7.946 | 3.3× |
| NN 8192³ | 1.688 | 8.412 | 5.0× |
| NN 2048×8192×2048 | 2.380 | 8.431 | 3.5× |
| NN 1024×16384×4096 | 2.258 | 8.322 | 3.7× |
| NN 256×4096×4096 | 2.281 | 7.312 | 3.2× |
| fp16 4096³ (sanity) | 27.19 | 28.49 | unchanged |

- MLP training step (4×fp32 Linear, batch 256): 34.78 ms → **14.76 ms**.
- Qwen2.5-0.5B-Instruct fp32 inference: 34.74 → **36.57 tok/s**.
- Stress: 1000 × 4096³ sustained **8.26 TFLOPS**, GPU peak 69 °C.
- Correctness: max-abs error vs float64 reference in the same family
  as stock (2e-4 @1024³, ~1e-3 @4096³, 2.3e-3 @8192³). Full method,
  grids and caveats: `CAMPAIGN_REPORT.md` in this bundle.

## ⚠ Excluded kernel — do not re-add

One candidate-pool kernel **hangs the GPU outright** and is
**blacklisted**: `Cijk_Ailk_Bljk_SB_MT64x4x32_..._TT4_1`
(`Ailk_Bljk` pool, solution index **1162084410** — indices are
per-logic-file). It is **not** in this library and must stay excluded
from any rebuild from the included logic files. Also excluded by
measurement: `GSU4`/`GSUAMB` kernels (deterministic
`HIPBLAS_STATUS_INTERNAL_ERROR` on gfx1151 through this stack) and
EPS1 tiny-tile kernels (spin for minutes at 8192³).

## Contents

- `lib/` — the full drop-in rocBLAS Tensile library (151 files,
  ~19 MB): stock copy with only the 4 Type_SS gfx1151 `.dat`/`.co`
  pairs replaced by the tuned builds.
- `logic/` — the retargeted SGEMM Tensile logic YAMLs (the candidate
  pools), the benchmark `grid.yaml`, and `winners.json` (the measured
  winner per shape/combo the final tables were built from).
- `CAMPAIGN_REPORT.md` — the full campaign report with method and
  honest limits (~8.5 TFLOPS is ~28% of the ~30 TFLOPS fp32 peak;
  the winners are GDDR6-tuned navi31 configs running on LPDDR5X).
- `SHA256SUMS.txt` — SHA-256 for every file in this bundle.

## License and attribution

The logic files and library format derive from AMD's **Tensile /
rocBLAS**, shipped with ROCm under the **MIT License** (AMD copyright
preserved; see ROCm/rocm-libraries). The tuning, retargeting,
benchmarking and packaging in this bundle were done by
**hrabanazviking** (RuneForgeAI) on his own hardware and are donated
under the same MIT terms, with AMD's attribution intact. This is a
community donation — it is not an AMD product and implies no AMD
endorsement.
