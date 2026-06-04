# UMT Python Web HW 13 - Contacts API

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1)
![Redis](https://img.shields.io/badge/Redis-7-red)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red)
![JWT](https://img.shields.io/badge/Auth-JWT_access%2Frefresh-black)

REST API для керування контактами з JWT access/refresh токенами, Redis-кешуванням,
скиданням пароля, ролями користувачів та автентифікацією.

## Можливості

- Реєстрація / login / logout.
- JWT **access token** (короткий, 15 хв) + **refresh token** (довгий, 7 днів).
- Endpoint `/api/auth/refresh` для оновлення пари токенів.
- Redis-кеш для `get_current_user`: cache hit → Redis, cache miss → DB + populate.
- Інвалідація кешу при зміні пароля, ролі, email confirmation та logout.
- Скидання пароля через email-посилання (JWT-токен, TTL 1 год).
- Ролі: `user` та `admin`. Перший зареєстрований користувач — адмін.
- Endpoint `/api/users/avatar` — тільки для адміністраторів (403 для звичайних).
- Email-верифікація при реєстрації.
- CRUD контактів з пошуком і фільтром по днях народження.
- Rate limiting на `/api/users/me`.
- Cloudinary для завантаження аватара.
- Sphinx-документація.
- Покриття тестами > 75% (pytest + pytest-cov).

## Структура проєкту

```text
.
├── alembic/               # міграції БД
├── docs/                  # Sphinx документація
│   └── _build/html/       # згенерована HTML-документація
├── src/
│   ├── api/               # auth, users, contacts роутери
│   ├── conf/              # Settings через pydantic-settings
│   ├── database/          # SQLAlchemy engine, ORM моделі
│   ├── repository/        # UserRepository, ContactRepository
│   ├── services/          # auth, email, redis_cache, upload_file, users
│   └── schemas.py         # Pydantic schemas
├── tests/                 # unit + integration тести
├── main.py                # FastAPI app entry point
├── pyproject.toml
├── render.yaml            # Render Blueprint (API + Postgres + Redis)
├── .env.example
└── docker-compose.yml     # локальна розробка (PostgreSQL + Redis)
```

## Налаштування `.env`

Скопіюйте `.env.example` → `.env` і заповніть:

```env
DB_URL=postgresql+asyncpg://postgres:your_db_pass@localhost:5432/contacts_db

# Used by docker-compose to set the DB container password (must match DB_URL)
POSTGRES_PASSWORD=your_db_pass

JWT_SECRET=your_super_secret_key_here_min_32_chars
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRATION_SECONDS=900
JWT_REFRESH_EXPIRATION_SECONDS=604800

REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=900

# Comma-separated CORS allowed origins (no trailing slashes)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

MAIL_USERNAME=example@gmail.com
MAIL_PASSWORD=your_app_password
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
CLD_API_SECRET=your_api_secret
```

> `.env` не комітиться в Git. В репозиторії — тільки `.env.example`.

## Локальний запуск (без Docker)

```powershell
# Встановити залежності (включно з dev)
uv sync --all-extras

# Застосувати міграції
uv run alembic upgrade head

# Запустити сервер
uv run uvicorn main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Docker Compose (локальна розробка)

Піднімає PostgreSQL 16 + Redis 7 + FastAPI застосунок.

```powershell
# Запуск
docker compose up --build

# Зупинка
docker compose down
```

Перед запуском — заповніть `.env`. `DB_URL` і `REDIS_URL` автоматично перевизначаються
через `environment:` у `docker-compose.yml`.

## Деплой на Render

У репозиторії є `render.yaml` для Render Blueprint. Він створює:

- Docker Web Service для FastAPI застосунку.
- Render Postgres database.
- Render Key Value instance для Redis-сумісного кешу.

При створенні Blueprint Render автоматично підставляє:

- `DB_URL` з Render Postgres `connectionString`;
- `REDIS_URL` з Render Key Value `connectionString`;
- `JWT_SECRET` через `generateValue`.

У коді `DB_URL` автоматично нормалізується з Render-формату `postgresql://...`
до `postgresql+asyncpg://...`, який потрібен для async SQLAlchemy.

Після створення Blueprint у Render Dashboard потрібно вручну заповнити секрети:

```text
MAIL_USERNAME
MAIL_PASSWORD
MAIL_FROM
CLD_NAME
CLD_API_KEY
CLD_API_SECRET
```

Якщо Render видасть іншу адресу сервісу або ви додасте frontend-домен, оновіть
`CORS_ORIGINS` у Render Dashboard.

## Тести

```powershell
# Запустити тести
uv run pytest tests/

# З coverage-звітом
uv run pytest tests/ --cov=src --cov-report=term-missing

# З мінімальним порогом (75%)
uv run pytest tests/ --cov=src --cov-fail-under=75
```

Тести використовують **SQLite in-memory** (не потребує PostgreSQL) і **fakeredis** (не потребує Redis).

## Sphinx-документація

```powershell
# Побудувати HTML-документацію
uv run sphinx-build -b html docs docs/_build/html
```

Готова документація буде в `docs/_build/html/index.html`.

## Postman Collection

Файл `Contacts_API.postman_collection.json` — готова колекція запитів для ручного тестування всіх endpoints API.

**Для чого:** дозволяє перевірити повний flow (реєстрація → підтвердження email → login → робота з контактами → logout) без написання коду. Кожен запит містить автоматичні тести (статус-коди, наявність полів) і пре-скрипти (генерація унікальних даних, збереження токенів між запитами).

### Як імпортувати

1. Відкрийте Postman.
2. Натисніть **Import** → оберіть файл `Contacts_API.postman_collection.json`.

### Налаштування base_url

За замовчуванням `base_url` вказує на Render-деплой. Для локального тестування:

1. Відкрийте колекцію → вкладка **Variables**.
2. Змініть `base_url` на `http://127.0.0.1:8000`.

### Рекомендований порядок запитів

```
Health / Root                        ← перевірка що API відповідає
Auth / Register user                 ← реєстрація (перший user стає admin)
  → відкрийте email, скопіюйте токен з посилання підтвердження
  → вставте токен у змінну verify_token
Auth / Confirm email by token        ← підтвердження email
Auth / Login                         ← зберігає access_token і refresh_token автоматично
Users / Get current user             ← перевірити роль (admin / user)
Contacts / Create random contact     ← зберігає contact_id автоматично
Contacts / Create upcoming birthday contact
Contacts / List contacts
Contacts / Get contact by id
Contacts / Update contact
Contacts / Search contacts - manual
Contacts / Search contacts - no matches
Contacts / Search contacts - empty query  ← очікує 422
Contacts / Upcoming birthdays
Contacts / Delete contact
Contacts / Delete birthday contact
Users / Update avatar (admin only)   ← оберіть файл зображення у Postman Body → form-data
Auth / Refresh tokens                ← ротує обидва токени
Auth / Request password reset        ← надсилає email; скопіюйте токен у reset_token
Auth / Confirm password reset        ← встановлює новий пароль, оновлює змінну password
Auth / Logout                        ← відкликає refresh token
```

### Змінні колекції

| Змінна | Встановлюється | Опис |
|---|---|---|
| `base_url` | вручну | URL API |
| `username` | Register (авто) | ім'я користувача |
| `email` | Register (авто) | email |
| `password` | вручну / Confirm reset (авто) | пароль |
| `verify_token` | **вручну** (з email) | токен підтвердження email |
| `reset_token` | **вручну** (з email) | токен скидання пароля |
| `access_token` | Login / Refresh (авто) | JWT access token |
| `refresh_token` | Login / Refresh (авто) | JWT refresh token |
| `contact_id` | Create contact (авто) | ID створеного контакту |

## Основні API маршрути

### Auth

| Method | URL | Опис |
|---|---|---|
| `POST` | `/api/auth/register` | Реєстрація |
| `POST` | `/api/auth/login` | Login → access + refresh token |
| `POST` | `/api/auth/refresh` | Оновлення пари токенів |
| `POST` | `/api/auth/logout` | Logout (відкликати refresh token) |
| `GET`  | `/api/auth/confirmed_email/{token}` | Підтвердження email |
| `POST` | `/api/auth/reset-password/request` | Запит на скидання пароля |
| `POST` | `/api/auth/reset-password/confirm` | Встановлення нового пароля |

### Users

| Method | URL | Опис |
|---|---|---|
| `GET`   | `/api/users/me` | Профіль поточного користувача (кешується в Redis) |
| `PATCH` | `/api/users/avatar` | Оновлення аватара (**тільки admin**) |

### Contacts

| Method | URL | Опис |
|---|---|---|
| `GET`    | `/api/contacts/` | Список контактів |
| `POST`   | `/api/contacts/` | Створення контакту |
| `GET`    | `/api/contacts/search?q=...` | Пошук |
| `GET`    | `/api/contacts/birthdays` | Найближчі 7 днів народження |
| `GET`    | `/api/contacts/{id}` | Контакт за ID |
| `PUT`    | `/api/contacts/{id}` | Оновлення |
| `DELETE` | `/api/contacts/{id}` | Видалення |

## Деталі реалізації

### Redis-кеш

`get_current_user` перевіряє Redis за ключем `user:{username}`. При cache miss — читає з DB і записує в кеш з TTL `REDIS_CACHE_TTL` секунд. Кеш **не містить** `hashed_password` або `refresh_token`. При будь-якій зміні даних користувача (пароль, роль, email, logout) кеш інвалідується.

### Скидання пароля

1. `POST /api/auth/reset-password/request` — відправляє email з JWT-посиланням (TTL 1 год). Завжди повертає 200, щоб не розкривати, чи існує email.
2. `POST /api/auth/reset-password/confirm` — перевіряє токен, оновлює пароль, відкликає refresh token, інвалідує Redis-кеш.

### Ролі

Перший зареєстрований користувач отримує роль `admin`, решта — `user`. Endpoint `/api/users/avatar` захищено dependency `require_role(UserRole.admin)` — звичайний користувач отримає `403 Forbidden`.

### Access/Refresh токени

- **Access token** — TTL 15 хв, поле `token_type: "access"`.
- **Refresh token** — TTL 7 днів, поле `token_type: "refresh"`, зберігається hash в DB.
- `POST /api/auth/refresh` — приймає refresh token, перевіряє тип і відповідність у DB, повертає нову пару.
- Logout відкликає refresh token (встановлює `NULL` в DB).

## Безпека

- Паролі — тільки bcrypt hash.
- JWT secrets, SMTP, Cloudinary credentials — тільки через `.env`.
- Жодних hardcoded секретів у коді.
- Кеш не зберігає `hashed_password` або `refresh_token`.
