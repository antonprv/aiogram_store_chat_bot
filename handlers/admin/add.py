from hashlib import md5
from typing import Tuple, List


from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram.types.chat import ChatActions
from aiogram.utils.callback_data import CallbackData

from loader import dp, db, bot
from filters import IsAdmin
from handlers.user.menu import settings
from states import CategoryState


# Определяю тип данных, которые получу при нажатии на кнопку.
# Первое значение - уникальный идентификатор кнопки, должно быть всегда.
# Следом уже нужные мне данные.
category_cb = CallbackData('category', 'id', 'action')

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


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict,
                                    state: FSMContext):
    
    category_idx = callback_data['id']
    
    # Временная переменная product добавлена для... Читаемости??
    products = db.fetchall('''SELECT * FROM products product
WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))
    
    await query.message.delete()
    await query.answer('Все добавленные товары в эту категорию')
    # Не очень понимаю, зачем в примере нужны эти 2 строки
    # await state.update_data(category_index=category_idx)
    # await show_products(query.message, products, category_idx)
    await show_products(query.message, products)


# Функционал при проваливании в кнопку с категорией.

# Все нужные для этого переменные:
# Колбэк при нажатии на кнопку.
product_cb = CallbackData('product', 'id', 'action')

cancel_message = '🚫 Отменить'
add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'


# Пока удалил category_idx
# async def show_products(message: Message, products: List[Tuple], category_idx):
async def show_products(message: Message, products: List[Tuple]):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    
    for idx, title, body, image, price, in products:
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(\
            '🗑️ Удалить',
            callback_data=product_cb.new(id=idx, action='delete')))
        await message.answer_photo(photo=image,
                             caption=text,
                             reply_makrup=markup)
        
    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)
    
    await message.answer('Хотите что-нибудь добавить или удалить?',
                   reply_markup=markup)
