# form-button-pins

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: калькулятор-обёртка над готовой `calc_button_pins` по skill `new-calculator`; прод — выкатка по `deploy-api` и копия формы по `ezfc-form-to-api`.
Чат: сначала Implementer (калькулятор), затем копия формы — Site ops по skill `ezfc-form-to-api`.

## Цель

Форма 12 CalcButtonPins считает `POST /api/v1/calc/button_pins`. В реестре API есть slug `button_pins`. Копия на черновике товара: GET = имя элемента, цена по ссылке та же. Боевая страница https://insain.ru/catalog/znachki-zakatnye-kruglye/ на старом JS, пока форму не возьмёт пакет переключения.

## Контекст и ссылки

- Эпик `todo/EPIC-forms-to-api.md`, пачка 5
- `.cursor/skills/new-calculator/SKILL.md` и `.cursor/skills/ezfc-form-to-api/SKILL.md`
- Логика уже есть: `calc_service/common/process_tools.py` `calc_button_pins`, JS `insaincalc.calcButtonPins`
- `docs/site/forms.md` — строка формы 12, только читать до переключения
- Остальное не открывать

## Scope

В git (Implementer):

1. Калькулятор по шаблону `_template.py`: обёртка над `calc_button_pins`, без копирования формул. Регистрация в `__init__.py`. Тесты: эталон со старого JS, обязательные поля ответа.
2. После зелёного `make check` и слияния — выкатка API (человек / Site ops по `infra/deploy.sh`).

На проде (Site ops), после API на проде:

3. Перевод формы 12 через копию по skill `ezfc-form-to-api`. Боевую не переключать.

## Файлы

- `calc_service/calculators/button_pins.py`, `calc_service/calculators/__init__.py`
- `calc_service/tests/test_calculators/test_button_pins.py`
- `wp-plugin/forms/button_pins.js` — на шаге копии
- WordPress: только копия формы и черновик товара

## Не-scope

- Боевая форма 12, `forms-batch-switch`, цены в JSON (наценка `marginButtonPins` уже есть)
- Другие значки (`metal_pins`, `badge`)

## Критерии приёмки

- [x] `python bot_service/check_calc_registry.py` на локальном API — в списке есть `button_pins` (нужен `make calc-up`)
- [x] `python -m pytest calc_service/tests/test_calculators/test_button_pins.py -q` — `passed`
- [x] Раннер JS и API: rel ≤ 0.001 на эталоне (команда раннера — из skill / `docs/js-runner-cases.md` после добавления кейса)
- [ ] Копия не на витрине: `draft` или `private`, гость `404`
- [ ] На копии POST `/api/v1/calc/button_pins` → 200, цена на странице = API с округлением `showResult`

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль формы только с подтверждения; боевая страница не меняется в этой задаче
- Цены: JSON не менять; `marginButtonPins` уже в `common.json`
- Формы: id боевой 12 не менять

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`.

17.11.2026 — Implementer, Grok 4.7 — калькулятор `button_pins` в ветке, `make check` зелёный — дальше Reviewer

17.11.2026 — Reviewer, Auto — принято по diff Implementer — дальше человек (слияние)

17.11.2026 — человек — принято — выкатка, дальше Site ops

## Найдено вне scope

- Старый JS кладёт в `isPrint` вставки строку `KMBizhubC220`, а не `{printerID, color}`: печать вставки не считается. API повторяет это, иначе цена разойдётся с боевой формой.
- В `pins.json` у D78 поле `title` говорит «56мм» при размере 78.
- Боевой `LaminationCalculator` делает `math.ceil` цены, `cut_plotter` и ламинация отдают `time_hours` через `round`, раннер — `ceil`. На эталоне 2×D38: price API 760.59 против раннера 759.88388712 (rel 0.00093), time 0.25 против 0.27. Боевые калькуляторы не менялись.

## Результат

- Ветка, PR или коммит: `task/form-button-pins` → `main`
- Сделано: публичный калькулятор `button_pins` — обёртка над `calc_button_pins`. Вставка через `StickerCalculator` (резка + ламинация, без печати). Заготовка читается из своей группы `ButtonPins` / `ButtonPinsAmalit` (плоский каталог затирал себестоимость). Для вставки в резку проброшены `interval`, метки и подложка; дефолт формы стикера не меняется. Сняты пропуски `calcButtonPins call calcSticker` и `calcCutPlotter option isCarrier`.
- Чем проверено:
  - `python scripts/dev.py check` — код выхода 0: `643 passed` (calc_service), `81 passed` (bot_service).
  - `python -m pytest calc_service/tests/test_calculators/test_button_pins.py -q` — `12 passed`. Временная подмена эталона `price` на 1 — `1 failed` с текстом `price: 760.59`, число возвращено.
  - Соседи: sticker, cut_plotter, process_tools, js_port_gaps — в общем прогоне `118 passed` до полного check.
  - Раннер `node scripts/run_js_calc.mjs calcButtonPins --data current --args '[2,\"D38\",{},1]'` → cost 519.3422813333333, price 759.88388712, unit_price 379.94, time 0.27, time_ready 16.27, weight 0.0108. API: cost тот же, price 760.59 (rel 0.00093), unit_price 380.295 (rel 0.00093), weight тот же.
  - Раннер `'[2500,\"D38\",{},1]'` и API: cost 28905, price 47982.30, time 10.5, time_ready 50.5, weight 13.5.
  - `python scripts/dev.py start calc`, POST `/api/v1/calc/button_pins` → 200, `share_url` есть, в materials есть `title`. `python bot_service/check_calc_registry.py` — slug совпали, в списке `button_pins`. API остановлен.
  - В `button_pins.py` нет чисел цен (`Select-String` по шаблону skill пустой).
- Не сделано и почему: выкатка API, копия формы 12 и проверка черновика — Site ops после ревью и слияния. Боевую форму не переключать. `docs/js-runner-cases.md` не правился (общий файл); кейс ниже.
- Требуется решение: нет. Коммит и слияние — после Reviewer, человеком.

Дописать в `docs/js-runner-cases.md` при слиянии (price — вывод раннера 17.11.2026, `--data current`):

| Функция | Slug API | `price` |
| --- | --- | --- |
| `calcButtonPins` 2×D38 mode 1 | `button_pins` | 759.88388712 |
| `calcButtonPins` 2500×D38 Амалит | `button_pins` | 47982.30000000001 |

```powershell
node scripts/run_js_calc.mjs calcButtonPins --data current --args '[2,\"D38\",{},1]'

node scripts/run_js_calc.mjs calcButtonPins --data current --args '[2500,\"D38\",{},1]'
```

Параметры API эталона: `{"quantity":2,"pin_id":"D38","mode":1}`. Упаковка: `is_packing: true` (автоподбор) или строка — код пакета.

## Ревью 1

**Вердикт:** принято

**Статус задачи:** `ревью` (без изменения; дальше человек — коммит, слияние в `main`, затем Site ops: `deploy-api`, копия формы 12 по `ezfc-form-to-api`)

**Замечания**

- **желательно:** при слиянии в `main` перенести в `docs/js-runner-cases.md` таблицу и команды из блока «Результат» (общий файл в worktree не трогали — ок).
- **желательно:** расхождение `price`/`unit_price` эталона 2×D38 (API 760.59 vs раннер 759.88388712, rel ≈ 0.00093) задокументировано в «Найдено вне scope»; тест держит раннер с `rel ≤ 0.001` — критерий закрыт, до точного совпадения с JS не гнаться без правки ламинации.

**Критерии Implementer (scope git)**

| Критерий | Сверка |
| --- | --- |
| Регистрация `button_pins`, обёртка над `calc_button_pins` | diff: `button_pins.py`, `__init__.py`; формул в обёртке нет |
| `make check` | `python scripts/dev.py check` — 643 + 81 passed, exit 0 (повтор Reviewer) |
| Тесты калькулятора | `test_button_pins.py` — 12 passed |
| Раннер vs API rel ≤ 0.001 | раннер `node … '[2,\"D38\",{},1]'` → price 759.88388712; API → cost совпал, price 760.59 (rel 0.00093) |
| Соседи cut_plotter/sticker | проброс `interval`/`is_find_mark`/`is_carrier` только при наличии в params; `marginsMark` в equipment; `test_sticker` + `test_cut_plotter` + `test_button_pins` — 66 passed |
| Инварианты AGENTS.md | обязательные поля и `title` в materials; цен в `button_pins.py` нет; JSON не менялся |
| `js_port_gaps_allowed.txt` | сняты `calcButtonPins call calcSticker`, `calcCutPlotter option isCarrier` |

Критерии копии формы (черновик, POST на странице) — вне этого круга; после слияния — Site ops.

**Чем проверено Reviewer**

- `git diff` / untracked: `button_pins.py`, `test_button_pins.py` + правки `process_tools`, `cut_plotter`, `sticker`, `equipment`, `js_port_gaps_allowed.txt`, `todo`, `dashboard.md`
- `python scripts/dev.py check` — exit 0
- `python -m pytest calc_service/tests/test_calculators/test_button_pins.py calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_calculators/test_cut_plotter.py -q` — 66 passed
- `node scripts/run_js_calc.mjs calcButtonPins --data current --args '[2,\"D38\",{},1]'` и локальный `ButtonPinsCalculator().execute` — cost 519.3422813333333, rel price 0.00093
