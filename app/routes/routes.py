import datetime

from flask import Blueprint, request, jsonify, render_template, redirect, flash, current_app
from requests import HTTPError

from app.forms import CityRouteForm
from app.services import get_coordinates_by_city
from app.services import get_current_weather, get_location_key, get_weather_by_location
from ..utils import check_bad_weather, translate_weather, extract_time

weather_blueprint = Blueprint('weather', __name__)


@weather_blueprint.route('/', methods=['GET', 'POST'])
def check_route_weather():
    if request.method == 'POST':
        # Извлекаем начальный, конечный город и промежуточные точки
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')
        waypoints = request.form.getlist('waypoints[]')  # Промежуточные точки

        # Проверяем начальный и конечный город
        if not start_city or not end_city:
            flash("Необходимо указать начальную и конечную точки маршрута.", "error")
            return redirect('/')

        # Получаем координаты начального и конечного пунктов
        start_coordinates = get_coordinates_by_city(start_city)
        end_coordinates = get_coordinates_by_city(end_city)

        # Получаем координаты для каждой промежуточной точки
        waypoint_forecasts = []
        for waypoint in waypoints:
            coordinates = get_coordinates_by_city(waypoint)
            if not coordinates:
                flash(f"Не удалось найти координаты для города: {waypoint}", "error")
                return redirect('/')

            forecast_data = get_weather_by_location(coordinates['lat'], coordinates['lon'])
            if not forecast_data:
                flash(f"Не удалось получить данные о погоде для города: {waypoint}", "error")
                return redirect('/')

            # Оценка погодных условий
            condition = check_bad_weather(
                forecast_data['DailyForecasts'][0]['Temperature']['Maximum']['Value'],
                forecast_data['DailyForecasts'][0]['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0),
                forecast_data['DailyForecasts'][0]['Day'].get('PrecipitationProbability', 0)
            )

            waypoint_forecasts.append({
                'city': waypoint,
                'coord': coordinates,
                'forecast': forecast_data['DailyForecasts'][0],
                'condition': "неблагоприятные" if condition == 'bad' else "благоприятные"
            })

        # Получаем прогнозы для начального и конечного пунктов
        start_forecast = get_weather_by_location(start_coordinates['lat'], start_coordinates['lon'])
        end_forecast = get_weather_by_location(end_coordinates['lat'], end_coordinates['lon'])

        if not start_forecast or not end_forecast:
            flash("Не удалось получить данные о погоде для начальной или конечной точки.", "error")
            return redirect('/')

        start_condition = check_bad_weather(
            start_forecast['DailyForecasts'][0]['Temperature']['Maximum']['Value'],
            start_forecast['DailyForecasts'][0]['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0),
            start_forecast['DailyForecasts'][0]['Day'].get('PrecipitationProbability', 0)
        )
        start_condition = "неблагоприятные" if start_condition == 'bad' else "благоприятные"

        end_condition = check_bad_weather(
            end_forecast['DailyForecasts'][0]['Temperature']['Maximum']['Value'],
            end_forecast['DailyForecasts'][0]['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0),
            end_forecast['DailyForecasts'][0]['Day'].get('PrecipitationProbability', 0)
        )
        end_condition = "неблагоприятные" if end_condition == 'bad' else "благоприятные"

        # шаблон с результатами прогноза для каждого пункта маршрута
        return render_template(
            'route_weather_results.html',
            start_city=start_city,
            end_city=end_city,
            start_coordinates=start_coordinates,
            end_coordinates=end_coordinates,
            waypoints=waypoint_forecasts,
            start_forecast=start_forecast['DailyForecasts'][0],
            end_forecast=end_forecast['DailyForecasts'][0],
            start_condition=start_condition,
            end_condition=end_condition
        )

    return render_template('index.html')


@weather_blueprint.route('/get_weather', methods=['GET'])
def get_weather():
    city_name = request.args.get('city', 'Moscow')
    days = int(request.args.get('days', 5))
    day_index = int(request.args.get('day_index', 0))

    try:
        coordinates = get_coordinates_by_city(city_name)
        if not coordinates:
            return jsonify({"error": "Не удалось найти координаты для указанного города."}), 500

        lat, lon = coordinates['lat'], coordinates['lon']
        location_key = get_location_key(lat, lon)
        if not location_key:
            return jsonify({"error": "Не удалось получить location_key для указанного города."}), 500

        forecast_data = get_weather_by_location(lat, lon, days=days)
        if not forecast_data or 'DailyForecasts' not in forecast_data:
            return jsonify({"error": "Не удалось получить данные о прогнозе погоды."}), 500

        current_weather_data = get_current_weather(location_key)
        if not current_weather_data:
            return jsonify({"error": "Не удалось получить текущие данные о погоде."}), 500

        current_temperature = current_weather_data[0]['Temperature']['Metric']['Value'] if isinstance(
            current_weather_data, list) else current_weather_data['Temperature']['Metric']['Value']

        # Инициализируем списки для данных
        dates, max_temps, min_temps, day_real_feels, night_real_feels = [], [], [], [], []
        day_humidities, night_humidities, day_clouds, night_clouds = [], [], [], []
        wind_speeds, precip_probs, precip_types = [], [], []
        day_min_humidities, day_avg_humidities, day_max_humidities = [], [], []
        night_min_humidities, night_avg_humidities, night_max_humidities = [], [], []
        sunrise_times, sunset_times = [], []

        for day_forecast in forecast_data['DailyForecasts'][:days]:
            # Форматируем дату и добавляем в список один раз
            date = day_forecast.get('Date', '')
            formatted_date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').strftime('%d.%m.%Y')
            dates.append(formatted_date)

            # Температуры
            max_temps.append(day_forecast['Temperature']['Maximum']['Value'])
            min_temps.append(day_forecast['Temperature']['Minimum']['Value'])

            # RealFeel температуры
            day_real_feels.append(day_forecast['RealFeelTemperature']['Maximum']['Value'])
            night_real_feels.append(day_forecast['RealFeelTemperature']['Minimum']['Value'])

            # Влажность
            day_min_humidities.append(day_forecast['Day']['RelativeHumidity'].get('Minimum', 0))
            day_avg_humidities.append(day_forecast['Day']['RelativeHumidity'].get('Average', 0))
            day_max_humidities.append(day_forecast['Day']['RelativeHumidity'].get('Maximum', 0))
            night_min_humidities.append(day_forecast['Night']['RelativeHumidity'].get('Minimum', 0))
            night_avg_humidities.append(day_forecast['Night']['RelativeHumidity'].get('Average', 0))
            night_max_humidities.append(day_forecast['Night']['RelativeHumidity'].get('Maximum', 0))

            # Другие параметры
            day_clouds.append(day_forecast.get('Day', {}).get('CloudCover', 0))
            night_clouds.append(day_forecast.get('Night', {}).get('CloudCover', 0))
            wind_speeds.append(day_forecast['Day'].get('Wind', {}).get('Speed', {}).get('Value', 0))
            precip_probs.append(day_forecast['Day'].get('PrecipitationProbability', 0))
            precip_types.append(day_forecast['Day'].get('PrecipitationType', 'None'))
            sunrise_times.append(extract_time(day_forecast['Sun'].get('Rise', 'Неизвестно')))
            sunset_times.append(extract_time(day_forecast['Sun'].get('Set', 'Неизвестно')))

        # Кэшируем данные для Dash
        current_app.config['DASH_DATA'] = {
            "dates": dates,
            "max_temps": max_temps,
            "min_temps": min_temps,
            "day_real_feels": day_real_feels,
            "night_real_feels": night_real_feels,
            "wind_speeds": wind_speeds,
            "precip_probs": precip_probs,
            "precip_types": precip_types,
            "day_humidities": day_humidities,
            "night_humidities": night_humidities,
            "day_clouds": day_clouds,
            "night_clouds": night_clouds,
            "day_min_humidities": day_min_humidities,
            "day_avg_humidities": day_avg_humidities,
            "day_max_humidities": day_max_humidities,
            "night_min_humidities": night_min_humidities,
            "night_avg_humidities": night_avg_humidities,
            "night_max_humidities": night_max_humidities,
            "sunrise_times": sunrise_times,
            "sunset_times": sunset_times,
        }

        return render_template(
            'get_weather.html',
            city=city_name,
            current_temperature=current_temperature,
            temperature_max=max_temps[day_index],
            temperature_min=min_temps[day_index],
            real_feel=day_real_feels[day_index],
            wind_speed=wind_speeds[day_index],
            day_humidity={
                'Minimum': day_min_humidities[day_index],
                'Average': day_avg_humidities[day_index],
                'Maximum': day_max_humidities[day_index]
            },
            night_humidity={
                'Minimum': night_min_humidities[day_index],
                'Average': night_avg_humidities[day_index],
                'Maximum': night_max_humidities[day_index]
            },
            cloud_cover=day_clouds[day_index],
            precipitation_probability=precip_probs[day_index],
            precipitation_type=translate_weather(precip_types[day_index]),
            icon_phrase=forecast_data['DailyForecasts'][day_index]['Day'].get('IconPhrase', 'Unknown'),
            sunrise=sunrise_times[day_index],
            sunset=sunset_times[day_index],
            day_index=day_index,
            date=dates[day_index],
            days=days,
        )

    except HTTPError as e:
        return render_template(f'errors/{e.response.status_code}.html'), e.response.status_code


@weather_blueprint.route('/check_route_weather', methods=['POST'])
def check_route_weather_ajax():
    """
    Эндпоинт для проверки погодных условий маршрута через AJAX.
    Возвращает JSON с погодными условиями для начальной и конечной точек.
    """
    print(1)
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
