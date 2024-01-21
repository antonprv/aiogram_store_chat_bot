from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions

from filters import IsAdmin
from handlers.user.menu import questions
from keyboards.default.markups import all_right_message, cancel_message, \
    submit_markup
from loader import dp, db, bot
from states import AnswerState
from utils.no_emoji import strip_emojis

question_cb = CallbackData('question', 'cid', 'qid', 'action')


@dp.message_handler(IsAdmin(), text=questions)
async def process_questions(message: Message):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    # Получаем из бз лист с кортежами
    questions = db.fetchall('SELECT * FROM questions')

    if len(questions) == 0:
        await message.answer('Нет вопросов')

    else:
        # Внутри каждой кнопки "ответить" хранятся id чата,
        # и действие-пересылка на следующего обработчика.
        for cid, qid, question, _ in questions:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                'Ответить',
                callback_data=question_cb.new(cid=cid, qid=qid,
                                              action='answer')))

            await message.answer(question, reply_markup=markup)


# Перехватываем экшен, и переходим к списку вопросов.
@dp.callback_query_handler(IsAdmin(), question_cb.filter(action='answer'))
async def process_answer(query: CallbackQuery, callback_data: dict,
                         state: FSMContext):
    async with state.proxy() as data:
        data['cid'] = callback_data['cid']
        data['qid'] = callback_data['qid']

    await query.message.answer('Напиши ответ.',
                               reply_markup=ReplyKeyboardRemove())
    await AnswerState.answer.set()


# Переходим на следующий стейт, с активной кнопкой отмены.
@dp.message_handler(IsAdmin(), state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer'] = strip_emojis(message.text)

    await AnswerState.next()
    await message.answer('Убедись, что в ответе нет ошибок.',
                         reply_markup=submit_markup())


# Перехватываем состояние, выводим сообщение, что всё отменено.
# На самом деле мы ничего и не сделали. В целях оптимизации
# БД обновляется только после всех подтверждений.
@dp.message_handler(IsAdmin(), text=cancel_message,
                    state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()


# Перехватываем колбэк кнопки и состояние, и обновляем БД.
# Удаляем из БД вопрос, выводим пользователю сообщение состоящее из
# вопроса и ответа.
@dp. message_handler(IsAdmin(), text=all_right_message,
                     state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    async with state.proxy() as data:
        answer = data['answer']
        qid = data['qid']
        cid = data['cid']

        db.query('UPDATE questions SET answer = ?'
                 ' WHERE qid = ?',
                 (answer, qid))

        text = 'На один из ваших вопросов только что дали ответ! ✨'
        await message.answer('Отправлено!',
                             reply_markup=ReplyKeyboardRemove())
        await bot.send_message(chat_id=cid, text=text)

    await state.finish()

