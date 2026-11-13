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
