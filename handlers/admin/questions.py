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


question_cb = CallbackData('question', 'cid', 'action')

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
        for cid, question in questions:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                'Ответить',
                callback_data=question_cb.new(cid=cid, action='answer')))

            await message.answer(question, reply_markup=markup)