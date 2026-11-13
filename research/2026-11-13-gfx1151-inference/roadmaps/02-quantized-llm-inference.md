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
