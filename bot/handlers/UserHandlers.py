import asyncio

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.services.weather_service import get_weather_by_location, get_location_key
from ..core import bot
from ..keyboards import UserKeyboards as User_kb
from ..states import UserStates

router: Router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer("<b>Привет! Я бот прогноза погоды. Используйте команду /weather для запроса прогноза.\n"
                         "Или команду /help для просмотра доступных команд</b>\n\n"
                         "<i>p.s. Прошу прощения за убогость бота, я его делал за 2ч до дедлайна</i>")


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать общение с ботом\n"
        "/help - Получить список команд\n"
        "/weather - Получить прогноз погоды для маршрута"
    )


@router.message(Command("weather"))
async def weather_command(message: Message, state: FSMContext):
    await message.answer(
        "<b>Укажите начальную точку маршрута:</b>\nВыберите вариант:",
        reply_markup=User_kb.location_input_kb()
    )
    await state.set_state(UserStates.input_start_point)


@router.callback_query(F.data == "select_location_map")
async def select_location_map(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Пожалуйста, отправьте свою геолокацию:",
        reply_markup=User_kb.location_request_kb()
    )


@router.callback_query(F.data == "enter_location_manual")
async def enter_location_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите координаты начальной точки в формате: широта, долгота")
    await state.set_state(UserStates.manual_input_start_point)


# Обработка конечной точки маршрута
@router.message(StateFilter(UserStates.input_end_point), F.location)
async def end_point_handler(message: Message, state: FSMContext):
    # Сохраняем координаты конечной точки
    end_point = (message.location.latitude, message.location.longitude)
    await state.update_data(end_point=end_point)

    await message.answer("Вы хотите добавить промежуточную точку или перейти к выбору прогноза?",
                         reply_markup=User_kb.intermediate_kb())
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
        "Промежуточная точка добавлена! Отправьте ещё одну геолокацию для следующей остановки "
        "или выберите 'Перейти к выбору интервала прогноза'."
    )


# Обработка выбора интервала прогноза погоды
@router.callback_query(F.data == "select_forecast")
async def interval_selected(callback: CallbackQuery, state: FSMContext):
    # Извлекаем данные маршрута
    data = await state.get_data()
    start_point = data['start_point']
    end_point = data['end_point']
    intermediate_points = data.get('intermediate_points', [])

    days = callback.data.split('_')[-1]

    # Получаем прогноз погоды для начальной точки
    start_forecast = get_weather_by_location(start_point[0], start_point[1], days)
    if not start_forecast:
        await callback.message.answer("Не удалось получить прогноз для начальной точки.")
        return

    # Получаем прогноз для конечной точки
    end_forecast = get_weather_by_location(end_point[0], end_point[1], days)
    if not end_forecast:
        await callback.message.answer("Не удалось получить прогноз для конечной точки.")
        return

    # Получаем прогнозы для всех промежуточных точек
    intermediate_forecasts = []
    for idx, point in enumerate(intermediate_points, start=1):
        forecast = get_weather_by_location(point[0], point[1], days)
        if forecast:
            intermediate_forecasts.append(forecast)
        else:
            await callback.message.answer(f"Не удалось получить прогноз для промежуточной точки {idx}.")
            return

    # Формируем текст с прогнозами
    forecast_message = (
        f"<b>Прогноз погоды на {days} дней:</b>\n\n"
        f"<b>Начальная точка:</b> {start_point}\n{start_forecast['DailyForecasts'][0]['Day']['IconPhrase']}\n"
        f"<b>Конечная точка:</b> {end_point}\n{end_forecast['DailyForecasts'][0]['Day']['IconPhrase']}\n"
    )

    if intermediate_forecasts:
        forecast_message += "\n<b>Промежуточные точки:</b>\n"
        for idx, forecast in enumerate(intermediate_forecasts, start=1):
            forecast_message += f"Точка {idx}: {forecast['DailyForecasts'][0]['Day']['IconPhrase']}\n"

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
async def add_intermediate(callback: CallbackQuery, state: FSMContext):
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
