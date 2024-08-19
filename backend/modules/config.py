from tomli import loads

from pathlib import Path

config: dict = loads(Path("./config.toml").read_text())
api_key = config["ai"]["openai"]
google_tts = config["ai"]["google_tts"]
