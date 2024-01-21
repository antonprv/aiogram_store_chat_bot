from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatActions, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from typing import List, Tuple

from filters import IsAdmin
from handlers.user.menu import orders
from loader import dp, db, bot
from keyboards.inline.order_states import *


# Обработчик заказов для администратора.
@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    orders = db.fetchall('SELECT * FROM orders')

    if len(orders) == 0:
        await message.answer('У вас нет заказов.')
    else:
        await order_answer(message, orders)


async def order_answer(message: Message, orders: List[Tuple]):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

    prev_cid = set()
    counter: int = 0

    for cid, ord_id, _, usr_name, _, _ in orders:

        prev_cid.add(cid)
        c_info = cid

        if cid in prev_cid:
            counter += 1
            c_info = f'{cid} ({counter})'

        text = f'Заказ:\n{c_info} пользователя {usr_name}'
        markup = InlineKeyboardMarkup()
        markup = order_info_markup(ord_id=ord_id, cid=cid)

        await message.answer(text=text,
                             reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), order_cb.filter(action='details'))
async def process_order(query: CallbackQuery, callback_data: dict):
    cid = callback_data['cid']
    ord_id = callback_data['id']

    order_one = db.fetchone('SELECT * FROM orders WHERE ord_id=? AND cid=?',
                            (ord_id, cid))

    text = (f'Заказ <b>№{order_one[0]}: {order_one[3]}</b>\n'
            f'Адрес доставки: {order_one[4]}\n'
            f'Состав заказа: {order_one[5]}')

    await query.message.answer(text=text)


@dp.callback_query_handler(IsAdmin(), order_cb.filter(action='status'))
async def process_order_status(query: CallbackQuery, state: FSMContext,
                               callback_data: dict):
    ord_id = callback_data['id']
    cid = callback_data['cid']

    await query.message.edit_reply_markup(order_state_markup(ord_id=ord_id,
                                                             cid=cid))


@dp.callback_query_handler(IsAdmin(), order_cb.filter(action='idle'))
@dp.callback_query_handler(IsAdmin(), order_cb.filter(action='going'))
@dp.callback_query_handler(IsAdmin(), order_cb.filter(action='arrived'))
async def process_status(query: CallbackQuery, callback_data: dict):
    cid: str = callback_data['cid']
    action: str = callback_data['action']
    order_state_temp: str = ''

    if action == 'idle':
        order_state_temp = order_idle
    elif action == 'going':
        order_state_temp = order_going
    elif action == 'arrived':
        order_state_temp = order_arrived

    db.query('UPDATE orders SET state = ? WHERE cid = ?',
             (order_state_temp, cid))
    await query.message.answer(text='Статус заказа изменён.')

