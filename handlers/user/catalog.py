from typing import List, Tuple

from aiogram.types import Message, CallbackQuery
from aiogram.types.chat import ChatActions

from filters import IsUser
from loader import db
from keyboards.inline.categories import category_cb, categories_markup
from keyboards.inline.products_from_catalog import product_markup
from keyboards.inline.products_from_catalog import product_cb
from loader import dp, bot
from .menu import catalog


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Выберите раздел, чтобы вывести список товаров: ',
                         reply_markup=categories_markup())


# Подхватываем коллбэк данные view
# и отображаем список товаров.
@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):
    products = db.fetchall('''SELECT * FROM products product
WHERE product.tag = (SELECT title FROM categories WHERE idx = ?)
AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                        (callback_data['id'], query.message.chat.id))

    await query.answer('Все доступные товары')
    await show_products(query.message, products)


# Функция для отображения товаров, которую подхватывает диспетчер.
async def show_products(message: Message, products: List[Tuple]):
    if len(products) == 0:
        await message.answer('Здесь ничего нет 😢')
    else:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, _ in products:

            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}'

            await message.answer_photo(photo=image,
                                       caption=text,
                                       reply_markup=markup)


# При нажатии кнопки "добавить" - добавляем 1 товар в корзину.
@dp.callback_query_handler (IsUser(), product_cb.filter(action='add'))
async def add_poduct_callback_handler(query: CallbackQuery,
                                      callback_data: dict):
    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Товар добавлен в корзину!')
    await query.message.delete()
