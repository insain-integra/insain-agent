# ezfc-options-testing-rules

Статус: черновик
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

- [ ] `Select-String -Path .cursor/skills/ezfc-form-to-api/verify.md -Pattern "REF_FORM_OPTIONS|матриц|материал"` — в `verify.md` описана матрица опций (все чекбоксы, radio, способы обработки/нанесения; не перебирать все материалы) и запрет оставлять опции формы в `js_port_gaps_allowed.txt` с аргументом «на дефолте не нужны».
- [ ] `Select-String -Path .cursor/skills/ezfc-form-to-api/copy.md -Pattern "матриц|Опция|POST"` — в `copy.md` шаг 14 требует прогон всех опций матрицы на копии и таблицу результатов в отчёте.
- [ ] `Select-String -Path docs/agents/roles/reviewer.md,docs/agents/roles/analyst.md -Pattern "опци|блокер|не нужен"` — в `reviewer.md` есть проверка полноты опций как `блокер`, в `analyst.md` уточнено назначение `Reviewer` для форм с опциями.
- [ ] `python -m pytest calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, новый тест на чекбоксы `syncUrl` ↔ `calcApi` проходит и падает при удалении передачи чекбокса в `calcApi` (подтвердить в «Результате»).
- [ ] `python scripts/dev.py check` — зелёный вывод (`calc_service/tests` и `bot_service/tests`).

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет
- Цены: нет
- Формы: нет (правится только регламент для следующих переносов и контрактный тест)

## Режим

обычный

## Журнал передач

- 27.11.2026 — Analyst — задача оформлена по разбору возвратов на `form-tablets`, `form-magnet-laminated`, `form-badge`, `form-notebook` — дальше Implementer

## Найдено вне scope

-

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
