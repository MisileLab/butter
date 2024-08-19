from modules.llm_function import middle_prompt, llm_mini
from modules.llm import api_key, llm, functions, middle_converting_functions
from modules.memory import print_it, m
from modules.config import config

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from loguru import logger
from openai import OpenAI
from binaryornot.check import is_binary_string
from google.cloud import texttospeech
from rvc_python.infer import infer_file
from torch.cuda import is_available
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse

from pathlib import Path
from base64 import b64encode
from copy import deepcopy
from inspect import iscoroutinefunction
from os import remove
import tempfile

app = FastAPI()

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

prompt = Path("./prompts/prompt").read_text()
summarize_prompt = Path("./prompts/summarize_prompt").read_text()
messages: list[SystemMessage | AIMessage | ToolMessage | HumanMessage] = [SystemMessage(prompt)]
whisper = OpenAI(api_key=api_key)
device = "cuda:0" if is_available() else "cpu"
logger.debug(f"device: {device}")
directory = Path(tempfile.mkdtemp())

@app.post("/chat/send")
async def send_message(
  name: str | None = Form(None),
  content: str | None = Form(None),
  files: list[UploadFile] = File(default=[])
) -> FileResponse:  # sourcery skip: low-code-quality
  logger.debug(messages[0])
  logger.debug(messages[-1])
  if name is None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be provided")
  logger.info(f"{name}: {content} with {files}")
  images = []
  result = f"here's the message of {name}:"
  if files is not None:
    result += "\n=====attachments====="
    for i in files:
      if i.filename is None:
        logger.debug("No filename, so skip")
        continue
      if is_binary_string(await i.read()):
        if True in [i.filename.startswith(v) for v in [".mp3", ".mp4"]]:
          transcripted = whisper.audio.transcriptions.create(
            file = i.file,
            model = "whisper-1"
          )
          result += f"{i.filename}(audio)'s transcripted text: {transcripted.text}"
        else:
          fname = i.filename
          ext = ""
          if fname.endswith(".png"):
            ext = "png"
          elif fname.endswith(".jpg") or fname.endswith(".jpeg"):
            ext = "jpeg"
          elif fname.endswith(".webp"):
            ext = "webp"
          else:
            logger.debug(f"{fname} is not valid")
            continue
          images.append(
            f"data:image/{ext};base64,{b64encode(await i.read()).decode('utf-8')}"
          )
      else:
        result += f"{i.filename}(text)'s content: {(await i.read()).decode('utf-8')}"
    result += "=====attachments end====="
  if content:
    result += f"=====content start=====\n{content}\n=====content end====="
  messages.append(
    HumanMessage(
      [{"type": "text", "text": result}] + [{"type": "image_url", "image_url": {"url": i}} for i in images] # type: ignore it is valid, trust
    )
  )
  logger.debug("stage 1: give message to llm")
  msg: AIMessage = await llm.ainvoke(messages) # type: ignore it's aimessage
  while msg.tool_calls:
    messages.append(msg)
    for tool in msg.tool_calls:
      logger.debug(f"call {tool}")
      f = middle_converting_functions[functions[tool["name"]]]
      if iscoroutinefunction(f):
        func_response = await f(**tool["args"])
      else:
        func_response = f(**tool["args"])
      messages.append(
        ToolMessage(tool_call_id=tool["id"], content=str(func_response))
      )
    msg: AIMessage = await llm.ainvoke(messages) # type: ignore it's aimessage
  messages.append(msg)
  logger.debug("stage 2: let's tts and rvc")
  if not isinstance(msg.content, str):
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Message content is not a string"
    )
  base_tts = generate_voice(msg.content)
  logger.debug(f"base_tts's path: {base_tts}")
  rvc_path = infer_file(
    input_path = base_tts,
    model_path = "./model/model.pth",
    index_path = "./model/model.index",
    f0method = "harvest",
    f0up_key = 2,
    opt_path = str(directory.joinpath("out.wav")),
    index_rate = 0.5,
    filter_radius = 3,
    resample_sr = 0,
    rms_mix_rate = 1,
    protect = 0.33,
    version = "v1",
    device = device
  )
  logger.debug("remove base_tts, because rvc ended")
  try:
    remove(base_tts)
  except PermissionError:
    logger.warning("base_tts can't removed due to permission error")
  if len(messages) >= 70:
    tmp_messages = messages[1:60]
    while tmp_messages[-1].__class__ in [ToolMessage, HumanMessage]:
      logger.debug(f"stripping {tmp_messages[-1]}, because it doesn't ending with ai message")
      tmp_messages = tmp_messages[:-1]
    summarized = llm_mini.invoke([SystemMessage(summarize_prompt)] + deepcopy(tmp_messages)).content
    tmp_messages = messages[60:]
    while tmp_messages[0].__class__ == ToolMessage:
      logger.debug(f"stripping {tmp_messages[0]}, because it's starting with tool message")
      tmp_messages = tmp_messages[1:]
    messages.clear()
    messages.extend(
      [SystemMessage(prompt), HumanMessage(summarized), AIMessage("알았어!")] + deepcopy(tmp_messages)
    )
  return FileResponse(path=rvc_path, media_type="audio/wav")

@app.post("/chat/reset")
async def reset_chat():
  messages.clear()
  messages.append(SystemMessage(prompt))

@app.post("/prompt/main")
async def set_prompt(content: str = Form()):
  global prompt
  prompt = content
  Path("./prompts/prompt").write_text(prompt)

@app.get("/prompt/main")
async def get_prompt():
  return prompt

@app.post("/prompt/middle")
async def set_middle_prompt(content: str = Form()):
  global middle_prompt
  middle_prompt = content
  Path("./prompts/middle_prompt").write_text(middle_prompt)

@app.get("/prompt/middle")
async def get_middle_prompt():
  return middle_prompt

@app.post("/prompt/summarize")
async def set_summarize_prompt(content: str = Form()):
  global summarize_prompt
  summarize_prompt = content
  Path("./prompts/summarize_prompt").write_text(summarize_prompt)

@app.get("/prompt/summarize")
async def get_summarize_prompt():
  return summarize_prompt

@app.post("/memory/save")
async def save_memory_api(
  content: str = Form(),
  username: str | None = Form(None)
):
  return m.add(content, user_id=username)

@app.post("/memory/get_all")
async def get_all_memories_api(username: str | None = Form(None)):
  return m.get_all(username)

@app.post("/memory/get")
async def get_memory_api(id: str = Form()):
  return m.get(id)

@app.post("/memory/search")
async def search_memory_api(
  query: str = Form(),
  username: str | None = Form(None)
):
  return m.search(query, username)

@app.post("/memory/update")
async def update_memory_api(
  id: str = Form(),
  content: str = Form()
):
  return m.update(id, content)

@app.post("/memory/history")
async def get_memory_history_api(id: str = Form()):
  return m.history(id)

@app.post("/memory/delete")
async def delete_memory_api(id: str = Form()):
  return m.delete(id)

@app.post("/memory/reset")
async def reset_memory_api():
  m.reset()

