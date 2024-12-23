import asyncio
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.services.weather_service import get_weather_by_location, get_location_key
from ..core import bot
from ..keyboards import UserKeyboards as User_kb
from ..lexicon import LEXICON
from ..states import UserStates

router: Router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(LEXICON['start_message'])


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(LEXICON['help_message'])


@router.message(Command("weather"))
async def weather_command(message: Message, state: FSMContext):
    await message.answer(
        text=LEXICON['weather_message'],
        reply_markup=User_kb.location_input_kb()
    )
    await state.set_state(UserStates.input_start_point)


@router.callback_query(F.data == "select_location_map")
async def select_location_map(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=LEXICON['select_location_message'],
        reply_markup=User_kb.location_request_kb()
    )


@router.callback_query(F.data == "enter_location_manual")
async def enter_location_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите координаты начальной точки в формате: широта, долгота")
    await state.set_state(UserStates.manual_input_start_point)


# Обработка конечной точки маршрута
@router.message(StateFilter(UserStates.input_end_point), F.location)
async def end_point_handler(message: Message, state: FSMContext):
    end_point = (message.location.latitude, message.location.longitude)  # Сохраняем координаты конечной точки

    await message.answer(
        text=LEXICON['end_point_message'],
        reply_markup=User_kb.intermediate_kb()
    )

    await state.update_data(end_point=end_point)
    await state.set_state(UserStates.input_intermediate_points)


# Обработка добавления промежуточных точек
@router.message(StateFilter(UserStates.input_intermediate_points), F.location)
async def intermediate_point_handler(message: Message, state: FSMContext):
    # Получаем и обновляем список промежуточных точек
    data = await state.get_data()
    intermediate_points = data.get("intermediate_points", [])
    intermediate_points.append((message.location.latitude, message.location.longitude))
    await state.update_data(intermediate_points=intermediate_points)

    await message.answer(
        LEXICON['intermediate_point_message']
    )


@router.callback_query(F.data == "select_forecast")
async def interval_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_point = data['start_point']
    end_point = data['end_point']
    intermediate_points = data.get('intermediate_points', [])

    days = int(callback.data.split('_')[-1])

    # Функция для форматирования детализированной информации о погоде
    def format_forecast(forecast_data):
        details = ""
        for i in range(days):
            day_forecast = forecast_data['DailyForecasts'][i]
            date = day_forecast.get('Date', '')
            formatted_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').strftime('%d.%m.%Y')

            details += f"<b>Дата:</b> {formatted_date}\n"
            details += f"<b>Макс. температура:</b> {day_forecast['Temperature']['Maximum']['Value']}°C\n"
            details += f"<b>Мин. температура:</b> {day_forecast['Temperature']['Minimum']['Value']}°C\n"
            details += f"<b>Днём ощущается как:</b> {day_forecast['RealFeelTemperature']['Maximum']['Value']}°C\n"
            details += f"<b>Ночью ощущается как:</b> {day_forecast['RealFeelTemperature']['Minimum']['Value']}°C\n"
            details += f"<b>Влажность днём:</b> {day_forecast['Day']['RelativeHumidity']}%\n"
            details += f"<b>Влажность ночью:</b> {day_forecast['Night']['RelativeHumidity']}%\n"
            details += f"<b>Облачность днём:</b> {day_forecast['Day']['CloudCover']}%\n"
            details += f"<b>Облачность ночью:</b> {day_forecast['Night']['CloudCover']}%\n"
            details += f"<b>Скорость ветра:</b> {day_forecast['Day']['Wind']['Speed']['Value']} км/ч\n"
            details += f"<b>Вероятность осадков:</b> {day_forecast['Day']['PrecipitationProbability']}%\n"
            details += f"<b>Тип осадков:</b> {day_forecast['Day'].get('PrecipitationType', 'Нет данных')}\n"
        return details

    # Получаем прогнозы для всех точек маршрута
    forecast_message = f"<b>Прогноз погоды на {days} дней:</b>\n\n"

    # Прогноз для начальной точки
    start_forecast = get_weather_by_location(start_point[0], start_point[1], days)
    if start_forecast:
        forecast_message += f"<b>Начальная точка:</b> {start_point}\n{format_forecast(start_forecast)}"
    else:
        await callback.message.answer("Не удалось получить прогноз для начальной точки.")
        return

    # Прогноз для конечной точки
    end_forecast = get_weather_by_location(end_point[0], end_point[1], days)
    if end_forecast:
        forecast_message += f"<b>Конечная точка:</b> {end_point}\n{format_forecast(end_forecast)}"
    else:
        await callback.message.answer("Не удалось получить прогноз для конечной точки.")
        return

    # Прогнозы для промежуточных точек
    if intermediate_points:
        forecast_message += "\n<b>Промежуточные точки:</b>\n"
        for idx, point in enumerate(intermediate_points, start=1):
            forecast = get_weather_by_location(point[0], point[1], days)
            if forecast:
                forecast_message += f"<b>Точка {idx}:</b> {point}\n{format_forecast(forecast)}"
            else:
                await callback.message.answer(f"Не удалось получить прогноз для промежуточной точки {idx}.")
                return

    forecast_message += LEXICON['additional_info']

    await callback.message.answer(forecast_message)
    await state.clear()


@router.message(StateFilter(UserStates.manual_input_start_point))
async def manual_start_point_handler(message: Message, state: FSMContext):
    try:
        lat, lon = map(float, message.text.split(","))
        await state.update_data(start_point=(lat, lon))
        await message.answer("<b>Теперь укажите конечную точку маршрута:</b>", reply_markup=User_kb.location_input_kb())
        await state.set_state(UserStates.input_end_point)
    except ValueError:
        await message.answer("Ошибка: координаты должны быть в формате широта, долгота. Попробуйте снова.")


@router.message(StateFilter(UserStates.input_start_point), F.location)
async def start_point_handler(message: Message, state: FSMContext):
    start_point = (message.location.latitude, message.location.longitude)
    await state.update_data(start_point=start_point)
    await message.answer("<b>Теперь укажите конечную точку маршрута:</b>", reply_markup=User_kb.location_input_kb())
    await state.set_state(UserStates.input_end_point)


@router.message(StateFilter(UserStates.input_end_point), F.location)
async def end_point_handler(message: Message, state: FSMContext):
    end_point = (message.location.latitude, message.location.longitude)
    await state.update_data(end_point=end_point)
    await message.answer(
        "Вы хотите добавить промежуточную точку или перейти к выбору прогноза?",
        reply_markup=User_kb.intermediate_kb()
    )
    await state.set_state(UserStates.input_intermediate_points)


@router.callback_query(F.data == "add_intermediate")
async def add_intermediate(callback: CallbackQuery):
    await callback.message.answer(
        "Пожалуйста, отправьте геолокацию для промежуточной точки.",
        reply_markup=User_kb.location_request_kb()
    )


@router.message(StateFilter(UserStates.input_intermediate_points), F.location)
async def intermediate_point_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    intermediate_points = data.get("intermediate_points", [])
    intermediate_points.append((message.location.latitude, message.location.longitude))
    await state.update_data(intermediate_points=intermediate_points)
    await message.answer(
        "Промежуточная точка добавлена! Отправьте ещё одну геолокацию для следующей остановки "
        "или выберите 'Перейти к выбору интервала прогноза'.",
        reply_markup=User_kb.intermediate_kb()
    )
