from aiogram.dispatcher.filters.state import StatesGroup, State

class OrderState(StatesGroup):
    info = State()
