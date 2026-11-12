#!/usr/bin/env python3
"""torch-health — one-command sanity check for the ROCm/PyTorch stack
on a gfx1151 (AMD Strix Halo / Radeon 8060S) machine.

Prints device identity, runs a correctness check, two GEMM perf probes and
a short stress loop, then a single-line verdict:

    TORCH-HEALTH OK / DEGRADED / FAIL

Usage:  /path/to/venv/bin/python torch-health.py
(e.g. the Python of any venv carrying the TheRock gfx1151 torch build)
"""
import sys
import time

import torch


def main() -> int:
    print("torch", torch.__version__, "| hip", torch.version.hip)
    if not torch.cuda.is_available():
        print("TORCH-HEALTH FAIL no GPU device visible")
        return 1
    dev = torch.device("cuda:0")
    props = torch.cuda.get_device_properties(0)
    print(f"device: {props.name} | CUs {props.multi_processor_count} | "
          f"{props.total_memory / 2**30:.1f} GiB visible")

    # correctness: 2048^2 fp32 matmul vs CPU reference
    a = torch.randn(2048, 2048, device=dev)
    b = torch.randn(2048, 2048, device=dev)
    got = (a @ b).float().cpu()
    want = a.cpu() @ b.cpu()
    maxdiff = (got - want).abs().max().item()
    correct = maxdiff < 0.5
    print(f"fp32 2048 matmul maxdiff vs CPU: {maxdiff:.4f} "
          f"({'OK' if correct else 'WRONG'})")

    def bench(dtype, size=2048, iters=20):
        x = torch.randn(size, size, device=dev, dtype=dtype)
        y = torch.randn(size, size, device=dev, dtype=dtype)
        for _ in range(3):
            x @ y
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(iters):
            x @ y
        torch.cuda.synchronize()
        dt = (time.perf_counter() - t0) / iters
        return 2 * size**3 / dt / 1e12

    fp32 = bench(torch.float32)
    fp16 = bench(torch.float16)
    print(f"GEMM 2048: fp32 {fp32:.2f} TFLOPS | fp16 {fp16:.2f} TFLOPS")

    # mini stress: 50 mixed iterations must not crash or hang
    x = torch.randn(1024, 1024, device=dev)
    for _ in range(50):
        x = torch.relu(x @ x * 0.01)
    torch.cuda.synchronize()
    peak = torch.cuda.max_memory_allocated() / 2**30
    print(f"stress: 50 iters OK, peak alloc {peak:.2f} GiB")

    healthy = correct and fp32 > 1.0 and fp16 > 5.0
    degraded = correct and fp32 > 0.5
    verdict = "OK" if healthy else ("DEGRADED" if degraded else "FAIL")
    print(f"TORCH-HEALTH {verdict}")
    return 0 if healthy else 2


if __name__ == "__main__":
    sys.exit(main())
