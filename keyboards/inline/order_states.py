from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

order_idle = '🏚 На складе'
order_going = '🛤 В пути'
order_arrived = '💫 Прибыл'

order_state_cb = CallbackData('order_status', 'id', 'action' )

def order_state_markup():
    global order_state_cb

    markup = InlineKeyboardMarkup()
    idle_button = InlineKeyboardButton(order_idle,
                                       callback_data=order_state_cb.new(id=idx,
                                                        action='idle'))

    going_button = InlineKeyboardButton(order_going,
                                        callback_data=order_state_cb.new(id=idx,
                                                            action='going'))

    arrived_button = InlineKeyboardButton(order_arrived,
                                       callback_data=order_state_cb.new(id=idx,
                                                            action='arrived'))

    markup.row(idle_button, going_button, arrived_button)

    return markup