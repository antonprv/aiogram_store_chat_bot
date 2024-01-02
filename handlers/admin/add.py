from loader import dp, db
from filters import IsAdmin
from handlers.user.menu import settings
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

# Определяю тип данных, которые получу при нажатии на кнопку.
category_cb = CallbackData('category', 'id', 'action')

@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):
    
    # Создаю объект клавиатуры.
    markup = InlineKeyboardMarkup()
    
    # Делаю запрос к базе данных, получаю список категорий,
    # из каждой категории извлекаю идентификатор и название
    # и раскидываю категории по кнопкам.
    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))
    
    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))
    
    await message.answer('Настройка категорий:', reply_markup=markup)
