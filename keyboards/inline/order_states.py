from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

order_details_message = '📝 Детали заказа'
order_status_message = '🚚 Изменить статус'

order_idle = '🏚 На складе'
order_going = '🛤 В пути'
order_arrived = '💫 Прибыл'

order_cb = CallbackData('order', 'id', 'cid', 'action')


def order_info_markup(ord_id, cid):
    markup = InlineKeyboardMarkup()
    order_details_button = InlineKeyboardButton(order_details_message,
                                                callback_data=order_cb.
                                                new(id=ord_id, cid=cid,
                                                    action='details'))
    change_status_button = InlineKeyboardButton(order_status_message,
                                                callback_data=order_cb.
                                                new(id=ord_id, cid=cid,
                                                    action='status'))

    markup.row(order_details_button, change_status_button)
    return markup


def order_state_markup(ord_id, cid):
    global order_cb

    markup = InlineKeyboardMarkup()
    idle_button = InlineKeyboardButton(order_idle,
                                       callback_data=order_cb.
                                       new(id=ord_id, cid=cid,
                                           action='idle'))

    going_button = InlineKeyboardButton(order_going,
                                        callback_data=order_cb.
                                        new(id=ord_id, cid=cid,
                                            action='going'))

    arrived_button = InlineKeyboardButton(order_arrived,
                                          callback_data=order_cb.
                                          new(id=ord_id, cid=cid,
                                              action='arrived'))

    markup.row(idle_button, going_button, arrived_button)
    return markup
