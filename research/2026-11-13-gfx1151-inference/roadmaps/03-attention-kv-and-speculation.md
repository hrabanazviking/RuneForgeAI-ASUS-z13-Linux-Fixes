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
