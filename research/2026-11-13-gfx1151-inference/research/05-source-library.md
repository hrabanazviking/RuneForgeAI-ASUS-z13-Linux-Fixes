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
