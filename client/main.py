import gradio as gr
import numpy as np
from pyannote.audio import Pipeline
from tomli import loads
from torch import tensor

from pathlib import Path

config = loads(Path("./config.toml").read_text())

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", use_auth_token=config["auth_token"])

def transcribe(stream, new_chunk):
    sr, y = new_chunk
    y = y.astype(np.float32)
    y /= np.max(np.abs(y))

    if stream is not None:
        stream = np.concatenate([stream, y])
    else:
        stream = y
    return stream, pipeline({"audio": stream})

demo = gr.Interface(
    transcribe,
    ["state", gr.Audio(sources=["microphone"], streaming=True)],
    ["state", "text"],
    live=True,
)

demo.launch()

