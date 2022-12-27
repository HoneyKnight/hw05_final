# Yatube - социальная сеть для публикации личных записей.

### Описание:
Социальная сеть для публикации личных записей. Реализована пагинация постов и кэширование данных, так же реализована регистрация пользователей с верификацией данных, сменой и восстановлением пароля через почту. Написаны тесты на unittest, проверяющие работу сервиса.
### Технологии
- Python 3.7
- Django 2.2.19
- SQLite
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
```
py -3.7 -m venv venv
source venv/scripts/activate
```
- Установите зависимости из файла requirements.txt
```
python -m pip install --upgrade pip
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполните команду:
- Выполнить migrate
```
python manage.py migrate
```
- Создайте пользователя
```
python manage.py createsuperuser
```
- (или) Сменить пароль для пользователя admin
```
python manage.py changepassword admin
```
- Запуск сервиса
```
python manage.py runserver
```
### Авторы
Егор Кляц
