from scipy.special import comb

from json import load, dump
from pathlib import Path
from os import listdir
from os.path import join, isfile

def bezier_curve(points, t):
  """Compute the Bezier curve value at parameter t."""
  n = len(points) - 1
  return sum(comb(n, i) * (t**i) * ((1 - t)**(n - i)) * p for i, p in enumerate(points))

def split_bezier_curve(points, num_segments):
  """Split a Bezier curve into num_segments segments."""
  # Ensure num_segments is a float
  num_segments = float(num_segments)
  
  # Generate t values based on float intervals
  ts = [i / num_segments for i in range(int(num_segments) + 1)]
  
  return [bezier_curve(points, t) for t in ts]

motion_dir = "./motions"

if not Path(motion_dir).is_dir():
  raise FileNotFoundError(f"{motion_dir} is not a directory")

Path('./motion_datas').mkdir(exist_ok=True)

for i in listdir(motion_dir):
  print(i)
  if not isfile(join(motion_dir, i)):
    print(f"Skipping directory: {i}")
    continue
  with open(join(motion_dir, i), 'r') as file:
    motion_data = load(file)
    processed_motion_data = {
      j["Id"]:
      split_bezier_curve(
        j["Segments"], 60 *
        motion_data['Meta']['Duration'])[:int(motion_data['End'] * 60)]
      for j in motion_data["Curves"]
    }
    final_data = {}
    for k, v in processed_motion_data.items():
      if k in ['ParamAngleZ']:
        final_data[k] = v
        continue
      elif k in ['ParamAngleX', 'ParamAngleY']:
        final_data[k] = v*3
      elif k in ['ParamEyeLOpen', 'ParamEyeLSmile', 'ParamEyeROpen', 'ParamEyeRSmile']:
        final_data[k] = v*180-90
      else:
        final_data[k] = v*90
    dump(final_data, open(join('./motion_datas', i), 'w'))
