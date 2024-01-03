from loader import dp, db
from filters import IsAdmin
from handlers.user.menu import settings
from states import CategoryState

from hashlib import md5

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.utils.callback_data import CallbackData

# Определяю тип данных, которые получу при нажатии на кнопку.
category_cb = CallbackData('category_title', 'id', 'action')

@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):
    
    # Создаю объект клавиатуры.
    markup = InlineKeyboardMarkup()
    
    # Делаю запрос к базе данных, получаю список категорий,
    # из каждой категории извлекаю идентификатор и название
    # и раскидываю категории по кнопкам.
    for idx, title in db.fetchall('SELECT * FROM categories'):
        # Через action 'view' свяжемся с другим обработчиком,
        # Который по ID категории перейдет к таблице и скажет,
        # что находится внутри категории.
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))
    
    # Тут так же привязываю указатель add_category, и ниже по коду
    # будет обработчик такого указателя.
    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))
    
    await message.answer('Настройка категорий:', reply_markup=markup)


# Создаю новую категорию, удаляю прошлое сообщение в чате с ботом,
# жду сообщение от пользователя, переключаю состояние на title.
@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Название категории?')
    await CategoryState.title.set()


# Обработчик перехватвывает состояние tittle, и сообщение пользователя.
# Сообщение от пользователя становится названием категории,
# а захешированная версия сообщения становится id категории.
@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):
    
    category_title = message.text
    idx = md5(category_title.encode('utf-8')).hexdigest()
    # Запускаю SQL-запрос с подстановкой названия категории и id.
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category_title))
    
    # Выхожу из состояния title.
    await state.finish()
    await process_settings(message)