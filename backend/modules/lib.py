from loguru import logger
from inspect import iscoroutinefunction
from functools import wraps

def print_it(func):
  @wraps(func)
  async def wrapper(*args, **kwargs):
    logger.debug(f'{func.__name__}, {args}, {kwargs}')
    res = await func(*args, **kwargs)
    logger.debug(f"return {res}")
    logger.debug(f"type is {type(res)}")
    return res

  @wraps(func)
  def non_async_wrapper(*args, **kwargs):
    logger.debug(f'{func.__name__}, {args}, {kwargs}')
    res = func(*args, **kwargs)
    logger.debug(f"return {res}")
    logger.debug(f"type is {type(res)}")
    return res
  return wrapper if iscoroutinefunction(func) else non_async_wrapper