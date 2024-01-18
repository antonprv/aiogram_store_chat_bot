from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

order_details_message = '📝 Детали заказа'
order_status_message = '🚚 Изменить статус'

order_idle = '🏚 На складе'
order_going = '🛤 В пути'
order_arrived = '💫 Прибыл'

order_cb = CallbackData('order', 'id', 'action')
order_state_cb = CallbackData('order', 'id', 'action')

def order_info_markup(idx):
    markup = InlineKeyboardMarkup()
    order_details_button = InlineKeyboardButton(order_details_message,
                                                callback_data=order_cb.
                                                new(id=idx, action='details'))
    change_status_button = InlineKeyboardButton(order_details_message,
                                                callback_data=order_cb.
                                                new(id=idx, action='status'))
    markup.row(order_details_button, change_status_button)
    return markup


def order_state_markup(idx):
    global order_state_cb

    markup = InlineKeyboardMarkup()
    idle_button = InlineKeyboardButton(order_idle,
                                       callback_data=order_state_cb.
                                       new(id=idx,
                                           action='idle'))

    going_button = InlineKeyboardButton(order_going,
                                        callback_data=order_state_cb.
                                        new(id=idx,
                                            action='going'))

    arrived_button = InlineKeyboardButton(order_arrived,
                                          callback_data=order_state_cb.
                                          new(id=idx,
                                              action='arrived'))

    markup.row(idle_button, going_button, arrived_button)

    return markup
