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
