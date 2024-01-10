from aiogram import types
from aiogram import executor
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove

from data.config import ADMINS
from loader import db, dp, bot
from logging import basicConfig, INFO
import handlers


# Проверка работы
def main():
    executor.start_polling(dp, on_startup=on_startup, skip_updates=False)


async def on_startup(dp):
    basicConfig(level=INFO)
    db.create_tables()


# Сама программа:
user_message = 'Пользователь'
admin_message = 'Админ'


# Обработчик комманды start, показывает самое первое сообщение бота.
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message) -> None:
    # Создаем объект-кнопки с подгонкой под размер окна телеги.
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    # Добавляем 2 кнопки в объект.
    markup.row(user_message, admin_message)

    # Выводим сообщение и 2 кнопки.
    await message.answer('''Привет! 👋

🤖 Я бот-магазин по подаже товаров любой категории.

🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся
товары, возпользуйтесь командой /menu.

❓ Возникли вопросы? Не проблема! Команда /help поможет 
связаться с админами, которые постараются как можно скорее откликнуться.
''', reply_markup=markup)


# Если выбрали кнопку админа, то вносим в список, выводим сообщение,
# кнопки выключаем.
@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message) -> None:
    cid = message.chat.id
    if cid not in ADMINS:
        ADMINS.append(cid)

    await message.answer('Включен админский режим.',
                         reply_markup=ReplyKeyboardRemove())


# Если юзер, то смотрим, есть ли в админах. Удаляем, если есть.
# кнопки выключаем.
@dp.message_handler(text=user_message) 
async def user_mode(message: types.Message):
    cid = message.chat.id
    if cid in ADMINS:
        ADMINS.remove(cid)

    await message.answer('Включен пользовательский режим.',
                         reply_markup=ReplyKeyboardRemove())


if __name__ == '__main__':
    main()
