import json

import redis
import requests

from app.core.config import Config

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=True
)


def get_weather_by_location(lat, lon, days=1):
    """
    Получение прогноза погоды по координатам с кэшированием данных.
    """
    if Config.TESTING:
        cache_key = f"forecast:{lat},{lon}:{days}"  # ключ для Redis
        forecast_data = redis_client.get(cache_key)

        if forecast_data:
            print("Weather forecast retrieved from cache")
            # ВРЕМЕННО
            print("Saved forecast Data JSON Response:", json.dumps(forecast_data, indent=2, ensure_ascii=False))
            return json.loads(forecast_data)

    # Получаем location_key для координат
    location_key = get_location_key(lat, lon)
    if not location_key:
        return None

    # Используем соответствующий API для получения прогноза
    if days == 1:
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}"
    else:
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"

    params = {
        'apikey': Config.ACCUWEATHER_API_KEY,
        'metric': 'true',
        'details': 'true',
        'language': 'ru'
    }

    response = requests.get(forecast_url, params=params)

    if response.status_code != 200:
        print(f"Ошибка при попытке получения прогноза погоды {response.status_code}: {response.text}")
        return None

    forecast_data = response.json()

    if Config.TESTING:
        redis_client.setex(cache_key, 86400, json.dumps(forecast_data))  # кэширование сутки

    return forecast_data


def get_current_weather(location_key):
    """
    Получение текущей погоды с использованием кэша.
    """
    if Config.TESTING:
        cache_key = f"current_weather:{location_key}"
        current_weather_data = redis_client.get(cache_key)

        if current_weather_data:
            print("Current weather retrieved from cache")
            return json.loads(current_weather_data)

    url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    params = {
        'apikey': Config.ACCUWEATHER_API_KEY,
        'metric': 'true',
        'details': 'true',
        'language': 'ru'
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Ошибка при попытке получения текущей погоды {response.status_code}: {response.text}")
        return None

    current_weather_data = response.json()

    if Config.TESTING:
        redis_client.setex(cache_key, 86400, json.dumps(current_weather_data))

    return current_weather_data


def get_location_key(lat, lon):
    """
    Получение и кэширование location_key по координатам (широта и долгота) через AccuWeather API.
    """
    if Config.TESTING:
        cache_key = f"location_key:{lat},{lon}"  # ключ для Redis
        location_key = redis_client.get(cache_key)

        if location_key:
            print("Location key retrieved from cache")
            return location_key

    # Если токена нет в кэше, делаем запрос к API
    url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
    params = {
        'apikey': Config.ACCUWEATHER_API_KEY,
        'q': f'{lat},{lon}'
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Ошибка при попытке получения location_key {response.status_code}: {response.text}")
        return None

    data = response.json()
    location_key = data.get('Key')

    if Config.TESTING and location_key:
        redis_client.setex(cache_key, 86400, location_key)

    return location_key


def clear_all_cache():  # это для тесте
    """
    Полная очистка базы данных Redis.
    """
    redis_client.flushdb()
    print("all Redis data is gone")
