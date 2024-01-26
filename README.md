Мокап-бот для организации интернет-продаж.

Реализованы:
1. Полностью функциональная база данных с заказами клиентов, каталогами товаров, корзиной.
2. Реализован функционал дистанционной поддержки клиентов с документированием в базе данных.
3. Эластичность и мастштабируемость бота, работа бота с многопоточностью.
4. Полностью реализован интерфейс взаимодействия с клиентом: клиент может заказать товар, оплатить товар, отслеживать свой заказ.
5. Асинхронность кода и всех взаимодействий с Базой Данных.


Инструкция по развёртке бота в Telegram:
1. Создаёте нового бота в https://t.me/BotFather
2. Даёте боту название и адрес, затем копируете API-ключ, и вставлете в переменную BOT_TOKEN по директории data/config.py
3. python pip install -r requirements.txt
4. Бота запускаете через команду python app.py из корня репозитория.
5. Готово! Вы восхитительны.

Немного скриншотов того, что вас ожидает:

<a href="https://imgur.com/q6UKi24"><img src="https://i.imgur.com/q6UKi24.png" title="source: imgur.com" /></a>
