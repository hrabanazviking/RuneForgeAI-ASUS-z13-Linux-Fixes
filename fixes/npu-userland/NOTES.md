# npu-userland — get the XDNA 2 NPU working from Linux

**Status: proven end-to-end** (XRT sees the silicon; an LLM
generating on the NPU, with the server log proving the NPU — not a
CPU fallback — did the work).

## Symptom

The Ryzen AI Max+ 395's XDNA 2 NPU is alive at kernel level
(in-tree `amdxdna` driver, device node present), but nothing in
userland can talk to it out of the box: no XRT tools, and the usual
"which vendor stack do I install" hunt ends in Windows-only dead
ends (see the last section).

## The road that works on Kubuntu / Ubuntu 26.10

### 1. XRT is already in Ubuntu universe — no PPA

```sh
sudo apt install libxrt-npu2 libxrt-utils-npu
```

On 26.10 these are version `1:2.25.0-4ubuntu1` from
`stonking/universe` — the NPU userland ships in the release itself.
No PPA, and no need to force another release's packages. The kernel
side (`amdxdna`) is in-tree and needs nothing.

### 2. The memlock drop-in is not optional

XRT maps large buffers, and the stock per-user memlock limit
(8192 KB) is far too small. Without the drop-in, the failure looks
like this:

```
$ xrt-smi examine
… mmap … failed (err=-11)
```

Install `30-memlock-npu.conf` (shipped in this folder) into
`/etc/security/limits.d/`:

```sh
sudo install -m 0644 30-memlock-npu.conf /etc/security/limits.d/
```

Then log in again (the limit is set by PAM at login) and check:

```sh
ulimit -l        # should print: unlimited
```

### 3. Verify XRT sees the silicon

```sh
xrt-smi examine
```

On the reference machine XRT 2.25.00 reports the device as
**NPU Strix Halo, aie2p, 6x8**, with **NPU firmware 1.1.2.65**
(the road needs firmware ≥ 1.1.0.0).

### 4. FastFlowLM — the LLM runtime that runs on the NPU

Install AMD's official vendor package (FastFlowLM v1.0.12):

```
fastflowlm_1.0.12_ubuntu26.04_amd64.deb
```

Despite the `ubuntu26.04` in the name, it dry-ran clean on 26.10 —
every dependency already satisfied — and installed as-is.

Validate the whole stack in one shot:

```sh
flm validate
```

All green on the reference machine: kernel, NPU device
`/dev/accel/accel0` (8 columns), firmware 1.1.2.65, `amdxdna`,
memlock: infinity, platform **aie2p**.

### 5. Proof — a model actually generating on the NPU

```sh
flm pull qwen3:0.6b      # 652 MB, all files verified
flm serve qwen3:0.6b     # serves on port 52625
```

The `Qwen3-0.6B-NPU2` artifact loaded in ~2 s and answered a chat
completion with real generated text. The part that proves it ran
on the NPU and not as a quiet CPU fallback: the server log wraps
generation in **`NPU Locked!` … `NPU Lock Released!`**. Measured on
the reference machine: prefill 43.18 tok/s, **decode 81.96 tok/s**.

No persistent service was set up — `flm serve` runs on demand,
which is all this road needs.

## The dead end, so you don't walk it again

The ONNX Runtime / VitisAI execution-provider road for this NPU is
**Windows-only**. On Linux, FastFlowLM (and the Lemonade stack
built on the same ground) is the working NPU LLM path; don't burn
an evening trying to make the Windows EP load here.

## Caveats

- Firmware floor: the XRT/FastFlowLM road expects NPU firmware
  ≥ 1.1.0.0; `xrt-smi examine` shows what you have.
- The memlock change is system-wide for the listed users/groups
  (the drop-in uses `*`). It raises a resource ceiling; it grants
  no privileges.
- Rollback: remove the two packages, delete the drop-in, and
  `apt remove fastflowlm` — nothing else on the system is touched.
