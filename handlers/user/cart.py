from typing import List, Tuple

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatActions, ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

from filters import IsUser
from keyboards.inline.products_from_cart import product_markup
from keyboards.inline.products_from_catalog import product_cb
from keyboards.default.markups import *
from loader import db, dp, bot
import logging
from .menu import cart, delivery_status
from states import CheckoutState


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
            markup.add(checkout_message)
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


@dp.message_handler(IsUser(), text=checkout_message)
async def process_checkout(message: Message, state: FSMContext):

    await CheckoutState.check_cart.set()
    await checkout(message, state)


async def checkout(message: Message, state: FSMContext):
    answer = ''
    total_price = 0

    async with state.proxy() as data:
        for title, price, count_in_cart in data['products'].values():
            temp_price = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {temp_price}₽\n'
            total_price += temp_price

    await message.answer(f'{answer}\nОбщая сумма заказа: {total_price}₽.',
                         reply_markup=check_markup())


@dp.message_handler(IsUser(),
                    lambda message: message.text not in [all_right_message,
                                                         back_message],
                    state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    await message.reply('Такого варианта ещё не было.')


@dp.message_handler(IsUser(), text=back_message,
                    state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message,
                    state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer('Укажите своё имя:', reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

        if 'address' in data.keys():
            await confirm(message)
            await CheckoutState.confirm.set()

        else:
            await CheckoutState.next()
            await message.answer('Укажите свой адрес места жительства.',
                                 reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message,
                    state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):
    async with state.proxy() as data:
        await message.answer('Ищменить имя с <b>' + data['name'] + '</b>?',
                             reply_markup=back_markup())
    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):
    await message.answer(
        'Убедитесь, что всё праивльно оформлено и подтвердите заказ.',
        reply_markup=confirm_markup())


@dp.message_handler(IsUser(),
                    lambda message: message.text not in [confirm_message,
                                                         back_message],
                    state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    await message.reply('Такого варианта не было')


@dp.message_handler(IsUser(), text=back_message,
                    state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    await CheckoutState.address.set()

    async with state.proxy as data:
        await message.answer('Изменить адрес с <b>' + data['address']
                             + '</b>?',
                             reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message,
                    state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    markup = ReplyKeyboardRemove()

    logging.info('A deal is made.')

    async with state.proxy() as data:
        cid = message.chat.id
        products = [idx + '=' + str(quantity)
                    for idx, quantity in db.fetchall('''SELECT idx,
                                                     quantity FROM cart
                                                     WHERE cid=?''',
                                                     (cid,))]

        db.query('INSERT INTO orders VALUES (?, ?, ?, ?)',
                 (cid, data['name'], data['address'], ' '.join(products)))
        db.query('DELETE FROM cart WHERE cid=?', (cid,))

        await message.answer('Ок! Ваш заказ уже в пути 🚀\nИмя: <b>' + data[
                'name'] + '</b>\nАдрес: <b>' + data['address'] + '</b>',
                             reply_markup=markup)
        await state.finish()


@dp.message_handler(IsUser(), text=delivery_status)
async def process_delivery_status(message: Message):
    orders = db.fetchall('SELECT * FROM orders WHERE cid=?',
                         (message.chat.id,))

    if len(orders) == 0:
        await message.answer('У вас нет активных заказов')
    else:
        await delivery_status_answer(message, orders)


async def delivery_status_answer(message, orders):
    res = ''

    for order in orders:
        res += f'Заказ <b>№{order[3]}</b>'
        answer = [
            ' лежит на складе.',
            ' уже в пути!',
            ' прибыл и ждёт вас на почте!'
            ]
        res += answer[0]
        res += '\n\n'

    await message.answer(res)
