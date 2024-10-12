import gradio as gr
from httpx import get, post

from datetime import datetime
from pathlib import Path

try:
  user # type: ignore
except NameError:
  # first launch before gradio reload
  user = ""
  tempv2 = {
    "files": []
  }
  BASE_URL = Path("./base_url").read_text().strip('\n')

def process_memories(memories: list[dict]):
  a = []
  for i in memories:
    tmp = i.get("created_at", None)
    if tmp is None:
      tmp = i.get("updated_at", 0)
    a.append([i["id"], datetime.fromisoformat(tmp), i.get("user_id", ""), i["memory"]])
  return a

def confirm(user_v, prompt_v, middle_prompt_v, summarize_prompt_v):
  post(f'{BASE_URL}/prompt/main', data={"content": prompt_v}).raise_for_status()
  post(f'{BASE_URL}/prompt/middle', data={"content": middle_prompt_v}).raise_for_status()
  post(f'{BASE_URL}/prompt/summarize', data={"content": summarize_prompt_v}).raise_for_status()
  global user
  user = user_v
  return [user, prompt_v, middle_prompt_v, summarize_prompt_v]

async def generate_message(content: str, _):
  if user is None or user == "":
    raise gr.Error("no user")
  file_list = {'files': (f, open(f, 'rb')) for f in tempv2["files"]}
  print(file_list)
  if file_list != []:
    res = post(f"{BASE_URL}/chat/send", data={
      "name": user,
      "content": content,
    }, files=file_list, timeout=None) # type: ignore nah, i'll ignore
  else:
    res = post(f"{BASE_URL}/chat/send", data={"name": user, "content": content}, timeout=None)
  res.raise_for_status()
  return res.content.decode()

with gr.Blocks() as frontend:
  with gr.Tab("Chatting"):
    chat = gr.ChatInterface(generate_message)
    with gr.Accordion("more inputs", open=False):
      file = gr.File(type="filepath", label="Files", file_count="multiple")
      file.change(lambda x: tempv2.__setitem__("files", x), file)
  with gr.Tab("Configuration"):
    user_input = gr.Textbox(label="user")
    prompt_input = gr.Textbox(label="prompt", show_copy_button=True, interactive=True, lines=13)
    middle_prompt_input = gr.Textbox(label="middle_prompt", show_copy_button=True, interactive=True)
    summarize_prompt_input = gr.Textbox(label="summarize_prompt", show_copy_button=True, interactive=True)
    confirm_button = gr.Button("Confirm")
    confirm_button.click(
      confirm,
      [user_input, prompt_input, middle_prompt_input, summarize_prompt_input],
      [user_input, prompt_input, middle_prompt_input, summarize_prompt_input]
    )
  with gr.Tab("Admin Panel"):
    reset_history = gr.Button("Reset History", variant="stop")
    reset_history.click(lambda: post(f"{BASE_URL}/chat/reset").raise_for_status())
    
    df = gr.Dataframe(label="memories", headers=["id", "created_at", "user", "text"], datatype=["str", "date", "str", "str"])
    refresh = gr.Button("Refresh", variant="secondary")
    refresh.click(lambda: process_memories(post(f"{BASE_URL}/memory/get_all").raise_for_status().json()), None, df)

    memory_id = gr.Textbox(label="id of memory that modify")
    memory_content = gr.Textbox(label="content of memory that modify")
    memory_user = gr.Textbox(label="user of memory that modify")
    memory_save = gr.Button("Save", variant="primary")
    memory_save.click(lambda user, content: post(f"{BASE_URL}/memory/save", data={
      "username": None if user == "" else user, "content": content
    }), [memory_user, memory_content])
    
    memory_update = gr.Button("Update", variant="primary")
    memory_update.click(lambda id, content: post(f"{BASE_URL}/memory/update", data={
      "id": id, "content": content
    }), [memory_id, memory_content])
    
    memory_delete = gr.Button("Delete", variant="stop")
    memory_delete.click(lambda id: post(f"{BASE_URL}/memory/delete", data={"id": id}).raise_for_status(), [memory_id])
  frontend.load(lambda: [
    user,
    get(f"{BASE_URL}/prompt/main").raise_for_status().json(),
    get(f"{BASE_URL}/prompt/middle").raise_for_status().json(),
    get(f"{BASE_URL}/prompt/summarize").raise_for_status().json()
  ], None, [user_input, prompt_input, middle_prompt_input, summarize_prompt_input])

frontend.launch(show_error=True, show_api=True)
