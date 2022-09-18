import sys
import logging
import os
from http import HTTPStatus
import time
import requests
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


SENT_MSGS_LOGS = []


class TokenNotExist(Exception):
    """Исключение для отсутствующих переменных виртуального окружения."""

    pass


class ResponseCodeError(Exception):
    """Исключение для кода ответа API-сервера отличного от 200."""

    pass


class ResponseIsEmptyDict(Exception):
    """Ответ от сервера - пустой словарь."""

    pass


class HWStatusUnknown(Exception):
    """Статус домашней работы не из словаря."""

    pass


def send_message(bot, message):
    """Отправка сообщения ботом."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Бот отправил сообщение: {message}')
    except Exception as error:
        logging.error(error)


def send_error_msg(bot, message):
    """Отправка ботом сообщений об ошибке."""
    try:
        if message not in SENT_MSGS_LOGS:
            send_message(bot, message)
            SENT_MSGS_LOGS.append(message)
    except Exception as error:
        logging.error(error)


def get_api_answer(current_timestamp):
    """Получаем информацию с API-Яндекс.Домашка."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != HTTPStatus.OK:
        bot = Bot(token=TELEGRAM_TOKEN)
        error_msg = (f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                     'недоступен. Код ответа API: 404')
        if homework_statuses.status_code != HTTPStatus.NOT_FOUND:
            error_msg = ('Сбой в работе программы: При обращении к эндпоинту'
                         f'{ENDPOINT} Был получен некорректный ответ. Код '
                         f'ответа API: {homework_statuses.status_code}')
        logging.error(error_msg)
        send_error_msg(bot, error_msg)
        raise ResponseCodeError(f'При обращении к {ENDPOINT}, получен ответ с '
                                'кодом "{homework_statuses.status_code}".')
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) is list:
        response = response[0]
    if len(response) == 0:
        error_msg = 'Функция check_response приняла пустой словарь.'
        logging.error(error_msg)
        send_error_msg(Bot(token=TELEGRAM_TOKEN), error_msg)
        raise ResponseIsEmptyDict(error_msg)
    homeworks = response.get('homeworks')
    if not homeworks and homeworks != []:
        error_msg = 'В ответе сервера нет ключа "homeworks"'
        logging.error(error_msg)
        send_error_msg(Bot(token=TELEGRAM_TOKEN), error_msg)
        raise KeyError(error_msg)
    status_date = response.get('current_date')
    if homeworks or homeworks == []:
        if homeworks == []:
            logging.debug('Статус ДЗ не изменился.')
        if type(homeworks) is not list:
            error_msg = 'homeworks - не список'
            logging.error(error_msg)
            send_error_msg(Bot(token=TELEGRAM_TOKEN), error_msg)
            raise TypeError(error_msg)
        return homeworks, status_date


def parse_status(homework):
    """Извлекает информацию о статусе работы."""
    if type(homework) is list:
        homework = homework[0]
    try:
        homework_name = homework['homework_name']
    except Exception:
        error_msg = 'В ответе сервера нет наименования домашней работы.'
        logging.error(error_msg)
        send_error_msg(Bot(token=TELEGRAM_TOKEN), error_msg)
        raise KeyError(error_msg)
    homework_status = homework.get('status')
    if not homework_status or homework_status not in HOMEWORK_STATUSES:
        error_msg = 'Статус домашней работы не из словаря.'
        logging.error(error_msg)
        send_error_msg(Bot(token=TELEGRAM_TOKEN), error_msg)
        raise HWStatusUnknown(error_msg)
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения.
    которые необходимы для работы программы.
    """
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if not token:
            logging.critical('Отсутствует обязательная переменная окружения.')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logging.info('Программа принудительно остановлена.')
        raise TokenNotExist('В переменных окружения отсутствует обязательный '
                            'токен')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    first_status: int = 0

    send_message(bot, 'Бот запущен')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            statuses, current_timestamp = check_response(response)
            if statuses:
                verdict = parse_status(statuses[first_status])
                send_message(bot, verdict)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG)
    logging.StreamHandler(sys.stdout)
    logging.info('Бот запущен')
    main()
