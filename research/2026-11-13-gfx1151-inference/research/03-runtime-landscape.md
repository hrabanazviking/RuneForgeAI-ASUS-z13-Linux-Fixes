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
