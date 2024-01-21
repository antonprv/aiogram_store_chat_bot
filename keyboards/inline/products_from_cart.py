from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

product_cb = CallbackData('product', 'id', 'action')


def product_markup(idx, count):
    global product_cb

    markup = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton('Меньше ⬅️',
                                       callback_data=product_cb.new(id=idx,
                                                                    action='decrease'))

    count_button = InlineKeyboardButton(count,
                                        callback_data=product_cb.new(id=idx,
                                                                     action='count'))

    next_button = InlineKeyboardButton('Больше ➡️',
                                       callback_data=product_cb.new(id=idx,
                                                                    action='increase'))

    markup.row(back_button, count_button, next_button)

    return markup
