from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text='Посмотреть прогноз погоды', callback_data='weather_button')
    ).adjust(1, 2)

    return kb.as_markup()


def interval_selection_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text='Прогноз на сегодня', callback_data='forecast_interval_1'),
        InlineKeyboardButton(text='Прогноз на 3 дня', callback_data='forecast_interval_3'),
        InlineKeyboardButton(text='Прогноз на неделю', callback_data='forecast_interval_5')
    ).adjust(1, 2)

    return kb.as_markup()


def confirm_route_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text='Подтвердить маршрут', callback_data='confirm_route'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel_route')
    ).adjust(1)

    return kb.as_markup()


def error_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back_to_menu')
    )

    return kb.as_markup()


def location_input_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text='Выбрать на карте', callback_data='select_location_map'),
        InlineKeyboardButton(text='Ввести вручную', callback_data='enter_location_manual')
    ).adjust(1)

    return kb.as_markup()


def intermediate_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="Добавить промежуточную точку", callback_data="add_intermediate"),
        InlineKeyboardButton(text="Перейти к выбору интервала прогноза", callback_data="select_forecast")
    ).adjust(1)

    return kb.as_markup()


def location_request_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить геолокацию 📍", request_location=True)],
            [KeyboardButton(text="Добавить промежуточную точку")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb
