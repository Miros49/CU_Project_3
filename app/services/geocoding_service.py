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


def get_coordinates_by_city(city_name):
    """
    Получение координат города с кэшированием.
    """
    cache_key = f"coordinates:{city_name.lower()}"
    coordinates = redis_client.get(cache_key)

    if coordinates:
        print("City coordinates retrieved from cache")
        return json.loads(coordinates)

    api_key = Config.POSITIONSTACK_API_KEY
    url = "http://api.positionstack.com/v1/forward"
    params = {
        'access_key': api_key,
        'query': city_name,
        'limit': 1
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Ошибка запроса. Статус: {response.status_code}, Текст ошибки: {response.text}")
        return None

    data = response.json().get('data')
    if not data:
        print("Не удалось найти данные для указанного города.")
        return None

    coordinates = {
        'lat': data[0]['latitude'],
        'lon': data[0]['longitude']
    }
    redis_client.setex(cache_key, 86400, json.dumps(coordinates))  # Кэширование на 24 часа
    return coordinates
