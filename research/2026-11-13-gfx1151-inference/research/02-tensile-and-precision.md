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
