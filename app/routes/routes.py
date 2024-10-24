from flask import Blueprint, request, jsonify, render_template, redirect, flash
from app.forms import CityRouteForm
from services.geocoding_service import get_coordinates_by_city
from services.weather_service import get_current_weather, get_location_key, get_weather_by_location
from utils.weather_utils import translate_weather, check_bad_weather

weather_blueprint = Blueprint('weather', __name__)


@weather_blueprint.route('/', methods=['GET', 'POST'])
def check_route_weather():
    form = CityRouteForm(request.form)  # Передаём request.form для работы с данными формы

    if request.method == 'POST' and form.validate():  # Проверяем метод запроса и валидируем данные формы
        start_city = form.start_city.data
        end_city = form.end_city.data

        # Получаем координаты для начальной и конечной точек
        start_coordinates = get_coordinates_by_city(start_city)
        end_coordinates = get_coordinates_by_city(end_city)

        if not start_coordinates or not end_coordinates:
            flash("Не удалось найти координаты для указанных городов.", "error")
            return redirect('/')

        # Получаем прогноз погоды для начальной и конечной точек
        start_forecast_data = get_weather_by_location(start_coordinates['lat'], start_coordinates['lon'])
        end_forecast_data = get_weather_by_location(end_coordinates['lat'], end_coordinates['lon'])

        if not start_forecast_data or not end_forecast_data:
            flash("Не удалось получить данные о погоде для указанных городов.", "error")
            return redirect('/')

        # Оцениваем погодные условия для начальной точки
        start_forecast = start_forecast_data['DailyForecasts'][0]
        start_temp = (start_forecast['Temperature']['Maximum']['Value'] - 32) * 5.0 / 9.0  # Цельсий
        start_wind = start_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0)
        start_precip = start_forecast['Day'].get('PrecipitationProbability', 0)
        start_condition = check_bad_weather(start_temp, start_wind, start_precip)

        # Оцениваем погодные условия для конечной точки
        end_forecast = end_forecast_data['DailyForecasts'][0]
        end_temp = (end_forecast['Temperature']['Maximum']['Value'] - 32) * 5.0 / 9.0  # Цельсий
        end_wind = end_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0)
        end_precip = end_forecast['Day'].get('PrecipitationProbability', 0)
        end_condition = check_bad_weather(end_temp, end_wind, end_precip)

        # Рендерим шаблон с результатами прогноза
        return render_template(
            'route_weather_results.html',  # Исправлено: добавлен шаблон для результатов
            start_city=start_city,
            end_city=end_city,
            start_condition=start_condition,
            end_condition=end_condition
        )

    return render_template('index.html', form=form)


@weather_blueprint.route('/check_route_weather', methods=['POST'])
def check_route_weather_ajax():
    """
    Эндпоинт для проверки погодных условий маршрута через AJAX.
    Возвращает JSON с погодными условиями для начальной и конечной точек.
    """
    start_city = request.json.get('start_city')
    end_city = request.json.get('end_city')

    # Проверка наличия городов
    if not start_city or not end_city:
        return jsonify({"error": "Оба города должны быть указаны."}), 400

    # Получаем координаты
    start_coordinates = get_coordinates_by_city(start_city)
    end_coordinates = get_coordinates_by_city(end_city)

    if not start_coordinates or not end_coordinates:
        return jsonify({"error": "Не удалось найти координаты для указанных городов."}), 500

    # Получаем прогноз погоды
    start_forecast_data = get_weather_by_location(start_coordinates['lat'], start_coordinates['lon'])
    end_forecast_data = get_weather_by_location(end_coordinates['lat'], end_coordinates['lon'])

    if not start_forecast_data or not end_forecast_data:
        return jsonify({"error": "Не удалось получить данные о погоде."}), 500

    # Оцениваем погодные условия
    start_forecast = start_forecast_data['DailyForecasts'][0]
    start_temp = (start_forecast['Temperature']['Maximum']['Value'] - 32) * 5.0 / 9.0
    start_wind = start_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0)
    start_precip = start_forecast['Day'].get('PrecipitationProbability', 0)
    start_condition = check_bad_weather(start_temp, start_wind, start_precip)

    end_forecast = end_forecast_data['DailyForecasts'][0]
    end_temp = (end_forecast['Temperature']['Maximum']['Value'] - 32) * 5.0 / 9.0
    end_wind = end_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0)
    end_precip = end_forecast['Day'].get('PrecipitationProbability', 0)
    end_condition = check_bad_weather(end_temp, end_wind, end_precip)

    return jsonify({
        "start_city": start_city,
        "start_weather_condition": start_condition,
        "end_city": end_city,
        "end_weather_condition": end_condition
    })


@weather_blueprint.route('/get_weather', methods=['GET'])
def get_weather():
    """
    Эндпоинт для получения прогноза погоды по названию города и текущей температуры.
    Возвращает HTML-страницу с подробным прогнозом и текущей температурой.
    """
    city_name = request.args.get('city', 'Moscow')

    # Получение координат города
    coordinates = get_coordinates_by_city(city_name)
    if not coordinates:
        return jsonify({"error": "Не удалось найти кооchрдинаты для указанного города."}), 500

    lat = coordinates['lat']
    lon = coordinates['lon']

    # Получение ключа местоположения (location_key)
    location_key = get_location_key(lat, lon)
    if not location_key:
        return jsonify({"error": "Не удалось получить location_key для указанного города."}), 500

    # Получение данных о прогнозе погоды с использованием location_key
    forecast_data = get_weather_by_location(lat, lon)
    if not forecast_data:
        return jsonify({"error": "Не удалось получить данные о прогнозе погоды."}), 500

    # Получение текущих данных о погоде
    current_weather_data = get_current_weather(location_key)
    if not current_weather_data:
        return jsonify({"error": "Не удалось получить текущие данные о погоде."}), 500

    # Извлекаем текущую температуру
    current_weather = current_weather_data[0]
    current_temperature = current_weather['Temperature']['Metric']['Value']

    # Извлекаем метеорологические параметры для анализа прогноза
    daily_forecast = forecast_data['DailyForecasts'][0]
    temperature_max = round((daily_forecast['Temperature']['Maximum']['Value'] - 32) * 5.0 / 9.0, 2)
    temperature_min = round((daily_forecast['Temperature']['Minimum']['Value'] - 32) * 5.0 / 9.0, 2)
    wind_speed = daily_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0)
    precipitation_probability = daily_forecast['Day'].get('PrecipitationProbability', 0)
    precipitation_intensity = translate_weather(daily_forecast['Day'].get('PrecipitationIntensity', 'None'))
    precipitation_type = translate_weather(daily_forecast['Day'].get('PrecipitationType', 'None'))

    # Применяем перевод погодного описания
    weather_icon_phrase = daily_forecast['Day'].get('IconPhrase', 'Unknown')
    translated_weather = translate_weather(weather_icon_phrase)

    # Проверка погодных условий на неблагоприятность
    weather_condition = check_bad_weather(temperature_max, wind_speed, precipitation_probability, precipitation_intensity)

    # Передаем данные в шаблон
    return render_template(
        'get_weather.html',
        city=city_name,
        forecast=forecast_data,
        weather_condition=weather_condition,
        current_temperature=current_temperature,
        temperature_max=temperature_max,
        temperature_min=temperature_min,
        wind_speed=wind_speed,
        precipitation_probability=precipitation_probability,
        precipitation_intensity=precipitation_intensity,
        precipitation_type=precipitation_type,
        translated_weather=translated_weather
    )
