# tests-plaque-poly-sticker-pack

Статус: черновик
Сложность: обычная
Implementer: Grok 4.7
Reviewer: Opus 5.5
Почему: только новые тесты в calc_service, без данных, прода, конфликта цен и правок правил.

## Цель

У калькуляторов `plaque` и `poly_sticker_pack` есть отдельные тесты в `calc_service/tests/test_calculators/`. Сейчас калькуляторы зарегистрированы в API, файлов тестов нет (BACKLOG I5).

## Контекст и ссылки

- `calc_service/calculators/plaque.py` — что считать: `execute` / `calculate`, ветка `noApplication`, `ValueError`.
- `calc_service/calculators/poly_sticker_pack.py` — параметры и `ValueError` при площади стикерпака ≤ 0.
- `calc_service/tests/test_calculators/test_poly_sticker.py` — образец набора тестов и эталона с допуском 3% (`_cmp`, `rel = 0.03`). Позитивные кейсы вызывать через `execute()`, чтобы в ответе был `share_url`.
- `calc_service/AGENTS.md` — обязательные поля ответа и `code` / `name` / `title` у каждого элемента `materials`. В базовом тесте образца `code` не проверяется; здесь проверять.
- Остальное не открывать. `docs/migration-guide.md`, JSON цен и `js_legacy/` не читать.

## Scope

Два новых файла, без правок калькуляторов:

- `calc_service/tests/test_calculators/test_plaque.py`
- `calc_service/tests/test_calculators/test_poly_sticker_pack.py`

В каждом файле, по образцу `test_poly_sticker.py`:

- `test_slug`
- `test_calculate_basic` — в ответе есть `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, `materials`; числа ≥ 0; у каждого элемента `materials` есть `code`, `name`, `title`
- `test_price_gte_cost`
- `test_share_url` — `share_url` содержит slug калькулятора
- `test_get_options`
- `test_get_tool_schema` — `name` равен `calc_plaque` или `calc_poly_sticker_pack`
- эталон `test_expected_values_*`: один прогон текущего `execute()` на фиксированных параметрах, ожидания записать в тест, сравнение `cost`, `price`, `time_hours`, `time_ready`, `weight_kg` с допуском 3%; материал с кодом запрошенного id (у plaque первый элемент — заготовка `plaque_id`)

Параметры позитивного прогона:

- plaque: `quantity` ≥ 1, `plaque_id` один из `Plaque2330` / `Plaque2025` / `Plaque1520`, `material_id` — код из `get_options()["materials"]`, `application=isUVPrint`, `mode=1`. В `get_options` есть ключи `plaques`, `materials`, `applications`, `modes`.
- poly_sticker_pack: `quantity=20`, `width=80`, `height=80`, `material_id=PaperCoated115M` (как в образце), остальные поля — значения по умолчанию из `get_tool_schema`. В `get_options` есть `materials` и `modes`.

Дополнительно к образцу, по веткам уже написанного `calculate`:

- plaque, `application=noApplication`: в `materials` только заготовка, `time_hours == 0`, `time_ready > 0`.
- plaque: `ValueError` при пустом `plaque_id`, пустом `material_id` и неизвестном `application`.
- poly_sticker_pack: `ValueError`, если `width * height <= 0`.

`pytest.skip`, если расчёт не выполнился, не использовать: такой кейс должен падать. Диагностический `print` допустим только в эталонном тесте, как в образце.

Если выбранный `material_id` даёт исключение, подставить другой код из `get_options()` и зафиксировать его в тесте. Калькулятор и JSON при этом не менять; если ни один код из опций не считается — остановиться и записать это в «Требуется решение».

## Не-scope

- Правки `plaque.py`, `poly_sticker_pack.py`, реестра калькуляторов, JSON цен и наценок.
- Сверка с `js_legacy/` и подгонка формул под старые числа.
- `test_poly_sticker.py` (там `pytest.skip` и в базовом тесте нет проверки `code`).
- `bot_service`, формы ezFC, WordPress, VDS.
- Новые калькуляторы C1–C11 из BACKLOG.

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_calculators/test_poly_sticker_pack.py -q` — код выхода 0, в итоге `passed` и `skipped` нет
- [ ] `python -m pytest calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_calculators/test_poly_sticker_pack.py --collect-only -q` — у каждого файла есть тесты slug, базового ответа, `price >= cost`, `share_url`, `get_options`, `get_tool_schema` и эталона; у plaque ещё `noApplication` и три `ValueError`; у poly_sticker_pack ещё `ValueError` при нулевой площади
- [ ] `git diff main --name-only` — изменены только `todo/tests-plaque-poly-sticker-pack.md`, `calc_service/tests/test_calculators/test_plaque.py`, `calc_service/tests/test_calculators/test_poly_sticker_pack.py`

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет
- Цены: нет правок JSON. Эталон записывает текущий результат расчёта; смена прайса позже уронит этот тест, как у соседних калькуляторов
- Формы: нет

## Режим

обычный

## Результат

Заполняет Implementer при сдаче.

- Ветка, PR или коммит: `task/tests-plaque-poly-sticker-pack` от `main`
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
