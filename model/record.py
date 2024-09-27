from pyvts import vts

from json import dump
from pathlib import Path
from os.path import join
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

datas = []

def normalize_value(data_type: str, value: float) -> float:
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
  index = 0
  while True:
    try:
      tmp = {}
      for i in parameters:
        data = await vts_inst.request(vts_inst.vts_request.requestParameterValue(i))
        tmp[i] = normalize_value(i, data['data']['value'])
      datas.append(tmp)
      sleep(0.01)
      if len(datas) >= 1000:
        print("dumping, 1000 length")
        dump(datas, open(join(data_dir, f'{name}_{index}.json'), 'w'))
        print(index)
        index += 1
        datas.clear()
    except KeyboardInterrupt:
      break

if __name__ == '__main__':
  data_dir = "./data"
  name = input('Enter the name of the data:')
  Path(data_dir).mkdir(exist_ok=True)
  try:
    run(main())
  except KeyboardInterrupt:
    print('dumping')
    dump(datas, open(join(data_dir, f'{name}.json'), 'w'))
