from flask import jsonify
from datetime import datetime

from app.services import get_weather_by_location
from app.services import get_coordinates_by_city


def get_weather_data(city_name):
    """
    Вспомогательная функция для получения координат и прогноза погоды по названию города.
    """
    coordinates = get_coordinates_by_city(city_name)

    if not coordinates:
        return None, jsonify({"error": "Не удалось найти координаты для указанного города."}), 500

    lat = coordinates['lat']
    lon = coordinates['lon']

    forecast_data = get_weather_by_location(lat, lon)

    if not forecast_data:
        return None, jsonify({"error": "Не удалось получить данные о погоде."}), 500

    return forecast_data, None, None


def check_bad_weather(temperature: float, wind_speed: float, precipitation_probability: float,
                      precipitation_intensity: str = None):
    """
    Оценивает погодные условия на основе температуры, скорости ветра и вероятности осадков.
    """
    if temperature < 0 or temperature > 35:
        return 'bad'

    if wind_speed > 50:
        return 'bad'

    if precipitation_probability > 70:
        return 'bad'

    if precipitation_intensity and precipitation_intensity.lower() in ['heavy', 'moderate']:
        return 'bad'

    return 'good'


def translate_weather(icon_phrase):
    """
    Переводит фразы погодных условий на русский язык.
    """
    translations = {
        "Mostly sunny": "Преимущественно солнечно",
        "Mostly cloudy w/ showers": "Преимущественно облачно с дождями",
        "Showers": "Ливни",
        "Rain": "Дождь",
        "Light rain": "Лёгкий дождь",
        "Clear": "Ясно",
        "Partly cloudy": "Переменная облачность",
        "Cloudy": "Облачно",
        "Thunderstorms": "Грозы",
        "Snow": "Снег",
        "Sleet": "Мокрый снег",
        "Light": "Лёгкие",
        "None": "Нет",
        "Partly sunny": "Облачно с прояснениями",
        "Partly sunny w/ showers": "Облачно с прояснениями с дождями"
    }

    return translations.get(icon_phrase, icon_phrase)


def extract_time(date_str: str) -> str:
    date_time_obj = datetime.fromisoformat(date_str)
    return date_time_obj.strftime("%H:%M")
