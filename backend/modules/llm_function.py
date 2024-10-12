from .config import api_key, config, minio, serpapi_key
from .lib import print_it

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage

from loguru import logger
from duckduckgo_search import AsyncDDGS
from httpx import AsyncClient, get
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from bs4.element import Comment
from pydantic import BaseModel, Field
from openai import BadRequestError

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

middle_prompt = Path("./prompts/middle_prompt").read_text()
llm_mini = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

class describeImageBase(BaseModel):
  """Question to AI that can describe and answer about certain image"""
  image_url: str = Field(description="Image's url that will describes, cannot empty, supported type is webp, png, jpg.")
  question: str = Field(description="Question that want ask to ai")

@print_it
async def describe_image(image_url: str, question: str):
  if not image_url:
    return "image url cannot empty"
  try:
    return (await llm_mini.ainvoke([
      {"role": "system", "content": "describe certain image and answer about user's interest"},
      {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": image_url}},
        {"type": "text", "text": question}
      ]}
    ])).content
  except BadRequestError:
    return "its not image"

llm_describe = ChatOpenAI(model="gpt-4o-mini", api_key=api_key).bind_tools([describeImageBase])

async def summarize_and_answer(content: str, question: str) -> str:
  finalvalue: list[str] = []
  end = False
  while True:
    _content = content
    if len(_content) >= 16384:
      _content = content[:16384]
      content = content[16384:]
    else:
      end = True
    summarized = "".join(
      f"String {i * 16384}~{(i + 1) * 16384} summarized:\n{i2}"
      for i, i2 in enumerate(finalvalue)
    )
    tmpmsg = [
      SystemMessage(middle_prompt),
      HumanMessage(f"content: {content}\nquestion: {question}\n{summarized}")
    ]
    tmp: AIMessage = await llm_describe.ainvoke(tmpmsg) # type: ignore nah, its compatible with BaseMessage
    tmpmsg.append(tmp)
    while tmp.tool_calls:
      logger.debug(tmp.tool_calls)
      for i in tmp.tool_calls:
        tmpmsg.append(ToolMessage(tool_call_id=i["id"], content=await describe_image(**i["args"])))
      tmp = await llm_describe.ainvoke(tmpmsg) # type: ignore same as above
    tmpmsg.append(tmp)
    if not isinstance(tmp.content, str):
      logger.error("summarize and answer doesn't return string")
      return "failed"
    finalvalue.append(tmp.content)
    if end:
      break
  return '\n'.join(f"Part {i+1}:\n{i2}" for i, i2 in enumerate(finalvalue))

def tag_visible(element):
  if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
    return False
  return not isinstance(element, Comment)

def text_from_html(body):
  soup = BeautifulSoup(body, 'lxml')
  texts = soup.findAll(text=True)
  visible_texts = filter(tag_visible, texts) 
  return u" ".join(t.strip() for t in visible_texts)

def get_date_from_string(date: str) -> datetime:
  d = datetime.fromisoformat(date)
  return d if d.tzinfo is not None else d.replace(tzinfo=timezone.utc)

@print_it
async def send_request(url: str, question: str) -> str:
  async with AsyncClient() as c:
    resp = await c.get(url)
  con = text_from_html(resp.content)
  return await summarize_and_answer(con, question)

@print_it
async def send_request_using_browser(url: str, question: str) -> str:
  op = Options()
  op.add_argument("--headless")
  web = Firefox(options=op)
  web.get(url)
  con = text_from_html(web.page_source)
  web.close()
  return await summarize_and_answer(con, question)

@print_it
async def search_internet(query: str, question: str) -> str:
  query = query.replace("\n", "")
  tmp = await AsyncDDGS().atext(query, region="ko-kr", max_results=10)
  res = []
  for i in tmp:
    res.append({"type": "text", "text": f"Title: {i["title"]}\ndescription: {i["body"]}\nhref: {i["href"]}"})
  logger.debug(res)
  f = (await llm_mini.ainvoke([
    {"role": "system", "content": middle_prompt},
    {"role": "user", "content": f"content: {res}\nquestion: {question}"}
  ])).content
  if not isinstance(f, str):
    logger.error("search_internet does not return string")
    return "failed"
  return f

@print_it
async def lens(question: str, image: str) -> str:
  if not image.startswith("https"):
    if not Path(image).exists():
      return "image not found"
    minio.fput_object("butter", Path(image).name, image)
  params = {
    "engine": "google_reverse_image",
    "q": question,
    "image_url": f"https://{config["minio"]["url"]}/butter/{quote_plus(Path(image).name)}",
    "api_key": serpapi_key
  }

  search = get("https://serpapi.com/search", params=params)
  minio.remove_object("butter", Path(image).name)
  logger.debug(search.json())
  if search.is_error:
    logger.error(search.json())
    return "failed"
  return await summarize_and_answer(str(search.json()), question)

class sendRequestBase(BaseModel):
  """send request to url and return the summarized content with llm, you can send the question to llm."""
  url: str = Field(description="url to send request")
  question: str = Field(description="question to ask llm")

class sendRequestUsingBrowserBase(BaseModel):
  """same with send_request, but use browser to get the content. should be used when the content is not loaded by http request."""
  url: str = Field(description="url to send request")
  question: str = Field(description="question to ask llm")

class searchInternetBase(BaseModel):
  """search the internet with query and return the summarized content with llm, you can send the question to llm."""
  query: str = Field(description="query to search")
  question: str = Field(description="question to ask llm")

class lensBase(BaseModel):
  """describe image and gives information about it"""
  question: str = Field(description="question that gives to llm and search engine")
  # you know it, it's duct tape
  image: str = Field(description="url or local file of image (if image is external must starts with https, if image is attachment must be starts with /tmp/gradio)")

functions = {
  "sendRequestBase": sendRequestBase,
  "sendRequestUsingBrowserBase": sendRequestUsingBrowserBase,
  "searchInternetBase": searchInternetBase,
  "describeImageBase": describeImageBase,
  "lensBase": lensBase
}

middle_converting_functions = {
  sendRequestBase: send_request,
  sendRequestUsingBrowserBase: send_request_using_browser,
  searchInternetBase: search_internet,
  describeImageBase: describe_image,
  lensBase: lens
}
