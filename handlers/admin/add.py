# Пока что реально добавляется только категория, остальное - реализация логики.
from hashlib import md5
from typing import Tuple, List


from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove, ContentType
from aiogram.types.chat import ChatActions
from aiogram.utils.callback_data import CallbackData

from loader import dp, db, bot
from filters import IsAdmin
from handlers.user.menu import settings
from states import CategoryState, ProductState


# Определяю тип данных, которые получу при нажатии на кнопку.
# Первое значение - уникальный идентификатор кнопки, должно быть всегда.
# Следом уже нужные мне данные.
category_cb = CallbackData('category', 'id', 'action')


@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):

    # Создаю объект клавиатуры.
    markup = InlineKeyboardMarkup()

    # Делаю запрос к базе данных, получаю список категорий,
    # из каждой категории извлекаю идентификатор и название
    # и раскидываю категории по кнопкам.
    for idx, title in db.fetchall('SELECT * FROM categories'):
        # Через action 'view' свяжемся с другим обработчиком,
        # Который по ID категории перейдет к таблице и скажет,
        # что находится внутри категории.
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    # Тут так же привязываю указатель add_category, и ниже по коду
    # будет обработчик такого указателя.
    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))

    await message.answer('Настройка категорий:', reply_markup=markup)


# Создаю новую категорию, удаляю прошлое сообщение в чате с ботом,
# жду сообщение от пользователя, переключаю состояние на title.
@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Введите название категории:')
    await CategoryState.title.set()


# Обработчик перехватвывает состояние tittle, и сообщение пользователя.
# Сообщение от пользователя становится названием категории,
# а захешированная версия сообщения становится id категории.
@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category_title = message.text
    idx = md5(category_title.encode('utf-8')).hexdigest()
    # Запускаю SQL-запрос с подстановкой названия категории и id.
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category_title))

    # Выхожу из состояния title.
    await state.finish()
    await process_settings(message)


# Перехватываю коллбэк с действием view:
@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict,
                                    state: FSMContext):

    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products product
                           WHERE product.tag =
                           (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Все товары этой категории:')
    # В текущем статусе диалога теперь будет храниться индекс категории.
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products)


# Функционал при проваливании в кнопку с категорией.

# Все нужные для этого переменные:
# Колбэк при нажатии на кнопку.
product_cb = CallbackData('product', 'id', 'action')

cancel_message = '🚫 Отменить'
add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'
back_message = '👈 Назад'
all_right_message = '✅ Все верно'


# Эта функция запускается из обработчика экшена 'view'.
async def show_products(message: Message, products: List[Tuple]):
    # Добавил по приколу. Будет показывать, будто бот печатает.
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

    # Для всех элементов каждого из кортежей из списка из fetchall
    # взять все элементы и сформировать с ними текст.
    for idx, title, body, image, price, tag in products:
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        # Для для каждого товара создаю кнопку "удалить" со своим колбэком.
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ Удалить',
            callback_data=product_cb.new(id=idx, action='delete')))
        # Для каждого кортежа из списка вывожу сообщение с фото, текстом
        # и собственной кнопкой "удалить"
        await message.answer_photo(photo=image,
                                   caption=text,
                                   reply_makrup=markup)

    # Создаю большие кнопки с вариантами (сверху)
    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)

    # Вывожу кнопки.
    await message.answer('Хотите что-нибудь добавить или удалить?',
                         reply_markup=markup)


# Логика удаления категории:
@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):
    # Подхватываем id категории из текущего статуса диалога.
    # Все значения в статусе диалога хранятся как словарь.
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']

            db.query('DELETE FROM products WHERE tag IN '
                     '(SELECT title FROM categories WHERE idx=?)',
                     (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)


# Добавление товара.
@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):
    # Ставим статус и подхватываем его следующим обработчиком.
    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await message.answer('Введите название товара:', reply_markup=markup)


# Отмена добавления названия товара.
@dp.message_handler(IsAdmin(), text=cancel_message,
                    state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Добавление товара отменено',
                         reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)


# Добавление названия товара.
@dp.message_handler(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):
    # Сохраняем название товара в текущем состоянии,
    # чтобы потом его подхватить в следующем обработчике.
    async with state.proxy() as data:
        data['title'] = message.text

    # Переходим к следующему состоянию (body)
    await ProductState.next()
    await message.answer('Введите описание:', reply_markup=back_markup())


def back_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(back_message)

    return markup


# Функционал перехода назад после ввода названия товара.
# Имя ставится заново.
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)


# Функционал перехода назад после ввода описания товара.
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):
    await ProductState.title.set()

    async with state.proxy() as data:
        await message.answer(f"Изменить название с <b>{data['title']}</b>"
                             " на...",
                             reply_markup=back_markup())


# Перехватываем смену состояний и сохраняем сообщение в контекст.
# Переключаемся на слеюущее состояние(картинка)
@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['body'] = message.text

    await ProductState.next()
    await message.answer('Фото?', reply_markup=back_markup())


# Обработчик фото.
@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO,
                    state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):
    # В телеграме фото обрабатываются как список элементов.
    # Через индекс [-1] берём последнее отправленное фото
    # и получаем его идентификатор.
    fileID = message.photo[-1].file_id
    # По идентификатору передаём фото боту.
    file_info = await bot.get_file(fileID)
    # Выполняем загрузку фото.
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    # Сохраняем данное фото в статус image, как до этого
    # сохраняли названия и описания в другие статусы.
    # Кстати статус - это словарь.
    async with state.proxy() as data:
        data['image'] = downloaded_file

    # Переключаемся на следующее состояние\статус.
    await ProductState.next()
    await message.answer('Цена?', reply_markup=back_markup())


# Вывод всей информации о товаре, который подхватывается из состояния цены.
# Прямо в обработчике проверяем, состоит ли сообщение цены только из цифр.
@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(),
                    state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text

        title = data['title']
        body = data['body']
        price = data['price']

        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\nЦена: {price}рублей.'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


def check_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(back_message, all_right_message)

    return markup


# Подхватывает состояние confirm и пишет товар в базу данных.
@dp.message_handler(IsAdmin(), text=all_right_message,
                    state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']

        tag = db.fetchone(
            'SELECT title FROM categories WHERE idx=?',
            (data['category_index'],))[0]
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()

        db.query('INSERT INTO products VALUES(?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), tag))

        await state.finish()
        await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
        await process_settings(message)


# Выхватывает колбэк-данные кнопки "удалить" из show_products
# и удаляет товар из базы данных.
@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery,
                                          callback_data: dict):
    product_idx = callback_data[id]
    db.query('DELETE FROM PRODUCTS WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):
    await ProductState.price.set()
    async with state.proxy as data:
        await message.answer(f'Изенить цену с <b>{data['price']}</b>?',
                             reply_makrup=back_markup())


@db.message_handler(IsAdmin(), content_types=ContentType.TEXT,
                    state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):
    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:
            await message.answer(f"Изменить описание с <b>{data['body']}</b>?",
                                 reply_markup=back_markup())
    else:
        await message.answer('Вам нужно прислать фото товара.')
