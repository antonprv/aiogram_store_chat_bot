from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatActions, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from typing import List, Tuple

from filters import IsAdmin
from handlers.user.menu import orders
from loader import dp, db, bot
from states import OrderState
from keyboards.default.markups import back_markup, back_message, \
    order_details_message
from keyboards.inline.order_states import order_state_markup


order_cb = CallbackData('order', 'id', 'action')


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
    OrderState.info.set()
    counter = 1

    for cid, usr_name, _, _ in orders:

        prev_cid.add(cid)
        text = f'Заказ <b>№{cid}</b>\n\n'
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text=order_details_message,
            callback_data=order_cb.new(id=cid, action='details')))

        await message.answer(text=f'Pаказ:\n{cid} пользователя {usr_name}',
                             reply_markup=markup)


@dp.message_handler(IsAdmin(), order_cb.filter(action='details'))
async def process_one_order(query: CallbackQuery):
    await query.message.delete()
    for cid, usr_name, usr_address, products in orders:
        text = (f'Заказ <b>№{cid}: {usr_name}</b>\n'
                f'Адрес доставки: {usr_address}\n'
                f'Состав заказа: {products}')

        await query.message.answer(text=text,
                                   reply_markup=InlineKeyboardMarkup().
                                   add(order_state_markup(), back_markup()))

