from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types import Message

from keyboards.default.markups import all_right_message, cancel_message
from keyboards.default.markups import submit_markup
from states import SosState
from filters import IsUser
from loader import dp, db


# Обработчик меню /sos
@dp.message_handler(commands='sos')
async def cmd_sos(message: Message):
    await SosState.question.set()
    await message.answer(
        'В чем суть проблемы? Опишите как можно детальнее'
        ' и администратор обязательно вам ответит.',
        reply_markup=ReplyKeyboardRemove())


# Подхватываем состояние question и записываем текст сообщения в прокси.
# После этого переходим к следующему состоянию.
@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text

        await message.answer('Убедитесь, что всё верно.',
                             reply_markup=submit_markup())
        await SosState.next()


# Подхватываем следующее состояние, обрабатываем ошибку пользователя.
@dp.message_handler(
    lambda message: message.text not in [cancel_message, all_right_message],
    state=SosState.submit)
async def process_price_invalid(message: Message):
    await message.answer('Такого варианта не было.')


# Подхватывает кнопку с отменой, и на самом деле ничего не делает.
# Только заканчивает состояние, что выбросит на дефолт.
@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()


# При подтверждении пишет в бд с вопросами.
@dp.message_handler(text=all_right_message, state=SosState.submit)
async def process_submit(message: Message, state: FSMContext):
    cid = message.chat.id

    # Новый вопрос добавляется только, если у пользователя нет
    # активных вопросов. Т.е, максимум вопросов на человека - 1.
    if db.fetchone('SELECT * FROM questions WHERE cid = ?', (cid,)) is None:
        async with state.proxy() as data:
            db.query('INSERT INTO questions VALUES (?, ?)',
                     (cid, data['question']))

        await message.answer('Отправлено!',
                             reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(
            'Превышен лимит на количество задаваемых вопросов.',
            reply_markup=ReplyKeyboardRemove())

    await state.finish()
# Таким образом, бд пользователей строится из колонок пользователь - вопрос.
