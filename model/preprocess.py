from os import listdir
from json import dump, load

for i in listdir('./data'):
  print(i)
  data = load(open(f'./data/{i}', 'r'))
  if isinstance(data, dict) and data.get('preprocessed', False) is True:
    continue
  print(len(data))
  data = [list(data.values()) for data in data[10:-10]]
  dump({'preprocessed': True, 'data': data}, open(f'./data/{i}', 'w'))
