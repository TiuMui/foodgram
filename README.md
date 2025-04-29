![event parameter](https://github.com/TiuMui/foodgram/actions/workflows/main.yml/badge.svg?event=push)

## Описание
Фудграм - сервис, на котором пользователи могут публиковать свои инструкции по приготовлению (рецепты), добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям доступен сервис «Список покупок», он позволяет создать и скачать в виде файла список продуктов, которые нужно купить для приготовления добавленных в «Список покупок» блюд.

Проект состоит из фронтенда - одностраничного web-приложения (SPA) и бэкенда, реализованного с помощью REST API. Функционирование проекта осуществляется с помощью **контейнеризации в Docker**.


## Использованные технологии
- **Python 3.13**
- **Django 5.1.4**
- **Django REST Framework 3.15.2**
- Контейнеризация: **Docker**, **Docker Compose**, **Docker Hub**
- CI/CD: **GitHub Actions**
- **Gunicorn 23.0.0**
- **Nginx 1.27.3**
- **PostgreSQL 17.2**

## Автор проекта
[Тимур Мустафин](https://github.com/TiuMui)

## Запуск проекта локально
Клонировать репозиторий:
```shell
git clone git@github.com:TiuMui/foodgram.git
```
Перейти в директорию проекта:
```shell
cd foodgram
```
Создать в директории проекта и заполнить файл `.env` собственными cекретами по примеру файла `.env.example`:

```
POSTGRES_USER=<имя_пользователя_БД>
POSTGRES_PASSWORD=<пароль_БД>
POSTGRES_DB=<имя_БД>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<секретный_ключ_Django>
DEBUG=<False>
ALLOWED_HOSTS=<перечислить через запятую доменные имена и IP-адреса>
CSRF_TRUSTED_ORIGINS=<перечислить через запятую доменные имена>
```
Запустить из директории проекта, где лежит файл `docker-compose.yml` контейнеры:
```shell
sudo docker compose up --build
```
В контейнере бэкенда применить миграции, собрать статику и скопировать ее в директорию, подключенную к volume, создать суперпользователя:
```shell
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py collectstatic
sudo docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
sudo docker compose exec backend python manage.py createsuperuser
```
Загрузить БД ингредиентами для рецептов:
```shell
sudo docker compose exec backend python manage.py loaddata fixtures/ingredients_fixtures.json
```
Получить доступ к проекту локально: http://localhost:8000.

## Техническая документация к API бэкенда:
Клонировать репозиторий:
```shell
git clone git@github.com:TiuMui/foodgram.git
```
Перейти в директорию:
```shell
cd foodgram/infra
```
Выполнить команду:
```shell
sudo docker compose up
```
Получить доступ к фронтенду локально: http://localhost,
спецификацию API: http://localhost/api/docs/.

## Запуск бэкенда локально
Клонировать репозиторий:
```shell
git clone git@github.com:TiuMui/foodgram.git
```
Перейти в директорию:
```shell
cd foodgram/backend
```
Создать и активировать виртуальное окружение:
```shell
python3.13 -m venv venv
source venv/bin/activate
```
Установить зависимости и выполнить миграции:
```shell
pip install -r requirements.txt
python manage.py migrate
```
Запустить сервер разработки:
```shell
python manage.py runserver
```

## Запуск проекта на удаленном сервере
Клонировать репозиторий:
```shell
git clone git@github.com:TiuMui/foodgram.git
```
Создать в директории проекта и заполнить файл `.env` собственными cекретами по примеру файла `.env.example`:

```
POSTGRES_USER=<имя_пользователя_БД>
POSTGRES_PASSWORD=<пароль_БД>
POSTGRES_DB=<имя_БД>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<секретный_ключ_Django>
DEBUG=<False>
ALLOWED_HOSTS=<перечислить через запятую доменные имена и IP>
CSRF_TRUSTED_ORIGINS=<перечислить через запятую доменные имена>

```

При осуществлении push в удаленный репозиторий, GitHub Actions осуществляет тестирование, сборку образов контейнеров фронтэнда, бэкенда, gateway и отправку их в Docker Hub, затем деплой проекта на удаленный сервер.

Для загрузки образов в Docker Hub необходимо в файле `docker-compose.production.yml` указать в именах образов собственный аккаунт на Docker Hub. А также в настройках собственного удаленного репозитория проекта на GitHub указать следующие **Secrets**:

- DOCKER_PASSWORD, DOCKER_USERNAME - пароль и имя польлзователя от аккаунта Docker Hub
- HOST - IP удаленного собственного сервера
- SSH_KEY, SSH_PASSPHRASE, USER - приватный ключ, пароль от него и имя пользователя для доступа к серверу с помощью SSH

Перед осуществлением push в удаленный репозиторий на удаленном сервере нужно выполнить следующее:
- Установить и настроить внешний Nginx на отправку всех запросов на http://127.0.0.1:9090 (порт 9090 хоста проброшен на порт 80 контейнера gateway)
- создать директорию `foodgram` и перенести в нее собственный файл с секретами `.env`.
