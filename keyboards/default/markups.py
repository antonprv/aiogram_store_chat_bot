from aiogram.types import ReplyKeyboardMarkup

back_message = '👈 Назад'
all_right_message = '✅ Все верно'
cancel_message = '🚫 Отменить'
checkout_message = '📦 Оформить заказ'
confirm_message = '✅ Подтвердить заказ'

order_details_message = '📝 Детали заказа'
order_status_message = '🚚 Изменить статус'
order_idle = '🏚 На складе'
order_going = '🛤 В пути'
order_arrived = ''


def back_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(back_message)

    return markup


def check_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(back_message, all_right_message)

    return markup


def confirm_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(confirm_message)
    markup.add(back_message)

    return markup


def submit_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(cancel_message, all_right_message)

    return markup
