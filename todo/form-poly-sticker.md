# form-poly-sticker

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: калькулятор `poly_sticker` уже в API, пропусков `calcPolySticker` в `js_port_gaps_allowed.txt` нет; копия формы по skill `ezfc-form-to-api`.

## Цель

Копия формы 30 CalcPolySticker на черновике товара считает `POST /api/v1/calc/poly_sticker`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/naklejki-s-polimernoj-zalivkoj/ остаётся на `insaincalc.calcPolySticker`. В пакет `forms-batch-switch` форма 30 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента.
- `docs/site/forms.md` — строка формы 30, только читать.
- `calc_service/calculators/poly_sticker.py`, `calc_service/tests/test_calculators/test_poly_sticker.py`.
- `docs/js-runner-cases.md` — кейс `calcPolySticker` 80×80, price 4107.8, если он ещё подходит дефолту формы. Новый кейс в этот файл из ветки не писать: строка — в «Результат».
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и текст `wp-plugin/forms/poly_sticker.js` (`calcApi`, `syncUrl`, `showResult`, без своей цены). `REF_FORM_DEFAULT` в `test_poly_sticker.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Калькулятор не на боевой форме API. Если дефолт формы не сходится с раннером — чинить в этой ветке, эталоны соседей не сдвигать. Отдельную предпосылку не заводить.
- На проде (Site ops): дубль формы 30 на черновик после того, как дефолт совпал с боевым API. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую форму 30 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/poly_sticker.js`
- `calc_service/calculators/poly_sticker.py`
- `calc_service/tests/test_calculators/test_poly_sticker.py`
- WordPress: только копия формы 30 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/js_port_gaps_allowed.txt` (новые строки не добавлять)
- `sticker.py`, форма 70, боевая форма 30, выкладка плагина, JSON цен
- `calc_service/calculators/__init__.py` — slug уже зарегистрирован

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPolySticker` — в блоке `calcPolySticker` строка `нет в Python` пустая, либо каждый пропуск уже есть и в docstring модуля, и в `scripts/js_port_gaps_allowed.txt`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_poly_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. В тесте есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/poly_sticker` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера, допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001.
- [ ] `Select-String -Path wp-plugin\forms\poly_sticker.js -Pattern "calcApi\('poly_sticker'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/poly_sticker` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 30. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcPolySticker`, не `calcApi`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 30 не меняется. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Если дефолт не сходится — правка калькулятора в этой ветке, не новый прайс.
- Формы: id боевой 30 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4 — дальше Implementer

## Найдено вне scope

- 

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-19 —
- Часы человека: оценка 4 ч
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение: после приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
