from typing import List, Tuple

from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatActions, ReplyKeyboardMarkup

from filters import IsUser
from keyboards.inline.products_from_cart import product_markup
from loader import db, dp, bot
from .menu import cart

@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):

    cart_data: List[Tuple] = db.fetchall(
        'SELECT * FROM cart WHERE cid = ?', (message.chat.id,))
    if len(cart_data) == 0:
        await message.answer('Ваша корзина пуста')
    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        # Создаём словарь с ключами из id товаров и значениями в виде их
        # параметров.
        async with state.proxy() as data:
            data['products'] = {}

        order_cost = 0

        for _, idx, count_in_cart in cart_data:
            # fethone возвращает 1 кортеж product.
            product: Tuple = db.fetchone('SELECT * FROM products WHERE idx = ?',
                                  (idx,))

            if product is None:
                db.query('DELETE FROM cart WHERE idx = ?', (idx,))
            else:
                # Распаковываем кортеж product в переменные по порядку.
                _, title, body, image, price, _ = product
                order_cost += price

                # Заполняем ранее созданный словарь.
                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price}₽.'

                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True,
                                         selective=True)
            markup.add('📦 Оформить заказ')
            await message.answer('перейти к оформлению?',
                                 reply_markup=markup)
