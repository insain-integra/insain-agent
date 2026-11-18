# mode-logic-and-checks

Статус: черновик
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
- Изменение `calc_service/calculators/notebook.py` (в `закрытии` по `todo/form-notebook.md`).

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_mode_contract.py calc_service/tests/test_equipment.py -q` — `passed`, `failed` нет; контракт проверяет все калькуляторы `CALCULATORS` и ловит `max(1, mode.value)`.
- [ ] `Select-String -Path calc_service\calculators\*.py,calc_service\common\process_tools.py -Pattern "max\(1,\s*mode"` — в расчётах `time_prepare` совпадений нет (допустимо только для логистики, например `milling.py` при `mode >= 1`).
- [ ] `node scripts/run_js_calc.mjs calcEmbossing --data current --args '[500,[50,30],"","foil","diary",[],{"isCliche":true},0]'` и аналогичный вызов `POST /api/v1/calc/embossing` с `mode=0` — `price` и `time_ready` совпадают с JS (`rel <= 0.001`). То же для `print_laser`, `print_offset`, `print_wide` на `mode=0`.
- [ ] В `docs/migration-guide.md`, `.cursor/skills/new-calculator/SKILL.md` и `.cursor/skills/ezfc-form-to-api/verify.md` зафиксированы стандарт `mode`, исключения (подрядчики/логистика) и проверка `mode=0, 1, 2`.
- [ ] После выкатки на прод: `Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/embossing ...` для `mode=0, 1, 2` отдаёт `price(0) < price(1) < price(2)` и `time_ready(2) < time_ready(1) < time_ready(0)`.

## Проверки

- [ ] `python scripts/dev.py check` — зелёный вывод (все тесты `calc_service` и `bot_service` `passed`)
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: исправление `max(1, mode.value)` снизит цену/время в `mode=0` для `embossing`, `print_offset`, `print_wide`, `print_laser`, `pad_print`, `design` (приведёт в соответствие с `js_legacy`); требуется деплой API на прод с `main`.
- Цены: JSON цен не меняются, обновляются только эталоны `mode=0` в затронутых тестах под актуальный `js_legacy`.
- Формы: пересечение в списке файлов с отложенными `todo/form-pad-print.md`, `todo/form-vizitki-promo.md`, `todo/ai-calc-authoring-skill.md` — при параллельном старте тем веткам потребуется `git rebase main` после слияния.

## Режим

прод

## Журнал передач

- 19.11.2026 — Analyst, Gemini 4 Hydrogen — оформлена задача по логике `mode`, хелперам, контрактным тестам, skills и починке 6 багов с деплоем — дальше Implementer

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
