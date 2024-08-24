import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import threading
from keyboard import add_hotkey, wait
from loguru import logger
from openai import OpenAI
from tomli import loads
from httpx import post
from playsound3 import playsound

from pathlib import Path

is_recording = False
audio_data = []
config = loads(Path("config.toml").read_text())
o = OpenAI(api_key=config["token_openai"])

def record_audio():
  global is_recording, audio_data
  while is_recording:
    # Record audio in chunks
    audio_chunk = sd.rec(int(44100 * 0.5), samplerate=44100, channels=1, dtype='int16')
    sd.wait()
    audio_data.append(audio_chunk) # type: ignore

def start_recording():
  global is_recording, audio_data
  logger.info("rec start")
  if not is_recording:
    is_recording = True
    audio_data = []
    # deepcode ignore MissingAPI: <please specify a reason of ignoring this>
    thread = threading.Thread(target=record_audio)
    thread.start()

def stop_recording_and_save():
  global is_recording, audio_data
  if is_recording:
    is_recording = False
    logger.info("rec stop")
    logger.debug("stage 1: save to wav")
    # Concatenate all the audio chunks and save to WAV file
    audio_data = np.concatenate(audio_data, axis=0)
    write('output.wav', 44100, audio_data)
    logger.debug("stage 2: send to whisper")
    resp = o.audio.transcriptions.create(file=open('output.wav', 'rb'), model="whisper-1").text
    logger.debug(f"resp: {resp}")
    logger.debug("stage 3: send to butter")
    resp = post(f"{config['BASE_URL']}/chat/send", timeout=None).content
    Path("output_butter.wav").write_bytes(resp)
    playsound("output_butter.wav", False)
    audio_data = []

def main():
  logger.debug("Hotkey pressed")
  logger.debug(is_recording)
  if not is_recording:
    start_recording()
  else:
    stop_recording_and_save()

add_hotkey('ctrl+q', main)
wait()
