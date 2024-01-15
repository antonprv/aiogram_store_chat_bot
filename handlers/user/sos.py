from aiogram.dispatcher import FSMContext
from aiogram.types import  ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types import Message

from keyboards.default.markups import all_right_message, cancel_message
from keyboards.default.markups import submit_markup
from states import SosState
from filters import IsUser
from loader import dp, db

@dp.message_handler(commands='sos')
async def cmd_sos(message: Message):
    await SosState.question.set()
    await message.answer(
        'В чем суть проблемы? Опишите как можно детальнее'
        ' и администратор обязательно вам ответит.',
        reply_markup=ReplyKeyboardRemove())