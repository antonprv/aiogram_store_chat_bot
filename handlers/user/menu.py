from aiogram.types import Message, ReplyKeyboardMarkup
from loader import dp
from filters import IsAdmin, IsUser

# Кнопки пользователя:
catalog: str = '🛍️ Каталог'
balance: str = '💰 Баланс'
cart: str = '🛒 Корзина'
delivery_status: str = '🚚 Статус заказа'

# Кнопки админа:
settings: str = '⚙️ Настройка каталога'
orders: str = '🚚 Заказы'
questions: str = '❓ Вопросы'


# Ответ на команду /menu для админа:
@dp.message_handler(IsAdmin(), commands='menu')
async def admin_menu(message: Message) -> None:
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions)
    markup.add(orders)
    
    await message.answer('Меню', reply_markup=markup)


# Ответ на команду /menu для пользователя:
# (кнопку баланса добавлю позже, когда появится функционал с QIWI)
@dp.message_handler(IsUser(), commands='menu')
async def user_menu(message: Message) -> None:
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    # markup.add(balance)
    markup.add(cart)
    markup.add(delivery_status)
    
    await message.answer('Меню', reply_markup=markup)