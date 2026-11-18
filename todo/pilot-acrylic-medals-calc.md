# pilot-acrylic-medals-calc

Статус: заблокировано: ждёт todo/ai-calc-authoring-skill.md
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: первый сквозной прогон нового механизма `create-calc-with-form` (два контура: Python API + справочники + автосборка формы на проде).

## Цель

Обкатать сквозной механизм создания нового калькулятора на примере **C2: Акриловые медали и ленты** (`acrylic_medals`): после снятия блокировки `Analyst` проводит интервью с владельцем по новому skill, затем `Implementer` реализует калькулятор на базе существующего `laser` (и при необходимости `uv_print` + новые материалы лент/фурнитуры и наценки в `calc_service/data/`), `wp-plugin/forms/acrylic_medals.js` и спеку формы, а `Site ops` собирает форму конструктором, привязывает к черновику товара WooCommerce, выкатывает API/плагин и передаёт форму на приёмку владельцу.

## Контекст и ссылки

- `.cursor/skills/create-calc-with-form/SKILL.md` (и этапы `interview.md`, `backend.md`, `form.md`) — основной сценарий выполнения.
- `BACKLOG.md` — строка C2 («акриловые медали и ленты, база `laser`, ориентир inari.pro»).
- `calc_service/calculators/laser.py`, `calc_service/calculators/uv_print.py`, `calc_service/data/materials/hardsheet.json`, `calc_service/data/materials/misc.json`, `calc_service/data/common.json` — переиспользуемые расчёты и справочники.
- `scripts/ezfc_build_form.py`, `scripts/ezfc_build_apply.php` — сборка новой формы ezFC на проде.
- Остальное не открывать.

## Scope

- **Шаг 0 (Analyst, после снятия блокировки):** провести интервью с владельцем по `create-calc-with-form/interview.md` (через `AskQuestion`) и заполнить конкретные параметры в этом файле до старта `Implementer`:
  - допустимые виды/толщины акрила из `hardsheet.json` (или новые позиции);
  - варианты нанесения (гравировка лазером, УФ-печать, без нанесения / полноцвет);
  - виды и цены лент и фурнитуры (добавить в JSON с датой и источником цены);
  - параметры расчёта (форма/резка, размеры, тиражи, наценка `margin…`, сроки);
  - точный набор полей формы ezFC, значения по умолчанию и условия показа.
- **В git (Implementer):**
  - При необходимости дополнить `calc_service/data/materials/*.json` (ленты/акрил/фурнитура) и `calc_service/data/common.json` (наценка, если отдельная).
  - Реализовать `calc_service/calculators/acrylic_medals.py` (переиспользуя `LaserCalculator` / `UVPrintCalculator` без дублирования формул), зарегистрировать в `calc_service/calculators/__init__.py`.
  - Написать `calc_service/tests/test_calculators/test_acrylic_medals.py` (эталоны тиражей ≥ 2, проверка обязательных полей, `materials` с `code`/`name`/`title`, `get_options`, `get_tool_schema`, негативные тесты на русском).
  - Написать `wp-plugin/forms/acrylic_medals.js` (`syncUrl`, `calcApi`, `showResult`, `showError`) и JSON-спеку формы (например, `site/forms/specs/acrylic_medals.json` — по формату из skill).
  - Строку для `docs/site/forms.md` (и обновление `BACKLOG.md` про C2) записать в раздел «Результат» для внесения при слиянии в `main`.
- **На проде (Site ops):**
  - Деплой API (`deploy-api`) и плагина `insain-calc-bridge` (`deploy-wp-plugin`) после слияния или по регламенту этапа.
  - Создать черновик товара WooCommerce (`draft`, недоступен гостям: 404) и новую форму ezFC через `scripts/ezfc_build_form.py` + `scripts/ezfc_build_apply.php`.
  - Проверить форму на черновике в браузере (Network `POST /api/v1/calc/acrylic_medals` = 200, консоль без ошибок, блок результата по эталону 79, GET-ссылка, смена всех dropdown/опций) и передать владельцу на приёмку через `AskQuestion`.

## Файлы

- `calc_service/calculators/acrylic_medals.py`
- `calc_service/calculators/__init__.py`
- `calc_service/data/materials/*.json` (только новые позиции лент/материалов для C2)
- `calc_service/data/common.json` (только если потребуется новая наценка `margin*`)
- `calc_service/tests/test_calculators/test_acrylic_medals.py`
- `wp-plugin/forms/acrylic_medals.js`
- `site/forms/specs/acrylic_medals.json` (или путь спеки по конвенции из `ai-calc-authoring-skill`)

## Не-scope

- Правка существующих боевых калькуляторов `laser.py` и `uv_print.py` (кроме вызова их публичных методов).
- Публикация товара в каталог `publish` без отдельного решения владельца на приёмке.
- Другие калькуляторы C1, C3–C11 из `BACKLOG.md`.

## Критерии приёмки

Критерии по конкретным эталонам цены и полям формы уточняются на Шаге 0 (`Analyst`) после интервью с владельцем; базовые обязательные критерии:

- [ ] `python -m pytest calc_service/tests/test_calculators/test_acrylic_medals.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет.
- [ ] Локальный API: `POST /api/v1/calc/acrylic_medals` и `GET /api/v1/tool_schema/acrylic_medals` — HTTP 200, ответ содержит `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, `materials` (с `code`, `name`, `title`), `share_url`.
- [ ] Боевой API после деплоя: `POST https://insain.ru/api/v1/calc/acrylic_medals` — HTTP 200 с ценой, равной эталону.
- [ ] На черновике товара (`draft`, `curl.exe` без cookies → `404`): форма собрана конструктором в стиле формы 79, в Network `POST /api/v1/calc/acrylic_medals` — 200, в консоли нет ошибок `insaincalc`/`ezfc`, блок результата и GET-ссылка работают, смена каждого опционального поля пересчитывает цену и материалы.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: только добавление новой формы и `draft`-товара; боевые формы и опубликованные товары не затрагиваются.
- Цены: при добавлении лент/фурнитуры в JSON обязательно фиксировать дату и источник цены (`cost_date`, `cost_source`), не хардкодить в Python.
- Формы: перед передачей `Implementer` необходимо завершить Шаг 0 (интервью `Analyst` с владельцем, статус временно перевести в `заблокировано: аналитик` при снятии ожидания или провести интервью сразу после закрытия `ai-calc-authoring-skill`).

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
