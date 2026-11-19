# mode-logic-and-checks

Статус: выкатка
Сложность: высокая
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: единые правила и контрактный тест для `mode` + правка skills/доков и исправление багов `max(1, mode.value)` в уже используемых на API калькуляторах с деплоем.

## Цель

Логика режимов `ProductionMode` (`0` — эконом, `1` — стандарт, `2` — экспресс) и её исключения формализованы, проверяются автоматическим контрактным тестом в `make check`, встроены в регламенты создания и переноса калькуляторов на API, а найденные баги `mode` в текущих калькуляторах исправлены и выкачены на прод.

## Контекст и ссылки

- `calc_service/calculators/base.py`, `calc_service/equipment/base.py`, `calc_service/calculators/_template.py`, `calc_service/calculators/laser.py` — `ProductionMode`, 1-based ловушка `EquipmentSpec.get_time_ready(mode)`.
- `calc_service/calculators/print_laser.py`, `print_offset.py`, `print_wide.py`, `pad_print.py`, `embossing.py`, `design.py` — баг `max(1, mode.value)` на `time_prepare` (не даёт снизить подготовку в режиме `0`).
- `calc_service/calculators/metal_pins.py`, `milling.py`, `cards.py`, `acrylic_prizes.py`, `plaque.py`, `common/process_tools.py` — исключения: подрядчики, логистика, многослойные/составные расчёты.
- `docs/migration-guide.md`, `docs/data-formats.md`, `calc_service/AGENTS.md` — документация и локальные правила ядра.
- `.cursor/skills/new-calculator/SKILL.md`, `.cursor/skills/ezfc-form-to-api/verify.md`, `todo/ai-calc-authoring-skill.md` — пайплайны нового калькулятора и перевода форм на API.
- `calc_service/tests/test_materials_contract.py`, `calc_service/tests/test_wp_plugin_forms.py`, `calc_service/tests/test_equipment.py` — образцы общих контрактных тестов.
- Остальное не открывать.

## Scope

- В git (Implementer):
  1. **Единые хелперы `mode`:** привести `EquipmentSpec.get_time_ready(mode)` в `calc_service/equipment/base.py` к `0, 1, 2` (обновить `laser.py`, `_template.py`, `test_equipment.py`) и добавить общие функции/методы (например, `apply_mode_defects(defect_rate, mode)` и `calc_time_prepare(base_prepare, mode)` / `pick_time_ready(times, mode)`), чтобы формула `mode` не дублировалась вручную.
  2. **Починка 6 калькуляторов с `max(1, mode.value)`:** заменить на честный `mode.value` (при `mode=0` подготовка = `0`, как в `js_legacy`) в `print_laser.py`, `print_offset.py`, `print_wide.py`, `pad_print.py`, `embossing.py`, `design.py`; проверить/уточнить `cards.py` (`time_prepare`), обновить их тесты (добавить эталоны/проверки на `mode=0` и `mode=2`).
  3. **Общий контрактный тест `calc_service/tests/test_mode_contract.py`:** прогон всех зарегистрированных `CALCULATORS` для `mode ∈ {0, 1, 2}`:
     - `time_ready(2) <= time_ready(1) <= time_ready(0)` и `time_hours(0) <= time_hours(1) <= time_hours(2)`;
     - `price(0) <= price(1) <= price(2)` (и строгое `price(0) < price(1) < price(2)` для собственного производства; явный задокументированный список исключений: подрядчики без вариативной цены — `offset_promo`, `cards`, `button_pins > 2000`, `plaque` и т.п.);
     - статическая/AST-проверка отсутствия `max(1, mode` в расчёте `time_prepare` и `mode or 1` при чтении режима.
  4. **Документация и skills:**
     - в `docs/migration-guide.md` и `docs/data-formats.md` прописать стандарт `mode` (0: `timePrepare * 0`, 1: базовый, 2: `timePrepare * 2` и `defects * 2`) и реестр исключений (подрядчики: `metal_pins`, `cards`, `offset_promo`, Амалит; логистика: `metal_pins`, `milling`; составные слои: `acrylic_prizes`, `print_sheet`, `tablets`);
     - в `.cursor/skills/new-calculator/SKILL.md` (шаги 5, 8) и `.cursor/skills/ezfc-form-to-api/verify.md` (шаги 1а, 2, 3) встроить обязательную проверку `mode=0, 1, 2` против JS/ТЗ при создании и переносе;
     - в `todo/ai-calc-authoring-skill.md` дописать требование уточнять в интервью тип исполнения (своё производство / подрядчик / логистика) и задавать логику `mode` по стандарту.
- На проде (Site ops): после слияния в `main` и зелёного CI — выкатка API по `.cursor/skills/deploy-api/SKILL.md` и smoke-проверка `mode=0, 1, 2` на затронутых калькуляторах (`print_laser`, `print_offset`, `print_wide`, `embossing`).

## Файлы

- `calc_service/calculators/base.py`
- `calc_service/calculators/_template.py`
- `calc_service/equipment/base.py`
- `calc_service/calculators/laser.py`
- `calc_service/calculators/print_laser.py`
- `calc_service/calculators/print_offset.py`
- `calc_service/calculators/print_wide.py`
- `calc_service/calculators/pad_print.py`
- `calc_service/calculators/embossing.py`
- `calc_service/calculators/design.py`
- `calc_service/calculators/cards.py`
- `calc_service/tests/test_mode_contract.py`
- `calc_service/tests/test_equipment.py`
- `calc_service/tests/test_calculators/test_*.py` (тесты затронутых калькуляторов)
- `docs/migration-guide.md`
- `docs/data-formats.md`
- `.cursor/skills/new-calculator/SKILL.md`
- `.cursor/skills/ezfc-form-to-api/verify.md`
- `todo/ai-calc-authoring-skill.md`

## Не-scope

- Перенос новых форм ezFC, правка `wp-plugin/forms/*.js`, админки WordPress.
- Изменение `presswall.py` (отдельная задача `todo/presswall-banner-mode.md`).
- Изменение цен, коэффициентов `defect_table` и `baseTimeReady` в `calc_service/data/*.json`.
- Изменение `calc_service/calculators/notebook.py` (в `закрытии` по `form-notebook` (закрыто 2026-11-19, `docs/history/log.md`)).

## Критерии приёмки

- [x] `python -m pytest calc_service/tests/test_mode_contract.py calc_service/tests/test_equipment.py -q` — `passed`, `failed` нет; контракт проверяет все калькуляторы `CALCULATORS` и ловит `max(1, mode.value)`.
- [x] `Select-String -Path calc_service\calculators\*.py,calc_service\common\process_tools.py -Pattern "max\(1,\s*mode"` — в расчётах `time_prepare` совпадений нет (допустимо только для логистики, например `milling.py` при `mode >= 1`).
- [x] `node scripts/run_js_calc.mjs calcEmbossing --data current --args '[500,[50,30],"","foil","diary",[],{"isCliche":true},0]'` и аналогичный вызов `POST /api/v1/calc/embossing` с `mode=0` — `price` и `time_ready` совпадают с JS (`rel <= 0.001`). То же для `print_laser`, `print_offset`, `print_wide` на `mode=0`.
- [x] В `docs/migration-guide.md`, `.cursor/skills/new-calculator/SKILL.md` и `.cursor/skills/ezfc-form-to-api/verify.md` зафиксированы стандарт `mode`, исключения (подрядчики/логистика) и проверка `mode=0, 1, 2`.
- [ ] После выкатки на прод: `Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/embossing ...` для `mode=0, 1, 2` отдаёт `price(0) < price(1) < price(2)` и `time_ready(2) < time_ready(1) < time_ready(0)`.

## Проверки

- [x] `python scripts/dev.py check` — зелёный вывод (все тесты `calc_service` и `bot_service` `passed`)
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: исправление `max(1, mode.value)` снизит цену/время в `mode=0` для `embossing`, `print_offset`, `print_wide`, `print_laser`, `pad_print`, `design` (приведёт в соответствие с `js_legacy`); требуется деплой API на прод с `main`.
- Цены: JSON цен не меняются, обновляются только эталоны `mode=0` в затронутых тестах под актуальный `js_legacy`.
- Формы: пересечение в списке файлов с отложенными `todo/form-pad-print.md`, `todo/form-vizitki-promo.md`, `todo/ai-calc-authoring-skill.md` — при параллельном старте тем веткам потребуется `git rebase main` после слияния.

## Режим

прод

## Журнал передач

- 19.11.2026 — Analyst, Gemini 4 Hydrogen — оформлена задача по логике `mode`, хелперам, контрактным тестам, skills и починке 6 багов с деплоем — дальше Implementer
- 20.11.2026 — Implementer, Gemini 4 Neon — реализованы хелперы `mode` (`parse_mode`, `calc_time_prepare`, `apply_mode_defects`, `pick_time_ready`), 0-based `EquipmentSpec.get_time_ready`, починены 6 калькуляторов с `max(1, mode.value)` (+ проверен `cards.py`), добавлен контрактный тест `test_mode_contract.py`, обновлены доки/skills/`todo/ai-calc-authoring-skill.md`; `python scripts/dev.py check` зелёный (722 + 81 passed) — дальше Reviewer
- 20.11.2026 — Reviewer, Grok 4.7 — ревью 1: принято, блокеров нет; хелперы 0-based, починка 6 калькуляторов и `cards.py`, контракт на 42 `CALCULATORS`, доки и skills на месте; pytest затронутых тестов 161 passed, JS `mode=0/2` для `embossing` / `print_laser` / `print_offset` / `print_wide` с `rel ≤ 0.001` — дальше человек (слияние и выкатка)
- 20.11.2026 — человек — принято с правкой «желательно» про `metal_pins` в `docs/data-formats.md`, затем слияние, push и выкатка API — дальше Implementer
- 20.11.2026 — Implementer, Gemini 4 Neon — поправлено замечание из Ревью 1 в `docs/data-formats.md` (`metal_pins` убран из группы подрядчиков без вариативной цены и описан как подрядчик с вариативной ценой/тарифом доставки Китай→РФ и `timePrepare * mode`); `python scripts/dev.py check` зелёный (722 + 81 passed) — дальше слияние, push и выкатка API (Site ops)

## Ревью 1

Итог: **принято**. Блокеров нет. Статус остаётся `ревью` (критерий smoke на проде — шаг Site ops после слияния, не блокер этого круга).

Сверено с diff и командами:

- Scope: правки в хелперах (`calculators/base.py`, `equipment/base.py`), `laser.py`, `_template.py`, шести калькуляторах с `max(1, mode.value)`, `cards.py`, их тестах, `test_mode_contract.py`, `test_equipment.py`, `docs/migration-guide.md`, `docs/data-formats.md`, skills и `todo/ai-calc-authoring-skill.md`. `presswall.py`, `notebook.py` и JSON цен не менялись. `docs/dashboard.md` в diff — пересборка `make check`, не замечание.
- `EquipmentSpec.get_time_ready` переведён на индекс `0, 1, 2`; в `laser.py` убран `mode.value + 1`. Вызовы `get_time_ready` в `print_offset.py` и `print_wide.py` уже были 0-based и остаются согласованными.
- `cards.py`: как в `calcCards.js`, `time_prepare` и цена не зависят от `mode`, `time_ready` берётся из `baseTimeReady` `[56, 40, 32]`.
- Контрактный тест покрывает все 42 ключа `CALCULATORS`, монотонность `time_hours` / `time_ready` / `price`, отдельные ветки `offset_promo`, `button_pins > 2000`, `rollup` без полотна и AST-запрет `max(1, mode...)` (кроме `milling.py` → `cost_ship`) и `mode or 1`.
- `python -m pytest calc_service/tests/test_mode_contract.py calc_service/tests/test_equipment.py` и тесты затронутых калькуляторов плюс `test_laser.py` — `161 passed in 22.84s`, падений нет.
- `Select-String -Pattern "max\(1,\s*mode"` по `calc_service/calculators/*.py` и `process_tools.py` — единственное совпадение `milling.py:312` (`cost_ship`, логистика).
- Раннер `node scripts/run_js_calc.mjs --data current` против `execute()` на `mode=0` и `mode=2`: `embossing`, `print_offset`, `print_wide` — `rel=0`; `print_laser` — `rel_price` 0.000093 / 0.000188, `rel_ready` 0.000589 / 0 (`≤ 0.001`).

Замечания:

- `желательно` — в `docs/data-formats.md` `metal_pins` стоит в группе «подрядчики без вариативной цены». На кейсе 100 шт. цена меняется: `20757` / `27615` / `34888` (тариф Китай→РФ и `timePrepare * mode`). В `docs/migration-guide.md` и в контракте (строгое неравенство, `metal_pins` не в исключениях) это описано верно. Сдачу не держит.

## Найдено вне scope

- `calc_service/tests/test_calculators/test_print_offset.py`: `EXPECTED_REF.price` = `14108.116` при фактической цене `14450.546` на том же `REF_PARAMS` и `mode=1`. Старый assert проходит только из-за `rel=0.03`. Цена от этой правки не менялась (`timePrepare=0`). Точное значение уже зафиксировано в `test_print_offset_modes_match_js`.

## Результат

- Ветка, PR или коммит: `task/mode-logic-and-checks` (worktree `..\insain-agent-mode-logic-and-checks`, без коммита — ревью 1 принято, ждёт человека)
- Период: 20.11.2026
- Часы человека: —
- Работа агентов: Analyst (Gemini 4 Hydrogen), Implementer (Gemini 4 Neon), Reviewer (Grok 4.7)
- Было / стало:
  - Было: 1-based `EquipmentSpec.get_time_ready(mode)` (требовал `mode.value + 1` в `laser.py`), 6 калькуляторов зажимали подготовку через `max(1, mode.value)` (в `mode=0` цена и время совпадали со стандартом вопреки `js_legacy`), отсутствовал общий контрактный тест режимов и единый регламент `mode` в доках/skills.
  - Стало: единые 0-based хелперы `parse_mode`, `calc_time_prepare`, `apply_mode_defects`, `pick_time_ready` в `calculators/base.py` и 0-based `EquipmentSpec.get_time_ready(mode)`; 6 калькуляторов (`print_laser`, `print_offset`, `print_wide`, `pad_print`, `embossing`, `design`) считают `time_prepare` честно через `mode.value` (совпадение с `js_legacy`, `rel <= 0.001`), подтверждено подрядное поведение `cards.py`; контрактный тест `calc_service/tests/test_mode_contract.py` покрывает все 42 `CALCULATORS` и AST-проверкой ловит `max(1, mode...)` и `mode or 1`; стандарт и исключения зафиксированы в `docs/migration-guide.md`, `docs/data-formats.md`, `.cursor/skills/new-calculator/SKILL.md`, `.cursor/skills/ezfc-form-to-api/verify.md`, `todo/ai-calc-authoring-skill.md`.
- Сделано:
  - `calc_service/calculators/base.py`: добавлены `parse_mode`, `calc_time_prepare`, `apply_mode_defects`, `pick_time_ready`.
  - `calc_service/equipment/base.py`, `calc_service/calculators/laser.py`, `calc_service/calculators/_template.py`, `calc_service/tests/test_equipment.py`: `EquipmentSpec.get_time_ready(mode)` переведён на 0-based (`0, 1, 2`), убран костыль `mode.value + 1` в `laser.py`.
  - `calc_service/calculators/print_laser.py`, `print_offset.py`, `print_wide.py`, `pad_print.py`, `embossing.py`, `design.py`: убран `max(1, mode.value)`, переведены на единые хелперы `mode`; проверен `cards.py` (подрядчик: `time_prepare` и цена фиксированы как в `calcCards.js`, меняется только `time_ready`), обновлён на `parse_mode` / `pick_time_ready`.
  - `calc_service/tests/test_mode_contract.py`: контрактный тест всех 42 `CALCULATORS` на `mode ∈ {0, 1, 2}`, проверка подрядных веток (`offset_promo`, `button_pins > 2000`, `rollup` без полотна) и AST-проверка отсутствия `max(1, mode...)` (кроме логистики `milling.py → cost_ship`) и `mode or 1`.
  - `calc_service/tests/test_calculators/test_{embossing,print_laser,print_offset,print_wide,pad_print,design,cards}.py`: добавлены эталоны/проверки на `mode=0` и `mode=2`.
  - `docs/migration-guide.md`, `docs/data-formats.md`, `.cursor/skills/new-calculator/SKILL.md`, `.cursor/skills/ezfc-form-to-api/verify.md`, `todo/ai-calc-authoring-skill.md`: описан стандарт `mode`, реестр исключений и обязательная проверка `mode=0, 1, 2`.
- Чем проверено:
  - `python -m pytest calc_service/tests/test_mode_contract.py calc_service/tests/test_equipment.py -q` → `66 passed in 13.73s`
  - `Select-String -Path calc_service\calculators\*.py,calc_service\common\process_tools.py -Pattern "max\(1,\s*mode"` → единственное совпадение `calc_service\calculators\milling.py:312: cost_ship *= max(1, mode.value)` (логистика)
  - Сверка `node scripts/run_js_calc.mjs` (`--data current`) vs `POST /api/v1/calc/<slug>` (FastAPI TestClient) на `mode=0`:
    - `embossing`: JS `13446.0 / 56.5`, API `13446.0 / 56.5` (`rel=0.000000`)
    - `print_laser`: JS `3658.3417 / 16.97`, API `3658.0 / 16.96` (`rel_p=0.000093`, `rel_r=0.000589`)
    - `print_offset`: JS `14450.546 / 72`, API `14450.546 / 72.0` (`rel=0.000000`)
    - `print_wide`: JS `692.0 / 24.12`, API `692.0 / 24.12` (`rel=0.000000`)
  - `python scripts/dev.py check` → `calc_service/tests`: `722 passed in 55.69s`; `bot_service/tests`: `81 passed in 3.03s` (exit code 0)
- Не сделано и почему: выкатка API на прод и smoke-проверка `https://insain.ru/api/v1/calc/embossing` — этап `Site ops` после ревью, приёмки и слияния в `main`.
- Требуется решение: ревью 1 принято. Дальше человек — слияние `task/mode-logic-and-checks` в `main` и выкатка API (`Site ops`, smoke `mode=0, 1, 2` на `embossing`).
