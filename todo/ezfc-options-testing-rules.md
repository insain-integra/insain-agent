# ezfc-options-testing-rules

Статус: закрытие
Сложность: высокая
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: не нужен
Почему: правка правил для агентов (skill и роли) + контрактный тест в `calc_service/tests/`, без изменений прода.

## Цель

Исключить пропуск опций при переносе форм ezFC на API: Implementer сверяет с JS и покрывает тестами каждую опцию формы (не перебирая все материалы), Site ops прогоняет те же опции на копии в браузере с таблицей результатов, Reviewer проверяет 100% покрытие опций формы, а `test_wp_plugin_forms.py` автоматически ловит чекбоксы, попавшие в `syncUrl` мимо `calcApi`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, `verify.md`, `copy.md` — текущий порядок сверки до перевода и отладки копии.
- `docs/ezfc-api-migration.md` — чеклист проверки формы на странице.
- `docs/agents/roles/analyst.md`, `docs/agents/roles/reviewer.md` — правила назначения и проверки `Reviewer`.
- `calc_service/tests/test_wp_plugin_forms.py` — контрактные тесты `wp-plugin/forms/*.js`.
- История возвратов из-за пропущенных опций: `docs/history/log.md` (`form-tablets`, `form-magnet-laminated`, `form-badge`, `form-notebook`).
- Остальное не открывать.

## Scope

- `.cursor/skills/ezfc-form-to-api/verify.md`:
  - Уточнить шаг 0: если опция присутствует на переводимой форме и влияет на цену в старом `cjsCalc`, её нельзя оставлять в `js_port_gaps_allowed.txt` с формулировкой «на дефолте не нужна» — либо портировать в задаче, либо `заблокировано: человек`.
  - Дополнить шаги 1а–3 матрицей опций формы (из шагов 5 и 5б):
    - проверять 100% чекбоксов (`ckb*`/`chk*`), 100% radio-переключателей (`rdo*`), 100% вариантов dropdown способов нанесения/резки/обработки/сложности (включая зависимые поля, которые открываются при их выборе);
    - **не перебирать все материалы/форматы/заготовки** — достаточно дефолтного + 1 альтернативного варианта;
    - сверять каждую строку матрицы one-factor-at-a-time (дефолт + опция) между JS-раннером и API, фиксировать эталоны в `test_<slug>.py` (`REF_FORM_OPTIONS`).
- `.cursor/skills/ezfc-form-to-api/copy.md`:
  - Дополнить шаг 14 обязательным прогоном на копии всех строк матрицы опций (чекбоксы, radio, способы нанесения/обработки; материалы — 1 смена dropdown) с проверкой: параметр уходит в `POST /api/v1/calc/<slug>`, цена и срок на странице совпадают с эталоном.
  - Зафиксировать формат таблицы проверки в отчёте (`Опция | Параметр в POST | Цена JS/API | Цена на копии | Срок`).
- `docs/ezfc-api-migration.md`:
  - Синхронизировать раздел «Чеклист перевода» с проверкой всех опций формы (без перебора всех материалов).
- `docs/agents/roles/reviewer.md` и `docs/agents/roles/analyst.md`:
  - В `reviewer.md` добавить обязательную сверку полноты опций при ревью переноса формы: список входных полей формы (шаги 5 и 5б) vs `forms/<slug>.js` vs `REF_FORM_OPTIONS` в тестах vs таблица прогона `Site ops`. Любая живая опция формы без проверки или без передачи в `calcApi` (без явной пометки «только URL») — `блокер`. Браузер `Reviewer` повторно не запускает.
  - В `analyst.md` уточнить правило `Reviewer: не нужен`: допустимо только для простых копий без чекбоксов и ветвлений способов нанесения/обработки; для форм с опциями/ветвлениями назначать `Reviewer`.
- `calc_service/tests/test_wp_plugin_forms.py`:
  - Добавить тест, который для всех `wp-plugin/forms/*.js` проверяет: каждый чекбокс `ckb*`/`chk*` из `insaincalc.syncUrl({...})` либо используется в формировании тела `calcApi`, либо явно перечислен в компактном allowlist существующих/url-only полей (по аналогии с `NO_FORM_DEFAULT_YET`, с комментарием-причиной). Проверить, что тест падает при искусственном удалении передачи чекбокса в `calcApi`.

## Файлы

- `.cursor/skills/ezfc-form-to-api/verify.md`
- `.cursor/skills/ezfc-form-to-api/copy.md`
- `docs/ezfc-api-migration.md`
- `docs/agents/roles/reviewer.md`
- `docs/agents/roles/analyst.md`
- `calc_service/tests/test_wp_plugin_forms.py`

## Не-scope

- Переделка или аудит уже принятых 33 копий форм и `wp-plugin/forms/*.js` (замечания по текущим 6 чекбоксам в `syncUrl`, если среди них найдутся реальные баги, фиксировать строкой в «Найдено вне scope»).
- Изменение `AGENTS.md` (лимит 150 строк; достаточно правки skill, ролей и автотеста).
- Любые операции на проде (VDS, WordPress, плагин).

## Критерии приёмки

- [x] `Select-String -Path .cursor/skills/ezfc-form-to-api/verify.md -Pattern "REF_FORM_OPTIONS|матриц|материал"` — в `verify.md` описана матрица опций (все чекбоксы, radio, способы обработки/нанесения; не перебирать все материалы) и запрет оставлять опции формы в `js_port_gaps_allowed.txt` с аргументом «на дефолте не нужны».
- [x] `Select-String -Path .cursor/skills/ezfc-form-to-api/copy.md -Pattern "матриц|Опция|POST"` — в `copy.md` шаг 14 требует прогон всех опций матрицы на копии и таблицу результатов в отчёте.
- [x] `Select-String -Path docs/agents/roles/reviewer.md,docs/agents/roles/analyst.md -Pattern "опци|блокер|не нужен"` — в `reviewer.md` есть проверка полноты опций как `блокер`, в `analyst.md` уточнено назначение `Reviewer` для форм с опциями.
- [x] `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, новый тест на чекбоксы `syncUrl` ↔ `calcApi` проходит и падает при удалении передачи чекбокса в `calcApi` (подтвердить в «Результате»).
- [x] `python scripts/dev.py check` — зелёный вывод (`calc_service/tests` и `bot_service/tests`).

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет
- Цены: нет
- Формы: нет (правится только регламент для следующих переносов и контрактный тест)

## Режим

обычный

## Ревью 1

Не принято. Критерии Select-String, контрактный тест и состав diff выполнены; приёмку держит формулировка в `analyst.md`.

Проверено по diff `main` (незакоммиченные правки ветки) и командой:

- `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` → `12 passed in 1.24s`.
- Удаление `is_packing: isPacking` из тела `calcApi` в `button_pins.js` (проверка в памяти, файл не менялся) даёт `chkPacking` = не используется — тест падает, как записано в «Результате».
- `docs/dashboard.md` в diff — не замечание.
- Allowlist из 6 чекбоксов: `cards` / `embossing` в старом JS на цену не влияют; `tablets` уже в `scripts/js_port_gaps_allowed.txt`; `sticker` `chkMark` уже в «Найдено вне scope». Полный `python scripts/dev.py check` в этой сессии не перезапускался: вывод Implementer (`907 passed`, `81 passed`) принят, расчёт и `bot_service` diff не трогает.

### блокер

`docs/agents/roles/analyst.md`, правило `Reviewer: не нужен`. Фраза «только простые копии форм» относится и к быстрому треку: по ней Analyst назначает Reviewer на смену цены в JSON, мелкий баг и правку доков. В `AGENTS.md` быстрый трек по-прежнему без Reviewer; `AGENTS.md` в не-scope, его не менять. Сузить нужно только копии и переносы форм: без чекбоксов `ckb*`/`chk*` и без ветвлений способов нанесения/резки/обработки — `Reviewer: не нужен`; с опциями или ветвлениями — назначать. Быстрый трек, который не является такой формой, оставить без Reviewer.

### желательно

- `test_sync_url_checkboxes_reach_calc_api` считает чекбокс переданным в `calcApi`, если имя переменной встретилось где угодно вне объявления и вне текущего `syncUrl`. Постороннее `var echoPack = isPacking` оставляет тест зелёным после удаления поля из тела `calcApi`. В `print_sheet.js` удаление `option_numbering: isNumber` только из второй ветки не роняет `ckbNumber`: то же имя видно в `calcApi` первой ветки. Имеет смысл смотреть вхождение в аргументе своего `insaincalc.calcApi(`.
- `verify.md`, шаг 3, последняя фраза по-прежнему «Форму не дублировать до совпадения дефолта» — для матрицы логично «до совпадения дефолта и строк `REF_FORM_OPTIONS`».

### вне scope

Новых нет. `sticker.js` `chkMark` уже записан в «Найдено вне scope».

## Ревью 2

Принято. Блокер «Ревью 1» снят. Статус остаётся `ревью`, дальше человек: слияние.

Проверен diff после прошлого круга: в `docs/agents/roles/analyst.md` относительно `main` одна строка правила `Reviewer`. Остальной diff ветки (skill, `reviewer.md`, `docs/ezfc-api-migration.md`, `test_wp_plugin_forms.py`) в круг 1 уже был принят; `docs/dashboard.md` — не замечание.

Новая формулировка закрывает блокер:

- быстрый трек, который не является переносом или правкой формы, остаётся без Reviewer (цена в JSON, мелкий баг, доки, правила);
- поточный трек при `Сложность: низкая`, включая простые копии и переносы без чекбоксов `ckb*`/`chk*` и без ветвлений способов нанесения/резки/обработки, — `Reviewer: не нужен`;
- копии и переносы форм ezFC с чекбоксами или такими ветвлениями — `Reviewer` обязателен.

Пункты `желательно` из «Ревью 1» не правились и сдачу не держат: тест по-прежнему считает чекбокс переданным, если имя переменной есть где угодно вне объявления и вне текущего `syncUrl`; в `verify.md` шаг 3 по-прежнему заканчивается «Форму не дублировать до совпадения дефолта».

`python scripts/dev.py check` в этой сессии не перезапускался: круг меняет только формулировку роли и файл задачи, вывод Implementer (`calc_service/tests`: `907 passed`, `bot_service/tests`: `81 passed`) принят.

## Журнал передач

- 27.11.2026 — Analyst — задача оформлена по разбору возвратов на `form-tablets`, `form-magnet-laminated`, `form-badge`, `form-notebook` — дальше Implementer
- 27.11.2026 — Implementer — дополнены регламенты (verify.md, copy.md, ezfc-api-migration.md, reviewer.md, analyst.md) и добавлен контрактный тест чекбоксов `syncUrl` ↔ `calcApi` в `test_wp_plugin_forms.py` — дальше Reviewer
- 27.11.2026 — Reviewer — ревью 1: не принято, блокер в `analyst.md` (формулировка «только простые копии» снимает «Reviewer: не нужен» с быстрого трека) — дальше Implementer
- 27.11.2026 — Implementer — доработка по «Ревью 1»: в `docs/agents/roles/analyst.md` правило `Reviewer: не нужен` сохранено для быстрого и поточного треков и сужено только для копий/переносов форм ezFC с чекбоксами или ветвлениями; прогнан `python scripts/dev.py check` — дальше Reviewer
- 27.11.2026 — Reviewer — ревью 2: принято, блокер в `analyst.md` снят (быстрый трек без формы остаётся без Reviewer; копии и переносы с чекбоксами или ветвлениями — с Reviewer) — дальше человек: слияние
- 27.11.2026 — человек — принято — закрытие

## Найдено вне scope

- `wp-plugin/forms/sticker.js` (форма 22): `chkMark` пишется в `syncUrl` с комментарием «в API стикера нет» и не уходит в `calcApi`, хотя в `calc_service/calculators/sticker.py` параметр `is_find_mark` обрабатывается (и передаётся формой 29), но отсутствует в `tool_schema`.

## Результат

- Ветка, PR или коммит: `task/ezfc-options-testing-rules`
- Период: 27.11.2026
- Часы человека: —
- Работа агентов: Implementer — Gemini 4 Hydrogen High (2 сессии); Reviewer — Grok 4.7 (2 круга)
- Было / стало: в регламенте перевода форм проверялся в основном дефолт (из-за чего опции терялись по дороге на `form-tablets`, `form-magnet-laminated`, `form-badge`, `form-notebook`), а чекбоксы в `syncUrl` мимо `calcApi` не отслеживались тестом / добавлена обязательная матрица опций (`REF_FORM_OPTIONS`), таблица прогона на копии, сверка опций в `reviewer.md`, уточнение `Reviewer: не нужен` в `analyst.md` и контрактный тест `test_sync_url_checkboxes_reach_calc_api` в `test_wp_plugin_forms.py`.
- Сделано:
  - `.cursor/skills/ezfc-form-to-api/verify.md`: в шаге 0 запрещено оставлять живые ценовые опции переводимой формы в `scripts/js_port_gaps_allowed.txt` с аргументом «на дефолте не нужны»; добавлен шаг 1б с матрицей опций one-factor-at-a-time (`100%` чекбоксов `ckb*`/`chk*`, `100%` radio `rdo*`, `100%` вариантов dropdown способов нанесения/резки/обработки/сложности с зависимыми полями; без перебора всех материалов — достаточно дефолта + 1 альтернативы) и фиксацией `REF_FORM_OPTIONS` в `test_<slug>.py`; шаги 2 и 3 расширены на все строки `REF_FORM_OPTIONS`.
  - `.cursor/skills/ezfc-form-to-api/copy.md`: в шаге 14 добавлен обязательный прогон матрицы опций на копии с проверкой тела `POST /api/v1/calc/<slug>`, цены и срока, а в шаге 16 — таблица `| Опция | Параметр в POST | Цена JS/API | Цена на копии | Срок |`.
  - `docs/ezfc-api-migration.md`: раздел «Чеклист перевода» синхронизирован с проверкой матрицы опций формы без перебора всех материалов.
  - `docs/agents/roles/reviewer.md`: добавлена обязательная сверка полноты опций формы (шаги 5/5б vs `forms/<slug>.js` vs `REF_FORM_OPTIONS` vs таблица `Site ops`), пропуск живой ценовой опции без пометки «только URL» — `блокер`, браузер повторно не запускается.
  - `docs/agents/roles/analyst.md`: правило `Reviewer: не нужен` сохранено для быстрого трека (кроме переноса/правки форм с опциями или ветвлениями) и поточного трека (`Сложность: низкая`, включая простые копии и переносы форм ezFC без чекбоксов `ckb*`/`chk*` и без ветвлений способов нанесения/резки/обработки); для копий и переносов форм с такими опциями или ветвлениями обязательно назначать `Reviewer`.
  - `calc_service/tests/test_wp_plugin_forms.py`: добавлен `SYNC_URL_ONLY_CHECKBOXES` (6 существующих полей с причинами) и тест `test_sync_url_checkboxes_reach_calc_api`, проверяющий каждый `ckb*`/`chk*` в `insaincalc.syncUrl({...})` по всем `wp-plugin/forms/*.js`.
- Чем проверено:
  - `Select-String` по `verify.md`, `copy.md`, `reviewer.md`, `analyst.md` — все ключевые секции найдены.
  - `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` → `12 passed in 1.36s`.
  - Негативная проверка `test_sync_url_checkboxes_reach_calc_api` (временное удаление `is_packing: isPacking,` в `wp-plugin/forms/button_pins.js`, затем восстановление): `1 failed` с `AssertionError: button_pins.js: чекбокс chkPacking (isPacking ? 0 : '') есть в syncUrl, но не участвует в calcApi`.
  - `python scripts/dev.py check` → зелёный вывод (пересборка `docs/dashboard.md`; `calc_service/tests`: `907 passed in 63.26s`; `bot_service/tests`: `81 passed in 0.98s`).
- Не сделано и почему: не коммитил и не пушил (по регламенту работы субагента — после ревью и выбора человека); пункты `желательно` из «Ревью 1» не трогались, так как сдачу не держат.
- Требуется решение: ревью 2 принято, статус `ревью`; дальше человек — слияние в `main`. Пункты `желательно` из «Ревью 1» сдачу не держат.
