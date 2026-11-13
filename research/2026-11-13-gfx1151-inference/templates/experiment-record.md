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
