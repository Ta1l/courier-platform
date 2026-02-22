# TEST_REPORT.md

## 1) Краткая сводка
- Дата прогона: 2026-02-22 (UTC).
- Окружение: staging на `85.198.64.119` (`https://kurer-spb.ru`, `https://kurer-spb.ru/admin`).
- Статус критического дефекта: **исправлен**.
- Критический сценарий (кампания -> бот -> заявка -> админка): **PASS** после фикса.
- Общий статус расширенного API/DB smoke-регресса: **17/17 PASS**.
- Часть пунктов из исходного чеклиста помечена как `BLOCKED/N/A` из-за отсутствия в текущем проекте соответствующих сущностей (`clicks`, `payouts`, `audit_logs`, export CSV/PDF) и отсутствия выделенного Telegram test harness для массовой эмуляции контактов.

## 2) Инцидент и первопричина

### Симптом
- В админке в разделе заявок показывалось: `Не удалось загрузить заявки.`
- API `GET /api/applications` возвращал `500`.

### Подтверждение из лога
- `sqlite3.OperationalError: no such column: a.campaign_id`
- Источник: `tg/api/routers/applications.py` (SQL использует `a.campaign_id`).

### Почему это произошло
- База была мигрирована до создания таблицы `applications` с помощью `runner.py`.
- Миграция `0001` расширяла `applications` только если таблица уже существовала.
- В результате таблица создалась позже в legacy-виде (без `campaign_id/status/revenue`), и API начал падать.
- Дополнительно `runner.py` по умолчанию мог работать не с тем DB path, если `DB_PATH` не экспортирован в shell (раньше `.env` не подгружался в миграторе).

## 3) Что исправлено в коде

### Коммиты
- `c4abe6a` — schema drift fix + регрессионные тесты миграций.
- `4c74b47` — backfill в `0002` (восстановление `campaign_id` из `source=camp_X`).
- `33a641e` — отдельная миграция backfill `0003` для уже развернутых БД.

### Изменения
- `tg/migrations/runner.py`
  - Добавлена загрузка `.env` из корня и `tg/.env` перед определением `DB_PATH`.
- `tg/migrations/versions/0002_reconcile_applications_schema.py`
  - Гарантирует наличие `applications` с admin-колонками (`campaign_id`, `revenue`, `status`) даже если таблица появилась позже.
  - Создает индексы по `campaign_id/status`.
  - Нормализует `status`.
  - Делает backfill `campaign_id` из `source=camp_X` (если кампания существует).
- `tg/migrations/versions/0003_backfill_application_campaign_id.py`
  - Backfill для уже применивших `0002` ранее.
- `tg/tests/test_migrations_applications_schema.py`
  - Тест на сценарий: миграции до создания таблицы + последующее восстановление схемы.
- `DEPLOY_UBUNTU_24_04.md`
  - Команды миграций обновлены на явный путь:
    `python tg/migrations/runner.py --db /opt/kurer-spb/tg/applications.db upgrade`.

## 4) Что применено на сервере

- Обновлен код до `33a641e`.
- Применены миграции:
  - `0002`
  - `0003`
- Перезапущены сервисы:
  - `kurer-api`
  - `kurer-bot`

### Проверка после фикса
- `GET /api/applications` -> `200`.
- `GET /api/applications?campaign=2` -> `200`, данные возвращаются.
- Существующая заявка восстановлена backfill-ом:
  - до: `(source='camp_2', campaign_id=NULL)`
  - после: `(source='camp_2', campaign_id=2, status='new')`

## 5) Snapshot / rollback

### Созданные backup-файлы
- `/opt/kurer-spb/backups/applications_20260222_221633.db`
- `/opt/kurer-spb/backups/applications_20260222_221940_before_0003.db`
- `/opt/kurer-spb/backups/qa_snapshot_20260222_222215.db`

### Проверка rollback
- После полного QA-прогона БД восстановлена из `qa_snapshot_20260222_222215.db`.
- Проверено:
  - тестовые инвесторы отсутствуют (`0`),
  - тестовые кампании отсутствуют (`0`),
  - исходная заявка осталась: `[(1, 'camp_2', 2, 'new')]`.

## 6) Выполненные тесты (staging)

## A. Функционал API/данные (выполнено)
- `admin_login` -> PASS
- `create_investor_a` -> PASS
- `create_investor_b` -> PASS
- `create_campaign_a` -> PASS
- `create_campaign_b` -> PASS
- `applications_filter_campaign_a` -> PASS (`count=3`)
- `applications_filter_campaign_b` -> PASS (`count=2`)
- `ownership_own_campaign_ok` -> PASS (`200`)
- `ownership_foreign_campaign_forbidden` -> PASS (`403`)

## B. Безопасность (выполнено)
- `rate_limit_login` -> PASS
  - коды: `401, 401, 401, 401, 401, 429, 429, 429, 429, 429`
- `validation_rejects_bad_login` -> PASS (`422` на payload `' OR 1=1 --`)

## C. Расчеты (выполнено)
- `formula_campaign_a` -> PASS
  - Ожидалось:
    - total_revenue = `42300`
    - net_profit = `37500`
    - investor_profit = `11250`
    - admin_profit = `26250`
    - ROI = `781.25`
  - Фактические значения совпали.

## D. Нагрузка (выполнено)
- `load_site_100_requests` -> PASS
  - success=`100`, errors=`0`, p95=`317.9 ms` (< 1000 ms порога)
- `concurrent_insert_50` -> PASS
  - inserted=`50`, errors=`0`, unique_ids=`true`

## E. Изоляция данных (выполнено)
- `cross_campaign_aggregate_present` -> PASS
  - SQL rows:
    - `(campaign_id=3, apps=53, rev=42300.0)`
    - `(campaign_id=4, apps=2, rev=20000.0)`

Примечание: большие числа `apps=53` получены из теста конкурентных вставок в кампанию A.

## 7) Блокеры/ограничения для полного чеклиста

- `site -> localStorage/cookie -> CTA href`:
  - Требует браузерную E2E автоматизацию (Playwright/Selenium) в этом прогоне не запускалась.
- Полноценная массовая эмуляция Telegram (контакты/анкета от 50 реальных аккаунтов):
  - Нужен test harness или набор Telegram test-аккаунтов/номеров.
- В текущей схеме отсутствуют таблицы/модули:
  - `clicks`, `payouts`, `audit_logs`.
- Экспорт `CSV/PDF` по кампании в API/UI:
  - endpoint/функция не обнаружены.

## 8) Критерии приемки (по доступным проверкам)

- Привязка заявок к нужной кампании: **PASS** (включая восстановление legacy-записи).
- Изоляция investor по чужим кампаниям: **PASS** (`403` на чужой `/api/stats/campaign/:id`).
- Нагрузка без 5xx: **PASS** в smoke-нагрузке.
- Формулы прибыли/ROI: **PASS**.

## 9) Рекомендации

- Добавить E2E browser suite (Playwright):
  - проверка `?camp=` в URL,
  - проверка CTA `href` на `t.me/...start=camp_X`.
- Добавить отдельный интеграционный стенд для Telegram-flow:
  - управляемые test accounts и сценарии отправки контакта.
- Ввести таблицу `clicks` и аудит `audit_logs` (если это требование бизнес-аналитики).
- Оставить `0002 + 0003` обязательными в пайплайне деплоя и всегда запускать миграции с явным `--db`.
