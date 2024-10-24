import requests
from core.config import Config


def get_weather_by_location(lat, lon):
    """
    Получение прогноза погоды по координатам.
    Возвращает None при ошибке запроса или проблемах с API.
    """
    try:
        location_url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        params = {
            'apikey': Config.ACCUWEATHER_API_KEY,
            'q': f'{lat},{lon}'
        }

        response = requests.get(location_url, params=params)
        response.raise_for_status()

        data = response.json()
        location_key = data.get('Key')

        if not location_key:
            raise ValueError("Не удалось получить location key")

        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}"
        params = {'apikey': Config.ACCUWEATHER_API_KEY}

        forecast_response = requests.get(forecast_url, params=params)
        forecast_response.raise_for_status()

        return forecast_response.json()

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None
    except ValueError as ve:
        print(f"Ошибка данных: {ve}")
        return None


def get_current_weather(location_key):
    """
    Получение текущей погоды по location_key через AccuWeather API.
    """
    url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    params = {
        'apikey': Config.ACCUWEATHER_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        error_message = f"Ошибка при попытке получения текущей погоды {response.status_code}: {response.text}"
        print(error_message.encode('utf-8', errors='ignore'))  # Преобразуем строку в utf-8
        return None

    return response.json()


def analyze_weather(forecast_data):
    """
    Анализ погодных данных для предсказания погодных условий на день и ночь.
    """
    if not forecast_data:
        return "Нет данных о погоде"

    daily_forecast = forecast_data.get('DailyForecasts', [])[0]

    # Извлечение температур с преобразованием в Цельсии
    max_temp_f = daily_forecast.get('Temperature', {}).get('Maximum', {}).get('Value')
    min_temp_f = daily_forecast.get('Temperature', {}).get('Minimum', {}).get('Value')

    if max_temp_f is not None and min_temp_f is not None:
        max_temp_c = fahrenheit_to_celsius(max_temp_f)
        min_temp_c = fahrenheit_to_celsius(min_temp_f)
    else:
        return "Не удалось получить данные о температуре."

    # Извлечение условий дня и ночи
    day_conditions = daily_forecast.get('Day', {}).get('IconPhrase', 'Нет данных')
    night_conditions = daily_forecast.get('Night', {}).get('IconPhrase', 'Нет данных')

    # Проверка на осадки ночью
    night_has_precipitation = daily_forecast.get('Night', {}).get('HasPrecipitation', False)
    precipitation_type = daily_forecast.get('Night', {}).get('PrecipitationType', 'None')
    precipitation_intensity = daily_forecast.get('Night', {}).get('PrecipitationIntensity', 'None')

    # Формирование итогового текста анализа
    analysis = (
        f"Прогноз на день:\n"
        f"- Максимальная температура: {max_temp_c:.1f}°C\n"
        f"- Минимальная температура: {min_temp_c:.1f}°C\n"
        f"- Дневные условия: {day_conditions}\n"
        f"- Ночные условия: {night_conditions}\n"
    )

    if night_has_precipitation:
        analysis += (
            f"- Осадки ночью: {precipitation_type}, интенсивность: {precipitation_intensity}\n"
        )
    else:
        analysis += "- Осадки ночью не ожидаются.\n"

    return analysis


def fahrenheit_to_celsius(fahrenheit):
    """
    Преобразование температуры из Фаренгейтов в Цельсии.
    """
    return (fahrenheit - 32) / 1.8


def get_location_key(lat, lon):
    """
    Получение location_key по координатам (широта и долгота) через AccuWeather API.
    """
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
    return data.get('Key')
