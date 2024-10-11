from pydantic import BaseModel, Field

class FaceAngle(BaseModel):
  """Live2D model's face angle"""
  x: float = Field(description="-30~30")
  y: float = Field(description="-30~30")
  z: float = Field(description="-90~90")

class Eye(BaseModel):
  """Live2D model's eye"""
  opened: float = Field(description="0~1")
  smiled: float = Field(description="0~1")

class EyeBall(BaseModel):
  """Live2D model's eyeball"""
  x: float = Field(description="-1~1")
  y: float = Field(description="-1~1")

class Point(BaseModel):
  "Point of bezier curve"
  face: FaceAngle = Field(description="Face angle of Live2D model")
  leftEye: Eye = Field(description="Left eye of Live2D model")
  rightEye: Eye = Field(description="Right eye of Live2D model")
  eyeBall: EyeBall = Field(description="Eye ball of Live2D model")
  eyeBrow: float = Field(description="Eye brow of Live2D model (-1~1)")

class VTubeModel(BaseModel):
  "Move Live2D model"
  points: list[Point] = Field(description="List of points that will connecting by bezier curve")
  second: float = Field(description="Duration of the movement (>=0)")