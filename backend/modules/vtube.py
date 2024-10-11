from pydantic import BaseModel, Field

class FaceAngle(BaseModel):
  """Live2D model's face angle"""
  x: float = Field(ge=-30,le=30)
  y: float = Field(ge=-30,le=30)
  z: float = Field(ge=-90,le=90)

class Eye(BaseModel):
  """Live2D model's eye"""
  opened: float = Field(ge=0,le=1)
  smiled: float = Field(ge=0,le=1)

class EyeBall(BaseModel):
  """Live2D model's eyeball"""
  x: float = Field(ge=-1,le=1)
  y: float = Field(ge=-1,le=1)

class Point(BaseModel):
  "Point of bezier curve"
  face: FaceAngle = Field(description="Face angle of Live2D model")
  leftEye: Eye = Field(description="Left eye of Live2D model")
  rightEye: Eye = Field(description="Right eye of Live2D model")
  eyeBall: EyeBall = Field(description="Eye ball of Live2D model")
  eyeBrow: float = Field(description="Eye brow of Live2D model", ge=-1, le=1)

class VTubeModel(BaseModel):
  "Move Live2D model"
  points: list[Point] = Field(description="List of points that will connecting by bezier curve")
  second: float = Field(description="Duration of the movement", ge=0)