# AGENTS.md — правила для ИИ-агентов в репозитории insain-agent

Компания Инсайн (реклама и производство). Репозиторий обслуживает сайт https://insain.ru
и расчёт стоимости продукции. Четыре контура:

1. **Сайт insain.ru** — WordPress на VDS: формы ezFC, страницы, WooCommerce, SEO, меню, медиа,
   плагин-мост `wp-plugin/` (insain-calc-bridge). Главный продуктовый контур.
2. **Расчётное ядро** — `calc_service/` (FastAPI): калькуляторы и справочники цен. Единый источник цен.
3. **ИИ-консультант** — `bot_service/`: консервация (тесты зелёные, не развивается, на VDS не разворачивается).
4. **Harness** — этот файл, `make check`, правила в `.cursor/rules/`. Средство, не продукт.

Текущее состояние прода (адреса, порты, контейнеры, версии плагинов) — `STATUS.md`.
План работ — `docs/refactoring-plan.md` (целиком не читать, только раздел «Протокол выполнения» и свою задачу).

## Приоритет правил при конфликте

1. Явное указание человека в текущей задаче.
2. `.cursor/rules/insain-site-autonomous.mdc` — для любых операций на проде (VDS, WordPress).
3. Этот файл.
4. Живые доки в `docs/` и `STATUS.md`.
5. `CLAUDE.md`, `docs/archive/` — справка; при расхождении с пунктами выше они устарели
   (например, прод-порт API — `8002`, не `8001`). Неоформленные идеи — `BACKLOG.md`.

## Режимы работы

Задачи — [todo/AGENTS.md](todo/AGENTS.md). Роли — [docs/agents/roles/](docs/agents/roles/).

- **Быстрый** — один файл, цена, опечатка. Правка → `make check` → просмотр diff.
- **Обычный** — калькулятор, bridge, форма, модуль. `todo/<задача>.md` → Implementer (модель из шапки
  задачи) → `make check` → self-review → Reviewer (другая модель) → ревью человека → merge.
  При распухшем контексте — новая сессия на этап.
- **Прод** — VDS, WordPress, данные на сервере. [Site ops](docs/agents/roles/site-ops.md) по
  `.cursor/rules/insain-site-autonomous.mdc`, опасные шаги — с подтверждения человека.

## Команды

Windows/PowerShell: `&&` не работает, разделитель `;`. Если нет `make` — `python scripts/dev.py <команда>`.

| Что | Команда |
| --- | --- |
| Проверка перед сдачей | `make check` (или `python scripts/dev.py check`): pytest `calc_service/tests`, затем `bot_service/tests`, ~2–4 мин |
| Быстрая петля | `python -m pytest calc_service/tests` |
| Локальный API | `make calc-up` → http://127.0.0.1:8001, `make calc-down`, `make status` |
| Сверка реестра калькуляторов с API | `python bot_service/check_calc_registry.py` (нужен запущенный API) |

### Деплой API (только с `main`)

Деплоить только коммит с зелёным CI (GitHub Actions, `make check`).

```bash
ssh insain-prod            # с первого раза может отвалиться по таймауту — повторить
cd /opt/insain-agent
bash infra/deploy.sh       # main + чистое дерево → tag rollback → pull → build → smoke → автооткат
curl -fsS https://insain.ru/api/v1/calculators | head -c 200
```

Smoke в скрипте: `GET /api/v1/calculators` и `POST /api/v1/calc/puzzle`. Упал — скрипт сам откатывает код
и образ на `insain-agent-calc-api:rollback` и выходит с ненулевым кодом. Проверка отката без поломки прода:
`SMOKE_EXTRA_PATH=/api/v1/nonexistent bash infra/deploy.sh`. Затем smoke на странице калькулятора.
Git на VDS: `git -c safe.directory=/opt/insain-agent -C /opt/insain-agent …`.

### Деплой плагина и WordPress

- Плагин: `Compress-Archive` → `scp` в `/tmp` → `sudo -u www-data wp plugin install <zip> --force --activate --path=/var/www/insain.ru`.
- Любой wp-cli: `sudo -u www-data wp … --path=/var/www/insain.ru`. Warning `Wt::__wakeup()` — шум.
- Каналы доступа к WP (wp-cli, REST, Browser MCP) и ограничения по объектам — `docs/site/access-tools.md`.
- **Формы ezFC:** структуру форм правят в админке ezFC; после правки агент снимает форму в репозиторий
  (история и diff, не источник для заливки — обратный импорт ломает id элементов). Custom JS переведённых
  на API форм — источник правды в git, в составе плагина. Детали — `docs/site/access-tools.md`,
  раздел «Принятый режим». Реестр форм — `docs/site/forms.md`.
- Товары WooCommerce и каталог поставщиков — перед любой правкой прочитать `docs/site/content-inventory.md`.

## Git

- Обычный и прод — ветка `task/<имя>` от `main`; после ревью merge в `main`
  (fast-forward, PR на GitHub не обязателен). Быстрый — сразу в `main`.
  Прод деплоится только с `main`.
- `git push` (в любую ветку) — только с подтверждения человека. Коммит — когда человек попросил.
- Изменения малыми порциями, не пакетом: один коммит — одна осмысленная правка.

## Инварианты

- **Цены, наценки, курсы, сроки — только из JSON в git** (`calc_service/data/common.json`,
  `data/materials/*.json`, `data/equipment/*.json`; формат json5 с комментариями). В Python не хардкодить.
  Цены на сервере руками не править.
- Наценка калькулятора — `get_margin("margin…")` поверх `MARGIN_OPERATION`, не ниже `MARGIN_MIN`.
- **Ответ калькулятора** обязательно содержит `cost`, `price`, `unit_price`, `time_hours`, `time_ready`,
  `weight_kg`, `materials`; `share_url` добавляет `BaseCalculator.execute()`
  (`calc_service/calculators/base.py`). Каждый элемент `materials` — с `code`, `name`, `title`.
- **Внутренние `code` материалов** не показывать пользователям сайта и бота — только `title`/`description`.
- Размеры на входе — в мм. Комментарии в коде и тексты ошибок — по-русски.
- Новый калькулятор: копия `calc_service/calculators/_template.py`, эталон — `laser.py`, регистрация в
  `calc_service/calculators/__init__.py`, тесты в `calc_service/tests/test_calculators/`
  (подробно — `docs/migration-guide.md`). Тесты обязательны для каждого калькулятора и функции.
- API-контракт и поля данных — `docs/data-formats.md`, `docs/common-json-reference.md`.

## Запреты

- Не коммитить и не выводить в ответы и логи `.env` и любые секреты (пароли, ключи, токены, `wp-config.php`).
- Без подтверждения человека: `wp search-replace`, `docker compose down -v`, удаление файлов и данных
  (локально и на сервере), смена DNS, отключение плагинов оплаты и SEO, прямой SQL в таблицы WordPress.
- `test.insain.ru` — не целевой адрес, работаем только с прод https://insain.ru.
- Не выходить за scope задачи: соседняя проблема — одна строка в отчёте, не правка.

## Перед сдачей

**`make check` зелёный. Упало — чини, не отчитывайся.** «Проверено» без вывода команды не пишется.
Если Grok дважды не получает зелёный `make check` или повторяет одинаковые правки — остановиться и написать в отчёте «нужна эскалация на Opus».

Self-review по своему diff:

1. Diff содержит только то, что требует задача; нет случайных файлов, отладочных print, закомментированного кода.
2. Ни одной захардкоженной цены, наценки или курса; новые данные — в JSON.
3. Ответ калькулятора — все обязательные поля; внутренние `code` не уходят пользователю.
4. Новая логика покрыта тестом; тест падал бы без правки.
5. Сообщения и комментарии по-русски; стиль как в соседнем коде.
6. Доки и `STATUS.md` не противоречат правке (порт, ветка, пути, команды).
7. Для прода: что выкачено, чем проверено (`curl`, smoke), как откатить.

Отчёт: сделано / чем проверено (команда и вывод) / не сделано и почему / требуется решение.

## Сессии

- Одна задача — одна сессия с чистым контекстом. Читать только нужное: блок задачи и файлы из её «Контекста».
- Целиком не открывать: `docs/refactoring-plan.md`, `CLAUDE.md`, `docs/archive/`,
  `bot_service/agent.py` — только grep по месту. `ROADMAP.md` удалён, идеи — в `BACKLOG.md`.
- Контекст распух или задача сменила этап — закончить отчётом и начать новую сессию.

## Ретроспектива

Ошибка агента, которую поймал человек или проверка, превращается ровно в одно из двух:

- **одну строку правила** — в этот файл, в раздел, где она будет прочитана; или
- **одну проверку** — тест или шаг в `make check`, который поймает повтор автоматически.

Правила добавляются по одному, отдельной малой правкой, не пакетом. Если строку можно заменить
проверкой — выбирать проверку. Лимит файла — 150 строк: новое правило вытесняет устаревшее.
