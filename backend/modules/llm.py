from .config import api_key
from . import memory, llm_function

from langchain_openai import ChatOpenAI
from pydantic import Field, BaseModel

functions = {**llm_function.functions, **memory.functions}
middle_converting_functions = {**llm_function.middle_converting_functions, **memory.middle_converting_functions}

class BodyAngle(BaseModel):
  """Live2D model's body angle"""
  x: float = Field(ge=-30,le=30)
  y: float = Field(ge=-30,le=30)
  z: float = Field(ge=-90,le=90)

class Eye(BaseModel):
  """Live2D model's eye"""
  opened: float = Field(ge=0,le=1)
  smiled: float = Field(ge=0,le=1)
  browForm: float = Field(ge=0,le=1)

class EyeBall(BaseModel):
  """Live2D model's eyeball"""
  x: float = Field(ge=-1,le=1)
  y: float = Field(ge=-1,le=1)

class Point(BaseModel):
  "Parameters for Live2D model (vtube studio)"
  body: BodyAngle = Field(description="Body angle of Live2D model")
  leftEye: Eye = Field(description="Left eye of Live2D model")
  rightEye: Eye = Field(description="Right eye of Live2D model")
  eyeBall: EyeBall = Field(description="Eye ball of Live2D model")

class Response(BaseModel):
  inner_thought: str = Field(description="Thought for next message but user can't see")
  message: str = Field(description="Message that you send to user")
  points: Point = Field(description="Point for vtube studio, between of lines will connecting by bezier curve")

llm = ChatOpenAI(model="gpt-4o", api_key=api_key).with_structured_output(Response).bind_tools(list(functions.values()))
