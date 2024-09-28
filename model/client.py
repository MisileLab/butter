from pyvts import vts
from tensorflow.keras.models import load_model
from numpy import array, expand_dims
from numpy.random import uniform
import numpy as np

from asyncio import run
from time import sleep
import math

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

model = load_model('./model.keras')

def normalize_value(data_type: str, value: float) -> float:
  if data_type in {'FaceAngleX', 'FaceAngleY'}:
    value /= 3
  elif data_type in {
      'EyeOpenLeft',
      'MouthSmile',
      'EyeOpenRight'
    }:
    value = (value+90)/180
  elif data_type not in ['FaceAngleZ']:
    value /= 90
  return value

def convert_value(data_type: str, value: float) -> float:
  if data_type in {'FaceAngleX', 'FaceAngleY'}:
    value *= 3
  elif data_type in {
      'EyeOpenLeft',
      'MouthSmile',
      'EyeOpenRight'
    }:
    value = value*180-90
  elif data_type not in ['FaceAngleZ']:
    value *= 90
  return value

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

async def main():
  vts_inst = vts(plugin_info={'plugin_name': 'butter_record', 'developer': 'misile', 'authentication_token_path': './token'})
  await vts_inst.connect()
  await vts_inst.request_authenticate_token()
  await vts_inst.request_authenticate()
  sleep(3)
  print('start')
  past_value = []
  while True:
    if not past_value:
      tmp = []
      for i in parameters:
        data = await vts_inst.request(vts_inst.vts_request.requestParameterValue(i))
        print(data)
        tmp.append(convert_value(i, min(max(data['data']['value'], data['data']['min']), data['data']['max'])))
      print(tmp)
      past_value = [tmp for _ in range(4)]
    raw_data = model.predict(expand_dims(array(past_value), axis=0))[0]
    data = [
      max(-90, min(90, float(i))) for i in raw_data
    ]
    data += uniform(-50, 20, (1, 9))[0]
    for i, j in zip(parameters, data):
      j = normalize_value(i, min(max(j, -90), 90))
    print(data)
    data_result = [
      bezier_curve((past_value[-1][i], data[i]), 10000)
      for i in range(len(parameters))
    ]
    for i in range(10000):
      await vts_inst.request(vts_inst.vts_request.requestSetMultiParameterValue(parameters, [data_result[j][i] for j in range(len(parameters))]))
      sleep(0.001)
    past_value.append([convert_value(parameters[i], data[i]) for i in range(len(parameters))])
    del past_value[0]

if __name__ == '__main__':
  run(main())
