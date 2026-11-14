# Our Own Tuned fp32 GEMM (Tensile) Tables for gfx1151 — Campaign Report

**Machine:** the reference machine (ROG Flow Z13, AMD Ryzen AI Max+ 395 / Strix Halo, Radeon 8060S, gfx1151)
**Date:** 2026-11-12 (overnight, EST)
**Order (Volmarr):** "we build our own better tables. We never wait for slow hardware makers to build the software they are too lazy to build."
**Outcome: DONE AND PROMOTED.** fp32 GEMM on the reference machine is now **3.2–6.9× faster** across the measured grid, with correctness identical to stock, fp16 untouched, and a one-file rollback.

---

## Headline verdict (same-session, back-to-back, ai-dev venv, `verdict_bench.py`)

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

- **MLP training step** (4×fp32 Linear, batch 256): 34.78 ms → **14.76 ms (2.36×)**.
- **Qwen2.5-0.5B-Instruct fp32 inference:** 34.74 → **36.57 tok/s** (+5%; see the decode-regression note in Stage 3 — the first tuned build regressed this to 24.1 and was fixed before promotion).
- **Stress:** 1000 × 4096³ iterations sustained **8.26 TFLOPS**, GPU peak **69 °C**, no errors.
- **Correctness:** max-abs error vs float64 reference in the same family as stock everywhere (2e-4 @1024³, ~1e-3 @4096³, 2.3e-3 @8192³ — the same growth stock shows). Odd shapes (1000³, 257×513×129, 128³) and batched `bmm` all pass. This is true IEEE fp32 SGEMM — no TF32 or split-precision emulation anywhere in the winning kernels (accuracy checks ran against float64 at every stage).

Promotion gate from the task (≥1.5× at 4096³ AND no regression anywhere): **cleared decisively** (3.3× at 4096³; the one regression found was fixed and re-measured before promotion).

---

## Stage 0 — Reconnaissance: the fallback, quantified

**Shipped library layout** (production torch 2.12.0a0+rocm7.13.0a20260411, TheRock wheels):
`~/ai/venvs/ai-dev/lib/python3.12/site-packages/_rocm_sdk_libraries_gfx1151/lib/rocblas/library/` — 151 files: `Kernels.so-000-gfx1151.hsaco`, the lazy master `TensileLibrary_lazy_gfx1151.dat`, and per-problem-type `.dat`/`.co`/`.hsaco` files.

**The smoking gun (msgpack-parsed solution counts in the shipped gfx1151 files):**

| Problem type | Solutions per transpose combo (gfx1151, shipped) |
|---|---|
| **SGEMM (Type_SS)** | **exactly 1** (all 4 combos) |
| BB (bf16) | 62–156 |
| HH (fp16) | 60–200 |
| I8I | 158–202 |

The lone shipped gfx1151 SGEMM solution (`Cijk_Alik_Bljk_..._MT32x32x8_..._TT2_2_WG16_16_1_WGM8`): a 32×32 macro tile, 2×2 thread tile, depthU 8 — a placeholder config, not a tuned one. The generic (arch-independent) fallback file carries 4 solutions. Contrast with a mature architecture's SGEMM logic in the rocBLAS source tree (navi31 / gfx1100): **134–366 solutions per combo**, with 1,054–5,275 size-table entries. (navi33/gfx1101 ships 1 solution per combo too — AMD tunes SGEMM only for flagship parts; this is the "fallback-grade" disease, proven numerically.)

**Override road — proven empirically:** `ROCBLAS_TENSILE_LIBPATH` is honoured by this librocblas build. Marker test: pointing it at a byte-copy of the stock library reproduced the baseline exactly (fp32 2.466/2.461/2.491 at 1024/2048/4096); removing the gfx1151 SGEMM `.dat`/`.co` from the copy produced a hard segfault instead of silently falling back to the wheel's originals — the env path is authoritative.

**Dispatch map** (which Tensile contraction each torch fp32 pattern uses, proven by one-at-a-time `.co` ablation at 4096³): NN (`a@b`) → `Ailk_Bljk`; NT (`a@b.t()`, i.e. `F.linear`) → `Alik_Bljk`; TN (`a.t()@b`) → `Ailk_Bjlk`; TT → `Alik_Bjlk`.

**Generator:** Tensile v4.44.0 (ROCm/Tensile HEAD `e8a8999`), rocBLAS source HEAD `defce20`, cloned to `~/ai/tensile-lab/src/`. Compilers: the wheel's own bundled SDK (HIP 7.13.60980, AMD clang 23). `TensileCreateLibrary` output matches the shipped file conventions byte-for-byte in structure (lazy master + per-type msgpack `.dat` + `.co` names). Device facts: 40 CUs, PCI ID 1002:1586, silicon fp32 peak ≈ 30 TFLOPS (40 CU × 128 FMA × 2 flop × ~2.9 GHz).

---

## Stage 1 — Pipeline proof (3 sizes, one combo)

Retargeted the navi31 `Ailk_Bljk` SGEMM logic to gfx1151 (ISA `[11,0,0]`→`[11,5,1]`, device list → `Device 1586`), pruned to the 3 winners at 1024/2048/4096 plus 10 big-tile diversity candidates = **13 solutions**, built with `TensileCreateLibrary` (lazy loading, msgpack, `--code-object-version=V5`), and merged into a copy of the stock library replacing only that combo's files.

Build gotchas solved (all recorded in `~/ai/tensile-lab/`): setting `ROCM_PATH` to the raw wheel SDK breaks clang's device-library search — a symlink-farm ROCm root fixes it; Tensile validates compiler basenames, so the compiler wrapper is named `amdclang++`; V5 code objects are required.

**Result:** fp32 **7.63 / 7.09 / 7.77 TFLOPS** at 1024/2048/4096 vs stock 2.47/2.46/2.49 (**~3.1×**), correctness in the stock family (2.4e-4 / 4.5e-4 / 1.1e-3), fp16 unchanged. **Dispatch evidence:** hiding our `.co` in the test library makes torch's `hipblasSgemm` fail with `HIPBLAS_STATUS_INTERNAL_ERROR`; restoring it restores the speed — the measured kernels are ours.

---

## Stage 2 — Full-grid tuning on this hardware

`TensileRetuneLibrary` at this Tensile HEAD is broken (it never passes required global parameters — `HipConfig`, `ROCmAgentEnumeratorPath`, compilers — and dies later on a missing `OutputPath` key; two patches only revealed the next hole). Rather than keep patching a bit-rotted tool, I built a harness on the machinery already proven in Stage 1:

1. **Candidate pools:** per combo, the navi31 solutions ranked by their recorded gfx1100 GFLOPS, top 64 + best-per-tile-family diversity → **80–98 candidates per combo** (361 total across the 4 combos), retargeted to gfx1151 and compiled into one library per combo.
2. **Forced-dispatch benchmarking:** for each candidate, rewrite the combo's matching table so every grid key points at that candidate, then bench **through torch itself** (the real production dispatch path) at the grid sizes, with a correctness check vs float64 in every run and a 150 s watchdog per candidate.
3. **Phases:** phase 1 = 6 sizes (cubes 1024–8192, 256×4096×4096, 4096×4096×8192); phase 2 = per-size top-3 candidates on the remaining 8 grid sizes (512–6144 cubes, transformer shapes 2048×8192×2048, 1024×16384×4096, 8192×2048×8192, 512×8192×8192); phase 3 = small-shape tuning (256³, M=1 and M=32 decode shapes, skinny shapes) with small-tile candidates.
4. **Table-key orientation proven empirically** with a marker kernel: the matching key is **[N, M, K]** in torch terms (rocBLAS's operand swap), not [M, N, K].

Coverage: Ailk_Bljk 98/98 candidates, Alik_Bljk 88/88, Ailk_Bjlk 95/95, Alik_Bjlk 69/80 (its tail is pathological tiny-tile configs, cut deliberately), plus full top-ups on a reduced grid.

**Failure classes found and excluded by measurement:**
- `GSU4/GSUAMB` (GlobalSplitU=4) kernels: deterministic `HIPBLAS_STATUS_INTERNAL_ERROR` on gfx1151 through this stack.
- EPS1 tiny-tile kernels: spin for minutes at 8192³ (watchdog-killed, recorded).
- **One kernel HANGS the GPU outright:** `Cijk_Ailk_Bljk_SB_MT64x4x32_..._TT4_1` (Ailk_Bljk, solution index 1162084410) — blacklisted by name in the lab records; it is not in the final library.

Run-to-run variance on this shared machine (Aesir forge co-resident) is ±25%; winners were picked across repeated measurements (phase 1 + top-up + phase 2 overlaps agree on the winner families: big-tile MT128-class, `AMAS3`, `TT8_8/8_16`, GSU1).

---

## Stage 3 — Verdict bench

Full table at the top of this report. Additional results:

- **Qwen decode regression — found, diagnosed, fixed.** The first assembled library (grid keys ≥512³ only) made Qwen2.5-0.5B fp32 inference *slower* than stock: 24.1 vs 34.4 tok/s. Cause: decode-time GEMMs have tiny M (1–32); nearest-key matching sent them to the 512³ big-tile winner, while the stock 32×32 fallback tile is genuinely good at tiny shapes. Fix: phase-3 small-shape tuning added six small keys per combo (256³, 1×4096×4096, 32×4096×4096, 1×896×896, 128×1024×1024, 64×2048×2048) with measured small-tile winners. Re-measured back-to-back: **stock 34.74 vs tuned 36.57 tok/s** — regression eliminated, small shapes now also win.
- **Stress:** 1000 × 4096³, sustained 8.26 TFLOPS, peak temp 69 °C (start 45 °C), final correctness 9.9e-4 (stock family).
- The final table carries **20 entries per combo** (14 grid + 6 small), each the measured on-device winner for its shape, with its measured GFLOPS recorded in the `speed` field.

## Stage 4 — Promotion (done)

- **Library home:** `~/ai/tensile-gfx1151/lib` on the reference machine — a full rocBLAS Tensile library (stock copy) with only the 4 Type_SS gfx1151 `.dat`/`.co` pairs replaced by ours. **The wheel's own files were never touched.**
- **Wiring:** a `sitecustomize.py` in each of `~/ai/venvs/ai-dev` and `~/ai/ComfyUI/venv` (site-packages) does `os.environ.setdefault("ROCBLAS_TENSILE_LIBPATH", "~/ai/tensile-gfx1151/lib")`. An explicit env var still wins; **rollback = delete those two files** (or point the env var at a stock copy). Nothing else to undo.
- **Post-promotion verification (clean shell, no env var):** ai-dev gemm bench fp32 9.26/7.62/**8.15** at 1024/2048/4096, fp16 27.9; `torch-health` → **TORCH-HEALTH OK, fp32 7.67 TFLOPS** (the same tool read 2.50 before); ComfyUI crown image regenerated on the wired venv — `/mnt/vault/comfyui/output/yrsa_crown_tensile_00001_.png`, prompt executed in 8.56 s, real 512×512 PNG verified.
- Documented on the machine in `~/ai/AI_STACK.md` (recipe, path, rollback, verify command). Configs + manifest + all lab scripts preserved in `~/ai/tensile-gfx1151/` on the machine and in `~/workspace/your_files/research/rog-flow-z13/tensile-gfx1151/` on the VM (the 19 MB of library binaries live on the machine in two places: `~/ai/tensile-gfx1151/lib` and `~/ai/tensile-lab/final-lib`).

## Incidents and honest limits

- **The machine rebooted mid-campaign** (2026-11-12 ~01:41 EST — not by me; it was the parallel robustness campaign's Stage 6 reboot, per the incident section of `Z13_FIX_LOG_2026-11-11.md`, whose SDDM-greeter incident then wedged the GPU ring with 41 ring timeouts 01:41–01:53 — that, not a tuning kernel, is what killed the Alik_Bjlk sweep at 69/80 and made the GPU briefly unavailable to new torch processes). No data was lost (results are append-only JSONL) and the sweep tails were completed or consciously cut afterwards. Side-discovery: after that reboot `/dev/kfd` lacked the user ACL and torch reported "No CUDA GPUs are available". Remedy proven: `sudo setfacl -m u:<user>:rw /dev/kfd /dev/dri/renderD128` (a desktop login also restores session ACLs). Recorded in AI_STACK.md.
- `TensileRetuneLibrary` at the cloned HEAD is broken upstream (missing required parameters); the custom harness replaced it. The two one-line patches I tried remain in the lab clone only — nothing in production was patched.
- **Remaining headroom:** ~8.5 TFLOPS is ~28% of the ~30 TFLOPS silicon fp32 peak. The winning kernels come from navi31's pool, tuned for GDDR6 bandwidth/latency, not for LPDDR5X unified memory. A from-scratch native parameter search on gfx1151 (Tensile BenchmarkProblems forks over tile/LDS/vector widths) is the known road further up; it is a bigger campaign than this one's grid retune. Only SGEMM was tuned — the wheel's fp16/bf16/int8 tables were already mature (60–200 solutions) and were left exactly as shipped. TF32 was deliberately not touched: this campaign is honest IEEE fp32.
- One grid entry is knowingly soft: Ailk_Bjlk at 4096×4096×8192 measures 5.85 TFLOPS (its winner there is weaker than at neighbouring shapes; still 2.4× stock-class performance at that shape).

## Pointers

- Machine: `~/ai/tensile-gfx1151/` (library + configs + scripts + winners.json + MANIFEST.txt), lab `~/ai/tensile-lab/` (sources, build trees, per-candidate results JSONL, logs).
- VM: this report + `~/workspace/your_files/research/rog-flow-z13/tensile-gfx1151/` (logic YAMLs, grid, winners, manifest, scripts).
- Prior art: `PYTORCH_FIX_REPORT_2026-11-11.md`, `PYTORCH_MATURITY_REPORT_2026-11-11.md` (same folder).
