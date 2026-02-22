# Logist ZP — Система управления перевозками и зарплатой

Учёт рейсов самосвалов, смен экскаваторов и расчёт зарплаты.

## Стек

- **Backend**: FastAPI + SQLAlchemy 2.x (async) + PostgreSQL + Alembic
- **Frontend**: Vue 3 + TypeScript + Naive UI + Pinia
- **Инфраструктура**: Docker + docker-compose

## Быстрый старт

### 1. Клонировать и настроить

```bash
cd logist_zp
cp .env.example .env
# Отредактируйте .env при необходимости (SECRET_KEY!)
```

### 2. Запуск (Без Docker)

На вашей машине не установлен Docker, поэтому используйте прямой запуск:

**Терминал 1 (Backend):**
```bash
cd backend
source venv/bin/activate  # если создавали venv, иначе просто:
uvicorn app.main:app --reload
```

**Терминал 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Сервисы:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Вход

При первом запуске автоматически создаются:

| Пользователь | Пароль   | Роль       |
|-------------|----------|------------|
| admin       | admin123 | admin      |
| dispatcher  | disp123  | dispatcher |

> ⚠️ **Смените пароли после первого входа!**

### 4. Тестовые данные (seed)

Автоматически создаются при первом запуске:
- 4 карьера с ценами
- 4 материала
- 3 закупщика
- 3 водителя, 2 оператора
- 3 машины, 2 экскаватора
- Настройка: тариф за час экскаватора = 5000

## Миграции

```bash
# Из контейнера backend:
docker-compose exec backend alembic upgrade head
```

Таблицы создаются автоматически при запуске через `create_all`.

## Архитектура

```
logist_zp/
├── docker-compose.yml
├── .env
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI + lifespan + middleware
│   │   ├── core/            # config, security (JWT), deps (RBAC)
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── schemas/         # Pydantic v2 схемы
│   │   ├── services/        # Бизнес-логика
│   │   ├── api/             # Роутеры
│   │   └── utils/           # Excel export
│   └── alembic/
└── frontend/
    └── src/
        ├── api/             # Axios client
        ├── stores/          # Pinia (auth)
        ├── router/          # Vue Router + guards
        ├── layouts/         # MainLayout (sidebar)
        └── views/           # Все страницы
```

## Роли

| Роль       | Возможности |
|------------|-------------|
| Admin      | Всё + управление пользователями + редактирование locked документов |
| Dispatcher | Накладные, смены экскаваторов, формирование зарплаты |
| Accountant | Просмотр ведомостей, отметка «выплачено», экспорт |

## Бизнес-логика

- **Накладные**: цена рейса фиксируется из карьера при создании
- **Дубликаты**: уникальность по `(invoice_number, trip_date, vehicle_id)`
- **Экскаваторы**: нельзя 2 открытых смены на 1 оператора/экскаватор; мин. оплата = 1 час
- **Закрытие месяца**: все документы получают статус `locked`
- **AuditLog**: все изменения locked документов записываются
