#!/bin/bash
export PATH="$PATH:$HOME/.local/bin"
pdm install
pdm run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
echo success
pdm run python main.py &> log
