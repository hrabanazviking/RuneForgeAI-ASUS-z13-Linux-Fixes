# Complete Z13 gfx1151 AI-inference research and roadmaps
**Bundle edition:** 2026-11-13. **No machine changes were performed.**
This single-file document consolidates the research and roadmap package for handing to Yrsa. Each original file remains available separately inside the ZIP.

---

## DOCUMENT: `README.md`

# RuneForgeAI / ASUS ROG Flow Z13 (2025): Native gfx1151 and AI-Inference Research

**Research snapshot:** 2026-11-13  | **Target:** GZ302EA, Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 128 GB unified LPDDR5X, Kubuntu 26.10  | **Status:** proposed engineering research, **not** a deployed modification.

Prepared to support **Volmarr's direction and Yrsa Freydisdottir's engineering leadership**. This is a documentation-only research and roadmap bundle. Nothing here modifies the machine, changes the production tables, upgrades ROCm, or overrides Yrsa's ongoing investigations. Yrsa should reconcile each idea with her current measurements before scheduling it.

## The central technical discovery

The project's existing work reports FP32 GEMM **3.2–6.9× faster than stock** on its measured grid after retuning Tensile for `gfx1151`, while the measured Qwen2.5-0.5B full-FP32 decode rate rose only **34.74 → 36.57 tokens/s** (about **5.3%**). Both observations can be true: standalone GEMM speed is not equivalent to full LLM inference speed. Decode may be constrained by DRAM bandwidth, quantized matrix-vector operations, attention/KV traffic, kernel dispatch, and expert routing. Tuning native SGEMM is valuable, but it cannot by itself unlock all quantized LLM pathways.

The machine's **256 GB/s** advertised peak memory bandwidth is a *theoretical hardware specification*, not an achieved sustainable decode rate. Measure effective memory bandwidth with profiling and workload-specific roofline analysis. The usable ~121.5 GiB GTT pool reported by this repository is a device-specific validated configuration, not a guarantee that every runtime can allocate or use that capacity.

## Navigating the bundle

| File | Purpose | Priority |
|---|---|---|
| [roadmaps/01-native-tensile-gfx1151.md](roadmaps/01-native-tensile-gfx1151.md) | Generate genuinely native kernel candidates, validate, autotune, select, roll back | High |
| [roadmaps/02-quantized-llm-inference.md](roadmaps/02-quantized-llm-inference.md) | Accelerate GGUF quantized GEMV/MMQ, MoE, prefill/decode, HIP and Vulkan | Highest for real-world LLM use |
| [roadmaps/03-attention-kv-and-speculation.md](roadmaps/03-attention-kv-and-speculation.md) | Long-context attention, KV cache, speculative decoding, tool-use correctness | High |
| [roadmaps/04-uma-npu-and-runtime.md](roadmaps/04-uma-npu-and-runtime.md) | Shared memory, CPU/GPU/NPU concurrency, power, multi-model capacity | High |
| [roadmaps/05-verification-and-upstream.md](roadmaps/05-verification-and-upstream.md) | Reproducibility, automated checks, safe rollout, packaging, upstream collaboration | Mandatory |
| [research/01-hardware-roofline.md](research/01-hardware-roofline.md) | Hardware facts, model-based bottleneck analysis, realistic performance ceilings | Foundational |
| [research/02-tensile-and-precision.md](research/02-tensile-and-precision.md) | AMD Tensile/rocBLAS/hipBLASLt mechanisms, parameter families, precision pitfalls | Foundational |
| [research/03-runtime-landscape.md](research/03-runtime-landscape.md) | llama.cpp HIP/Vulkan, PyTorch, Triton, vLLM, FastFlowLM; evaluation criteria | Foundational |
| [research/04-validation-matrix.md](research/04-validation-matrix.md) | Workload matrix, benchmarks, quality gates, safety controls, data schema | Mandatory |
| [research/05-source-library.md](research/05-source-library.md) | Source links, claim provenance, version risks, watchlist | Reference |
| [templates/experiment-record.md](templates/experiment-record.md) | Reusable candidate evaluation protocol | Operational |
| [templates/results-schema.csv](templates/results-schema.csv) | Machine-readable performance/results template | Operational |

## Highest-value sequence (not a claim that current work is incomplete)

1. **Freeze a trustworthy baseline:** pin current working versions, measurements, model artifacts, kernel choices, power state, and fallback images. Save accuracy and full token-generation transcripts.
2. **Map the inference hot path:** profile representative *actual* models in HIP and Vulkan, separately for prefill, single-request decode, long context, MoE and concurrency. Identify whether each path invokes Tensile, hipBLASLt, ggml custom quant kernels or attention kernels.
3. **Native `gfx1151` search:** for real GEMM shapes, generate new legal configurations and tune them against existing winning tables with strict failure isolation and accuracy gates. Preserve the dangerous blacklists in the existing repository.
4. **Quantized first-class optimization:** select kernel dispatch and fused quantized GEMV/MMQ, dequantization, MoE routing, and cache movement experiments from the profiling evidence. Native Tensile alone cannot cover all of this.
5. **Long-context / speculation / NPU studies:** only after proving the model and backend are correct under realistic prompts; test power and contention explicitly.
6. **Promote by evidence:** side-by-side model-level metrics with no correctness regressions, easy per-process opt-out, complete provenance, reproducibility and independent test runs.

## Working definitions

- **Proven in user repository:** a measurement or working procedure documented in `RuneForgeAI-ASUS-z13-Linux-Fixes`; independently re-test before publishing generalized claims.
- **Externally documented:** a vendor or upstream capability. It does not mean validated on this exact Z13/Kubuntu/kernel combination.
- **Community-observed:** useful lead, not a universal prediction.
- **Hypothesis / research target:** a proposed experiment requiring benchmark evidence.
- **Success:** improved *correct* AI output per unit of time/energy/human attention, not a bigger isolated number.

## Non-negotiable safeguards

**Do not** mutate the working PyTorch wheels, swap rocBLAS across incompatible releases, enable the repo's blacklisted hanging Tensile kernel, or deploy untested kernel search results globally. The existing repository reports hangs under incompatible rocBLAS + hipBLASLt combinations and one specific retargeted candidate. Use a copied library plus `ROCBLAS_TENSILE_LIBPATH` or another version-correct, isolated opt-in mechanism, and run test jobs with external timeouts and remote/system rollback readiness. Keep IOMMU enabled for the NPU; the repo specifically warns against `amd_iommu=off`.

This document deliberately makes **no claim** to have executed the roadmaps or improved performance since the repo's last documented measurements.

## Project evidence / sources

- User repository: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes
- Existing tuning notes: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/tensile-fp32-tables/NOTES.md
- Existing ROCm and NPU notes: `fixes/pytorch-gfx1151/NOTES.md`, `fixes/unified-memory-params/NOTES.md`, `fixes/npu-userland/NOTES.md`
- AMD hardware specifications: https://www.amd.com/en/products/processors/desktops/ryzen/ryzen-ai-halo/ryzen-ai-max-plus-395.html
- All external primary sources with annotations are in [research/05-source-library.md](research/05-source-library.md).

---

## DOCUMENT: `roadmaps/01-native-tensile-gfx1151.md`

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

---

## DOCUMENT: `roadmaps/02-quantized-llm-inference.md`

# Roadmap II — Real quantized LLM inference on Radeon 8060S

**Mission:** optimize **correct** local LLM performance for Volmarr's everyday uses. The primary scoreboard is model-level prefill speed, time-to-first-token, decode speed, long-context stability, memory footprint, useful quality and watts/token. Tensile FP32 is only one contributor.

## Why this campaign outranks FP32 microbenchmarks for many local models

Most practical local LLMs run with **quantized weights** (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `IQ4_XS`, `Q8_0`, architecture-supported formats) and FP16/BF16 activations/accumulation or specialized low-bit operations. `llama.cpp` HIP and Vulkan backends have custom quantized MMQ/MMVQ kernels and backend heuristics. Some inference calls never invoke rocBLAS's `Type_SS` SGEMM catalog. Thus even a **6× FP32 GEMM acceleration** need not yield a corresponding LLM token-rate gain. The user's repository itself demonstrates this (large GEMM gains, ~5% FP32 Qwen rate improvement).

## Campaign A — Establish an inference truth table

Choose models actually useful to the user, subject to license, memory, and quality checks. Suggested representative **classes**, not prescribed downloads: dense 0.5–4B, dense 7–14B, MoE ~30–35B with ~3B active, dense ~27–32B, a ~70B-class quantized model if capacity allows, and a long-context tool-calling model. At minimum include one GGUF Q4_K_M, Q6_K or Q8_0, one importance-matrix/IQ quant if supported, and one non-GGUF torch model. Fix hashes/quant details before comparing.

For each model log **architecture, total params vs active experts, quant, file size, context length, KV type, concurrency, number of layers offloaded, actual backend path, batch/ubatch and speculative settings**. An MoE with 35B total/3B active has memory capacity needs based on total model size but per-token arithmetic closer to activated experts. Do not confuse them.

Use `llama-bench` for `pp`/`tg`, and `llama-server` for end-to-end TTFT, streaming tokens/s, concurrency, tool-call accuracy and power. Do not assume single-request `llama-bench` is a proxy for agent workflows. Record requests/sec at offered load and latency percentiles for concurrent serving.

**A exit gate:** immutable baseline per model/quant under both the current working HIP and Vulkan builds, including quality/correctness. A result without a recorded output is not a valid performance win.

## Campaign B — Find which kernels actually dominate

Profile one-token decode and long-prefill separately. Attribute time to:

- quantized `mul_mat` / `mul_mat_id` (MMVQ, MMQ, dequantization, BLAS fallback), including expert-wise MoE paths;
- attention and KV-cache read/write/copy/quantization;
- activation/norm/rope/sampling and graph/launch overhead;
- tensor transfers, CPU processing, memory-bandwidth pressure and any CPU/GPU/NPU contention;
- batch/concurrency and speculative verification.

Map every hot kernel name back to a **source file and chosen code path** in the pinned ggml build. Existing source provides `ggml/src/ggml-cuda/mmq.cu` and build switches `GGML_CUDA_FORCE_MMQ`, `GGML_CUDA_FORCE_CUBLAS`; in HIP, these names are historical and build-dependent. Forcing an option is an *experiment*, not automatically a faster or safer default.

**B exit gate:** top 5–10 kernels account for most time in target scenarios; identify their precision, dispatch decision and memory traffic.

## Campaign C — Native quantized and mixed-precision optimization

**C01: GEMV decode.** For `M=1` and tiny batch, optimize fused dequant + vector multiplication rather than copying full tensors into float first. Investigate vectorized unpack, per-block scaling and zero points, LDS/register tiling, wave-per-row/workgroup mapping, cache-friendly weight streams and occupancy. Tune separately by quant format and matrix shape. Quantized layout matters: bit packing and accuracy are not interchangeable across formats.

**C02: GEMM prefill.** For larger M and shared activations, compare ggml MMQ against dequant+hipBLAS/rocBLAS or datatype-native BLAS. Profile thresholds where each wins. Tune matrix tile sizes, architecture-specific WMMA use if legal, activation staging and workspace tradeoffs. Confirm whether the current ROCm build already has good RDNA3.5 heuristics before changing them.

**C03: MoE dispatch.** Measure per-expert active token counts, `mul_mat_id`, expert gather/scatter overhead, top-k sorting/routing, fused gate/up/down and grouped expert kernels. Very high expert counts often behave differently from dense matmul. Explore batched expert grouping and fused dequantization while preserving determinism and correct routing.

**C04: Mixed precision.** Profile FP16/BF16 pathways and tolerances before assuming custom fp32 will improve inference. Test any lower precision technique on representative quality evaluations (reasoning, code, tool JSON), not just matmul MSE. Quantization may hurt small models or long-context tasks more than it helps speed.

**C05: Dispatch map.** Build a measured per-architecture, per-quant, per-batch threshold table where dispatch selects correct MMVQ/MMQ/BLAS path. Version-lock the mapping and retain unmodified runtime as a rollback. Avoid global overrides of all models based on one benchmark.

**C exit gate:** model-level improvement on at least one priority model, stable quality, no hidden CPU fallback, and no material regressions for other representative models.

## Campaign D — HIP versus Vulkan, without ideology

Maintain two isolated executables built from **the same llama.cpp commit** and tested against identical model GGUF, quant, contexts, power mode and serving settings. The GPU is the same, but different backends may choose entirely different kernel implementations. Never claim HIP always wins or Vulkan always wins. Strix Halo community measurements through 2026 show examples in both directions.

Run paired correctness probes before counting tok/s. A mid-2026 `llama.cpp` HIP/gfx1151 issue reported *corrupt tool-call outputs* on certain model/backend/config combinations that passed simple sentence generation checks. That is a **historical issue and a regression-test lead**, not proof the current pinned version is broken. Include deep prompt/tool-array, parallel-request and prefix-cache tests. Record backend binary by its real executable path, not its launcher name.

**D exit gate:** a per-workload backed-up choice: `HIP`, `Vulkan`, or `CPU/NPU`, each with documented reason and exact version. No universal 'best backend' assumption.

## Campaign E — Measure end-to-end benefit and power

Run models across short interactive chat, 8k/32k/64k context, coding-agent prompts with many tools, image-generation-adjacent text prompts, and concurrent model calls. Capture *TTFT*, `pp` tok/s, `tg` tok/s, p50/p95 latencies, actual correctness, KV growth, peak resident memory, battery/AC power and GPU temperature. Keep the same data for stock, current-tuned and experimental profiles.

**Suggested goals (NOT predictions):** ≥15% repeatable decode gains or ≥20% prefill gain on a high-priority target without quality regressions; stable multi-hour sessions; no hung GPU; rollback under a minute. Reject apparent wins within run-to-run noise. Prefer a 10% real-workload gain over a 100% gain in an unused microbenchmark.

## Work packages for independent teams

- Kernel team: quantized GEMV/MMQ architecture-specific tuning and test kernels.
- Model team: selection, quantization, quality suite and output validation.
- Profiling team: path attribution, memory/roofline, thermal/performance traces.
- Runtime team: HIP/Vulkan builds, dispatch profile, API serving, launcher correctness.
- Reliability team: GPU resets, corruption regression, long soak, rollback.
- Integration team: outcome dashboards and interface to Yrsa's higher-level agent system.

**Sources:** `llama.cpp` build and backend https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md ; quantized MMQ source https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-cuda/mmq.cu ; feature matrix https://github.com/ggml-org/llama.cpp/wiki/Feature-matrix ; community benchmark https://github.com/ggml-org/llama.cpp/discussions/15021 ; correctness lead https://github.com/ggml-org/llama.cpp/issues/27579 .

---

## DOCUMENT: `roadmaps/03-attention-kv-and-speculation.md`

# Roadmap III — Long-context attention, KV cache and speculative decoding

**Mission:** optimize the tasks that matter to a multi-agent AI workstation: long research/code contexts, tool calls, simultaneous conversations, low latency and reliable decoding. These are separate from Tensor/BLAS tuning.

## Campaign A — Correct long-context baseline

Build scenarios with 1k, 8k, 32k and 64k+ prompts where supported by the selected model and runtime. Test a standard document Q&A, exact retrieval from early/middle/end of context, multi-tool JSON arguments, source code editing requirements, and conversational continuations. Include repeated sessions with prefix reuse and cold prefill.

For each scenario log: model+revision, quantization, KV precision, `ctx-size`, batch/ubatch, flash-attention on/off, prefix-cache on/off, slot count, positional encoding and sampling settings. Compare output quality with reference prompts under fixed seeds where supported; no claims about correctness from token speed alone.

**Gate:** reference correct outputs and an end-to-end latency breakdown, with regression probes for reported HIP corruption under complex tool arrays and concurrent slots.

## Campaign B — Efficient attention and cache traffic

- Profile attention kernel speed against context length and head size; identify whether prompt attention, decode attention, KV reads or memory management dominates.
- Evaluate backend-supported flash attention and its precise input/KV formats. Forcing flash attention without verifying backend/quant combinations can change accuracy or simply select fallback paths.
- Compare fp16/bf16, q8_0 and q4_0 KV caches where a selected runtime supports them. Report memory saved, output quality, decode overhead and supported attention implementations.
- Investigate paged/block KV and reuse for concurrent agents **only if** the runtime has correct ownership/isolation of requests and validated prefix semantics; avoid cross-slot contamination.
- Consider head-specific tile size, split-K or chunked attention only after profiling indicates a bottleneck; test uneven masks, very short context, high context, ALiBi/RoPE variants and model-specific architectures.

**Gate:** repeatable improvements in long-context TTFT and decode with equivalent quality, no cross-session content leakage, and rollback.

## Campaign C — Speculative decoding and early-exit strategies

Use `llama.cpp`'s documented draft-model, n-gram, EAGLE-3 and model-native MTP mechanisms where supported by the pinned release/model. These are alternatives, not universal add-on speed multipliers.

Measure both draft **acceptance rate** and real delivered target-token throughput. A larger draft length may generate more rejected tokens and slow the system. Record draft/target memory footprint, extra inference cost, latency distribution and long-context behavior. Check the exact runtime's current flag names; the spec-type interfaces have changed over time.

Candidate tests:

1. **No speculation**: correct reference.
2. **Same-model MTP** when the weight artifact includes usable heads.
3. **Small draft model** if tokenizers and sampling constraints are compatible.
4. **N-gram speculation** for code editing and repetitive text, benchmark under real agent prompts.
5. **Parallel speculative verification** only where accuracy and scheduling make sense.

Compare outputs with a statistically defensible metric under deterministic decoding or probability-preserving sampling where applicable. Record **accepted target tokens/sec**, not drafted tokens/sec.

**Gate:** any speculative profile promoted to default must outperform unspeculated baseline on representative prompts without introducing invalid outputs or unacceptable memory/power costs.

## Campaign D — Agent serving and concurrent correctness

Test 1/2/4/8 simultaneous sessions for the current target workload and record throughput, p95 latency, peak memory, per-session quality and cache isolation. Do not reuse a single end-to-end completion transcript as sufficient evidence: run multiple seeds, model architectures and prompt depths. Tag each session with unique sentinel text and verify no content appears in the wrong stream.

Investigate batching and queuing policies in real conditions: prompt-heavy background research versus interactive voice chat versus coding-agent execution. Prioritize interactive responsiveness without unnecessarily starving long batch tasks.

## Research warnings

- The 2026 community issue https://github.com/ggml-org/llama.cpp/issues/27579 reports certain HIP/gfx1151 tool-call and concurrency correctness regressions on specific builds. Verify whether fixes landed in the exact running checkout; test rather than presuming all HIP builds are affected.
- Simple short-response prompts can pass even while deep tool arrays fail. An HTTP 200 response is not evidence of correct inference.
- Don't assume flash attention, KV quantization or speculative decoding is always faster; benefits depend on model, backend, context, memory and batch.

**Sources:** https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md ; https://github.com/ggml-org/llama.cpp/wiki/Feature-matrix ; https://github.com/ggml-org/llama.cpp/issues/27579 ; https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md .

---

## DOCUMENT: `roadmaps/04-uma-npu-and-runtime.md`

# Roadmap IV — Unified-memory, CPU/GPU/NPU scheduling and sustainable inference

**Mission:** exploit the APU as a coherent *system*, not an isolated GPU. The Ryzen AI MAX+ 395 has a 16-core CPU, 40-CU Radeon 8060S, XDNA 2 NPU and 128 GB of physically shared LPDDR5X; shared memory increases capacity flexibility, but CPU/GPU/NPU workloads can compete for memory bandwidth and power.

## Existing project evidence

- The repo records **GTT pool 60.75 → 121.5 GiB** using `iommu=pt amdgpu.gttsize=126976 ttm.pages_limit=32505856`, while keeping the NPU visible. An 80 GB FP32 GPU tensor was allocated and validated. This is evidence for this machine's tested configuration, not advice to stack further kernel flags.
- On the project's pinned Kubuntu 26.10 build, the NPU is visible through `amdxdna` and XRT; `FastFlowLM` generated on the NPU with Qwen3-0.6B and a reported **81.96 tok/s** decode. This does not imply that any arbitrary model can be moved to the NPU.
- AMD advertises the processor memory at 256-bit LPDDR5X-8000 with **256 GB/s peak bandwidth**. Effective sustainable bandwidth to GPU models is workload- and power-dependent.

## Campaign A — Memory capacity and allocation integrity

1. Document real physical memory, `MemAvailable`, GTT/debugfs counters, pinned allocations, CPU model memory, page cache, resident CPU agents, NPU allocation and GPU device allocations across realistic model loads. Account for OS and safety margin; a 121.5 GiB GTT pool is not a promise of 121.5 GiB usable for weights plus KV cache.
2. Test allocator behavior at 40/60/80/96 GiB model+KV allocations as appropriate, not necessarily a single tensor. Check fragmentation, long-context KV growth, release behavior and swap involvement.
3. Analyze zero-copy/unified-memory path claims with actual traces; absence of explicit PCIe transfers does not equal no synchronization or zero allocation overhead. Record where pinned buffers or host-shared allocations affect backend correctness.
4. Compare mmap-on-demand, preloading, mlock, huge pages and model cache methods only where supported; ensure no configuration silently induces OOM or application pressure. Never turn off IOMMU to chase a microbenchmark when the NPU requires it.

**Gate:** reliable model loading/unloading under multi-agent use without OOM, stale mapped memory or hidden CPU fallback; state preserved through restarts.

## Campaign B — CPU/GPU/NPU role atlas

Define workloads for all three compute units: GPU large model decode/prefill, NPU small local models, CPU preprocessing/tokenization and fallback tasks. Measure them individually first, then pairwise and three-way under the same power modes. Record end-to-end tokens/s, task success, memory bandwidth, power and per-device temperature. A workload should be assigned to the NPU only after verifying compatible runtime/model/firmware and practical gains.

Candidate roles to **test**:

- NPU: suitable compact assistant, classifier, routing, wake-word or background inference where FastFlowLM or another verified implementation supports the exact architecture and model.
- GPU: the largest quantized LLM, high-throughput prefill, transformer attention and parallel workloads; verify HIP/Vulkan path per model.
- CPU: tokenizer, orchestration, I/O and limited preprocessing; avoid contention with the GPU memory fabric under heavy load.

Do **not** assert arbitrary split execution of one transformer between NPU and GPU is possible or beneficial. Transport and graph-format restrictions may eliminate the opportunity; explicit middleware and tests are required.

## Campaign C — Memory-bandwidth and power-aware scheduling

1. Measure sequential-stream bandwidth/latency with validated microbenchmarks and GPU profiler. Use actual achieved bandwidth as denominator for per-token weight-read efficiency, not always the advertised 256 GB/s.
2. Assess sustained throughput across machine-supported power profiles; do not assume the desktop AMD Halo platform's 120 W rating is achievable indefinitely in the thin 13-inch Z13 chassis. Record AC supply, charge cap, thermal and fan profiles, package power, GPU clock residency and throttling.
3. For multiple agents, compare parallel model processes against queued requests to one model server. Model instances duplicate weights and KV caches; batching may deliver better shared-resource efficiency.
4. Explore interactive-service scheduling: prioritize latency-sensitive voice/chat without starving research, code generation or embedding jobs. Stage downloads, indexing and backups outside measurement windows.
5. Capture joules/token and useful task completions per watt, with a clear source for power samples and sampling interval. Heat stability and low fan noise can matter more than peak benchmark speed.

## Campaign D — Reliability and proactive maintenance

Integrate with the repo's existing battery-charge cap, home snapshot timer, hardware telemetry and read-only health-verdict scripts. Avoid creating a second restart supervisor or unbounded autonomous power-reconfiguration loop. A watchdog should quarantine an experiment or restore its isolated environment, not modify firmware/BIOS without explicit high-level authorization.

**Suggested success:** improved model completion time and stable parallel tasks at acceptable power/noise; no loss of current NPU functionality; no untested kernel flags or global memory-manager changes.

**Sources:** existing repo `fixes/unified-memory-params/NOTES.md`, `fixes/npu-userland/NOTES.md`, `fixes/power-thermal-watch/`; AMD developer device specification https://www.amd.com/en/products/processors/desktops/ryzen/ryzen-ai-halo/ryzen-ai-max-plus-395.html ; AMD system optimization https://rocm.docs.amd.com/en/docs-7.2.0/how-to/system-optimization/strixhalo.html .

---

## DOCUMENT: `roadmaps/05-verification-and-upstream.md`

# Roadmap V — Verification, rollout, upstream impact and long-term maintenance

**Mission:** convert promising performance experiments into reproducible, user-safe improvements. A performance gain without output correctness, stable use, version provenance and recovery is not an engineering completion.

## Campaign A — Evidence-grade experiment control

- Every run names the exact kernel library manifest, compilation flags, ROCm/TheRock/torch/llama.cpp commit, GPU architecture, GPU/firmware/BIOS and kernel versions, power profile, ambient/starting temperature, model SHA/quant, context, batch and prompts.
- Run a preflight self-check (existing repo's `torch-health.py` where relevant). Record before-and-after state. A session that includes a GPU reset, stuck process or anomalous clock must not silently enter the performance comparison.
- Use matched A/B/A or randomized A/B runs and repeat across cold and warm states; record p50, spread, p95 and 5th/95th percentile tokens/s rather than a single best run. Control CPU background activity, model caching and rate limits.
- Keep full output transcripts for tool-call, reasoning and retrieval tests. Binary success, HTTP status and syntactic JSON are insufficient to prove semantic correctness.
- Declare test power and thermal envelope *before* the experiment. Record sustained 10–30-minute performance separately from a seconds-long burst.

## Campaign B — Automated correctness and memory integrity

Test: GEMM NN/NT/TN/TT, odd/padded sizes, independent strides, batched and mixed precision, fp32 reference comparison; model prefill, single-token, long decode, KV-cache reuse, quantized cache, tool arrays, instruction following, long-context recall and concurrency. Guard against cross-session content contamination with unique sentinels. Check NaN, Inf, determinism where applicable, memory leaks and GPU crashes.

In particular, **watch for the historical HIP/gfx1151 correctness reports in 2026**. Treat the GitHub issue as a regression test inspiration; investigate which upstream versions actually contain a fix. Also check model-specific correctness when using speculative decoding and newly quantized weights.

## Campaign C — Safe prototype-to-production ladder

**Level 0 — Research only:** notes, source audit, hypotheses; no machine impact.

**Level 1 — Sandboxed microbench:** isolated per-process library selection, external watchdog, safe fallback, no always-on agents and no automatic system configuration edits.

**Level 2 — Lab inference:** pinned backend and known-good model, thorough correctness suite, memory/thermal soak, workload benchmark.

**Level 3 — Opt-in real workloads:** one agent/service on selected tasks, monitor output errors, p95 TTFT and watts/token; abort on regression.

**Level 4 — Default candidate:** only after repeated gains, healthy GPU and no safety/quality regressions, with one-step rollback and documentation.

**Level 5 — Upstream proposal:** sanitized reproducer, exact source-level changes and test evidence, license compatibility, parameter search and device results.

Maintain the current production configuration until Yrsa elects to promote a candidate. Do not modify active ROCm wheels in place. The existing source warns that mixed-version rocBLAS+hipBLASLt swaps can hang the GPU; maintain strict version coherence.

## Campaign D — Engineering leadership and autonomous workflow

The following is an organizational **option**, not an assignment overriding Yrsa's existing team structure. The six Mythic Engineering workstreams can operate independently:

1. **Reconnaissance:** source investigation, version checks, hardware and upstream issue triage.
2. **Kernel forge:** native candidate generation, legal-parameter grammar, isolated builds.
3. **Inference laboratory:** model/quant/runtime measurements, contextual quality checks.
4. **Reliability ward:** correctness, hang recovery, regression, thermal and multi-agent tests.
5. **Integration:** opt-in packaging, precise rollback, compatibility manifests, deployment checks.
6. **Knowledge/upstream:** reports, reproducible data, license checks, issue/PR drafts.

Yrsa handles scheduling, dependency resolution, routine decisions and workstream redirection. Human attention should be reserved for actual authorization, new strategic choices, major risks and irreversible actions. A blocked approval should not stall independent work. A request to the human must contain choices, consequences, urgency and safe default, and be placed on the existing human-action list.

## Campaign E — Acceptance gates / release record

No candidate is 'released' unless:

- **Performance:** predeclared target metric improves outside noise in at least one priority application; data covers realistic workflows and a sustained run.
- **Correctness:** all mandatory model, tool-call, context and microkernel tests pass; no unexplained divergent output or semantic corruption.
- **Compatibility:** exact kernel, library, and device/runtime versions are named; unsupported platforms explicitly excluded.
- **Safety:** no hangs/OOM/thermal excursions under the relevant test; rollback test passes; other Z13 users warned about hardware variation.
- **Reproducibility:** scripts/configs and machine-readable performance records published with measurement methodology and honest limitations.
- **Maintenance:** review upstream updates periodically and retire local fixes when an upstream implementation demonstrably supersedes them.

## Publishable deliverables

- `PERFORMANCE.md`: version-pinned paired results for each workload, including failed experiments.
- `COMPATIBILITY.md`: supported distro/kernel/ROCm/torch/model/backend matrix.
- `SAFETY.md`: known-bad kernels, recovery, version mixing, opt-in/rollback.
- `CHANGELOG.md`: intervention, observations and proof of effect.
- Upstream issue reports/prs with isolated minimal repro, attribution and upstream license compliance.

**Sources:** repo notes for tuning and torch health; AMD Tensile https://rocm.docs.amd.com/projects/Tensile/en/latest/src/index.html ; ROCm Compute Profiler https://rocm.docs.amd.com/projects/rocprofiler-compute/en/latest/quick-reference/rocprofiler-compute-at-a-glance.html ; community correctness tracking https://github.com/ggml-org/llama.cpp/issues/27579 .

---

## DOCUMENT: `research/01-hardware-roofline.md`

# Research I — Strix Halo hardware facts, roofline reasoning and inference ceilings

**Research date:** 2026-11-13. Mark **vendor specification**, **user-repo measurement**, **external community result**, and **hypothesis** separately.

## 1. Verified hardware context

| Item | Evidence | Meaning |
|---|---|---|
| Processor | Ryzen AI MAX+ 395, 16 Zen 5 cores / 32 threads | CPU-heavy preprocessing or hybrid execution must compete for resources |
| GPU | Radeon 8060S, 40 RDNA 3.5 compute units, `gfx1151` | Kernels must target this gfx architecture, not presume CDNA matrix features |
| NPU | XDNA 2 | Distinct runtime/model/firmware stack; cannot assume direct compatibility with GPU kernels |
| RAM | 128 GB shared LPDDR5X-8000, 256-bit | High capacity, shared with CPU/GPU/NPU, not dedicated HBM |
| Bandwidth | **256 GB/s theoretical** (AMD Halo developer-platform spec) | Absolute nominal peak, not measured sustained inference bandwidth |
| Integrated form factor | 2025 Z13 GZ302EA | Thin chassis may have lower sustainable GPU clocks than desktop Halo platforms |
| Linux working state | Per user repo: Kubuntu 26.10 kernel 7.3.0-10-generic; TheRock gfx1151 wheels | Pin exact running build when proposing new changes; do not assume new release is an upgrade |

AMD hardware: https://www.amd.com/en/products/processors/desktops/ryzen/ryzen-ai-halo/ryzen-ai-max-plus-395.html . Existing Z13 repo: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes .

## 2. Roofline: what can Tables actually accelerate?

A kernel's arithmetic intensity `I = FLOPs / bytes fetched from memory` drives whether it is primarily compute-bound or bandwidth-bound. A simplified roofline is:

`achievable_FLOPs/s ≤ min(sustained_compute_FLOPs/s, I × measured_sustained_memory_B/s)`.

FP32 large GEMM reuses operands extensively, often becoming limited by compute/occupancy/cache/dispatch. A specialized small-M decode path must stream model weights with much less reuse, so **memory bandwidth and weight bytes/token** can dominate. A fast 4096³ SGEMM is therefore necessary for some workloads but insufficient for most quantized single-token decoding.

For a dense model with `P` active parameters, `b` effective bits/weight, ignoring scale/metadata/KV reads, the lower-bound model-weight traffic per token is `P × b/8` bytes. A deliberately optimistic bandwidth-limited token ceiling is:

`tokens/s ≤ usable_bandwidth_B/s / estimated_weight_bytes_per_token`.

**Illustrative calculation only** (assume 256 GB/s theoretical bandwidth and zero overhead):

| Hypothetical active weight traffic | Upper bound before all overhead |
|---|---|
| 2 GB/token | 128 tok/s |
| 10 GB/token | 25.6 tok/s |
| 20 GB/token | 12.8 tok/s |
| 40 GB/token | 6.4 tok/s |

The real result is generally lower because sustainable bandwidth is below peak, GGUF metadata and scales increase bytes/weight, embeddings and KV cache move, cache helps some operations, and contention/synchronization incur overhead. For a mixture-of-experts model, *total weight capacity* follows all stored experts, while active per-token weight reads can be far lower. These estimates must not be presented as measured performance.

## 3. The memory-capacity breakthrough

The user's repo documents `GTT 60.75 GiB → 121.5 GiB` and successful 80 GB tensor GPU allocation. That matters enormously to whether 70B-class and large MoE GGUF models fit on the GPU. It **does not** guarantee all 121.5 GiB is available after system activity, model metadata, context/KV, memory fragmentation and multi-agent load.

`iommu=pt`, not `amd_iommu=off`, preserved the NPU in the user's test. The repo intentionally **did not** enable `amdgpu.no_system_mem_limit=1`; don't layer unproven flags in a performance study. See https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/unified-memory-params/NOTES.md .

## 4. Compute and data movement are both relevant

- **Prompt prefill** typically exposes larger GEMM and parallel attention opportunities; Tensile/hipBLASLt/native GEMM and attention fusion can matter.
- **Single-user token decode** often uses low-M quantized matrix-vector operations and memory streaming; quant format, MMVQ, cache and bandwidth are paramount.
- **MoE decode** processes smaller active expert matrices but can suffer from many launch/routing decisions and uncoalesced access; optimize dispatch and grouping, not just dense GEMM.
- **Long context** increases attention/KV traffic and can degrade TTFT or per-token response despite unchanged weight sizes.
- **Multiple concurrent agents** can improve batching efficiency but also induce memory pressure, KV duplication and incorrect synchronization if the backend is immature.
- **NPU plus GPU** may run separate tasks, but share power/LPDDR5X; measure combined throughput and throttling.

## 5. Proposed instrumentation / studies

1. GPU bandwidth microbenchmark in device memory, with known access pattern and separate read/write/copy tests. Record measured GB/s and source. Compare to 256 GB/s only as utilization ratio.
2. Cache hierarchy characterization with working sets below and above L2; ensure actual counter support for gfx1151 before interpreting GPU profiler output.
3. Time kernel types across small/large M and shape irregularity; plot GFLOP/s against estimated FLOP/byte (a *measured* roofline rather than a marketing peak).
4. Model-level weight bytes/token accounting (total weights, active MoE weights, quant metadata, KV read/write) compared to observed per-token GPU throughput.
5. End-to-end thermal/power study in the Z13 chassis at each truly supported performance mode, including fan noise if relevant.

## 6. Questions for further research

- Does UMA streaming bandwidth change with CPU cores simultaneously compiling or indexing files?
- Does quantized model layout allow cache reuse across multiple concurrent requests?
- For large-M prefill, do registers/LDS limit compute utilization more than memory?
- What is the break-even size for custom quantized matvec vs cuBLAS/hipBLAS-style GEMM after dequant?
- At what context does KV traffic become a material fraction of decode bandwidth?
- Are any truly native gfx1151 kernel designs significantly more energy-efficient than the retargeted winners?

## 7. External observations, not guaranteed predictions

Community tests in 2026 have reported impressive Strix Halo GGUF throughput and differing ROCm/Vulkan outcomes, but they vary in model, quantization, code commit, power and OS. Use them as experiment design inspiration, **not** as numerical promises for this Z13. See https://github.com/ggml-org/llama.cpp/discussions/15021 ; https://github.com/matnum/local-llm-benchmarks ; https://github.com/visorcraft/strix-halo-llm-perf .

---

## DOCUMENT: `research/02-tensile-and-precision.md`

# Research II — Tensile, rocBLAS, hipBLASLt, precision and native-kernel search

## 1. Architecture of AMD matrix multiplication stacks

**Tensile:** generates and catalogs matrix multiplication and tensor contraction kernels; uses solution selection catalogs mapping hardware, operation/transpose, problem properties and candidate solutions. Modern runtime catalogs are often serialized as `MessagePack .dat`; code objects are `.co`. File or YAML names alone do not prove what kernel the runtime dispatched.

**rocBLAS:** BLAS API layer; depending on build and operation, selects Tensile kernels or other paths. AMD documents profile logging and `rocblas-gemm-tune`, including `ROCBLAS_TENSILE_GEMM_OVERRIDE_PATH` for a supported override. Override support and exact behavior must be verified for the pinned ROCm build.

**hipBLASLt:** flexible GEMM API and kernel heuristics. AMD documents `hipblaslt-bench`, `HIPBLASLT_TUNING_FILE`, and `HIPBLASLT_TUNING_OVERRIDE_FILE`; indices are not stable across library releases/architectures. The pinned working environment in the user's repo has warnings about hipBLASLt defaults and cross-library mixing; do not assume a modern page describes the old wheel identically.

**ggml HIP custom kernels:** quantized MMVQ/MMQ and other ops may bypass rocBLAS; optimization needs profiling at the layer that runs the model. `GGML_CUDA_FORCE_MMQ` and `GGML_CUDA_FORCE_CUBLAS` are relevant experimental toggles for some releases but can harm accuracy/performance and are not global recommendations.

Primary docs: https://rocm.docs.amd.com/projects/Tensile/en/latest/src/index.html ; https://rocm.docs.amd.com/projects/Tensile/en/docs-7.2.0/src/conceptual/solution-selection-catalogs.html ; https://rocm.docs.amd.com/projects/rocBLAS/en/latest/how-to/Programmers_Guide.html ; https://rocm.docs.amd.com/projects/hipBLASLt/en/develop/how-to/how-to-use-hipblaslt-offline-tuning.html .

## 2. Why the existing Z13 discovery matters

Project forensic inspection found **exactly one `Type_SS` SGEMM solution** per transpose combination in its pinned gfx1151 production library, compared with dozens/hundreds of solutions in mature architectures and other data types. The team retargeted navi31's SGEMM pool to gfx1151, resolved actual table-matching orientation via ablation, tuned candidates through the production dispatch path, and built isolated tables.

The project reports NN 4096³ **2.374 → 7.946 TFLOPS**, multiple 3.2–6.9× kernel improvements, and a large **34.78 → 14.76 ms** FP32 MLP training-step improvement. But its Qwen2.5-0.5B FP32 inference gain is only ~5%. The preliminary table with only large grid shapes even **regressed** Qwen decode to 24.1 tok/s, later corrected by adding small-M tuning cases. This demonstrates three lessons:

1. GPU software selection/candidate quality, not only silicon, can determine achieved GEMM throughput.
2. Table logic nearest-match behavior can produce severe out-of-domain regressions.
3. End-to-end AI workloads require their actual kernel path and their actual shape distribution, not just cubic benchmarks.

Source: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/tensile-fp32-tables/NOTES.md .

## 3. Native candidate parameter families to investigate

These are **search dimensions** that must be checked against the exact Tensile version and gfx1151 capabilities:

| Family | Candidate exploration | Potential constraint |
|---|---|---|
| Thread/workgroup tile | `ThreadTile`, `WorkGroup`, macro-tile size, wave mapping | Register pressure, occupancy, tail efficiency |
| Reduction loop | `DepthU`, `LoopUnroll`, pipeline staging, `PrefetchGlobalRead` | Code size, LDS usage, synchronization |
| Memory reads | global vector width, coalescing, local buffer mapping, bank layout | Odd dimensions, alignment, LPDDR5X latency |
| Split strategy | Local/GlobalSplitU and Stream-K equivalents where supported | Accumulation precision, extra traffic, known failures |
| Instruction path | scalar/vector F32 vs architecture-legal matrix instructions | Data types/instruction availability; no unsupported FP32 matrix assumptions |
| Scheduling | waves/workgroup, persistent work, grid occupancy | Small-M underutilization, thermal behavior |
| Dispatch | exact/nearest shape keys, transpose and strides | Out-of-grid regressions |

AMD's Tensile parameter reference: https://rocm.docs.amd.com/projects/Tensile/en/docs-7.1.1/src/conceptual/kernel-parameters.html . Benchmark configuration example: https://rocm.docs.amd.com/projects/Tensile/en/latest/src/tutorial/benchmark-config-example.html .

For native new kernels, generating candidates from constrained parameter combinations is a stronger claim than merely selecting a different kernel from an existing pool. Maintain separate provenance labels so a benchmark can identify which kind of innovation was tested.

## 4. Precision paths cannot be lumped together

- **FP32 (Type_SS):** essential for FP32 workloads and some accumulations. Existing major deficit fixed in part. IEEE FP32 correctness must be validated; different reduction order can change low bits. BF16-split or TF32 techniques should not be advertised as true FP32.
- **FP16/BF16:** frequently relevant to prompt prefill, training and activations; the repo already reports strong fp16/bf16 GEMM ~20+ TFLOPS in one test and indicates those shipped tables were much more mature than SGEMM. They should be benchmarked, not replaced automatically.
- **INT8/FP8/FP4/low-bit formats:** instruction support and actual backend execution vary; do not assume the theoretical TOPS of a hardware format imply a usable native model kernel.
- **GGUF Q4/Q5/Q6/IQ:** custom packed formats, scale and unpack operations; many hot kernels are fused dequantization/matvec, not Tensile library GEMMs. For optimized inference, this can matter more than pure SGEMM.
- **Accumulator vs weight precision:** always record input, multiply, accumulation and output type separately. A model that stores 4-bit weights may still use FP16, BF16 or FP32 intermediates.

## 5. Safe research methodology

**Stage 1: Source review.** Lock Tensile source version, target GPU and exact code-object format; enumerate supported parameter combinations and compile checks. Reject unsupported hardware/precision early.

**Stage 2: Microkernel search.** Use representative GEMM shapes, external watchdog, cold/hot runs, reference numerical validation and per-candidate manifest. Record performance *and* errors. Never hide failing candidates from the experiment log.

**Stage 3: Library selection.** Compare new native solutions to stock and the project's tuned retargeted winners. Verify the real dispatch path through one-at-a-time ablation or supported tracing, not merely a build-success message.

**Stage 4: Application benchmarks.** Run PyTorch tests and actual LLM workloads; if they do not invoke SGEMM, log that explicitly and move to the relevant subsystem.

**Stage 5: Optional deployment.** Preserve the known-good build with per-process opt-in library selection, hashes and a demonstrated rollback. Do not mutate the original wheel or globally override an incompatible program.

## 6. Known dangerous and misleading paths from repository evidence

- Blacklisted `Ailk_Bljk` `MT64x4x32 ... TT4_1`, local solution `1162084410` (hangs GPU). It must remain excluded from **any rebuild** derived from the shipped research YAML.
- `GSU4`/`GSUAMB` in that candidate pool produce `HIPBLAS_STATUS_INTERNAL_ERROR`; bad tiny-tile options can stall in huge GEMMs.
- The repo reports a ROCm/hipBLASLt mix-and-match hung the GPU. Version pairing is a hard requirement.
- The repository tested BF16-based FP32 emulation and found it either less accurate or slower; do not re-propose as a proven win.
- A newer tested nightly regressed default FP32 dispatch despite improvements elsewhere; newer version != faster in every case.
- `amdgpu.no_system_mem_limit=1` remains **deliberately unapplied**; this roadmap should not change it.

## 7. Open research hypotheses

1. gfx1151-specific cache/issue tuning could improve FP32 beyond retargeted kernels on some shapes; magnitude unknown.
2. Small-M and grouped MoE kernels may benefit more from bespoke quantized paths than from any Tensile FP32 modification.
3. Better backend routing/dispatch might yield meaningful gains without generating new kernels at all.
4. End-to-end throughput may be limited by bandwidth or latency such that large compute wins have negligible effect.
5. A native source-level Tensile/hipBLASLt contribution might eventually make private tables obsolete, a desirable upstream outcome.

## 8. Testable completion criteria

At least one robust performance advantage on a **chosen real workload**, correctness at expected numeric tolerance, full model-output and tool-call tests, no crash/thermal regression, and reproducibility with version-pinned artifacts. Report both absolute baseline and relative improvement; never conflate `TFLOPS`, `TOPS`, `tokens/sec`, and `task completions/hour`.

---

## DOCUMENT: `research/03-runtime-landscape.md`

# Research III — Inference runtime landscape and integration opportunities

**Scope:** compare execution paths; do **not** declare a universally best framework or assume compatibility with the current Kubuntu 26.10 + gfx1151 stack without installation-free validation first.

## Executive map

| Runtime / stack | Strength worth testing | Caveat on gfx1151 | Engineering role |
|---|---|---|---|
| `llama.cpp` + HIP/ROCm | GGUF, GPU inference, extensive quant support, HTTP serving, speculative decoding | Build/kernel correctness is version-specific; historical HIP tool-call and concurrent-output corruption reports | Main real-world inference workhorse candidate |
| `llama.cpp` + Vulkan/RADV | GGUF and comparatively portable GPU backend | Vulkan dispatch may beat HIP in one quant/model and trail it in another | Equal-status reference and fallback, not merely a control |
| PyTorch + TheRock `gfx1151` wheels | Training, model experimentation, ComfyUI, tensor benchmark and custom kernels | Existing repo documents wheel pins, unstable alternatives and FP32 gaps | Validation and custom-op prototyping |
| `hipBLASLt`/rocBLAS/Tensile | Accelerated GEMM and offline tuning | Only useful where runtime actually dispatches into this library and compatible release | GEMM campaign |
| Triton on ROCm | Kernel DSL for custom fused ops and parameter autotuning | Architecture/toolchain and specific ops require exact-build validation | Exploratory candidate generator, not presumed working production |
| vLLM (ROCm) | High-throughput serving, paged scheduling, multi-request benchmarks | Specific RDNA/gfx1151 support may differ from general ROCm documentation; plugin/toolchain compatibility can be fragile | Research branch and possible future service |
| FastFlowLM / XRT / `amdxdna` | Proven path in user's repo for compact model on XDNA2 NPU | Supported models and firmware constrained; no free arbitrary GPU offloading | NPU-specific small model service |
| A.E.S.I.R. / Yggdrasil projects | User's planned native inference/distributed orchestration ecosystem | No capabilities should be assumed without current repository testing | Long-term integration target |

## 1. llama.cpp HIP: where the key opportunities lie

Current upstream ggml `CMakeLists.txt` includes `GGML_HIP`, GPU graph options and other backend toggles; older/historical file paths for HIP/CUDA have evolved. Treat code paths as commit-specific. The shared HIP/CUDA implementation includes custom quantized matrix multiplication (`mmq.cu`), and architecture-specific decisions can choose it rather than library GEMM. Detect these cases before spending time on native SGEMM.

Important questions for a profiler-backed HIP evaluation:

1. Which kernels dominate `tg128` at the target quant and model architecture?
2. Does prefilling 4k+ tokens choose custom quant MMQ or dequant + BLAS?
3. Are `mul_mat_id` and expert gather paths dominant for 64+ expert MoEs?
4. Do graph capture and pinned host memory improve time or introduce race/correctness bugs?
5. Do any HIP ops silently fall back to CPU? Confirm real GPU activity and output.

Primary source: https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-cuda/mmq.cu and https://github.com/ggml-org/llama.cpp/blob/master/ggml/CMakeLists.txt .

## 2. Vulkan: competitive alternative rather than assumption

A published Strix Halo community comparison at https://github.com/ggml-org/llama.cpp/discussions/15021 includes August 2026 gfx1151 head-to-head results showing Vulkan faster for some models. Another September 2026 guide at https://howquant.dev/guides/llama-cpp-strix-halo/ reports ROCm prefill advantages in some dense workloads, with varied decode behavior. The methodology differs (commits, ROCm versions, MoE architecture, power). **Interpretation:** choose per-workload A/B; no universal performance ratio is supported.

Pin two builds from *one* ggml/llama.cpp SHA. Record Mesa version and RADV compiler path. Compare both direct llama-bench and server outputs, cold context and cached prefix, under matched task load. Don't compare one backend's optimized quant to a different quant or model revision.

## 3. PyTorch and its special role

The user's existing repo documents reliable arch-matched TheRock nightly wheels for this machine after an official wheel segfault and shows a successful ComfyUI GPU image generation, correctness tests, a 1000-iteration stress test and a 3-minute sustained GEMM. The exact wheel pins are **a reproducible historic baseline**, not a recommendation to upgrade automatically.

For custom kernel exploration, a Python/PyTorch test can validate precision and autograd (if relevant), but the deployed inference engine may still use another path. Prove the mapping from the candidate kernel to actual model speed before declaring success. Do not replace pinned wheel libraries with a different release's rocBLAS or hipBLASLt in-place.

Project note: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/pytorch-gfx1151/NOTES.md .

## 4. Direct tuning APIs in rocBLAS and hipBLASLt

AMD documents rocBLAS `rocblas-gemm-tune`, runtime-selected solution indices and a Tensile override path. It separately documents hipBLASLt offline tuning with `HIPBLASLT_TUNING_FILE` and `HIPBLASLT_TUNING_OVERRIDE_FILE`. Kernel index numbers are **not portable** between releases or architectures. Before adopting any mechanism on the Z13, run a read-only source/binary version inspection and a controlled temporary test. The user's repository demonstrated that `ROCBLAS_TENSILE_LIBPATH` really redirected its pinned runtime; do not infer identical behavior for newer binaries.

Sources:
- https://rocm.docs.amd.com/projects/rocBLAS/en/latest/how-to/Programmers_Guide.html
- https://rocm.docs.amd.com/projects/hipBLASLt/en/develop/how-to/how-to-use-hipblaslt-offline-tuning.html

## 5. Profiling beyond single timing numbers

AMD ROCm Compute Profiler describes compute throughput, memory hierarchy traffic, instruction mix, occupancy and empirical roofline comparisons. **Caution:** some specialized profiling features are hardware-specific; e.g. a newer experimental memory bottleneck analysis page explicitly limits that feature to MI350-class devices. On gfx1151 validate the counter availability rather than interpreting absent metrics.

Timing is the fallback truth: time CPU/client request, kernel dispatch, end-to-end token streaming, and cold/warm context separately. Record actual frequency, load and power state where supported.

Docs: https://rocm.docs.amd.com/projects/rocprofiler-compute/en/latest/quick-reference/rocprofiler-compute-at-a-glance.html ; https://rocm.docs.amd.com/projects/rocprofiler-compute/en/develop/how-to/membw_analysis.html .

## 6. vLLM and service concurrency

vLLM can be attractive for high-concurrency serving, but avoid assuming general ROCm documentation certifies gfx1151 compatibility with every version and model. In the current project context, it should be a **sandboxed compatibility campaign** with minimal model import, correct single-request output, then tool use, 2/4/8 parallel requests, long-context stability and only then throughput. Compare its goodput, VRAM/UMA pressure, setup cost, implementation maturity and expected operator maintenance with llama.cpp.

A 2026 community correctness discussion reported that a vLLM ROCm path avoided a particular llama.cpp HIP multi-slot corruption on one setup. This is a diagnostic clue, not a statement that all vLLM configurations are safe or faster. Evidence: https://github.com/ggml-org/llama.cpp/issues/27579 .

## 7. NPU runtimes

The user's repo explicitly verified XRT 2.25 on Kubuntu 26.10, firmware 1.1.2.65, `amdxdna` and FastFlowLM 1.0.12 with a small Qwen3 model. Use this as a **starting compatibility card**, then test model support, latency, wake-up time, energy per token and interaction with concurrent GPU inference. Do not confuse the 50 NPU TOPS marketing number with real tok/s for arbitrary model formats.

Project source: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/npu-userland/NOTES.md .

## 8. Selection framework

Choose the runtime per actual role, not by hype:

- **Interactive human chat:** lowest p95 TTFT and acceptable decode speed/quality.
- **Background coding agents:** tool-call correctness, long-context integrity, prefix reuse, concurrency and reliable memory usage.
- **Large dense models:** sufficient GPU allocation and predictable 64k+ KV cache if used.
- **MoE reasoning:** expert routing and quant decode; more model parameters in RAM do not automatically mean more active compute.
- **NPU background task:** explicitly supported lightweight model, low contention and power.
- **Image generation/training:** working PyTorch/ComfyUI and math correctness before changing backend.

For each role capture: model ID/hash, quant, backend, build SHA, tokens/s, p95 TTFT, peak memory, watts/token, output correctness, failures and operational friction.

## 9. High-risk traps

1. Installing a newer ROCm because it is newer, despite the repo's measured regressions on a later nightly.
2. Thinking FP32 Tensile improvements cover GGUF low-bit kernels.
3. Comparing HIP and Vulkan with different model revisions or prompt cache behavior.
4. Measuring only throughput in a backend that emits corrupt tool-call output.
5. Importing an unsupported GPU profiler metric from a different AMD architecture.
6. Mixing library releases, silently forcing GPU architecture overrides, or modifying stable wheels globally.
7. Calling a model 'NPU-accelerated' without device-lock or hardware-counter evidence.

---

## DOCUMENT: `research/04-validation-matrix.md`

# Research IV — Benchmark design, acceptance tests, failure modes and experimental controls

## A. Benchmark design principles

- **Isolation:** never let a generated experiment overwrite the known-good library, production model server, GRUB settings, or system service without Yrsa's deliberate, separate rollout.
- **Attribution:** label kernel benchmark vs PyTorch workload vs llama.cpp server request vs complete agent task; only compare like with like.
- **Correctness first:** an invalidly generated answer at 120 tok/s is not an improvement over a correct answer at 60 tok/s.
- **Scope:** model, quant, context, output length, backend, batch, concurrency, power and temperature all affect results.
- **Replicability:** output source/pins/commands/prompts/seed/hashed binaries; record failed candidates too.
- **Noise control:** randomize A/B order, run cold and warm conditions separately, allow thermal recovery and repeated trials; specify a minimum sample count before accepting an effect.
- **Throughput vs latency:** a higher total tokens/s at concurrency 8 can coexist with unacceptable p95 individual request latency.

## B. Microkernel test matrix

| Axis | Minimum cases | Why |
|---|---|---|
| Transpose | NN, NT, TN, TT | The existing repo has separate table combinations |
| M | 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 4096 | Decode vs prefill vs large GEMM |
| N/K | Model-derived 896/2048/4096/8192/16384 and irregular 513/1000 | Transformer feed-forward and odd-size tails |
| Batch/strides | batched 1/2/8; contiguous and supported noncontiguous | Attention and inference layout correctness |
| Precision | F32, F16, BF16, packed quant formats where relevant | Different kernels and semantics |
| Initial values | random, zeros, ones, large scale, signed mix, NaN/Inf when defined | Numerical sensitivity |
| Reference | Float64 for F32; high-precision/reference kernel or curated model output for other formats | Detect silent math errors |
| Kernel timing | warmup + ≥10 timed samples per candidate; ≥3 independent groups | Robustness over lucky single run |
| Watchdog | external process timeout and GPU-reset detection | Some documented candidates hang the GPU |

Note: only execute combinations legal for the selected BLAS API and kernel. Some very large cases require too much memory or are invalid for a candidate; log as unsupported, never as a silent pass.

## C. Inference benchmark matrix

| Scenario | Variables | Metrics | Critical validation |
|---|---|---|---|
| Interactive 4–8B | Q4/Q6/Q8; short context | p50/p95 TTFT, tok/s, watts/token | Prompt following, semantic coherence |
| Dense ~27–32B | quant+context choice | prompt/decoding speed, peak memory | Tool JSON and long-context recall |
| MoE ~30–35B | experts/active experts, quant | tok/s, expert routing time | Determinism/selected expert correctness |
| Large ~70B-class | compatible Q4/Q5 if fits | memory pressure, tokens/sec, session stability | Complete loading, no fallback/OOM |
| Long agent prompt | 8k/32k/64k, 1–20 tools | TTFT, recall, correct tool arguments | Exact target tool, no omitted early tools |
| Multi-agent serving | 1/2/4/8 clients | total throughput, p95 latency, memory | No cross-session or slot corruption |
| Speculative | none / draft / MTP / n-gram | accepted tok/s, acceptance fraction, overhead | Output semantics and sampling checks |
| GPU+NPU | sequential vs concurrent | combined task completions/s, power | Actual hardware usage and no contention errors |
| Sustained | 15–60 min at supported power modes | token drift, thermals, reset count | Stable result, no power-cut or throttling surprise |

The exact model list is a **decision for the owner's actual use cases**. Do not download large model weights by default merely to fill this grid; work with legally acquired, already available representative models first.

## D. Record structure

For every trial record:

`timestamp,project_commit,device,firmware,os,kernel,rocm,torch,llama_commit,backend,binary_hash,library_hash,model_id,model_sha,quant,model_arch,active_params,context,batch,ubatch,parallel,kv_type,flash_attn,speculation,power_mode,temp_start,prefill_tok_s,decode_tok_s,ttft_ms,p95_ms,peak_ram_gb,peak_gtt_gb,watts_avg,energy_j,accuracy_score,error_count,gpu_resets,notes`.

Not every field applies to every microkernel or model test. Mark unavailable, never invent zero. Provide a `results-schema.csv` that can be imported by the teams.

## E. Qualitative validation is essential

Use prompts with expected factual or exact structural outcomes. Example classes:

1. A request with 20 named tool signatures, requiring selection of the exact earliest tool.
2. JSON arguments with escaping/unicode, nested arrays and exact schema.
3. Retrieval question whose answer appears only in the first 5% of a long context.
4. Long multi-turn chat with precise memory/speaker boundary checks.
5. Text containing adversarial instructions in retrieved content; verify the assistant treats source data as data.
6. Concurrent sessions with unique sentinel strings to detect stream mixing.
7. Repeated fixed-seed completions to spot rare nondeterministic corruption.

Explicitly compare generated **content**, not only whether an HTTP response completed. The mid-2026 gfx1151 HIP/llama.cpp issue https://github.com/ggml-org/llama.cpp/issues/27579 is a cautionary example.

## F. Stop conditions / controlled recovery

Stop test and quarantine candidate on: GPU hang, reset, firmware crash, kernel timeout, correctness mismatch, tool-call corruption, OOM, sustained thermal limit excursion, obvious model output degradation, unexpected CPU fallback, or inability to prove which binary ran. Capture trace/logs only if safe, revert to known-good library and assess the machine before resuming.

If a kernel prevents graphics recovery, do not build an unattended loop that repeatedly runs the same candidate. The existing repo already identifies a concrete hanging solution; never include it in a sweep. Watchdogs should run outside the GPU-dependent process and use a bounded restart policy with clear human escalation.

## G. Statistical acceptance

Set a performance budget **before** exploring. A candidate is a potential win only if the paired relative effect persists across multiple independent runs and its confidence interval/noise band excludes a trivial difference. Compare p50 and p95 latency, not just mean tok/s. Prefer end-to-end gains even when a microkernel wins much more; disclose any regression.

Suggested project policy (not observed facts): ≥10% end-to-end gain in a priority scenario, no repeatable >3% slowdown in important control cells, zero newly introduced correctness failures, no hangs, and full rollback demonstration. The threshold can be revised by Yrsa for each workload.

## H. Multi-objective optimization

Do not optimize solely TFLOPS or tok/s. Build a Pareto frontier for:

- p95 TTFT/latency for interactive requests;
- decode throughput and useful work per hour;
- memory capacity and context length;
- energy cost, heat and fan acoustics;
- correctness and reliability;
- human attention needed for maintenance.

A 7% performance loss may be worthwhile for 40% lower power in an overnight agent run; a 20% speed gain that breaks tool use is unacceptable. Let the **use case**, not one corporate benchmark, determine priorities.

## I. Known baseline numbers (from user repo, not rerun here)

- Tensile fp32 4096³ NN: **2.374 → 7.946 TFLOPS**.
- Overall measured FP32 GEMM improvement: **3.2–6.9×** on specified grid.
- MLP FP32 step: **34.78 ms → 14.76 ms**.
- Qwen2.5-0.5B full FP32 decode: **34.74 → 36.57 tok/s**.
- GTT pool: **60.75 → 121.5 GiB**, 80 GB tensor allocation validated.
- NPU Qwen3-0.6B FastFlowLM decode: **81.96 tok/s** for one observed test.

These numbers must not be conflated with arbitrary GGUF, 70B, MoE or long-context model benchmarks. Existing source: https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes .

---

## DOCUMENT: `research/05-source-library.md`

# Research V — Annotated primary sources, provenance and uncertainties

**As of 2026-11-13.** Links may evolve. Prioritize exact release/tag/commit documentation when Yrsa begins a campaign. This file is a curated external research index, not proof that every tool works on Kubuntu 26.10/gfx1151.

## A. Project's existing firsthand evidence

1. **Root repository and README** — working Z13 Linux fixes, statuses, environment, timestamps through November 2026. https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes
2. **Tensile fp32 tables** — candidate pool, solution/table matching, measured FP32 speedups, small-M regression, blacklist and rollback. https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/tensile-fp32-tables/NOTES.md
3. **PyTorch `gfx1151` wheel stack** — runtime mismatch, exact TheRock pins, FP16/BF16 and FP32 benchmarks, real ComfyUI generation. https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/pytorch-gfx1151/NOTES.md
4. **Unified memory parameters** — validated GTT allocation, IOMMU/NPU warning, intentionally unapplied optional flag. https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/unified-memory-params/NOTES.md
5. **NPU Linux userland** — XRT/`amdxdna`/FastFlowLM path with model-level test and NPU lock log. https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/blob/main/fixes/npu-userland/NOTES.md
6. **Full fixes tree** — health timers, thermal monitor, greeter-wedge issue, Btrfs snapshots, battery cap, firewall and package hygiene. https://github.com/hrabanazviking/RuneForgeAI-ASUS-z13-Linux-Fixes/tree/main/fixes

These are user-repo observations, not independently reproduced by this research author. Do not treat the `known issue` entries as solved.

## B. Official AMD hardware and platform guidance

7. **AMD Ryzen AI MAX+ 395 processor specifications** — cores, 40-CU Radeon 8060S, 256-bit LPDDR5X-8000, 128 GB ceiling. https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-ai-max-series/amd-ryzen-ai-max-plus-395.html
8. **AMD Halo developer platform specifications** — explicitly lists 256 GB/s bandwidth, Linux/Windows, 128 GB RAM, 40 CUs. Note: desktop Halo board has different thermals from a Z13. https://www.amd.com/en/products/processors/desktops/ryzen/ryzen-ai-halo/ryzen-ai-max-plus-395.html
9. **AMD Strix Halo system optimization** — GPUVM, kernel, memory and NPU-related configuration guidance, published Feb 20 2026; compare with exact new versions before changing anything. https://rocm.docs.amd.com/en/docs-7.2.0/how-to/system-optimization/strixhalo.html
10. **TheRock FAQ** — gfx1151-specific compatibility advice, Linux/kernel caveats and links to system optimization. https://github.com/ROCm/TheRock/blob/main/docs/faq.md

## C. Tensile / BLAS direct primary documentation

11. **Tensile official documentation home** — GEMM/tensor contraction generation and source tree. https://rocm.docs.amd.com/projects/Tensile/en/latest/src/index.html
12. **Tensile solution selection catalogs** — architecture / operation / problem / exact-solution hierarchy, lazy library and MessagePack catalog. https://rocm.docs.amd.com/projects/Tensile/en/docs-7.2.0/src/conceptual/solution-selection-catalogs.html
13. **Tensile kernel parameters** — `WorkGroup`, `ThreadTile`, `MatrixInstruction`, loop and memory parameters. Versioned 7.1.1 page; inspect the *pinned source* for allowed gfx1151 values. https://rocm.docs.amd.com/projects/Tensile/en/docs-7.1.1/src/conceptual/kernel-parameters.html
14. **Tensile benchmark config example** — global benchmark parameters, validation and library logic generation. https://rocm.docs.amd.com/projects/Tensile/en/latest/src/tutorial/benchmark-config-example.html
15. **rocBLAS programmer's guide** — `rocblas-gemm-tune`, logging, override for supported backend and build. https://rocm.docs.amd.com/projects/rocBLAS/en/latest/how-to/Programmers_Guide.html
16. **hipBLASLt offline tuning** — best-solution indices and version/device invalidation, tuning and override files. https://rocm.docs.amd.com/projects/hipBLASLt/en/develop/how-to/how-to-use-hipblaslt-offline-tuning.html
17. **hipBLASLt documentation** — capability and programming reference. https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/index.html

**Uncertainty:** the AMD documentation site has multiple versions and may surface features newer than the repo's pinned TheRock wheels. Avoid copy/pasting env vars into production without confirming the exact version and actual dispatch.

## D. Profiling and roofline

18. **ROCm Compute Profiler at a glance** — kernel counters, speed-of-light, caches, empirical roofline, comparative analysis. https://rocm.docs.amd.com/projects/rocprofiler-compute/en/latest/quick-reference/rocprofiler-compute-at-a-glance.html
19. **ROCm Compute Profiler overview** — profiler goals, metrics, analysis models; confirm hardware support per metric. https://rocm.docs.amd.com/projects/rocprofiler-compute/en/develop/what-is-rocprof-compute.html
20. **Experimental memory bottleneck analysis** — warning: the described advanced stall analysis is currently MI350-targeted, not a generic gfx1151 guarantee. https://rocm.docs.amd.com/projects/rocprofiler-compute/en/develop/how-to/membw_analysis.html

## E. llama.cpp / ggml technical primary sources

21. **llama.cpp source and docs** — release-independent entrypoint. https://github.com/ggml-org/llama.cpp
22. **Backend build and tuning options** — HIP and Vulkan build modes, MMQ/BLAS choices and precision settings. https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md
23. **Backend feature matrix (updated Nov 8 2026)** — quantization, Flash Attention, MoE, cache support; marks are broad capabilities, not gfx1151 correctness proofs. https://github.com/ggml-org/llama.cpp/wiki/Feature-matrix
24. **GGML CMake config** — `GGML_HIP`, graphs, conditional backend flags. https://github.com/ggml-org/llama.cpp/blob/master/ggml/CMakeLists.txt
25. **Custom quant MMQ source** — quant formats and architecture-dependent selection; inspect pinned commit rather than assuming current main matches installed code. https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-cuda/mmq.cu
26. **Speculative decoding** — draft models, EAGLE3, MTP, n-gram and measurement. https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
27. **2026 HIP correctness issue #27579** — historically observed tool-array/context and multi-slot corruption, workaround experiments and partial cause investigation. This is not proof of current failure, but it is a high-value regression test source. https://github.com/ggml-org/llama.cpp/issues/27579

## F. Community datasets and comparisons (valuable, not authoritative)

28. **llama.cpp HIP performance discussion #15021** — 2026 comments include same-host Strix Halo ROCm vs Vulkan comparison. Records models, quants and compiler/runtime versions; do not generalize to other models. https://github.com/ggml-org/llama.cpp/discussions/15021
29. **How Quant Strix Halo setup and comparison** — September 2026 ROCm 7.14/RADV experiments with method description; another hardware platform with same APU. https://howquant.dev/guides/llama-cpp-strix-halo/
30. **matnum/local-llm-benchmarks** — reproducible model/quant × backend matrix including latency, tokens/watt and quality axes. https://github.com/matnum/local-llm-benchmarks
31. **visorcraft/strix-halo-llm-perf** — single- and distributed-host experimental results (2026), not necessarily portable to Z13 thermal limits. https://github.com/visorcraft/strix-halo-llm-perf
32. **huppiflupp/strix-halo-llm-speeds** — broad community test collection; hardware/backend/method diversity means rows are not apples-to-apples. https://github.com/huppiflupp/strix-halo-llm-speeds

## G. What the research *does not* establish

- That 256 GB/s of external memory bandwidth is sustained for arbitrary models on this laptop.
- That native gfx1151 FP32 Tensile can add another 2× or 3× for useful model-level inference.
- That arbitrary quantized GGUF, NPU and PyTorch formats can all be accelerated by the same table.
- That ROCm or Vulkan is universally faster, more correct or better for all models in November 2026.
- That the community's 2026 output corruption issues still reproduce in the specific current fixed build.
- That a published desktop Halo performance result extrapolates directly to the Z13's thermals.
- That 'up to 128 GB unified memory' equals the exact amount every runtime can allocate for a model.
- That any of these proposed campaigns have run or passed on the owner's Z13; only the **existing repo** claims firsthand measurements.

## H. Follow-up research questions and monitoring

1. Check TheRock gfx1151 wheel changelogs for newly tuned SGEMM/hipBLASLt candidates and exact compatibility.
2. Check upstream `ggml` HIP RDNA3.5 patches for quant MMQ, MoE, flash attention and graph synchronization; use exact commit dates.
3. Check whether the known HIP/gfx1151 corruption regression has reproducible upstream fixes, not merely anecdotal workarounds.
4. Watch official Tensile kernel-grammar, selection and offline-tune APIs for changes that affect reproducibility.
5. Determine measured per-power-mode sustained GPU memory bandwidth and thermal limits on the **actual Z13**.
6. Monitor NPU model support and compatibility for FastFlowLM/XRT while preserving currently working firmware.
7. Identify whether a native search improves real inference or whether quantized dispatch and cache work is the higher-return research line.

## I. Citation and claim etiquette for public README or upstream PR

Use source type tags: `[USER-MEASURED]`, `[AMD-DOCUMENTED]`, `[UPSTREAM-DOCUMENTED]`, `[COMMUNITY-OBSERVED]`, `[HYPOTHESIS]`. Each published performance claim should include setup, numeric before/after, benchmark method and validation. If a numerical result is inferred by a simple roofline calculation, label it **illustrative upper bound** rather than a benchmark. If a source is a versioned page, include that version and date instead of implying it is current production state.

---

## DOCUMENT: `templates/experiment-record.md`

# gfx1151 experiment record — copy for each campaign

**Experiment ID:** `YYYYMMDD-group-unique`  
**Owner/workstream:**  
**Hypothesis:**  
**Source of motivation:** `[USER-MEASURED] / [AMD-DOCUMENTED] / [UPSTREAM-DOCUMENTED] / [COMMUNITY-OBSERVED] / [HYPOTHESIS]`  
**Expected workload benefit:**  
**Why this is on the real hot path:**  
**Required permissions / human decision:**  
**Risk class / isolation method / recovery:**

## Baseline manifest

- Device, BIOS, firmware, OS, kernel, GPU architecture:
- Power mode, idle temperature, wall/power meter:
- ROCm/HIP, TheRock, torch, ggml/llama.cpp SHAs:
- Tensor/Tensile library hashes and active opt-in env variables:
- Model artifact SHA, quantization, architecture and tokenizer:
- Benchmark command and input prompt hash:
- Initial profiler identifying kernel dispatch and bottleneck:

## Candidate

- Source branch/commit:
- Parameter-space restriction or patch:
- Compiler/build command and exact flags:
- Candidate `.co`/`.dat`/binary SHA256:
- Known-bad candidate checks and static validation:
- Rollback command tested? [ ]

## Results

| Metric | Stock/unmodified | Existing known-good tuned | New candidate | Variance / CI | Comment |
|---|---:|---:|---:|---:|---|
| Microkernel GFLOP/s or latency | | | | | |
| Prefill tokens/s | | | | | |
| Decode tokens/s | | | | | |
| TTFT p50/p95 (ms) | | | | | |
| Peak CPU/RAM/GTT (GiB) | | | | | |
| Average power and energy/token | | | | | |
| Correct tool calls (n/N) | | | | | |
| Output semantic/quality score | | | | | |
| GPU errors/hangs | | | | | |

## Validity gates

- [ ] Same model, quant, context and power conditions in paired comparisons
- [ ] Proper warmup and randomized A/B repetitions
- [ ] Running executable and selected kernel observed, not assumed
- [ ] Numeric kernel correctness and odd/small shape cases
- [ ] Full model-output quality and long context/tool arrays
- [ ] Concurrency and session-sentinel isolation
- [ ] Sustained thermal/power sampling
- [ ] No GPU hang, reset, leaks, silent CPU fallback or corrupt output
- [ ] Existing good baseline remains independently runnable
- [ ] Full rollback exercised and result verified

## Decision record

**Outcome:** Rejected / Research-only / Retest / Opt-in lab / Production candidate / Upstream-ready  
**Why:**  
**Known regressions:**  
**Other workstreams unblocked:**  
**Next independent experiment:**  
**Needs Volmarr's input?** (If yes, specify *actual* choices, urgency, consequences and safe default):
