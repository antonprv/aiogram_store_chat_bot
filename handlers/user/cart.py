from typing import List, Tuple

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatActions, ReplyKeyboardMarkup

from filters import IsUser
from keyboards.inline.products_from_cart import product_markup
from keyboards.inline.products_from_catalog import product_cb
from loader import db, dp, bot
from .menu import cart


# Выводим список товаров в корзине.
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
            product: List[Tuple] = db.fetchone(
                'SELECT * FROM products WHERE idx = ?',
                (idx,))

            # Если кортеж пустой, удаляем из корзины продукты.
            if product is None:
                db.query('DELETE FROM cart WHERE idx = ?', (idx,))
            else:
                # Распаковываем кортеж product в переменные по порядку.
                _, title, body, image, price, _ = product
                order_cost += price

                # Заполняем ранее созданный словарь.
                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                # Именно этот маркап будет редактироваться последним await.
                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price}₽.'

                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        # Кнопки отобрааются только если стоимость заказа больше 0.
        # Если заказ стоит 0 - значит, заказа не было.
        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True,
                                         selective=True)
            markup.add('📦 Оформить заказ')
            await message.answer('перейти к оформлению?',
                                 reply_markup=markup)


# Подхватываем любые нажатия на клавиатуру под заказанными товарами.
@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def product_callback_handler(query: CallbackQuery,
                                   callback_data: dict,
                                   state: FSMContext):
    idx = callback_data['id']
    action = callback_data['action']

    # Ели нажмём на счётчик:
    if action == 'count':
        async with state.proxy() as data:

            # Перестраховался на случай, если кнопка нажмётся случайно.
            # Тогда просто запустится process_cart и выведет сообщение о
            # пустой корзине.
            if 'products' not in data.keys():
                await process_cart(query.message, state)
            else:
                await query.answer('Количество - ' + data['products'][idx][2])
    else:
        async with state.proxy() as data:
            if 'products' not in data.keys():
                await process_cart(query.message, state)
            else:
                data['products'][idx][2] += 1 if action == 'increase' else -1

                count_in_cart = data['products'][idx][2]

                if count_in_cart == 0:
                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))
                    await query.message.delete()
                else:
                    db.query('''UPDATE cart
                    SET quantity = ?
                    WHERE cid = ? AND idx = ?''',
                                (count_in_cart, query.message.chat.id, idx))

                    # .edit_reply_markup редактирует существующий маркап.
                    await query.message.edit_reply_markup(
                        product_markup(idx, count_in_cart))
