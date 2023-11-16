[![Main Foodgram workflow](https://github.com/Merdan0595/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/Merdan0595/foodgram-project-react/actions/workflows/main.yml)

### Добро пожаловать в Foodgram:

Социальная сеть для обмена рецептами.

### Стек технологий:

- [Python]
- [Django]
- [Gunicorn]
- [Nginx]
- [Certbot]
- [Docker]
- [GitHub]

### Как запустить проект:

Клонировать репозиторий из GitHub и перейти в него в командной строке:

```
git clone https://github.com/<your_login>/foodgram-project-react.git

cd foodgram-project-react/
```

Создать в корневой папке файл .env с необходимыми переменными окружения. Пример:

```
SECRET_KEY=secretkey
DEBUG=True
ALLOWED_HOSTS=ххх.ххх.ххх.ххх,ххх.ххх.ххх.,localhost,<domain_name>
POSTGRES_DB=kittygram
POSTGRES_USER=kittygram_user
POSTGRES_PASSWORD=kittygram_password
DB_NAME=kittygram

DB_HOST=db
DB_PORT=5432
```

Сохранить, выполнит коммит и запушить изменения на Git:

```
git add .
git commit -m '<название_коммита>'
git push
```

Каждый пуш автоматически запускает тестирование, сборку, развертывание проекта 
 
Проверить проект по доменному имени:

```
https://delovoynos.hopto.org/
158.160.27.232:8000
```
Администратор:
Логин: admin@mail.ru
Пароль: admin


### Автор проекта:

[Merdan Askerov](https://github.com/Merdan0595) - Foodgram(foodgram-project-react) 

