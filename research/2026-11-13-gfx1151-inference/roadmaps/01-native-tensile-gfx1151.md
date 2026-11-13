# Roadmap I — Native `gfx1151` Tensile kernel generation and adaptive selection

**Mission:** advance beyond retargeted navi31 FP32 GEMM tables by creating and evaluating **native, legal kernel configurations** tuned for gfx1151's compute units, wave behavior, cache/LPDDR5X environment, and real AI shapes. Protect the current measured winners as the control. This is a proposal for Yrsa's consideration, not a statement about what her teams have or have not started.

## Current evidence to preserve

- The existing project's four `Type_SS` transpose combinations cover NN, NT, TN, TT with a per-combination retargeted pool, 361 candidates evaluated, and 20 keyed winners per combination (14 principal grid entries plus 6 smaller-shape entries).
- Baseline stock NN 4096³ is reported as **2.374 TFLOPS**, tuned **7.946 TFLOPS**. Other cases yield 3.2–6.9× improvements. A four-layer FP32 MLP training step improves **34.78 → 14.76 ms**; Qwen2.5-0.5B FP32 inference rises by only ~5%.
- Original retargeting from navi31 means kernels are not necessarily optimized for this APU's memory hierarchy or performance/power envelope. The repo estimates ~8.5 TFLOPS as a representative current achieved ceiling and warns that theoretical FP32 peak is not a realistic guaranteed target.
- **Known dangerous candidate:** retargeted `Ailk_Bljk` solution named `Cijk_Ailk_Bljk_SB_MT64x4x32_..._TT4_1` with local solution index `1162084410` hangs the GPU; indices are **per file**, not global. Do not enumerate into the production candidate set. Additional excluded classes: `GSU4/GSUAMB` internal errors, problematic tiny tiles at 8192³, cross-build library mixing.

## Campaign A — Freeze provenance and truth baseline

**A01** Inventory GPU PCI ID (`Device 1586` in the current project notes), gfx target, power mode, clock ranges, Mesa/kernel/firmware, TheRock wheel hashes, ROCm/HIP runtime, Tensile version, Python/torch/llama.cpp versions, library SHA256s and the current effective environment. Save to a machine-readable test manifest.

**A02** Archive exact stock and retuned dispatch maps, source YAML, compiled `.co`/`.dat` hashes, all blacklist rules, and both numeric and quality baselines. Label evidence `stock`, `retargeted`, `candidate-native`, and `candidate-hybrid`. No implicit overwrites.

**A03** Install a health gate: before each experiment, run the repository's existing `torch-health.py`, record idle temperature and power, and confirm GTT/NPU identity. Stop on any GPU reset, regression, or exception. Arrange a recovery workflow that does not depend on the GPU being responsive.

**Exit gate:** existing winner table can be reproduced within predefined variance; rollback tested; test harness distinguishes true kernel time from full framework time.

## Campaign B — Shape census from actual models

**B01** Capture GEMM calls from representative fp32, fp16, bf16 training/inference workloads, with shapes, `M,N,K`, transpose, strides, batched count, alpha/beta, memory layout and invoking backend. The `F.linear` path must not be confused with plain `a @ b`; the project's note already mapped transpose orientation empirically.

**B02** Include separate shape families: tiny-M (1/2/4/8/16/32), medium-M (64/128/256), long-prefill M (512–4096), large square/rectangular GEMM, irregular dimensions, batched attention-projection shapes, and MoE expert-local small groups. Use model-derived shape histograms to weight optimization; avoid overfitting to cubic 4096³.

**B03** Record the *actual* BLAS backend. If the workload uses a dedicated quantized ggml kernel rather than rocBLAS, do not credit improvements to Tensile or prioritize this roadmap for that path.

**Exit gate:** top real-world shapes and time share explain at least 90% of observed GEMM time for the chosen representative workloads; exclusions logged.

## Campaign C — Generate native candidates rather than merely retarget

**C01** Study Tensile's documented parameters, including `WorkGroup`, `ThreadTile`, `MatrixInstruction` (where legal for datatype/instructions), `LoopUnroll`, `GlobalReadVectorWidth`, `DepthU`, `PrefetchGlobalRead`, LDS usage, `LocalSplitU`, global split, register pressure, occupancy, masking for odd sizes, and wave/tiling constraints. Verify supported options against the **pinned Tensile source and gfx1151 ISA**, not generic examples.

**C02** Construct a constrained *parameter grammar* for native kernels. Use hardware-valid combinations only; compile in batches, record generation failures, eliminate near-duplicate generated kernels, and reject candidates exceeding resource envelopes. Include both vector/VALU F32 paths and any architecture-valid alternatives after correctness/performance inspection. Never assume FP32 benefits automatically from matrix instructions just because FP16 does.

**C03** Search in stages: coarse Latin-hypercube/random or design-of-experiments coverage; guided local neighborhoods around promising configurations; multi-objective Bayesian or evolutionary exploration only after the simple baselines demonstrate signal. Keep diversity across shape families. Store rejected configurations and reasons.

**C04** Incorporate architectural objectives: LPDDR5X bandwidth, L2/cache reuse, register occupancy, wave32 scheduling where supported, power/frequency scaling, and full-kernel dispatch overhead. Test when a smaller kernel with less peak TFLOPS wins for tiny-M decode.

**C05** Analyze each candidate with hardware counters only when the profiler supports the device and the metric. Do not mistake generic profiler support for permission to use features that are limited to CDNA/MI350. Fall back to wall time, HIP events, memory microbenchmarks, and validated counters.

**Exit gate:** a new-native candidate library exists, with artifact hashes, candidate-level failure records, and rigorous float64-reference correctness for all four transpose classes, without touching the wheel's original files.

## Campaign D — Benchmark, select and validate

**D01** Compare stock / current retargeted / new native candidates, same session and environment, randomized A/B ordering, warm-up, repeated medians + dispersion, thermal and sustained checks. Record energy per operation as an additional axis.

**D02** Check small/odd dimensions, tails, strides, zero-sized accepted cases, batched operations, non-contiguous `F.linear`, alpha/beta semantics, NaN/Inf behavior, gradients where relevant, high-amplitude inputs, random seeds and numerical tolerance specific to each format. Compare to float64 and to a known correct reference; do not demand bitwise identity from different reduction orders.

**D03** Treat microbench winners as provisional. After reconstructing dispatch tables, run full PyTorch workloads and one or more *model-level* benchmarks. The project's earlier 24.1 tokens/s Qwen regression illustrates the danger of large-tile winners being dispatched to tiny-M decode.

**D04** Use Pareto selection: kernel latency, model tokens/s, memory, temperature, power, quality and robustness. Keep a separate winner for a shape family where appropriate. Evaluate whether match-table nearest-key behavior produces surprising crossovers at sizes not in the grid.

**Exit gate:** demonstrable advantage over existing tuned baseline, not just AMD stock. Suggested provisional criterion: ≥10% robust end-to-end gain in at least one target use case, no >3% repeatable regressions on important cases, zero correctness or reliability regressions. These are **project goals, not observed results**.

## Campaign E — Deploy as an optional, version-locked profile

**E01** Keep tuned library in an isolated path and use opt-in `ROCBLAS_TENSILE_LIBPATH` after verifying current pinned rocBLAS actually honors it. Re-run an intentionally tiny benign dispatch diagnostic before enabling any performance workloads. Document compatibility to each exact wheel/ROCm/Tensile SHA.

**E02** Self-check candidate table manifest, code-object integrity, kernel ISA and selected rows. Do not mix rocBLAS and hipBLASLt binaries from different releases.

**E03** Release profiles e.g. `safe-stock`, `known-good-retargeted`, `native-fp32-lab`, `native-fp32-validated`, chosen per process/venv rather than modifying the whole machine. Rollback = unset opt-in and verify stock baseline returns.

**E04** Maintain an upstream-ready package with reproducible search config, benchmark CSVs, test scripts, **all excluded failures**, license compliance and concise results.

## Research questions Yrsa's team should answer

1. Which exact layer limits F32 speed today: issued VALU instructions, occupancy, cache/memory, workgroup scheduling, codegen, or dispatch overhead?
2. Are additional 2–3× native SGEMM improvements plausible on real transformer-derived matrices, or has the practical memory/power roofline already been reached?
3. Do new native table wins translate into *PyTorch or inference* gains; if not, which path is outside rocBLAS?
4. Does hipBLASLt provide better candidates for some shapes, and does this pinned version support safe offline tuning on gfx1151?
5. Are small-M GEMV kernels the dominant remaining problem, requiring a separate purpose-built path rather than Tensile SGEMM?

## Suggested outputs

- Native parameter-search grammar, allowlist, blacklist, compiler diagnostic corpus.
- Reproducible search notebooks/scripts and machine-readable winner data.
- `gfx1151` kernel performance atlas by shape/precision/power mode, plus artifact hashes.
- Accuracy and model-level A/B report; optional non-default production profile; upstream technical report.

**Primary references:** existing repo `fixes/tensile-fp32-tables/NOTES.md`; Tensile docs https://rocm.docs.amd.com/projects/Tensile/en/latest/src/index.html ; kernel parameters https://rocm.docs.amd.com/projects/Tensile/en/docs-7.1.1/src/conceptual/kernel-parameters.html ; offline rocBLAS tuning https://rocm.docs.amd.com/projects/rocBLAS/en/latest/how-to/Programmers_Guide.html .
