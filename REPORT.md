# REPORT

## 1. Состояние проекта ДО изменений

Фактическое состояние на старте:

- `tg/`:
  - Telegram-бот на `aiogram`.
  - SQLite база (`tg/applications.db`) с единственной рабочей таблицей `applications`.
  - Сохранение заявок через FSM flow (`handlers/test.py`).
  - `/start` сохранял только payload в поле `source`.
- `vie/`:
  - Отдельный React/Vite лендинг.
  - Deep-link в бота через `?start=...`.
  - Отдельной админки и backend API не было.
- HTTP backend для админки отсутствовал.
- Миграционного слоя не было.
- Проверка показала, что единый git-репозиторий на уровне `C:\Ref` отсутствует (`.git` нет). Отдельный `.git` есть только в `vie/`.

## 2. Что добавлено

### Backend/API

Добавлен новый backend-слой на FastAPI с изолированным префиксом `/api`:

- JWT auth (access + refresh)
- bcrypt хеширование паролей
- role-check (`admin` / `investor`)
- ownership-check для investor
- rate limit на `/api/auth/login`
- CORS-конфигурация
- раздача SPA из `admin-dist` по маршруту `/admin`

### Миграции

Добавлен migration runner (`up/down`) + ревизия `0001`:

- новые таблицы: `users`, `campaigns`, `refresh_tokens`
- безопасное расширение `applications`: `campaign_id`, `revenue`, `status` (nullable)

### Интеграция с ботом

Сохранена старая логика, добавлено:

- разбор campaign payload из `/start` (`camp_123` или `123`)
- валидация кампании (существует + `active`)
- логирование невалидных payload
- сохранение `campaign_id` в `applications` при наличии мигрированной схемы

### SPA админка

Добавлен отдельный проект `admin-spa` (React + Vite + TypeScript):

- `/login`
- `/admin/dashboard`
- `/admin/users` (только admin)
- `/admin/campaigns`
- `/admin/applications`
- auth store (Zustand), Axios с refresh-flow
- build в `admin-dist` (prod, без sourcemap)

## 3. Файлы, которые добавлены/изменены и зачем

### Добавлены

- `.env.example`
  - Единый шаблон env для бота/API/SPA server settings.
- `pytest.ini`
  - Конфиг pytest.
- `tg/server.py`
  - Entry point FastAPI сервера.

#### Миграции

- `tg/migrations/__init__.py`
- `tg/migrations/runner.py`
- `tg/migrations/versions/__init__.py`
- `tg/migrations/versions/0001_admin_schema.py`

#### API

- `tg/api/__init__.py`
- `tg/api/app.py`
- `tg/api/bootstrap.py`
- `tg/api/config.py`
- `tg/api/database.py`
- `tg/api/deps.py`
- `tg/api/metrics.py`
- `tg/api/rate_limit.py`
- `tg/api/schemas.py`
- `tg/api/security.py`
- `tg/api/routers/__init__.py`
- `tg/api/routers/auth.py`
- `tg/api/routers/users.py`
- `tg/api/routers/campaigns.py`
- `tg/api/routers/applications.py`
- `tg/api/routers/stats.py`

#### Тесты

- `tg/tests/test_api_auth_and_scope.py`

#### SPA

- `admin-spa/package.json`
- `admin-spa/package-lock.json`
- `admin-spa/tsconfig.json`
- `admin-spa/tsconfig.node.json`
- `admin-spa/vite.config.ts`
- `admin-spa/index.html`
- `admin-spa/src/main.tsx`
- `admin-spa/src/App.tsx`
- `admin-spa/src/styles.css`
- `admin-spa/src/vite-env.d.ts`
- `admin-spa/src/types.ts`
- `admin-spa/src/store/auth.ts`
- `admin-spa/src/lib/api.ts`
- `admin-spa/src/lib/format.ts`
- `admin-spa/src/components/ProtectedRoute.tsx`
- `admin-spa/src/components/AdminLayout.tsx`
- `admin-spa/src/pages/LoginPage.tsx`
- `admin-spa/src/pages/DashboardPage.tsx`
- `admin-spa/src/pages/UsersPage.tsx`
- `admin-spa/src/pages/CampaignsPage.tsx`
- `admin-spa/src/pages/ApplicationsPage.tsx`

### Изменены

- `tg/database/db.py`
  - Совместимое сохранение заявок для старой/новой схемы.
  - Добавлены функции парсинга/проверки `campaign_id`.
- `tg/handlers/start.py`
  - Валидация campaign payload и логирование ошибок.
- `tg/handlers/test.py`
  - Передача `campaign_id`, `status`, `revenue` в сохранение заявки.
- `tg/requirements.txt`
  - Добавлены зависимости для API/security/tests.
- `vie/src/config.ts`
  - Логика `?camp=XXX` -> payload `camp_XXX` в `?start=` без поломки старого `utm_source/start`.
- `tg/README.md`
  - Документация по миграциям и запуску API.
- `.gitignore`
  - Игнор новых build/runtime артефактов (`admin-dist`, `admin-spa/node_modules`, `.pytest_cache`).
- `package.json`
  - Добавлены root scripts для управления `admin-spa`.

## 4. Миграции и откат

### Применение

```bash
python tg/migrations/runner.py upgrade
```

### Статус

```bash
python tg/migrations/runner.py status
```

### Откат 1 ревизии

```bash
python tg/migrations/runner.py downgrade --steps 1
```

### Что делает ревизия `0001`

- Создаёт:
  - `users`
  - `campaigns`
  - `refresh_tokens`
- Расширяет `applications` nullable-колонками:
  - `campaign_id`
  - `revenue`
  - `status`
- Добавляет индексы по ключевым полям.
- `downgrade` пересобирает `applications` в исходный формат и удаляет новые таблицы.

## 5. Переменные окружения (`.env`)

См. `.env.example`.

Ключевые переменные:

- Bot:
  - `BOT_TOKEN`
  - `ADMIN_ID`
  - `DB_PATH`
- API:
  - `API_HOST`
  - `API_PORT`
  - `API_RELOAD`
  - `API_AUTO_MIGRATE`
  - `API_CORS_ORIGINS`
  - `API_JWT_SECRET`
  - `API_JWT_ALGORITHM`
  - `API_ACCESS_TOKEN_EXPIRE_MINUTES`
  - `API_REFRESH_TOKEN_EXPIRE_DAYS`
  - `API_LOGIN_RATE_LIMIT`
  - `API_LOGIN_RATE_WINDOW_SECONDS`
  - `ADMIN_BOOTSTRAP_LOGIN`
  - `ADMIN_BOOTSTRAP_PASSWORD`
  - `ADMIN_BOOTSTRAP_NAME`
- SPA/static:
  - `ADMIN_DIST_DIR`
  - `SITE_BASE_URL`

## 6. Как запускать

### Dev

1. Установить Python-зависимости:

```bash
python -m pip install -r tg/requirements.txt
```

2. Создать `.env` из `.env.example` и заполнить секреты.

3. Применить миграции:

```bash
python tg/migrations/runner.py upgrade
```

4. Запустить API backend:

```bash
python tg/server.py
```

5. Запустить Telegram-бота:

```bash
python tg/main.py
```

6. Запустить SPA в dev:

```bash
cd admin-spa
npm install
npm run dev
```

### Prod

1. Собрать SPA:

```bash
cd admin-spa
npm ci
npm run build
```

2. Убедиться, что `admin-dist/` создан.

3. Запустить backend (`API_RELOAD=false`).

4. Backend раздаёт SPA по `GET /admin` и `GET /admin/*`.

## 7. Deploy

Целевой поток:

1. `cd admin-spa && npm run build` -> `admin-dist/`
2. `python tg/migrations/runner.py upgrade`
3. Запуск `python tg/server.py` как service (systemd/supervisor)
4. Запуск `python tg/main.py` как отдельный service
5. Reverse proxy (Nginx):
   - `/api/*` -> FastAPI
   - `/admin/*` -> FastAPI (или напрямую статика)

## 8. Тестирование

### Что выполнено автоматически

- `npm run build` в `admin-spa` — успешно.
- `python -m compileall tg` — успешно.
- `python -m pytest tg/tests -q` — 2 passed.
- Проверка миграции и rollback на тестовой копии БД — успешно.

### Smoke test (ручной сценарий)

1. Войти в `/admin/login` под bootstrap-admin.
2. Создать investor в разделе users.
3. Создать campaign и привязать к investor.
4. Скопировать ссылку `https://kurer-spb.ru/?camp={id}` из campaigns.
5. Открыть ссылку, перейти в бота, пройти flow.
6. Проверить, что новая заявка появилась в `/admin/applications` с `campaign_id`.
7. Изменить статус/revenue заявки.
8. Проверить dashboard и campaign stats.

### Чеклист ручной проверки

- Auth:
  - login, me, refresh, logout.
  - невалидный пароль -> 401.
  - rate limit на login -> 429.
- Role:
  - investor не видит `/admin/users` функционально и через API получает 403.
- Ownership:
  - investor видит только свои campaigns/applications/stats.
- Campaign integration:
  - `?camp=123` -> `start=camp_123`.
  - несуществующая/paused кампания логируется и не привязывается.
- Prod SPA:
  - `/admin` открывается, роуты SPA работают при прямом переходе.

## 9. Риски и TODO

### Риски

- `on_event("startup")` в FastAPI помечен deprecated (работает, но желательно перейти на lifespan).
- Refresh/login rate limit реализован in-memory (под single instance). Для multi-instance нужен Redis-backed limiter.
- В существующих исходниках есть признаки проблем кодировки (mojibake в строках), это не ломалось в рамках задачи, но требует отдельной нормализации.
- `npm audit` для `admin-spa` показал 4 high vulnerabilities в dependency tree; нужен отдельный dependency hardening.

### TODO

1. Перевести startup hooks на lifespan API FastAPI.
2. Вынести rate limit/refresh revoke в shared storage (Redis).
3. Добавить e2e smoke с Telegram sandbox/mock.
4. Доработать unit-тесты на формулы `stats` и edge cases (budget=0, negative profit, null revenue).
5. Добавить CI pipeline (build + pytest + migration check).

## 10. Git/ветки/коммиты

По требованию требовалась ветка `feature/spa-admin-panel` и коммиты по шагам.

Фактическое ограничение среды:

- На уровне `C:\Ref` нет `.git` (это не git-репозиторий).
- Отдельный git есть только внутри `vie/`, тогда как изменения затрагивают и `tg/`.

Из-за этого создать единую ветку/осмысленные коммиты для всего проекта в текущей структуре невозможно без предварительной инициализации/реорганизации репозитория.
