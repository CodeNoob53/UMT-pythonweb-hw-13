# UMT Python Web HW 11 - Contacts API

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red)
![Alembic](https://img.shields.io/badge/Alembic-migrations-orange)
![JWT](https://img.shields.io/badge/Auth-JWT-black)
![Cloudinary](https://img.shields.io/badge/Cloudinary-avatar_upload-3448C5)
![Postman](https://img.shields.io/badge/Postman-collection-FF6C37)

REST API застосунок для керування контактами з автентифікацією, JWT-авторизацією, email verification, rate limiting, CORS та оновленням аватара через Cloudinary.

Проєкт виконано для домашнього завдання **Тема 11. Аутентифікація та авторизація REST API**.

## Можливості

- Реєстрація користувача з перевіркою унікальності `email` та `username`.
- Хешування паролів через `bcrypt`.
- Login через `OAuth2PasswordRequestForm`.
- JWT access token для захищених маршрутів.
- Доступ користувача тільки до власних контактів.
- Email verification через token-посилання.
- Rate limit для маршруту `/api/users/me`.
- CORS для REST API.
- Оновлення аватара користувача через Cloudinary.
- CRUD для контактів.
- Пошук контактів за `first_name`, `last_name` або `email`.
- Перегляд контактів із днями народження у найближчі 7 днів.
- Postman collection для ручного тестування API.

## Технології

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- asyncpg
- python-jose
- bcrypt
- FastAPI Mail
- SlowAPI
- Cloudinary
- Pydantic Settings
- Uvicorn

## Структура

```text
.
├── alembic/                         # міграції бази даних
├── src/
│   ├── api/                         # API маршрути
│   ├── conf/                        # конфігурація з .env
│   ├── database/                    # DB engine та SQLAlchemy models
│   ├── repository/                  # робота з БД
│   ├── services/                    # auth, email, users, Cloudinary upload
│   └── schemas.py                   # Pydantic schemas
├── Contacts_API.postman_collection.json
├── Dockerfile
├── docker-compose.yml
├── main.py
├── pyproject.toml
└── .env.example
```

## Налаштування середовища

Створіть `.env` у корені проєкту на основі `.env.example`.

```env
DB_URL=postgresql+asyncpg://postgres:your_db_pass@localhost:5432/contacts_db

JWT_SECRET=your_super_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

MAIL_USERNAME=example@gmail.com
MAIL_PASSWORD=
MAIL_FROM=example@gmail.com
MAIL_PORT=465
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Contacts API
MAIL_STARTTLS=False
MAIL_SSL_TLS=True
USE_CREDENTIALS=True
VALIDATE_CERTS=True

CLD_NAME=your_cloud_name
CLD_API_KEY=your_api_key
CLD_API_SECRET=
```

> `.env` не має потрапляти в Git. У репозиторії зберігається тільки `.env.example`.

## Запуск локально

Встановіть залежності у віртуальне середовище.

```powershell
uv sync
```

Якщо `uv` не використовується, встановіть залежності будь-яким зручним способом з `pyproject.toml`.

Переконайтесь, що PostgreSQL запущений локально і база з `DB_URL` існує.

Застосуйте міграції:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Запустіть API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Документація FastAPI буде доступна за адресами:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Docker Compose

Docker Compose піднімає всі потрібні сервіси для застосунку:

- `db` - PostgreSQL 16;
- `api` - FastAPI застосунок.

Перед запуском створіть `.env` на основі `.env.example`. Для Docker Compose значення `DB_URL` автоматично перевизначається на адресу контейнера бази даних `db`, а інші змінні з `.env` використовуються для JWT, пошти та Cloudinary.

Запуск:

```powershell
docker compose up --build
```

Контейнер `api` перед стартом сервера виконує:

```text
alembic upgrade head
```

Після запуску API буде доступне за адресою:

```text
http://127.0.0.1:8000/docs
```

## Основні API маршрути

### Auth

| Method | URL | Опис |
|---|---|---|
| `POST` | `/api/auth/register` | Реєстрація користувача |
| `POST` | `/api/auth/login` | Login, отримання JWT access token |
| `GET` | `/api/auth/confirmed_email/{token}` | Підтвердження email |

### Users

| Method | URL | Опис |
|---|---|---|
| `GET` | `/api/users/me` | Дані поточного користувача |
| `PATCH` | `/api/users/avatar` | Оновлення аватара через Cloudinary |

### Contacts

| Method | URL | Опис |
|---|---|---|
| `GET` | `/api/contacts/?skip=0&limit=100` | Список контактів поточного користувача |
| `POST` | `/api/contacts/` | Створення контакту |
| `GET` | `/api/contacts/search?q=...` | Пошук контактів |
| `GET` | `/api/contacts/birthdays` | Дні народження у найближчі 7 днів |
| `GET` | `/api/contacts/{contact_id}` | Отримання контакту |
| `PUT` | `/api/contacts/{contact_id}` | Оновлення контакту |
| `DELETE` | `/api/contacts/{contact_id}` | Видалення контакту |

## Postman Collection

Файл колекції:

```text
Contacts_API.postman_collection.json
```

Колекція потрібна для ручної перевірки API без написання окремого фронтенду. У ній зібрані запити для реєстрації, підтвердження email, логіну, роботи з користувачем, контактами, пошуком, днями народження та avatar upload.

### Як користуватися

1. Запустіть API:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

2. У Postman натисніть `Import` і виберіть `Contacts_API.postman_collection.json`.

3. Перевірте collection variable `base_url`:

   ```text
   http://127.0.0.1:8000
   ```

4. Відкрийте `Auth / Register user` і в body введіть власні дані:

   ```json
   {
     "username": "your_username",
     "email": "your_real_email@example.com",
     "password": "Password123!"
   }
   ```

   Після успішної реєстрації колекція автоматично збереже `username`, `email` та `password` у collection variables.

5. Підтвердіть email:

   - якщо налаштована пошта, перейдіть за посиланням із листа;
   - або вставте token з листа у collection variable `verify_token` і виконайте `Confirm email by token`;
   - для локальної перевірки без пошти можна вручну виставити `confirmed=true` у БД.

6. Виконайте `Auth / Login`.

   Після успішного login колекція автоматично збереже `access_token`. Далі захищені запити використовують його як Bearer token.

7. Для контактів:

   - `Create random contact` створює випадковий контакт;
   - `List contacts` показує список контактів;
   - `Search contacts - manual` дозволяє вручну ввести `q` у Params;
   - `Search contacts - no matches` перевіряє сценарій без результатів;
   - `Search contacts - empty query` перевіряє валідацію порожнього пошуку;
   - `Create upcoming birthday contact` створює контакт із днем народження через 3 дні;
   - `Upcoming birthdays` перевіряє вибірку днів народження у найближчі 7 днів.

8. Для `Update avatar`:

   - відкрийте `Users / Update avatar`;
   - у `Body -> form-data` виберіть поле `file`;
   - оберіть файл зображення;
   - переконайтесь, що Cloudinary credentials у `.env` мають права на upload/create.

## Поведінка відповідей

- При повторній реєстрації з існуючим email або username API повертає `409 Conflict`.
- При неправильному login або паролі API повертає `401 Unauthorized`.
- Якщо email не підтверджений, login повертає `401 Unauthorized`.
- Захищені маршрути без Bearer token повертають `401 Unauthorized`.
- Створення ресурсу повертає `201 Created`.
- Видалення контакту повертає повідомлення:

```json
{
  "message": "Contact deleted successfully"
}
```

- Пошук без результатів повертає:

```json
{
  "message": "No contacts found",
  "count": 0,
  "contacts": []
}
```

## Безпека

- Паролі користувачів зберігаються тільки у вигляді bcrypt hash.
- JWT secret, SMTP password, Cloudinary credentials та DB credentials читаються з `.env`.
- `.env`, virtualenv, cache-файли та локальні службові папки ігноруються через `.gitignore`.
- Користувач має доступ тільки до власних контактів.

## Перевірка

Базова перевірка після запуску:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Очікуваний результат — поточна revision з позначкою `(head)`.

Також можна відкрити Swagger UI:

```text
http://127.0.0.1:8000/docs
```