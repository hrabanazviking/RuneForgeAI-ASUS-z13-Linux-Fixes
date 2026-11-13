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
