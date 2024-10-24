import requests
from core.config import Config


def get_coordinates_by_city(city_name: str = 'Moscow'):
    """
    Получение широты и долготы города с использованием PositionStack API.
    """
    api_key = Config.POSITIONSTACK_API_KEY
    url = "http://api.positionstack.com/v1/forward"
    params = {
        'access_key': api_key,
        'query': city_name,
        'limit': 1
    }

    response = requests.get(url, params=params)

    # Проверка статуса ответа и вывод ошибки
    if response.status_code != 200:
        print(f"Ошибка запроса. Статус: {response.status_code}, Текст ошибки: {response.text}")
        return None

    # Проверка, что в ответе есть данные
    data = response.json().get('data')
    if not data:
        print("Не удалось найти данные для указанного города.")
        return None

    return {
        'lat': data[0]['latitude'],
        'lon': data[0]['longitude']
    }
