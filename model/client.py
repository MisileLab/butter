from pyvts import vts
from tensorflow.keras.models import load_model
from numpy import array, expand_dims

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
      past_value = [tmp for _ in range(10)]
    raw_data = model.predict(expand_dims(array(past_value[-3:-1]), axis=0))[0]
    data = [
      normalize_value(k, max(-90, min(90, float(i)))) for k, i in zip(parameters, raw_data)
    ]
    print(data)
    await vts_inst.request(vts_inst.vts_request.requestSetMultiParameterValue(parameters, data))
    del past_value[0]
    past_value.append([convert_value(parameters[i], data[i]) for i in range(len(parameters))])

if __name__ == '__main__':
  run(main())
