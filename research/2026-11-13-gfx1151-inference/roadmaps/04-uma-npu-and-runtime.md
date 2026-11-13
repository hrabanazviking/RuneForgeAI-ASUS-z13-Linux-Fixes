# Roadmap IV — Unified-memory, CPU/GPU/NPU scheduling and sustainable inference

**Mission:** exploit the APU as a coherent *system*, not an isolated GPU. The Ryzen AI MAX+ 395 has a 16-core CPU, 40-CU Radeon 8060S, XDNA 2 NPU and 128 GB of physically shared LPDDR5X; shared memory increases capacity flexibility, but CPU/GPU/NPU workloads can compete for memory bandwidth and power.

## Existing project evidence

- The repo records **GTT pool 60.75 → 121.5 GiB** using `iommu=pt amdgpu.gttsize=126976 ttm.pages_limit=32505856`, while keeping the NPU visible. An 80 GB FP32 GPU tensor was allocated and validated. This is evidence for this machine's tested configuration, not advice to stack further kernel flags.
- On the project's pinned Kubuntu 26.10 build, the NPU is visible through `amdxdna` and XRT; `FastFlowLM` generated on the NPU with Qwen3-0.6B and a reported **81.96 tok/s** decode. This does not imply that any arbitrary model can be moved to the NPU.
- AMD advertises the processor memory at 256-bit LPDDR5X-8000 with **256 GB/s peak bandwidth**. Effective sustainable bandwidth to GPU models is workload- and power-dependent.

## Campaign A — Memory capacity and allocation integrity

1. Document real physical memory, `MemAvailable`, GTT/debugfs counters, pinned allocations, CPU model memory, page cache, resident CPU agents, NPU allocation and GPU device allocations across realistic model loads. Account for OS and safety margin; a 121.5 GiB GTT pool is not a promise of 121.5 GiB usable for weights plus KV cache.
2. Test allocator behavior at 40/60/80/96 GiB model+KV allocations as appropriate, not necessarily a single tensor. Check fragmentation, long-context KV growth, release behavior and swap involvement.
3. Analyze zero-copy/unified-memory path claims with actual traces; absence of explicit PCIe transfers does not equal no synchronization or zero allocation overhead. Record where pinned buffers or host-shared allocations affect backend correctness.
4. Compare mmap-on-demand, preloading, mlock, huge pages and model cache methods only where supported; ensure no configuration silently induces OOM or application pressure. Never turn off IOMMU to chase a microbenchmark when the NPU requires it.

**Gate:** reliable model loading/unloading under multi-agent use without OOM, stale mapped memory or hidden CPU fallback; state preserved through restarts.

## Campaign B — CPU/GPU/NPU role atlas

Define workloads for all three compute units: GPU large model decode/prefill, NPU small local models, CPU preprocessing/tokenization and fallback tasks. Measure them individually first, then pairwise and three-way under the same power modes. Record end-to-end tokens/s, task success, memory bandwidth, power and per-device temperature. A workload should be assigned to the NPU only after verifying compatible runtime/model/firmware and practical gains.

Candidate roles to **test**:

- NPU: suitable compact assistant, classifier, routing, wake-word or background inference where FastFlowLM or another verified implementation supports the exact architecture and model.
- GPU: the largest quantized LLM, high-throughput prefill, transformer attention and parallel workloads; verify HIP/Vulkan path per model.
- CPU: tokenizer, orchestration, I/O and limited preprocessing; avoid contention with the GPU memory fabric under heavy load.

Do **not** assert arbitrary split execution of one transformer between NPU and GPU is possible or beneficial. Transport and graph-format restrictions may eliminate the opportunity; explicit middleware and tests are required.

## Campaign C — Memory-bandwidth and power-aware scheduling

1. Measure sequential-stream bandwidth/latency with validated microbenchmarks and GPU profiler. Use actual achieved bandwidth as denominator for per-token weight-read efficiency, not always the advertised 256 GB/s.
2. Assess sustained throughput across machine-supported power profiles; do not assume the desktop AMD Halo platform's 120 W rating is achievable indefinitely in the thin 13-inch Z13 chassis. Record AC supply, charge cap, thermal and fan profiles, package power, GPU clock residency and throttling.
3. For multiple agents, compare parallel model processes against queued requests to one model server. Model instances duplicate weights and KV caches; batching may deliver better shared-resource efficiency.
4. Explore interactive-service scheduling: prioritize latency-sensitive voice/chat without starving research, code generation or embedding jobs. Stage downloads, indexing and backups outside measurement windows.
5. Capture joules/token and useful task completions per watt, with a clear source for power samples and sampling interval. Heat stability and low fan noise can matter more than peak benchmark speed.

## Campaign D — Reliability and proactive maintenance

Integrate with the repo's existing battery-charge cap, home snapshot timer, hardware telemetry and read-only health-verdict scripts. Avoid creating a second restart supervisor or unbounded autonomous power-reconfiguration loop. A watchdog should quarantine an experiment or restore its isolated environment, not modify firmware/BIOS without explicit high-level authorization.

**Suggested success:** improved model completion time and stable parallel tasks at acceptable power/noise; no loss of current NPU functionality; no untested kernel flags or global memory-manager changes.

**Sources:** existing repo `fixes/unified-memory-params/NOTES.md`, `fixes/npu-userland/NOTES.md`, `fixes/power-thermal-watch/`; AMD developer device specification https://www.amd.com/en/products/processors/desktops/ryzen/ryzen-ai-halo/ryzen-ai-max-plus-395.html ; AMD system optimization https://rocm.docs.amd.com/en/docs-7.2.0/how-to/system-optimization/strixhalo.html .
