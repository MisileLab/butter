from pyvts import vts
from tensorflow.keras.models import load_model
from numpy import array
from numpy.random import uniform

from asyncio import run
from time import sleep

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
    value = value/180+90
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

async def main():
  vts_inst = vts(plugin_info={'plugin_name': 'butter_record', 'developer': 'misile', 'authentication_token_path': './token'})
  await vts_inst.connect()
  await vts_inst.request_authenticate_token()
  await vts_inst.request_authenticate()
  sleep(3)
  print('start')
  past_value = {}
  while True:
    try:
      if not past_value:
        tmp = []
        for i in parameters:
          data = await vts_inst.request(vts_inst.vts_request.requestParameterValue(i))
          tmp.append(convert_value(i, data['data']['value']))
        past_value = tmp
      raw_data = model.predict(array(past_value).reshape(1, -1))[0]
      #raw_data += uniform(-1, 1, raw_data.shape)
      data = [
        normalize_value(k, float(i)) for k, i in zip(parameters, raw_data)
      ]
      print(data)
      await vts_inst.request(vts_inst.vts_request.requestSetMultiParameterValue(parameters, data))
      past_value = data
    except KeyboardInterrupt:
      break

if __name__ == '__main__':
  run(main())
