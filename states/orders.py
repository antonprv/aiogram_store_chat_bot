from aiogram.dispatcher.filters.state import StatesGroup, State


class OrderState(StatesGroup):
    list = State()
    details = State()

class OrderDeliveryState(State):
    delivery_state = State()
