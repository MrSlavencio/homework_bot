from mailbox import FormatError
import sys
import logging
import os
from http import HTTPStatus
import time
import requests
from telegram import Bot
from dotenv import load_dotenv
from exceptation import (
    SendMessageError,
    TokenNotExist,
    ResponseCodeError,
    ResponseIsEmptyDict,
    HWStatusUnknown
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения ботом."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise SendMessageError(error)
    else:
        logging.info(f'Бот отправил сообщение: {message}')


def get_api_answer(current_timestamp):
    """Получаем информацию с API-Яндекс.Домашка."""
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': current_timestamp}
    }
    homework_statuses = requests.get(**request_params)
    if homework_statuses.status_code != HTTPStatus.OK:
        error_msg = (f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                     'недоступен. Код ответа API: 404')
        if homework_statuses.status_code != HTTPStatus.NOT_FOUND:
            error_msg = ('Сбой в работе программы: При обращении к эндпоинту'
                         f'{ENDPOINT} Был получен некорректный ответ. Код '
                         f'ответа API: {homework_statuses.status_code}')
        logging.error(error_msg)
        raise ResponseCodeError(f'При обращении к {request_params["url"]}, '
                                f'заголовки: {request_params["headers"]}, '
                                f'параметры: {request_params["params"]}, '
                                'получен ответ с кодом: '
                                f'"{homework_statuses.status_code}", '
                                f'текст ответа: "{homework_statuses.text}"')
    try:
        return homework_statuses.json()
    except Exception as error:
        raise FormatError(error)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if isinstance(response, list):
        response = response[0]
    if len(response) == 0:
        error_msg = 'Функция check_response приняла пустой словарь.'
        logging.error(error_msg)
        raise ResponseIsEmptyDict(error_msg)
    homeworks = response.get('homeworks')
    if not homeworks and homeworks != []:
        error_msg = 'В ответе сервера нет ключа "homeworks"'
        logging.error(error_msg)
        raise KeyError(error_msg)
    status_date = response.get('current_date')
    if homeworks or homeworks == []:
        if homeworks == []:
            logging.debug('Статус ДЗ не изменился.')
        if not isinstance(homeworks, list):
            error_msg = 'homeworks - не список'
            logging.error(error_msg)
            raise TypeError(error_msg)
        return homeworks, status_date


def parse_status(homework):
    """Извлекает информацию о статусе работы."""
    if not homework:
        raise ValueError('Домашняя работа отсутствует.')
    if isinstance(homework, list):
        homework = homework[0]
    try:
        homework_name = homework['homework_name']
    except Exception:
        error_msg = 'В ответе сервера нет наименования домашней работы.'
        logging.error(error_msg)
        raise KeyError(error_msg)
    homework_status = homework.get('status')
    if not homework_status or homework_status not in HOMEWORK_VERDICTS:
        error_msg = 'Статус домашней работы не из словаря.'
        logging.error(error_msg)
        raise HWStatusUnknown(error_msg)
    verdict = HOMEWORK_VERDICTS.get(homework_status)
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
        current_report = dict()
        previous_report = dict()
        try:
            response = get_api_answer(current_timestamp)
            statuses, current_timestamp = check_response(response)
            if statuses:
                verdict = parse_status(statuses[first_status])
                current_report['статус ДЗ'] = verdict
                if current_report != previous_report:
                    send_message(bot, verdict)
                previous_report = current_report.copy()
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            try:
                current_report['ошибка'] = message
                if current_report != previous_report:
                    send_message(bot, message)
                previous_report = current_report.copy()
            except Exception as error:
                logging.error('Ошибка при отправке сообщения об ошибке: '
                              f'{error}')

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format=('%(asctime)s '
                '[%(levelname)s] '
                '--%(funcName)s-- '
                'row %(lineno)d: '
                '%(message)s'),
        level=logging.DEBUG)
    logging.StreamHandler(sys.stdout)
    logging.info('Бот запущен')
    main()
