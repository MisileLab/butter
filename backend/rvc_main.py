from modules.config import config
from modules.lib import print_it

from fastapi import FastAPI, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import texttospeech
from loguru import logger
from torch.cuda import is_available
from rvc_python.infer import RVCInference

import tempfile
from os import remove
from base64 import b64encode
from pathlib import Path

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

device = "cuda:0" if is_available() else "cpu"
logger.debug(f"device: {device}")

rvcinf = RVCInference(models_dir="model", device=device)
logger.debug(rvcinf.list_models())
rvcinf.load_model("model", "v1")
rvcinf.f0method = "harvest"
rvcinf.f0up_key = 2

wss: list[WebSocket] = []
@print_it
def generate_voice(content: str) -> str:
  client = texttospeech.TextToSpeechClient(client_options={
    "api_key": config["ai"]["google_tts"]
  })
  resp = client.synthesize_speech(
    input = texttospeech.SynthesisInput(text=content),
    voice = texttospeech.VoiceSelectionParams(
      language_code="ko-KR",
      name="ko-KR-neural2-A",
      ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    ),
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
  )
  with open(tempfile.mkstemp(suffix=".mp3")[1], "wb") as f:
    f.write(resp.audio_content)
    return f.name

async def broadcast(event_type: str, data: str):
  for ws in wss:
    await ws.send_json({"type": event_type, "data": data})

@app.post("/rvc")
async def recv_rvc(content: str = Form()):
  await broadcast("rvc", "start")
  base_tts = generate_voice(content)
  logger.debug(f"base_tts's path: {base_tts}")
  logger.debug("start rvc")
  rvcinf.infer_file(base_tts, "output.wav")
  await broadcast("rvc", "end")
  logger.debug("end rvc")
  try:
    remove(base_tts)
  except PermissionError:
    logger.warning("base_tts can't removed due to permission error")
  return b64encode(Path("output.wav").read_bytes()).decode('utf-8')
