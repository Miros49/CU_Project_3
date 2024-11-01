from hypercorn.asyncio import serve
from hypercorn.config import Config

from .core import flask_app


async def run_flask():
    config = Config()
    config.bind = ["127.0.0.1:5000"]
    await serve(flask_app, config)
