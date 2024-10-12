from modules.llm_function import middle_prompt, llm_mini
from modules.llm import api_key, llm, functions, middle_converting_functions, llm_vtube
from modules.vtube import VTubeModel
from modules.memory import m
from modules.config import wss
from modules.lib import is_binary_string
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from loguru import logger
from openai import OpenAI
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
from base64 import b64encode, b64decode
from copy import deepcopy
from inspect import iscoroutinefunction
from typing import Any

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

async def broadcast(event_type: str, data: Any):
  for ws in wss:
    await ws.send_json({"type": event_type, "data": data})

prompt = Path("./prompts/prompt").read_text()
summarize_prompt = Path("./prompts/summarize_prompt").read_text()
messages: list[SystemMessage | AIMessage | ToolMessage | HumanMessage] = [SystemMessage(prompt)]
whisper = OpenAI(api_key=api_key)
current_points = None

@app.post("/chat/send")
async def send_message(
  name: str | None = Form(None),
  content: str | None = Form(None),
  files: list[UploadFile] = File(default=[])
):  # sourcery skip: low-code-quality
  logger.debug(messages[0])
  logger.debug(messages[-1])
  if name is None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be provided")
  logger.info(f"{name}: {content} with {files}")
  images = []
  result = f"here's the message of {name}:"
  if False in [is_binary_string(Path(i.filename).read_bytes()) for i in files if i.filename is not None]:
    result += "\n=====attachments====="
  for i in files:
    if i.filename is None:
      logger.debug("No filename, so skip")
      continue
    logger.debug(f"{i.filename}, {is_binary_string(Path(i.filename).read_bytes())}")
    if is_binary_string(Path(i.filename).read_bytes()):
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
        logger.debug(f"data:image/{ext};base64,{b64encode(Path(i.filename).read_bytes()).decode('utf-8')}")
        images.append(
          f"data:image/{ext};base64,{b64encode(Path(i.filename).read_bytes()).decode('utf-8')}"
        )
    else:
      result += f"{i.filename}(text)'s content: {(Path(i.filename).read_bytes()).decode('utf-8')}"
  if False in [is_binary_string(Path(i.filename).read_bytes()) for i in files if i.filename is not None]:
    result += "=====attachments end====="
  if content:
    result += f"=====content start=====\n{content}\n=====content end====="
  messages.append(
    HumanMessage(
      [{"type": "text", "text": result}] + [{"type": "image_url", "image_url": {"url": i, "detail": "high"}} for i in images] # type: ignore it is valid, trust
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
  if not isinstance(msg.content, str):
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Message content is not a string"
    )
  if len(messages) >= 70:
    tmp_messages = messages[1:60]
    while tmp_messages[-1].__class__ in [ToolMessage, HumanMessage]:
      logger.debug(f"stripping {tmp_messages[-1]}, because it doesn't ending with ai message")
      tmp_messages = tmp_messages[:-1]
    summarized = (await llm_mini.ainvoke([SystemMessage(summarize_prompt)] + deepcopy(tmp_messages))).content
    tmp_messages = messages[60:]
    while tmp_messages[0].__class__ == ToolMessage:
      logger.debug(f"stripping {tmp_messages[0]}, because it's starting with tool message")
      tmp_messages = tmp_messages[1:]
    messages.clear()
    messages.extend(
      [SystemMessage(prompt), HumanMessage(summarized), AIMessage("알았어!")] + deepcopy(tmp_messages)
    )
  global current_points
  con = msg.content
  _con = await llm_vtube.ainvoke([
    SystemMessage(prompt + f"\nthis is your character, move model based on input and character.\n{f'current model parameter is {current_points.model_dump()}' if current_points is not None else ''}"),
    HumanMessage(f"question: {content}, answer: {con}")
  ])
  logger.debug(_con)
  if not isinstance(_con, VTubeModel):
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="VTubeModel is not returned"
    )
  await broadcast("model", _con.model_dump())
  current_points = _con
  return PlainTextResponse(con)

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

@app.post("/whisper")
async def audio_to_text(file: str = Form()):
  logger.debug("start whisper")
  Path("temp_whisper.wav").write_bytes(b64decode(file))
  transcripted = whisper.audio.transcriptions.create(
    file = open('temp_whisper.wav', 'rb'),
    model = "whisper-1",
    prompt = "voice is mostly english and sometimes korean, If you dont know language just select to english"
  )
  logger.debug("end whisper")
  await broadcast("whisper", transcripted.text)
  return transcripted.text

@app.websocket("/event")
async def event(ws: WebSocket):
  await ws.accept()
  wss.append(ws)
  try:
    while True:
      data = await ws.receive_text()
      logger.debug(data)
  except WebSocketDisconnect:
    wss.remove(ws)
