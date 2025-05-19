# status_bot
Простой telegram-бот предназначенный для взаимодействия с API сервиса ЯП. После ответа сервиса бот присылает актуальный статус проекта в чат телеграмма.

## Стек использованных технологий
* Python
* pyTelegramBotAPI
* pytest

## Реализованные возможности
* раз в n минут бот опрашивает сервис API и проверяет статус;
* при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
* бот логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

## Установка проекта на локальный компьютер из репозитория
* Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:<username>/status_bot.git
```
```
cd status_bot
```
* Установить и активировать виртуальное окружение:

Команда для Linux и macOS:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
Команда для Windows:
```
python -m venv venv
```
```
source venv/Scripts/activate
```
* Установить зависимости pip install -r requirements.txt
```
pip install -r requirements.txt
```
* В корневой папке создать файл .env:
```
touch .env
```
* В файле .env добавить переменные из файла .env.example
* Запустить проект:

Команда для Linux и macOS:
```
python3 manage.py runserver
```
Команда для Windows:
```
python manage.py runserver
```

## Автор
* [Андрей Петров](https://github.com/AndreiPetrov94)
