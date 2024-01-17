from aiogram.dispatcher.filters.state import StatesGroup, State


class OrderState(StatesGroup):
    details = State()
    set_date = State()
    arrived = State()
