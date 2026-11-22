# form-poly-sticker-pack

Статус: выкатка
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: калькулятор `poly_sticker_pack` уже в API, пропусков `calcPolyStickerPack` в `js_port_gaps_allowed.txt` нет; копия формы по skill `ezfc-form-to-api`.

## Цель

Копия формы 70 CalcPolyStickerPack на черновике товара считает `POST /api/v1/calc/poly_sticker_pack`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/stikerpaki-s-polimernoj-zalivkoj/ остаётся на `insaincalc.calcPolyStickerPack`. В пакет `forms-batch-switch` форма 70 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 70, только читать.
- `calc_service/calculators/poly_sticker_pack.py`, `calc_service/tests/test_calculators/test_poly_sticker_pack.py`.
- `docs/js-runner-cases.md` — кейс `calcPolyStickerPack` 80×80, price 6341.1. Новый кейс в этот файл из ветки не писать.
- `todo/EPIC-forms-to-api.md` — пачка 4. Это не форма 29 (`form-sticker-pack`, slug `sticker`).
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/poly_sticker_pack.js`. `REF_FORM_DEFAULT` в `test_poly_sticker_pack.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Калькулятор не на боевой форме API. Расхождение дефолта чинить в этой ветке, соседей не сдвигать. Предпосылку не заводить.
- На проде (Site ops): дубль формы 70 на черновик после совпадения дефолта с боевым API. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 70 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/poly_sticker_pack.js`
- `calc_service/calculators/poly_sticker_pack.py`
- `calc_service/tests/test_calculators/test_poly_sticker_pack.py`
- WordPress: только копия формы 70 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, новые строки в `scripts/js_port_gaps_allowed.txt`
- `poly_sticker.py`, `sticker.py`, форма 30, форма 29, боевая форма 70, выкладка плагина, JSON цен
- `calc_service/calculators/__init__.py`

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcPolyStickerPack` — в блоке `calcPolyStickerPack` строка `нет в Python` пустая, либо каждый пропуск уже есть и в docstring, и в `scripts/js_port_gaps_allowed.txt`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_poly_sticker_pack.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [ ] Боевой `POST /api/v1/calc/poly_sticker_pack` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Локально сходится; прод 22.11.2026: price 6407.8, time_ready 41.64 против раннера 6928.75 и 41.79.
- [x] `Select-String -Path wp-plugin\forms\poly_sticker_pack.js -Pattern "calcApi\('poly_sticker_pack'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `draft` или `private`, гость без cookies — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/poly_sticker_pack` → 200. Цена на странице = `price` API с округлением `showResult`.
- [ ] URL копии обновляется GET-именами формы 70. Ссылка с этими GET открывает те же значения и ту же цену.
- [ ] Боевая страница в HTML содержит `calcPolyStickerPack`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 70 не меняется. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять.
- Формы: id боевой 70 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4 — дальше Implementer
22.11.2026 — Implementer, Grok 4.7 — локально дефолт сходится с раннером, JS формы в git; боевой API старый

Блокер: копию формы 70 нельзя делать, пока боевой API не отдаёт дефолт раннера
Пробовал: POST https://insain.ru/api/v1/calc/poly_sticker_pack телом REF_FORM_DEFAULT — price 6407.8, time_ready 41.64. Раннер mode 1 — price 6928.75, time_ready 41.79. Локальный Python — price 6929.9 (rel 0.00017), time_ready 41.79. `python scripts/dev.py check` — код 0 (801 + 81 passed).
Гипотеза: на проде нет прокидки lamination_id и is_find_mark и нет брака рулонной ламинации по ceil(n/2). Калькулятор не на боевой форме API (на API только puzzle).
Вопрос: слить ветку и выкатить API до дубля формы или оставить правку только в ветке
Следующая сессия: человек, затем Site ops, модель Grok 4.7

Варианты:
1. Закоммитить task/form-poly-sticker-pack, слить в main, выкатить API, затем Site ops делает копию формы 70. (Рекомендуется)
2. Не сливать и не выкатывать: копию не создавать, задача ждёт отдельной выкатки.
3. Откатить lamination.py и делать копию на текущем проде: дефолт mode 1 будет 6900 против раннера 6928.75.
22.11.2026 — человек — закоммитить ветку, слить в main, выкатить API, затем копия формы 70 — дальше Site ops

## Найдено вне scope

- У эпоксидки в JS размер 0, в API у EpoxyPoly нет size_mm. Плёнка 320×450 и ламинация 330×0 в ответе есть.
- Ряды наклеек формы 71 в share-URL не пишутся: numW и numH совпадают с размером пака.
- Боевая страница на старом прайсе: cost 3721, раннер current 3734. Оба округляются до 7000.

## Результат

- Ветка, PR или коммит: ветка task/form-poly-sticker-pack, коммита нет
- Период: 2026-11-19 — 2026-11-22
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, сверка и JS
- Было / стало: форма 70 на insaincalc.calcPolyStickerPack. В git есть forms/poly_sticker_pack.js и эталон дефолта. Боевая страница не переключена. Копии нет.
- Сделано: порт без пропусков. REF_FORM_DEFAULT формы 70 (100×50×50, одна наклейка 20×20, RaflatacMW, фон, метки, Laminat32G, print_method No). В poly_sticker_pack прокинуты lamination_id и is_find_mark, эталон 80×80 не сдвинут. В lamination.py односторонняя рулонная ищет брак по ceil(n/2), как calcLamination.js; тесты sticker, poly_sticker и lamination остались зелёными. JS копии: calcApi, syncUrl, showResult, ряды наклеек через getElementsByClassName.
- Чем проверено: `python scripts/js_port_gaps.py calcPolyStickerPack` — `нет в Python` пусто. Раннер mode 1/0/2: price 6928.75 / 6372.15 / 8873.4, time_ready 41.79 / 57.6 / 26.32. Локальный калькулятор в допуске. pytest формы и `python scripts/dev.py check` — код 0. Select-String: три вызова есть, `querySelector` и `price =` нет. Боевой POST — price 6407.8, time_ready 41.64, не в допуске.
- Не сделано и почему: шаги 6–16 (дубль, черновик, отладка копии). Боевой API ещё без этой правки, дубль до совпадения дефолта нельзя. Плагин не выкладывался, боевая 70 не переключалась. `docs/js-runner-cases.md` из ветки не менялся.
- Поля не в calcApi: fluAtrwork (файл). lamination_id и is_find_mark в форме нет — их задаёт dpdPrint. print_method в API всегда No: боевой cjsCalc передаёт isPrint строкой, calcSticker ждёт .printerID, печать в цену не входит.
- GET для шага 10: `--get numN --get numW --get numH --get dpdMaterial:index --get dpdPrint:index --get chkBackground:index --get rdoModeProduction:value`
- Строка будущего пакета: форма 70 `poly_sticker_pack` после приёмки копии идёт в `forms-batch-2`, не в текущий `forms-batch-switch`. Id копии ещё нет.
- Требуется решение: выкатить API с этой ветки до дубля формы. После приёмки копии строка идёт в будущий `forms-batch-2`, не в текущий пакет.
