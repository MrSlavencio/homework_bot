# Python telegram bot

## Описание:
Проект сервиса telegram_bot, работающий с API сервиса Практикум.Домашка.

Даёт возможность:

* Отправлять запросы к сервису Практикум.Домашка с выбранной периодичностью и получать статус проверки домашней работы.
* Получать оповещение об обновлении статуса проверки домашней работы в Телеграме.
* Получать оповещение об ошибках в работе бота в Телеграме.

В проекте применяется логирование, обработка исключений, токены доступа хранятся в пространстве переменных окружения.

Бот размещен и работает на сервере [Heroku][https://www.heroku.com/]: homework-check-bot-mrslavencio

Системные требования
Python 3.7+
Works on Linux, Windows, macOS
Используемые технологии:
Python 3.7+
Pytest
Telegram Bot API
Requests
Запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:

git clone https://github.com/Seniacat/telegram_bot.git
cd telegram_bot
Cоздать и активировать виртуальное окружение:

python3 -m venv env
source env/bin/activate (Mac OS, Linux) или source venv/Scripts/activate (Win10)
Установить зависимости из файла requirements.txt:

python3 -m pip install --upgrade pip
pip install -r requirements.txt
Создать файл виртуального окружения .env в корневой директории проекта:

touch .env
В нём указать свои ключи для окен API сервиса Практикум.Домашка и Telegram:

- PRAKTIKUM_TOKEN =
- TELEGRAM_TOKEN =
- TELEGRAM_CHAT_ID =
Запустить проект на локальной машине:

python homework.py
