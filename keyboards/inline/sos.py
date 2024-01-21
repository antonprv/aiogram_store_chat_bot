from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

question_cb = CallbackData('question', 'qid', 'action')

question_ask = 'Задать вопрос'
question_show_answers = 'Все мои вопросы'

delete_all_btn = 'Удалить все вопросы ❌'


def question_delete_markup(qid):
    markup = InlineKeyboardMarkup()
    delete_button = InlineKeyboardButton(text='Удалить вопрос ❌',
                                         callback_data=question_cb.
                                         new(qid=qid, action='remove'))
    markup.add(delete_button)

    return markup
