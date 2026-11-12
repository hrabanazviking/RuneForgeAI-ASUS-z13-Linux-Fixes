#!/bin/sh
# Install the arch-matched TheRock PyTorch build for gfx1151 into a venv.
#
# Usage:  ./install-pytorch-gfx1151.sh /path/to/venv
#
# The pins below are the exact nightly build verified on the ROG Flow Z13
# (GZ302EA). They must come from AMD's gfx1151 nightly index — PyPI and
# download.pytorch.org do NOT carry a working gfx1151 build (see NOTES.md).
set -eu

VENV="${1:?usage: install-pytorch-gfx1151.sh /path/to/venv}"
INDEX="https://rocm.nightlies.amd.com/v2/gfx1151/"

uv pip install --python "$VENV/bin/python" --index-url "$INDEX" \
    'torch==2.12.0a0+rocm7.13.0a20260411' \
    'torchvision==0.27.0a0+rocm7.13.0a20260411' \
    'torchaudio==2.11.0a0+rocm7.13.0a20260411'

echo
echo "Installed. Now verify with:"
echo "  $VENV/bin/python torch-health.py"
echo "Expected: arch list ['gfx1151'] and a TORCH-HEALTH OK verdict."
