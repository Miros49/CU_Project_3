import sys
import asyncio
import locale

from app import flask_app, run_flask
from app.routes import weather_blueprint, errors_blueprint
from bot import run_bot

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

flask_app.register_blueprint(weather_blueprint)
flask_app.register_blueprint(errors_blueprint)


async def main():
    await asyncio.gather(run_flask(), run_bot())


if __name__ == '__main__':
    asyncio.run(main())
