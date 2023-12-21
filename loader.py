# Диспетчер запросов, конструктор бота,
# и types - Режим форматирования сообщений. 
from aiogram import Bot, Dispatcher, types
# Состояния между этапами взаимодействия с ботом будут храниться
# в оперативной памяти.
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# Мой класс-менеджер БД.
from utils.db.storage import DatabaseManager

# Импортирую файл с константами, оттуда беру токен бота.
from data import config

# Создаю объект бота на основе класса-конструктора, передаю
# токен и режим форматирования сообщений. Сообщения бот будет отправлять
# с HTML-разметкой.
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = DatabaseManager('data/database.db')
