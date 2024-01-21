from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Message, CallbackQuery, ChatActions
from aiogram.utils.callback_data import CallbackData
from uuid import uuid4

from keyboards.default.markups import all_right_message, cancel_message
from keyboards.default.markups import submit_markup
from states import SosState
from loader import dp, db, bot
from data.config import QUESTIONS_LIMIT
from filters import IsUser
from keyboards.inline.sos import *
from utils.no_emoji import strip_emojis


# Обработчик меню /help
@dp.message_handler(commands='help')
async def cmd_help(message: Message):
    cid = message.chat.id
    limit: int = len(db.fetchall('SELECT * FROM questions'
                                 ' WHERE cid = ?', (cid,)))
    if limit is not None:
        if limit < 3:
            text = (f'Ещё можно задать вопросов:'
                    f' <b>{QUESTIONS_LIMIT - limit}</b>.')
        else:
            text = (f'Вы больше не можете задавать вопросы. '
                    f'Максимум - <b>{QUESTIONS_LIMIT}</b>')
    else:
        text = f'Вы ещё не задавали вопросов.'

    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(question_ask)
    markup.add(question_show_answers)

    await message.answer(text='Чем можем вам помочь?', reply_markup=markup)
    await bot.send_message(chat_id=cid, text=text)


@dp.message_handler(text=question_ask)
async def question_cmd_ask(message: Message):
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
        data['question'] = strip_emojis(message.text)

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
    if (len(db.fetchall('SELECT * FROM questions WHERE cid = ?', (cid,)))
            <= QUESTIONS_LIMIT):
        async with state.proxy() as data:
            qid = str(uuid4())[:8]
            db.query('INSERT INTO questions VALUES (?, ?, ?, ?)',
                     (cid, qid, data['question'], 'пока без ответа'))

        await message.answer('Отправлено!',
                             reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(
            'Превышен лимит на количество задаваемых вопросов.',
            reply_markup=ReplyKeyboardRemove())

    await state.finish()


# Таким образом, бд пользователей строится из колонок пользователь - вопрос.


@dp.message_handler(text=question_show_answers)
async def delete_all_button(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(delete_all_btn)
    await message.answer('Все ваши вопросы:', reply_markup=markup)
    await show_answers(message)


async def show_answers(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id,
                               action=ChatActions.TYPING)

    questions = db.fetchall('SELECT * FROM questions WHERE cid = ?',
                            (message.chat.id,))

    if len(questions) > 0:
        for _, qid, question, answer in questions:
            text = (f'Вопрос: {question}\n\n'
                    f'Ответ: {answer}')

            await message.answer(text=text,
                                 reply_markup=question_delete_markup(qid=qid))
    else:
        await message.answer('У вас пока нет вопросов 🥺')


@dp.callback_query_handler(question_cb.filter(action='remove'))
async def question_delete(query: CallbackQuery, callback_data: dict):
    qid = callback_data['qid']

    db.query('DELETE FROM questions WHERE qid = ?',
             (qid,))
    await query.message.answer(text='Вопрос удалён!')


@dp.message_handler(text=delete_all_btn)
async def delete_all_confirm(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('Да, удалите всё.')
    await message.answer(text='Вы уверены?', reply_markup=markup)


@dp.message_handler(text='Да, удалите всё.')
async def delete_all(message: Message):
    db.query('DELETE FROM questions WHERE cid = ?',
             (message.chat.id,))
    await message.answer(text='Все вопросы удалены!',
                         reply_markup=ReplyKeyboardRemove())
