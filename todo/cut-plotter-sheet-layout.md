# cut-plotter-sheet-layout

Статус: выкатка
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: предпосылка не-боевого порта по skill `port-fix-prerequisite` (разблокирует `form-sticker`); `Reviewer: Auto`, т.к. меняется ответ API; `Site ops` — выкатка API и smoke на проде по `deploy-api`.

## Цель

Листовая ветка `CutPlotterCalculator` раскладывает изделия на размер листа материала (`material.sizes`) с JS-порядком `margins` `[left, top, right, bottom]` и отдаёт `size_mm` в `materials`, а `CutPlotterCalculator` и `StickerCalculator` сходятся по `cost`, `price` и `time_ready` с JS-раннером (`--data current`) на дефолте формы 22 (`100` шт `50×50` `RAFLACOAT`, без печати) и на кейсе `50×50 VHI80 4+0`. `scripts/run_js_calc.mjs` запускает `calcCutPlotter` и `calcSticker`.

## Контекст и ссылки

- `.cursor/skills/port-fix-prerequisite/SKILL.md` — шаги 6–13.
- `todo/form-sticker.md` — блокер дефолта формы 22 (`price` и `time_ready` не сходятся, `size_mm` нет).
- `js_legacy/calc/calcCutPlotter.js:188–229, 256–259` и `js_legacy/calc/calcLayout.js:15–35` — раскладка по `setSizeMaterial`, порядок `margins` `[left, top, right, bottom]` (`[30, 10, 10, 10]`), `result.cost = Math.ceil(...)`, `result.time = Math.ceil(timeCut * 100) / 100`.
- `calc_service/calculators/cut_plotter.py:334–364, 396–403` и `calc_service/common/layout.py:14–24, 56–98` (`layout_on_sheet` принимает `[top, right, bottom, left]`).
- `js_legacy/calc/calcSticker.js:122–125` и `calc_service/calculators/sticker.py:388–395` (лишний `math.ceil(price_total)` при отсутствии округления до рубля в JS; см. `test_sticker.py:104`).
- `docs/js-runner-cases.md` — замороженный кейс `50×50 VHI80` (`sticker-vs-js`) и команды раннера.
- Остальное не открывать.

## Scope

- В git (Implementer, ветка `task/cut-plotter-sheet-layout` от `main`):
  1. `scripts/run_js_calc.mjs`: подключить `js_legacy/calc/calcCutPlotter.js`, `js_legacy/calc/calcSticker.js` и `js_legacy/equipment/plotter.json` (+ `calc_service/data/equipment/plotter.json` в `CURRENT_FILES` и `LEGACY_DATA` для `--data current`).
  2. `calc_service/calculators/cut_plotter.py`:
     - в листовой ветке перебирать `material.sizes` (при `material is None` — fallback на `max_plotter`), вызывать `layout_on_sheet` с перестановкой `margins` из JS `[left, top, right, bottom]` в формат `layout_on_sheet` `[top, right, bottom, left]`, выбирать размер листа с минимальной стоимостью материала (как `calcCutPlotter.js:214–219`);
     - `cost = math.ceil(...)`, в `materials_out` передавать `size_mm` (лист `[w, h]`, рулон `[roll_w, 0]`) через `material_line()`;
     - проверить `time_hours` (`math.ceil(time_cut * 100) / 100.0` vs `round`) так, чтобы сошлись листовые кейсы и не упали рулонные эталоны `test_cut_plotter.py`.
  3. `calc_service/calculators/sticker.py`: убрать `math.ceil(price_total)` на строке 394; при нескольких размерах листа брать выбранный `size_mm` из `cut_result["materials"]`.
  4. Эталоны с JS-раннера (`--data current`, пометка `# JS, ДД.ММ.ГГГГ`, `rel=0.001`):
     - `test_cut_plotter.py`: листовой кейс (`100` шт `50×50` `RAFLACOAT`, `size_item=50`, `mode=1`) + сохранение рулонных эталонов `Avery500c`;
     - `test_sticker.py`: `REF_FORM_DEFAULT` (`100` шт `50×50` `RAFLACOAT`, без печати, `size_item=50`, `mode=1` → раннер `--data current`: `cost 411.9`, `price 662.134`, `time_ready 16.2`, 3 листа `[320, 450]`) и пересъёмка `REF_PARAMS` (`100` шт `50×50` `VHI80`, `4+0`, `mode=1` → раннер `--data current`: `cost ~814.05`, `price ~1307.56`, `time_ready 16.39`, 4 листа `[297, 420]`);
     - соседи `test_poly_sticker.py` и `test_poly_sticker_pack.py`: переснять `EXPECTED_REF` и `quantity_approx` (`1 → 2` листа) с JS-раннера `--data current` (эталоны от `05.11.2026` снимались со сломанной раскладки `[603, 5000]`).
  5. Проверить падение новых кейсов без правки `cut_plotter.py` / `sticker.py` (шаг 9 skill `port-fix-prerequisite`) и прохождение `test_keychain.py`.
  6. `docs/js-runner-cases.md`: добавить команды раннера для `calcCutPlotter` и `calcSticker` (`RAFLACOAT` и `VHI80`), снять заметку о замороженном расхождении `50×50 VHI80` (`sticker-vs-js`).
- На проде (Site ops, после слияния в `main` и зелёного CI):
  - деплой API по skill `deploy-api` (`bash infra/deploy.sh`);
  - smoke `POST https://insain.ru/api/v1/calc/sticker` на дефолте `RAFLACOAT` и `50×50 VHI80 4+0` — `price` и `time_ready` равны раннеру (`abs <= 0.02`, `rel <= 0.001`), в `materials[0]` есть `size_mm`.

## Файлы

- `calc_service/calculators/cut_plotter.py`
- `calc_service/calculators/sticker.py`
- `scripts/run_js_calc.mjs`
- `calc_service/tests/test_calculators/test_cut_plotter.py`
- `calc_service/tests/test_calculators/test_sticker.py`
- `calc_service/tests/test_calculators/test_poly_sticker.py`
- `calc_service/tests/test_calculators/test_poly_sticker_pack.py`
- `docs/js-runner-cases.md`

## Не-scope

- Изменение `calc_service/common/layout.py` и других калькуляторов.
- Внедрение `time_del_film` (`is_del_film`), опции `isCarrier`, правка рулонной ветки `cut_plotter.py`.
- Широкоформатная печать/ламинация и `isFindMark` в `sticker.py`.
- Правка `calc_service/data/*.json` и курса USD на сайте `insain.ru/icalc/`.
- Форма 22 и `wp-plugin/forms/sticker.js` (`todo/form-sticker.md`).

## Критерии приёмки

- [x] `node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[100,[50,50],50,0,1,\"RAFLACOAT\",{},1]'` и `node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"RAFLACOAT\",{},1]'` — возвращают JSON без ошибок.
- [x] `python -m pytest calc_service/tests/test_calculators/test_cut_plotter.py calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_calculators/test_poly_sticker.py calc_service/tests/test_calculators/test_poly_sticker_pack.py calc_service/tests/test_calculators/test_keychain.py -q` — все `passed`, в `test_sticker.py` есть `REF_FORM_DEFAULT` и обновлённый `VHI80` с `# JS, ДД.ММ.ГГГГ`.
- [x] Откат `cut_plotter.py` и `sticker.py` (`git stash push -- calc_service/calculators/cut_plotter.py calc_service/calculators/sticker.py`) роняет новые кейсы `test_cut_plotter.py` / `test_sticker.py`, старые эталоны `Avery500c` проходят; после `git stash pop` всё `passed`.
- [x] `python scripts/dev.py check` — код выхода 0.
- [ ] После деплоя на прод (`deploy-api`): `POST https://insain.ru/api/v1/calc/sticker` на `RAFLACOAT` и `VHI80 4+0` совпадает с JS-раннером (`abs <= 0.02`, `rel <= 0.001`), в `materials[0]` есть `size_mm` (`[320, 450]` и `[297, 420]`).

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: меняет ответы `/api/v1/calc/cut_plotter`, `/api/v1/calc/sticker`, `/api/v1/calc/poly_sticker`, `/api/v1/calc/poly_sticker_pack` (и листовые расчёты > 1 листа в `/api/v1/calc/keychain`). Ни одна боевая форма и ни одна принятая копия на этих slug сейчас не работают (`docs/site/forms.md`).
- Цены: JSON не меняются; `insain.ru/icalc/calc/common.json` в браузере использует старый USD (`653.134`), API и `--data current` — `USD=95` из git (`662.134`).
- Формы: формы ezFC не меняются.

## Режим

прод

## Журнал передач

14.11.2026 — аналитик — оформлена предпосылка по блокеру `form-sticker` — дальше Implementer (Grok 4.7)
14.11.2026 — Implementer (Grok 4.7) — листовая раскладка, эталоны раннера 14.11.2026, pytest 43 passed, шаг 9: без правки 3 failed / Avery passed — дальше Reviewer (Auto)
14.11.2026 — Reviewer (Auto) — принято по working tree: локальные критерии закрыты, прод-критерий открыт для Site ops — дальше человек (слияние)
14.11.2026 — человек — принято, слияние и выкатка — дальше Site ops

## Ревью 1

принято

Сверка с working tree (`git diff`, коммита нет) и разделом «Результат»; модель сессии Auto ≠ Implementer Grok 4.7.

| Критерий | Итог |
| --- | --- |
| Раннер `calcCutPlotter` / `calcSticker` RAFLACOAT | OK: JSON без ошибок; cut `cost 357` `price 571` `time_ready 16.2`; sticker `cost 411.9` `price 662.134` `time_ready 16.2` |
| pytest + эталоны `# JS, 14.11.2026` | OK: 43 passed; `REF_FORM_DEFAULT`, обновлённый VHI80, листовой RAFLACOAT с `size_mm` |
| Шаг 9 (stash калькуляторов) | OK: без правки упали новые кейсы (sheet/form/VHI80), Avery500c прошли; после `stash pop` снова passed |
| `python scripts/dev.py check` | OK: код 0 (перепрогон Reviewer) |
| Прод deploy-api + smoke POST `/api/v1/calc/sticker` | не закрыт — Site ops после слияния в `main` |

Diff в scope: листовой перебор `material.sizes`, перестановка margins `[L,T,R,B]→[T,R,B,L]`, `cost=ceil(raw)`, `price` от raw, `size_mm` через `material_line`, у sticker снят `ceil(price_total)` и берётся `size_mm` из резки, раннер + plotter.json, эталоны соседей, `js-runner-cases.md`. `layout.py` и JSON цен не тронуты. Остатки `print_laser` / вес эпоксидки — в «Найдено вне scope», не блокеры.

## Найдено вне scope

- `print_laser.py`: время `round` вместо JS `Math.ceil` — `poly_sticker` time_hours 0.88 против раннера 0.89, стикерпак 1.79 против 1.8. `price` там ещё `int(...)`, из-за этого стикер VHI80 1307.28 против 1307.5632666666668 (внутри rel 0.001).
- Вес эпоксидки в `common/process_tools.py` округляется `round`: стикерпак 0.19 кг против раннера 0.2. На цену не влияет.
- `calcCutPlotter` в JS не заполняет `weight` (раннер 0); Python на RAFLACOAT считает 0.0475 кг. В эталон резки вес не входил.

## Результат

- Ветка, PR или коммит: ветка `task/cut-plotter-sheet-layout`, коммита нет
- Период: 2026-11-14 — 2026-11-14
- Часы человека: оценка 1 ч на коммит задачи
- Работа агентов: 1 сессия; Grok 4.7
- Было / стало: листовая резка клала изделия на max_plotter [603, 5000] без size_mm; стало — лист материала, RAFLACOAT 3×[320, 450] price 662.134, VHI80 4+0 4×[297, 420] price 1307.56
- Сделано: раннер считает calcCutPlotter, calcSticker, calcPolySticker (файл нужен, чтобы снять эталоны соседей) и подмешивает plotter.json; листовая ветка перебирает material.sizes с перестановкой margins, cost = ceil от сырой суммы, price от суммы до ceil; size_mm в materials; у sticker снят ceil цены. time_hours резки оставлен round: на листовых кейсах он совпал с JS (0.2 и 0.39), ceil поднял бы Avery500c 100 шт с 0.22 до 0.23 и уронил эталон 0.21 при допуске 5%.
- Чем проверено: раннер `--data current` 14.11.2026; pytest четырёх калькуляторов и keychain — 43 passed; шаг 9 — без правки cost резки RAFLACOAT 294.4296, стикер VHI80 689.891, дефолт формы 312.7296, Avery passed (18 passed, 3 failed), после pop снова passed; `python scripts/dev.py check` — код 0.
- Не сделано и почему: деплой API и smoke на проде — Site ops после ревью и слияния в main. Коммит не делался.
- Требуется решение: принять diff и слить; прод выкатывает Site ops.
