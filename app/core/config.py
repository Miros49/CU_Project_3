import os
from dotenv import load_dotenv

from flask import Flask
from dash_app import create_dash_app

# Загрузка переменных окружения из файла .env
load_dotenv()


class Config:
    ACCUWEATHER_API_KEY = os.getenv('ACCUWEATHER_API_KEY')
    POSITIONSTACK_API_KEY = os.getenv('POSITIONSTACK_API_KEY')
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    TESTING = os.getenv("TESTING", False)


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    create_dash_app(app)

    return app


flask_app = create_app()
