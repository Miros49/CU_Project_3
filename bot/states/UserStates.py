from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    input_start_point: State = State()
    input_end_point: State = State()
    input_intermediate_points: State = State()
    select_forecast_interval: State = State()
    manual_input_start_point: State = State()
