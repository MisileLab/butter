from pyvts import vts as pvts
from loguru import logger

from asyncio import run, sleep
from secrets import SystemRandom

class LocalCache:
  def __init__(self, name: str, value: float, min: float, max: float, randmin: float, randmax: float):
    self.name = name
    self.value = value
    self.min = min
    self.max = max
    self.randmin = randmin
    self.randmax = randmax

  def get_rand_number(self):
    v = round(SystemRandom().uniform(self.randmin, self.randmax), 2)
    logger.debug(v)
    self.value += v

local_cache = [LocalCache("FaceAngleX", 0, -30, 30, -5, 5)]

async def main():
  vts = pvts()
  await vts.connect()
  await vts.request_authenticate_token()
  await vts.request_authenticate()
  try:
    while True:
      local_cache[0].get_rand_number()
      await vts.request(vts.vts_request.requestSetParameterValue("FaceAngleX", local_cache[0].value, face_found=True))
      await sleep(1)
  except KeyboardInterrupt:
    pass
  finally:
    await vts.close()

if __name__ == "__main__":
  run(main())