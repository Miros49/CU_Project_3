import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()


class Config:
    ACCUWEATHER_API_KEY = os.getenv('ACCUWEATHER_API_KEY')
    POSITIONSTACK_API_KEY = os.getenv('POSITIONSTACK_API_KEY')
