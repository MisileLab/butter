from httpx_ws import aconnect_ws
from loguru import logger
from pyvts import vts
import numpy as np

from asyncio import run
import math

BUTTER_URL = "http://192.168.0.159:10002"

def bernstein_poly(i, n, t):
  """
  Compute the Bernstein polynomial of n, i as a function of t.
  """
  return math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))

def bezier_curve(control_points, num_points=100):
  """
  Generate a one-dimensional Bézier curve from control points.
  
  Args:
  control_points: A list of control points, each represented as a scalar.
  num_points: The number of points to calculate on the Bézier curve.
  
  Returns:
  A numpy array of shape (num_points,) containing the curve points.
  """
  n = len(control_points) - 1
  t_values = np.linspace(0, 1, num_points)
  curve = np.zeros(num_points)
  for i, t in enumerate(t_values):
    point = sum(
      bernstein_poly(j, n, t) * control_point
      for j, control_point in enumerate(control_points))
    curve[i] = point
  return curve

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
  async with aconnect_ws(f"{BUTTER_URL}/ws") as b:
    while True:
      msg = await b.receive_json()
      logger.debug(msg)
      if msg["type"] == "move_model":
        converted_data = [[] for _ in range(len(parameters))]
        for point in msg["data"]:
          logger.debug(point)
          converted_data[0].append(point["face"]["x"])
          converted_data[1].append(point["face"]["y"])
          converted_data[2].append(point["face"]["z"])
          converted_data[3].append(point["leftEye"]["smiled"])
          converted_data[4].append(point["leftEye"]["opened"])
          converted_data[5].append(point["rightEye"]["opened"])
          converted_data[6].append(point["eyeBall"]["x"])
          converted_data[7].append(point["eyeBall"]["y"])
          converted_data[8].append(point["eyeBrow"])
        converted_data = [bezier_curve(data, 100 * msg["data"]["second"]) for data in converted_data]
        for i in range(100 * msg["data"]["second"]):
          await vts_inst.request(vts_inst.vts_request.requestSetMultiParameterValue(parameters, [converted_data[j][i] for j in parameters]))

run(main)