import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
from telebot import TeleBot
from dotenv import load_dotenv

from exceptions import NoSendMessage


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправление сообщений в Telegram-чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug('Сообщение отправлено в Telegram.')
    except NoSendMessage as error:
        message = f'Исключение {error}'
        logger.error(message)
        raise NoSendMessage(message)


def get_api_answer(timestamp):
    """Делает запрос к API-сервису ЯндексПрактикум."""
    payload = {'from_date': timestamp}
    try:
        responce = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        logger.debug(f'Отправлен запрос к API.'
                     f'Код ответа API: {responce.status_code}')
    except requests.RequestException as error:
        message = f'Эндопинт недоступен: {error}'
        logger.error(message)
    if responce.status_code != HTTPStatus.OK:
        raise requests.exceptions.HTTPError(
            f'Status_code: {responce.status_code}'
        )
    try:
        return responce.json()
    except ValueError:
        logger.error('Ошибка формирования JSON')
        raise ValueError('Ошибка формирования JSON')


def check_response(response):
    """Проверка ответа API на соответствие."""
    if type(response) is not dict:
        raise TypeError('Ответ содержит ошибку типа данных: ожидается dict.')
    key = 'homeworks'
    homeworks = response.get(key)
    if not homeworks:
        raise KeyError('В ответе API нет ключа: homeworks')
    if type(homeworks) is not list:
        raise TypeError('Ответ содержит ошибку типа данных: ожидается list.')
    return response


def parse_status(homework):
    """Получение конкретного статуса домашней работы."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError:
        raise KeyError('нет')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Отстутствуют токены. Работа остановлена.'
        )
        raise
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_timestamp = timestamp - 2629743
    previous_status = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks is None:
                logger.warning('Отсутствуют домашние задания')
                continue
            updated_status = parse_status(homeworks['homeworks'][0])

            if updated_status != previous_status:
                send_message(bot, updated_status)
                previous_status = updated_status
                current_timestamp = response.get('timestamp')
            else:
                logger.error('Ошибка отправки сообщения')
        except Exception as error:
            failure_message = f'Сбой в работе программы: {error}'
            message = failure_message
            logging.error(failure_message)

            if message != failure_message:
                if send_message(bot, message):
                    failure_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
