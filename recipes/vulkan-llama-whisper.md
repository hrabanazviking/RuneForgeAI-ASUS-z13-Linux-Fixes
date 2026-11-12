# Recipes — universal bits from the reference machine's AI stack

Short, hardware-specific recipes that other GZ302 / Strix Halo owners
will hit immediately. (Model storage layout and service wiring from the
reference machine are deliberately *not* here — those were one owner's
choices, not universal fixes.)

## llama.cpp / whisper.cpp with Vulkan on gfx1151

Vulkan is the dependable GPU path for llama.cpp on this hardware (RADV
driver, device name `STRIX_HALO`).

Build dependencies — the SPIRV/glslang set is the part everyone misses:

```sh
sudo apt install libvulkan-dev vulkan-tools glslc \
                 libcurl4-openssl-dev libssl-dev \
                 spirv-headers glslang-tools spirv-tools
```

Without `spirv-headers` and `glslang-tools` the first configure fails
(missing SPIRV-Headers / glslangValidator). Note `libglslang-dev` does
**not** exist in the Ubuntu 26.10 archive — the tools package above is
the right one.

Build:

```sh
cmake -B build -DGGML_VULKAN=ON
cmake --build build -j
```

Measured on the reference machine (llama-bench, qwen2.5:0.5b Q4_K GGUF,
99/99 layers offloaded to the Radeon 8060S): **pp256 ≈ 12,782 tok/s,
tg64 ≈ 356 tok/s**.

- llama.cpp — MIT — https://github.com/ggml-org/llama.cpp
- whisper.cpp — MIT — https://github.com/ggml-org/whisper.cpp

## uv tool installs: pin the interpreter

`uv tool install` for heavier AI front-ends (**open-webui**,
**langflow**, **aider**) failed on the reference machine when uv picked
the newest Python (3.14) as the tool interpreter. Pin 3.12 explicitly:

```sh
uv tool install --python 3.12 open-webui
uv tool install --python 3.12 langflow
uv tool install --python 3.12 aider-chat
```

Same lesson applies to venvs for the PyTorch stack (see
`../fixes/pytorch-gfx1151/`): on a fast-moving distro, *choose* the
interpreter; don't let the tool choose the newest one for you.
