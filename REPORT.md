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

---

## Security Cleanup (2026-02-22)

### Состояние ДО работ

- Был риск-комментарий от пользователя: Chrome отмечал сайт как опасный.
- На сервере отсутствовали явные security headers в nginx-конфиге сайта.
- В `nginx.conf` были ослабленные глобальные TLS-настройки (`TLSv1/TLSv1.1`).
- SSH root login по паролю включён, в `auth.log` шёл активный brute-force.
- Дополнительно зафиксирован `WARNING`: при первом подключении к серверу изменился SSH host key.

### Финальный статус по шагам

| Шаг | Статус | Результат |
|---|---|---|
| I. Бэкап | PASS | Создан `/root/backups/20260222_2249/`, сохранены БД/дамп/код/nginx-конфиги |
| II. Git подготовка | PASS | Ветка `fix/security-cleanup-20260222`, `.gitignore` усилен, секреты в tracked-файлах не обнаружены |
| III. Аудит кода | WARNING | Признаков вредоносного инжекта не найдено; есть внешние зависимости (Metrika/fonts), placeholders (`your-domain.com`) |
| IV. Аудит сервера | WARNING | Руткитов/бэкдоров не обнаружено; есть brute-force на SSH и включённый root password login |
| V. Внешние проверки | WARNING | Google Safe Browsing/Sucuri/OpenSSL проверены; VirusTotal и SSL Labs API ограничены внешними факторами |
| VI. Hardening nginx | PASS | Добавлены security headers + CSP, TLS ужесточён, `server_tokens off` |
| VII. Hardening backend | PASS | Добавлен middleware security headers в FastAPI, CORS проверен и ограничен |
| VIII. Обновление зависимостей | PASS | `npm audit`: 4 high -> 0; Python-пакеты актуальны |
| IX. Тестирование | PASS | `pytest` (4 passed), сборки SPA успешны, сервисы/бот работают |
| X. Git commits/push | PASS | Логические коммиты выполнены, ветка запушена в origin |
| XI. Deploy на сервер | PASS | Ветка развернута на сервере, сервисы перезапущены, ошибок старта нет |
| XII. Post-deploy verification | WARNING | Внешние проверки частично ограничены (VT/SSL Labs), flow и headers подтверждены |

### I. Бэкап (PASS)

Папка: `/root/backups/20260222_2249/`

Содержимое:
- `applications.db`
- `applications_dump.sql`
- `site/` (из `/opt/kurer-spb/dist`)
- `backend/` (из `/opt/kurer-spb/tg/api`)
- `tg/`
- `admin-dist/`
- `nginx.conf`
- `sites-enabled/`
- `suspicious-files/`
- `manifest.txt`

### II. Git подготовка (PASS)

- Создана ветка: `fix/security-cleanup-20260222`.
- `.gitignore` дополнен: `.env`, `*.pem`, `private.key` (а также локальные `.env`-варианты).
- Скан по секретам выполнен, в tracked-файлах реальные секреты не найдены.

### III. Аудит кода (WARNING)

Проверены паттерны:
- `eval/document.write/atob/btoa/unescape/innerHTML/outerHTML`
- `window.location.href/replace`, `meta refresh`
- внешние `src`/`iframe`
- длинные base64-последовательности

Итог:
- Явных вредоносных вставок не обнаружено.
- В сборках есть ожидаемые внешние домены: `mc.yandex.ru`, `fonts.googleapis.com`, `fonts.gstatic.com`, `t.me`.
- В `dist/robots.txt` и `dist/sitemap.xml` найден placeholder `your-domain.com` (не malware, но нужно исправить).

### IV. Аудит сервера (WARNING)

Артефакты:
- `/root/backups/20260222_2249/chkrootkit.log`
- `/root/backups/20260222_2249/rkhunter.log`
- `/root/backups/20260222_2249/cron_audit.txt`
- `/root/backups/20260222_2249/users_shells.txt`
- `/root/backups/20260222_2249/network_ss.txt`
- `/root/backups/20260222_2249/network_lsof.txt`
- `/root/backups/20260222_2249/auth_audit.txt`
- `/root/backups/20260222_2249/syslog_audit.txt`

Результаты:
- `chkrootkit`: rootkit/backdoor signatures не найдены.
- `rkhunter`: `Possible rootkits: 0`.
- Зафиксированы предупреждения по hardening:
  - `PermitRootLogin yes` (SSH root по паролю).
  - Массовые неуспешные SSH-попытки (brute-force фоново).

Критическое правило STOP не активировалось: признаков активного руткита/бэкдора не выявлено.

### V. Внешние проверки (WARNING)

1. Google Safe Browsing API (PASS):
   - `https://transparencyreport.google.com/transparencyreport/api/v3/safebrowsing/status?site=kurer-spb.ru`
   - Ответ: `["sb.ssr",1,false,false,false,false,false,...]` (явных unsafe-флагов нет).
2. Sucuri SiteCheck API (PASS):
   - `https://sitecheck.sucuri.net/api/v3/?scan=https://kurer-spb.ru`
   - `score=B`, `blacklists=0`, `security_warnings=0`.
3. VirusTotal GUI (WARNING):
   - Страница доступна, но автоматическое извлечение verdict без API key/интерактивной сессии ограничено.
4. SSL Labs API (WARNING):
   - `api.ssllabs.com` вернул capacity-error (`Running at full capacity`).
5. OpenSSL из консоли (PASS):
   - CN: `kurer-spb.ru`
   - Issuer: Let's Encrypt `E8`
   - Срок: `notBefore=2026-02-22`, `notAfter=2026-05-23`
   - Поддержка: TLS 1.2 / TLS 1.3.

### VI. Hardening nginx (PASS)

Изменено на сервере:
- `/etc/nginx/nginx.conf`
  - `server_tokens off;`
  - `ssl_protocols TLSv1.2 TLSv1.3;`
  - `ssl_prefer_server_ciphers off;`
- `/etc/nginx/sites-enabled/kurer-spb.ru`
  - добавлены headers:
    - `Strict-Transport-Security`
    - `X-Content-Type-Options`
    - `X-Frame-Options`
    - `X-XSS-Protection`
    - `Referrer-Policy`
    - `Permissions-Policy`
    - `Content-Security-Policy-Report-Only`
    - `Content-Security-Policy`

Проверка:
- `nginx -t` -> OK
- `systemctl reload nginx` -> OK
- Open proxy/wildcard redirect уязвимых паттернов не найдено.

### VII. Hardening backend FastAPI (PASS)

Изменён файл:
- `tg/api/app.py`

Что добавлено:
- Middleware security headers (defence in depth).
- Санитизация CORS origins:
  - wildcard `*` отбрасывается;
  - fallback к `SITE_BASE_URL` origin при необходимости.

Проверка:
- `OPTIONS` с `Origin: https://evil.com` -> `400 Disallowed CORS origin`.
- `OPTIONS` с `Origin: https://kurer-spb.ru` -> `200` + `Access-Control-Allow-Origin`.
- На `/api/*` и `/admin` headers присутствуют.

### VIII. Обновление зависимостей (PASS)

Артефакты в бэкапе:
- `npm_audit_before.json`
- `npm_audit_after.json`
- `npm_audit_after_force.json`
- `pip_outdated.txt`
- `pip_upgrade.log`
- `admin_build.log`
- `admin_build_after_force.log`

Итог:
- Node (`admin-spa`):
  - до: `high=4`, `critical=0`
  - после `npm audit fix --force`: `high=0`, `critical=0`
  - обновлены `axios` и `react-router-dom`.
- Python:
  - `pip list --outdated` пустой;
  - обновление по `tg/requirements.txt` без новых пакетов;
  - совместимость сохранена.

### IX. Тестирование (PASS)

Локально:
- `python -m compileall tg` -> OK
- `python -m pytest tg/tests -q` -> `4 passed`
- `cd admin-spa && npm run build` -> OK

На сервере:
- `systemctl is-active kurer-api` -> active
- `systemctl is-active kurer-bot` -> active
- `systemctl is-active nginx` -> active
- `curl https://api.telegram.org/bot<TOKEN>/getMe` -> `ok: true`, bot `@kurer_pro_bot`
- Ошибок в `nginx/error.log` по результатам проверки не зафиксировано.

### X. Git commits/push (PASS)

Коммиты:
1. `chore: harden gitignore for secrets and build artifacts`
2. `security: add FastAPI security headers and strict CORS sanitization`
3. `chore: update admin-spa dependencies to remediate high vulnerabilities`

Push:
- `git push -u origin fix/security-cleanup-20260222` выполнен.

### XI. Deploy на сервер (PASS)

Шаги:
1. `git fetch origin`
2. `git checkout fix/security-cleanup-20260222`
3. `git pull --ff-only origin fix/security-cleanup-20260222`
4. `python tg/migrations/runner.py upgrade`
5. `cd admin-spa && npm ci && npm run build`
6. `systemctl restart kurer-api`
7. `systemctl reload nginx`

Примечание:
- Перед checkout создан stash на сервере для локальных npm-изменений:
  - `stash@{0}: temp-before-security-branch-switch`

### XII. Post-deploy verification (WARNING)

Повторно проверено:
- security headers на `https://kurer-spb.ru/`, `https://kurer-spb.ru/admin`, `https://kurer-spb.ru/api/*` -> OK
- CORS ограничение origin -> OK
- внешние проверки:
  - Google Safe Browsing -> OK
  - Sucuri -> OK
  - SSL Labs API -> ограничение по capacity
  - VirusTotal -> нужна ручная/авторизованная проверка

### Что изменено (файлы)

В репозитории:
- `.gitignore` — исключение чувствительных файлов/артефактов
- `tg/api/app.py` — security headers middleware + CORS sanitation
- `admin-spa/package.json` — обновление зависимостей
- `admin-spa/package-lock.json` — lockfile после security-fix

На сервере (вне git-репозитория):
- `/etc/nginx/nginx.conf` — TLS/server_tokens hardening
- `/etc/nginx/sites-enabled/kurer-spb.ru` — security headers + CSP

### Рекомендации на будущее

1. Перевести SSH на key-based auth, отключить `PermitRootLogin yes`, добавить fail2ban/ufw.
2. Исправить `your-domain.com` placeholders в `robots.txt`/`sitemap.xml`.
3. Провести ручную проверку в Google Search Console: Security Issues -> Request a Review.
4. По возможности заменить `X-XSS-Protection` на современные механизмы (CSP уже применён).
5. Перевести FastAPI `on_event` на lifespan hooks (deprecation cleanup).

### Rollback

Если нужен откат:
1. Код:
   - `cd /opt/kurer-spb`
   - `git checkout main && git pull --ff-only`
2. Nginx:
   - восстановить из `/root/backups/20260222_2249/nginx.conf`
   - восстановить `/root/backups/20260222_2249/sites-enabled/`
   - `nginx -t && systemctl reload nginx`
3. БД:
   - бинарный restore: `/root/backups/20260222_2249/applications.db`
   - или SQL restore из `/root/backups/20260222_2249/applications_dump.sql`
4. Сервисы:
   - `systemctl restart kurer-api`
   - `systemctl restart kurer-bot`
