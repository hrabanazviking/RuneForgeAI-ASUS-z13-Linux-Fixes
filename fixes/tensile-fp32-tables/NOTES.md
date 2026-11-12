# tensile-fp32-tables — tuned fp32 GEMM tables for gfx1151

**Status: fixed (measured on the reference machine). fp32 GEMM is
3.2–6.9× faster than stock across the measured grid, correctness
identical to stock, fp16 untouched, and the whole change rolls
back by removing one wiring file. Read the warnings before
building anything from these files.**

## Symptom

On the TheRock PyTorch wheels for gfx1151 (see
[`../pytorch-gfx1151/`](../pytorch-gfx1151/)), fp32 matrix
multiplication crawls at roughly **2.4–2.6 TFLOPS** — while the
same silicon runs fp16 GEMM at ~27 TFLOPS. Anything that trains
or infers in true fp32 (no TF32, no fp16 tricks) pays for it.

## Diagnosis — AMD ships a placeholder, not a tuning

rocBLAS picks GEMM kernels from per-architecture *Tensile logic*
files. Counting the solutions shipped in the production library
(torch `2.12.0a0+rocm7.13.0a20260411`, TheRock wheels) for
gfx1151, per transpose combination:

| Problem type | Solutions per transpose combo (gfx1151, shipped) |
|---|---|
| **SGEMM (Type_SS, fp32)** | **exactly 1** |
| BB (bf16) | 62–156 |
| HH (fp16) | 60–200 |
| I8I (int8) | 158–202 |

The lone shipped SGEMM solution is
`Cijk_Alik_Bljk_..._MT32x32x8_..._TT2_2_WG16_16_1_WGM8` — a
**32×32 macro tile** with a 2×2 thread tile: a placeholder config,
not a tuned one. (The arch-independent generic fallback file
carries only 4.) Contrast with a mature architecture's SGEMM
logic in the rocBLAS source tree — navi31 / gfx1100 carries
**134–366 solutions per combo**. AMD tunes SGEMM for its flagship
discrete parts; the APU gets the fallback. That one row of the
table is the entire defect.

Which logic file serves which PyTorch pattern was proven by
one-at-a-time `.co` ablation at 4096³:

| PyTorch pattern | Transpose | Tensile contraction |
|---|---|---|
| `a @ b` | NN | `Ailk_Bljk` |
| `a @ b.t()` — i.e. `F.linear` | NT | `Alik_Bljk` |
| `a.t() @ b` | TN | `Ailk_Bjlk` |
| `a.t() @ b.t()` | TT | `Alik_Bjlk` |

One more fact the whole fix stands on, proven empirically on
this build: **`ROCBLAS_TENSILE_LIBPATH` is authoritative.**
Pointing it at a byte-copy of the stock library reproduced the
baseline exactly (fp32 2.466 / 2.461 / 2.491 TFLOPS at
1024³/2048³/4096³); deleting the gfx1151 SGEMM `.dat`/`.co` from
the copy produced a hard segfault instead of a silent fallback
to the wheel's originals. So a replacement library is really
used — and a broken one fails loudly, not silently.

## The method — retarget a mature pool, tune it on the metal

1. **Retarget.** Take navi31's SGEMM solution pool from the
   rocBLAS source tree and retarget it to gfx1151 (ISA
   `[11,0,0]` → `[11,5,1]`, device list → `Device 1586`, the
   Strix Halo PCI device). The four retargeted logic files ship
   in this folder.
2. **Build with the wheel's own toolchain.** Tensile v4.44.0
   builds the library using the SDK bundled inside the wheel
   itself (HIP 7.13.60980, AMD clang 23), so the output matches
   the shipped file conventions (lazy master + per-type msgpack
   `.dat` + `.co`, V5 code objects).
3. **Tune through PyTorch itself.** Upstream's own retune tool
   (`TensileRetuneLibrary`) is bit-rotted at HEAD — it never
   passes required global parameters and dies on a missing
   `OutputPath` key — so a **forced-dispatch harness** replaced
   it: for each candidate kernel, rewrite the combo's matching
   table so every grid key points at that candidate, then bench
   through torch's real production dispatch path, with a
   correctness check against a float64 reference in every run
   and a watchdog per candidate. Pool: 80–98 candidates per
   combo, 361 total. Grid: cubes 512³–8192³, transformer shapes,
   and — after the lesson in the warnings below — small-M decode
   shapes (256³, M=1 and M=32), across **all four transpose
   patterns**. (One orientation fact the harness had to prove
   with a marker kernel: the matching-table key is **[N, M, K]**
   in torch terms, because rocBLAS swaps operands.)
4. **Keep the measured winners only.** The final table carries
   20 entries per combo (14 grid + 6 small shapes), each the
   measured on-device winner for its shape, recorded in
   `winners.json` in this folder.

## Measured result (stock vs tuned, back-to-back, same session)

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

- **MLP training step** (4×fp32 Linear, batch 256):
  34.78 ms → **14.76 ms (2.36×)**.
- **Qwen2.5-0.5B-Instruct fp32 inference:** 34.74 →
  **36.57 tok/s** (+5% — and see the small-shape warning below:
  the first tuned build *regressed* this to 24.1 tok/s before
  the small shapes were tuned).
- **Stress:** 1000 × 4096³ iterations sustained **8.26 TFLOPS**,
  GPU peak **69 °C**, no errors.
- **Correctness:** this is true IEEE fp32 SGEMM — no TF32 or
  split-precision emulation anywhere in the winning kernels.
  Max-abs error vs a float64 reference stays in the same family
  as stock everywhere (2e-4 @1024³, ~1e-3 @4096³, 2.3e-3
  @8192³ — the same growth stock shows). Odd shapes (1000³,
  257×513×129, 128³) and batched `bmm` all pass.
- **fp16/bf16/int8 were not touched** — their shipped tables
  were already mature, and they were left exactly as shipped.

## ⚠ Warnings — read before building or shipping a library

- **One kernel in the candidate pool HANGS the GPU outright:**
  `Cijk_Ailk_Bljk_SB_MT64x4x32_..._TT4_1` in the `Ailk_Bljk`
  pool, solution index **1162084410**. It is blacklisted and is
  **not** in the built library this entry's numbers come from.
  If you rebuild from these logic files, exclude it first — it
  must never ship in a rebuilt library. (Solution indices are
  per-logic-file: the same index number in another combo's file
  names a *different* kernel. The blacklist is this name, in
  this pool.)
- **Two more failure classes were excluded by measurement, not
  by taste:** `GSU4`/`GSUAMB` (GlobalSplitU=4) kernels fail
  deterministically with `HIPBLAS_STATUS_INTERNAL_ERROR` on
  gfx1151 through this stack, and EPS1 tiny-tile kernels spin
  for minutes at 8192³ (watchdog-killed during tuning).
- **Tune the small shapes too.** The first assembled library
  carried grid keys ≥512³ only — and made Qwen fp32 decode
  *slower than stock* (24.1 vs 34.4 tok/s), because decode-time
  GEMMs have tiny M (1–32) and nearest-key matching sent them
  to the 512³ big-tile winner, while the stock 32×32 fallback
  tile is genuinely good at tiny shapes. Six small keys per
  combo (256³, 1×4096×4096, 32×4096×4096, 1×896×896,
  128×1024×1024, 64×2048×2048) with measured small-tile winners
  fixed it. A big-tile-only library is a regression wearing a
  benchmark's clothes.
- **The honest ceiling.** ~8.5 TFLOPS is ~28% of this silicon's
  ~30 TFLOPS theoretical fp32 peak (40 CUs). The winners derive
  from navi31's pool, tuned for GDDR6 bandwidth/latency — not
  natively tuned for LPDDR5X unified memory. A from-scratch
  native parameter search is the known road further up; this
  entry is the retune, and it does not pretend to be more.
- One grid entry is knowingly soft: `Ailk_Bjlk` at
  4096×4096×8192 measures 5.85 TFLOPS — weaker than its
  neighbours, still ~2.4× stock-class at that shape.
- Run-to-run variance on the tuning machine was ±25% (it was
  shared during the campaign); winners were picked across
  repeated measurements, and the winner families agree across
  phases (big-tile MT128-class, `AMAS3`, `TT8_8`/`TT8_16`,
  GSU1).

## What's in this folder

- `gfx1151_Cijk_<combo>_SB.yaml` ×4 — the retargeted SGEMM
  Tensile logic files (the candidate pools the tuned library
  was built from; see the blacklist warning above).
- `grid.yaml` — the benchmark shape grid.
- `winners.json` — the measured winner per shape and combo
  (GFLOPS, solution index, kernel name): the 20-entry final
  table per combo.
- `MANIFEST.txt` — SHA-256 of the compiled `.dat`/`.co` files
  in the library that produced the numbers above.

## Apply (wiring)

The wheel's own files are **never touched**. The tuned library
is a separate directory: a full copy of the stock rocBLAS
Tensile library with only the four Type_SS gfx1151 `.dat`/`.co`
pairs replaced by the tuned builds. Point rocBLAS at it:

```sh
export ROCBLAS_TENSILE_LIBPATH=~/ai/tensile-gfx1151/lib
```

For Python venvs, the durable pattern is a `sitecustomize.py`
in the venv's `site-packages`, so every interpreter start picks
it up and an explicit environment variable still wins:

```python
# sitecustomize.py — place in your venv's site-packages
import os

os.environ.setdefault(
    "ROCBLAS_TENSILE_LIBPATH",
    os.path.expanduser("~/ai/tensile-gfx1151/lib"),
)
```

## Verify

Bench fp32 GEMM through your framework before and after wiring
(`torch.randn(4096, 4096) @ torch.randn(4096, 4096)` timing, or
the `torch-health.py` in [`../pytorch-gfx1151/`](../pytorch-gfx1151/)):
expect roughly **2.4 → 7.9 TFLOPS** at 4096³. If you see a
segfault instead, your library directory is incomplete — the
env path is authoritative, there is no silent fallback (that's
the proof above, cutting the other way).

## Rollback

Remove the wiring: delete the `sitecustomize.py` file(s) (or
unset `ROCBLAS_TENSILE_LIBPATH`). Nothing else to undo — the
wheel was never modified, so stock behaviour returns exactly.
