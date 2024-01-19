from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatActions, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from typing import List, Tuple
from uuid import uuid4

from filters import IsAdmin
from handlers.user.menu import orders
from loader import dp, db, bot
from states import OrderState, OrderDeliveryState
from keyboards.default.markups import back_markup, back_message
from keyboards.inline.order_states import *


# Обработчик заказов для администратора.
@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    orders = db.fetchall('SELECT * FROM orders')
    await OrderState.list.set()

    if len(orders) == 0:
        await message.answer('У вас нет заказов.')
    else:
        await order_answer(message, orders)


async def order_answer(message: Message, orders: List[Tuple]):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

    prev_cid = set()
    counter: int = 1

    for cid, usr_name, _, _ in orders:

        idx = str(uuid4())[:8]
        prev_cid.add(cid)

        if cid in prev_cid:
            counter += 1
            cid = f'{cid} ({counter})'

        text = f'Заказ:\n{cid} пользователя {usr_name}'
        markup = InlineKeyboardMarkup()
        markup = order_info_markup(idx=idx, cid=cid)

        await message.answer(text=text,
                             reply_markup=markup)


@dp.message_handler(IsAdmin(), order_cb.filter(action='details'),
                    state=OrderState.list)
async def process_order(query: CallbackQuery):
    await OrderState.next()
    await query.message.delete()
    for cid, usr_name, usr_address, products in orders:
        text = (f'Заказ <b>№{cid}: {usr_name}</b>\n'
                f'Адрес доставки: {usr_address}\n'
                f'Состав заказа: {products}')

        await query.message.answer(text=text,
                                   reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=back_message, state=OrderState.details)
async def process_order_back(message: Message, state: FSMContext):
    await state.finish()
    await process_orders(message)


@dp.message_handler(IsAdmin(), order_cb.filter(action='status'),
                    state=OrderState.details)
async def process_order_status(query: CallbackQuery, state: FSMContext,
                               callback_data: dict):
    idx = callback_data['id']
    await state.finish()
    await OrderDeliveryState.delivery_state.set()
    await query.message.edit_reply_markup(order_state_markup(idx))
    await query.message.answer(back_markup())


@dp.message_handler(IsAdmin(), order_cb.filter(action='idle'),
                    state=OrderDeliveryState.delivery_state)
@dp.message_handler(IsAdmin(), order_cb.filter(action='going'),
                    state=OrderDeliveryState.delivery_state)
@dp.message_handler(IsAdmin(), order_cb.filter(action='arrived'),
                    state=OrderDeliveryState.delivery_state)
async def process_status_idle(query: CallbackQuery, callback_data: dict):
    cid: str = callback_data['cid']
    action: str = callback_data['action']
    order_state_temp: str = ''

    if action == 'idle':
        order_state_temp = order_idle
    else:
        order_state_temp = order_going if action == 'going' else order_arrived

    db.query('UPDATE orders SET state = ? WHERE cid = ?',
             (order_state_temp, cid))
    await query.message.delete()
    await query.message.answer(text='Статус заказа изменён.')
    await process_order_status


@dp.message_handler(IsAdmin(), text=back_message,
                    state=OrderDeliveryState.delivery_state)
async def process_order_state_back(message: Message, state: FSMContext):
    await state.finish()
    await process_orders(message)
