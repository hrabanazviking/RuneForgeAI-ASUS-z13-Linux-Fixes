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
