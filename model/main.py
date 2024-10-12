from httpx_ws import aconnect_ws
from loguru import logger
from pyvts import vts
import numpy as np

from asyncio import run, sleep
from math import factorial
from pydantic import BaseModel, Field

class FaceAngle(BaseModel):
  """Live2D model's face angle"""
  x: float = Field(ge=-30,le=30)
  y: float = Field(ge=-30,le=30)
  z: float = Field(ge=-90,le=90)

class Eye(BaseModel):
  """Live2D model's eye"""
  opened: float = Field(ge=0,le=1)

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
  smiled: float = Field(description="Smile of Live2D model", ge=0, le=1)

class VTubeModel(BaseModel):
  "Move Live2D model"
  points: list[Point] = Field(description="List of points that will connecting by bezier curve")
  second: float = Field(description="Duration of the movement", ge=0)

BUTTER_URL = "http://192.168.0.159:10002"

def bezier_curve(points, num_output_points):
  """
  Generates a 1D Bezier curve for a given set of control points, allowing for float calculations.
  
  Parameters:
  points (list of float): Control points for the Bezier curve.
  num_output_points (int): The number of points to generate on the Bezier curve.
  
  Returns:
  list of float: Generated points on the Bezier curve.
  """
  n = len(points) - 1  # Degree of the Bezier curve
  t_values = np.linspace(0, 1, num_output_points)
  
  # Helper function to calculate a single Bezier point at t
  def bezier_point(t):
    bezier_sum = 0.0
    for i in range(n + 1):
      # Binomial coefficient for floats
      binomial_coeff = factorial(n) / (factorial(i) * factorial(n - i))
      bezier_sum += binomial_coeff * ((1 - t)**(n - i)) * (t**i) * points[i]
    return bezier_sum
  
  return [bezier_point(t) for t in t_values]

parameters = [
  'FaceAngleX',
  'FaceAngleY',
  'FaceAngleZ',
  'MouthSmile',
  'EyeOpenLeft',
  'EyeOpenRight',
  'EyeRightX',
  'EyeRightY',
  'Brows'
]

async def main():
  vts_inst = vts(plugin_info={'plugin_name': 'butter', 'developer': 'misile', 'authentication_token_path': './token'})
  await vts_inst.connect()
  await vts_inst.request_authenticate_token()
  await vts_inst.request_authenticate()
  async with aconnect_ws(f"{BUTTER_URL}/event", keepalive_ping_interval_seconds=None, keepalive_ping_timeout_seconds=None) as b:
    logger.debug("connected")
    while True:
      msg = await b.receive_json()
      logger.debug(msg["type"])
      if msg["type"] == "model":
        logger.info("hello")
        data = VTubeModel.model_validate(msg["data"])
        logger.info(data)
        logger.info(msg["data"]["second"])
        converted_data = [[] for _ in range(len(parameters))]
        for point in data.points:
          logger.debug(point)
          converted_data[0].append(point.face.x)
          converted_data[1].append(point.face.y)
          converted_data[2].append(point.face.z)
          converted_data[3].append(point.smiled)
          converted_data[4].append(point.leftEye.opened)
          converted_data[5].append(point.rightEye.opened)
          converted_data[6].append(point.eyeBall.x)
          converted_data[7].append(point.eyeBall.y)
          converted_data[8].append(point.eyeBrow)
        d = []
        for i in parameters:
          d.append((await vts_inst.request(vts_inst.vts_request.requestParameterValue(i)))['data']['value'])
        logger.debug(d)
        converted_data.insert(0, d)
        converted_data = [bezier_curve(data, int(100 * msg["data"]["second"])) for data in converted_data]
        logger.debug(converted_data)
        for i in range(int(100 * msg["data"]["second"])):
          logger.debug(i)
          await vts_inst.request(vts_inst.vts_request.requestSetMultiParameterValue(parameters, [converted_data[j][i] for j in range(len(parameters))]))
          await sleep(0.01)

run(main())