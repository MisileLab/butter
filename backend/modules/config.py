from tomli import loads
from fastapi import WebSocket
from minio import Minio

from pathlib import Path

config: dict = loads(Path("./config.toml").read_text())
api_key = config["ai"]["openai"]
google_tts = config["ai"]["google_tts"]
serpapi_key = config["search"]["serpapi"]
minio = Minio(config["minio"]["url"], access_key=config["minio"]["access"], secret_key=config["minio"]["secret"])
wss: list[WebSocket] = []
