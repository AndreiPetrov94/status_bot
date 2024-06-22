import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
from telebot import TeleBot
from dotenv import load_dotenv


load_dotenv()
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
        return True
    except ConnectionError as error:
        message = f'Исключение {error}'
        logger.error(message)
        return False


def get_api_answer(timestamp):
    """Делает запрос к API-сервису ЯндексПрактикум."""
    try:
        responce = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        logger.debug(f'Отправлен запрос к API.'
                     f'Код ответа API: {responce.status_code}')
    except requests.RequestException as error:
        message = f'Эндопинт недоступен {error}'
        raise ConnectionError(message)
    if responce.status_code != HTTPStatus.OK:
        raise ConnectionError(
            f'Status_code: {responce.status_code}'
        )
    try:
        return responce.json()
    except ValueError:
        raise ValueError('Ошибка обработки запроса')


def check_response(response):
    """Проверка ответа API на соответствие."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка обработки ответа')
    homeworks = response.get('homeworks')
    if not homeworks:
        raise ValueError('Отсутствуют домашние задания')
    if not isinstance(homeworks, list):
        raise TypeError('Ошибка обработки ответа')
    return response


def parse_status(homework):
    """Получение конкретного статуса домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError('Ошибка обработки ответа')
    try:
        homework_name = homework['homework_name']
    except KeyError:
        raise ValueError('Ошибка отсутствия названия домашней работы')
    try:
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError:
        raise ValueError('Ошибка отсутствия значения статуса домашней работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отстутствуют токены. Работа остановлена.')
        sys.exit('Работа бота остановлена.')
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_timestamp = timestamp - 2600000
    message_telegram = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                updated_status = parse_status(homeworks['homeworks'][0])
                if updated_status != message_telegram:
                    if send_message(bot, updated_status):
                        message_telegram = updated_status
                        current_timestamp = response.get('timestamp')
            else:
                logger.error('Ошибка отправки сообщения')
        except Exception as error:
            failure_message = f'Сбой в работе программы: {error}'
            logging.error(failure_message)
            if failure_message != message_telegram:
                send_message(bot, failure_message)
                message_telegram = failure_message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(message)s',
        encoding='utf-8'
    )
    main()
