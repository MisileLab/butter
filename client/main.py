from discord import Bot, VoiceClient, sinks
from discord.abc import GuildChannel
from discord.sinks.wave import WaveSink
from discord.sinks.errors import RecordingException
from tomli import loads
from httpx import post
from openai import OpenAI
from simpleaudio import play_buffer
from wave import open as wopen
from loguru import logger

from pathlib import Path
from io import BytesIO
from enum import Enum
from tempfile import mkstemp
from threading import Thread
from time import sleep
from os import remove

class Sinks(Enum):
  mp3 = sinks.MP3Sink()
  wav = sinks.WaveSink()
  pcm = sinks.PCMSink()
  ogg = sinks.OGGSink()
  mka = sinks.MKASink()
  mkv = sinks.MKVSink()
  mp4 = sinks.MP4Sink()
  m4a = sinks.M4ASink()

class UserVoice:
  name: str = ""
  io: BytesIO = BytesIO()
  silence_duration: float = 0

config = loads(Path("./config.toml").read_text())
user_data: dict[str, UserVoice] = {}
audio_queue = []
bot = Bot()
o = OpenAI(api_key=config["token_openai"])

def callback_sub():
  logger.info("start callback sub")
  while True:
    for i in audio_queue[:]:
      with wopen(i, "rb") as f:
        logger.debug(f"{i} playing")
        p = play_buffer(
          f.readframes(f.getnframes()),
          f.getnchannels(),
          f.getsampwidth(),
          f.getframerate()
        )
        p.wait_done()
        remove(i)
    sleep(1)

async def callback(sink):
  for u in user_data.values():
    u.silence_duration += 1
  for u, audio in sink.audio_data.items():
    if user_data.get(u, None) is None:
      user_data[u] = UserVoice()
    user_data[u].name = mkstemp(suffix=".wav")[1]
    user_data[u].io.write(BytesIO(audio.file.read()).getvalue())
    user_data[u].silence_duration = 0
  templist = []
  for k, u in user_data.items():
    if u.silence_duration < 2:
      Path(u.name).write_bytes(u.io.getvalue())
      logger.debug(u.name)
      exit()
      res = post(f"${config["url"]}/chat/send", data={"name": k, "content": o.audio.transcriptions.create(
        file=open(u.name, "rb"), model="whisper-1"
      ).text})
      res.raise_for_status()
      temp = mkstemp(suffix=".wav")[1]
      Path(temp).write_bytes(res.content)
      audio_queue.append(temp)
      templist.append(k)
  for i in templist:
    del user_data[i]

def timer_init(vc: VoiceClient):
  logger.info("timer init")
  while True:
    try:
      vc.start_recording(WaveSink(), callback)
      sleep(1)
      vc.stop_recording()
    except RecordingException:
      logger.warning("why not record")

@bot.listen(once=True)
async def on_ready():
  logger.info("Butter starting")
  b: GuildChannel = await bot.fetch_channel(config["voice"]) # type: ignore it must be voice channel
  vc = await b.connect() # type: ignore see above
  Thread(target=timer_init, args=(vc, )).start()
  Thread(target=callback_sub).start()

bot.run(config["token"])

