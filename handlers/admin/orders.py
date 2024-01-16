from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatActions, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from typing import List, Tuple

from filters import IsAdmin
from handlers.user.menu import orders
from loader import dp, db, bot
from states import OrderState



order_cb = CallbackData('order', 'id', 'action')


# Обработчик заказов для администратора.
@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    orders = db.fetchall('SELECT * FROM orders')

    if len(orders) == 0:
        await message.answer('У вас нет заказов.')
    else:
        await order_answer(message, orders)


async def order_answer(message: Message, orders: List[Tuple],
                       state: FSMContext):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

    prev_cid = set()
    OrderState.info.set()
    order_info: dict = {}


    for cid, usr_name, usr_address, products in orders:

        cid = order_info['cid']
        usr_name =

        counter = 1
        prev_cid.add(cid)
        text = f'Заказ <b>№{cid}</b>\n\n'

        if cid in prev_cid:
            counter += 1
            text += f'Заказ <b>№{cid} {counter}</b>\n\n'
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                '📝 Детали заказов',
                callback_data=order_cb.new(id=cid, action='same_cid')))

            await message.answer(text=f'Все заказы пользователя {usr_name}:'
                                f'{text}',
                           reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                '📝 Детали заказа',
                callback_data=order_cb.new(id=cid, action='diff_cid')))

            await message.answer(text=f'У пользователя {usr_name}'
                                      f'только 1 заказ:',
                                 reply_markup=markup)


@dp.message_handler(IsAdmin(), order_cb.filter(action='diff_cid'))
async def process_one_order(query: CallbackQuery):
    query.message.delete()
    query.message.answer()

@dp.message_handler(IsAdmin(), order_cb.filter(action='same_cid'))
