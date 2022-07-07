## Yatube

Реализация REST API для социальной сети Yatube

***

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/qutha/yatube.git
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

***

### Использованные технологии


- Python 3.7
- Django 2.2
- Django REST 3.12
- SQLite

***

### Автор

Студент по специальности информатика и вычислительная техника, backend разработчик, или же просто Василий
