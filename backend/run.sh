#!/bin/bash
export PATH="$PATH:$HOME/.local/bin"
pdm install
pdm run pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm6.1
echo success
pdm run fastapi run main.py --port 50000
