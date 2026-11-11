# flag-materials-size-mm

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: предпосылка `form-flag` — шаг 3а skill `ezfc-form-to-api`; без `size_mm` в API копия 55 не покажет размеры в `showResult`.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

На дефолте боевой формы 55 (100 шт., 200×99 мм, `PaperCoated115M`, `4+0`, mode 1) ответ `POST /api/v1/calc/flag` содержит в `materials` те же размеры, что старый JS на странице: бумага `320×450`, скобы `6×0`, трубочка `5×380`. Поля `cost`, `price`, `time_ready` не меняются.

## Контекст и ссылки

- Блокер — `todo/form-flag.md`, журнал 2026-11-11, шаг 3а `.cursor/skills/ezfc-form-to-api/verify.md`.
- Образец починки — закрытая `pennant-materials-size-mm` (`docs/history/log.md` 2026-11-11): `pennant._material_out`, `calc_set_rope` в `common/process_tools.py`.
- Гипотеза Implementer: `flag.py` 205–229 не копирует `size_mm` из печати; `calc_set_staples` / `calc_set_shaft` не пишут размер из каталога (`Staples26_6`, `PlasticShaft380`).
- Эталон задачи формы — `REF_PARAMS` в `calc_service/tests/test_calculators/test_flag.py` (`price` 3934.410784).
- Дефолт формы 55: quantity 100, width 200, height 99, material `PaperCoated115M`, color `4+0`, mode 1 — `price` раннера/API 4052.296608, `time_ready` 9.442 (отчёт `form-flag`, 11.11.2026).
- Остальное не открывать.

## Scope

- В git (Implementer): прокинуть `size_mm` в ответ `flag` и в материалы `calc_set_staples` / `calc_set_shaft` по образцу `calc_set_rope`; тесты с assert на размеры и на неизменность `price` эталона и дефолта.
- На проде (Site ops): после merge в `main` и зелёного CI — skill `deploy-api`; smoke `POST /api/v1/calc/flag` на дефолте формы 55 — в теле есть `size_mm` у трёх позиций, `price` как до выкатки.

## Файлы

- `calc_service/calculators/flag.py`
- `calc_service/common/process_tools.py`
- `calc_service/tests/test_calculators/test_flag.py`
- `calc_service/tests/test_process_tools.py` — при правке assert на скобы/палочку
- Сосед: `calc_service/tests/test_calculators/test_notebook.py` — только прогон, файл не менять без падения

## Не-scope

- `wp-plugin/`, копия формы 55, `todo/form-flag.md` (кроме снятия «ждёт» при close).
- `calc_service/data/`, цены и наценки.
- Подстановка размеров в `forms/flag.js`.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.

- [x] Эталон `REF_PARAMS`: `price` и `time_ready` rel ≤ 0.001 к значениям до правки (3934.410784, 9.406).

```powershell
python -m pytest calc_service/tests/test_calculators/test_flag.py::test_expected_values_flag -q
```

- [x] Дефолт формы 55: в тесте `REF_FORM_DEFAULT` / assert на `size_mm` — `PaperCoated115M` `[320, 450]`, `Staples26_6` `[6, 0]`, `PlasticShaft380` `[5, 380]`; `price` 4052.296608 (rel ≤ 0.001).

```powershell
python -m pytest calc_service/tests/test_calculators/test_flag.py -q -k "form_default or size_mm or materials"
```

- [x] Сосед `notebook` не сдвинулся по эталонам.

```powershell
python -m pytest calc_service/tests/test_calculators/test_notebook.py -q
```

- [x] Тест падает без правки: откат только `flag.py` и фрагмента `process_tools` — новые кейсы `failed`, старый эталон `passed`; после возврата правки — снова `passed`.

- [ ] Боевой API после деплоя на дефолте — три `size_mm`, `price` 4052.296608 (rel ≤ 0.001).

```powershell
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/flag -ContentType 'application/json' -Body '{"quantity":100,"width_mm":200,"height_mm":99,"material_id":"PaperCoated115M","color":"4+0","mode":1}' | ConvertTo-Json -Depth 6
```

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: деплой API меняет JSON ответа у всех вызовов `flag` (и материалы у `calc_set_staples` в `notebook`); цены не должны сдвинуться.
- Цены: JSON не трогать.
- Формы: боевую 55 не менять.

## Режим

обычный

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

2026-11-11 — Analyst, Grok 4.7 — задача заведена, `form-flag` ждёт — дальше Implementer
2026-11-11 — Implementer, Grok 4.7 — `size_mm` у бумаги, скоб и трубочки, цены эталона и дефолта на месте — дальше Reviewer
2026-11-11 — Reviewer, Auto — принято — дальше человек (merge), затем Site ops
2026-11-12 — человек — принято, слияние в `main` — дальше Site ops (`deploy-api`, smoke)

## Ревью 1

принято

Проверено по uncommitted diff ветки `task/flag-materials-size-mm` (коммита нет) и прогоном тестов в worktree.

- Diff в scope: `flag.py` (`_material_out` как в `pennant`), `process_tools` (`calc_set_staples` / `calc_set_shaft` как `calc_set_rope`), `test_flag.py`, `test_process_tools.py`; `docs/dashboard.md` от задачи — ок. `test_notebook.py` и `calc_service/data/` не в diff.
- Эталон `REF_PARAMS`: `price` 3934.410784, `time_ready` 9.406; `test_expected_values_flag` — 1 passed (rel 0.001).
- Дефолт формы 55: `PaperCoated115M` `[320, 450]`, `Staples26_6` `[6, 0]`, `PlasticShaft380` `[5, 380]`; `price` 4052.296608, `time_ready` 9.442; `test_form_default_materials_size_mm` — 1 passed.
- Сосед notebook: файл не менялся; `test_notebook.py` — 6 passed.
- `TestSetStaples` / `TestSetShaft` — 2 passed.
- Боевой API — вне этого ревью (после merge + deploy).

## Найдено вне scope

- Пусто.

## Результат

- Ветка, PR или коммит: `task/flag-materials-size-mm`, слита в `main` 2026-11-12 (fast-forward)
- Период: 2026-11-11
- Часы человека:
- Работа агентов: Implementer, Grok 4.7, одна сессия
- Было / стало: в `materials` дефолта формы 55 не было `size_mm` у бумаги, скоб и трубочки; стало `PaperCoated115M` `[320, 450]`, `Staples26_6` `[6, 0]`, `PlasticShaft380` `[5, 380]`. `price` эталона 3934.410784 и дефолта 4052.296608, `time_ready` 9.406 и 9.442.
- Сделано: `flag._material_out` копирует `size_mm` из печати, скоб и палочки; `calc_set_staples` и `calc_set_shaft` пишут размер из каталога, как `calc_set_rope`. Тесты на размеры и неизменность цены.
- Чем проверено: pytest эталона (`1 passed`), дефолта (`1 passed, 7 deselected`), скоб и палочки (`2 passed`), `test_notebook.py` (`6 passed`). Откат `flag.py` и `process_tools.py`: `3 failed, 7 passed` (`KeyError: size_mm` у трёх новых кейсов, эталон в семёрке `passed`); после возврата дефолт и палочка снова `passed`. `python scripts/dev.py check` — код 0: calc_service `543 passed`, bot_service `81 passed`.
- Не сделано и почему: боевой API — после ревью, merge в `main` и зелёного CI (Site ops, skill `deploy-api`). Коммит не делался.
- Требуется решение: нет. Слияние — после вердикта Reviewer.
