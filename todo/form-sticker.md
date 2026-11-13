# form-sticker

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 22 CalcSticker на черновике товара считает `POST /api/v1/calc/sticker`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 22 на странице https://insain.ru/catalog/plotternaya-rezka/ по-прежнему на `insaincalc.calcSticker`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 22, только читать.
- `todo/EPIC-forms-to-api.md` — пачка 3. Форма 29 CalcStickerPack на том же slug — отдельная задача после принятия этой копии.
- `docs/js-runner-cases.md` — команда раннера для `calcSticker`, если кейс уже есть. Там же известное расхождение 50×50 VHI80.
- Остальное не открывать.

## Scope

- В git (Implementer): сверка по skill `verify.md` (порт `calcSticker`, эталон, `REF_FORM_DEFAULT`, раннер, боевой API). `wp-plugin/forms/sticker.js`: id элементов боевой формы 22, `insaincalc.syncUrl`, `insaincalc.calcApi('sticker'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_sticker.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Команду раннера дописать одной строкой в `docs/js-runner-cases.md`; файл общий для пачки, в «Файлы» его нет. Если строку в файл не вносили — она в «Результат», вносят при слиянии.
- В git (Implementer, расширение 14.11.2026): порт ошибки «Размер изделия больше допустимого» из `js_legacy/calc/calcCutPlotter.js` в `calc_service/calculators/cut_plotter.py`. Листовой материал, ни один размер листа не вмещает изделие — `ValueError` с этим текстом вместо пустого результата. `sticker.py` вызов резки не перехватывает: то же исключение у `StickerCalculator`. `POST /api/v1/calc/sticker` и `POST /api/v1/calc/cut_plotter` — HTTP 400, `detail` — этот текст. Эталоны границ с раннера (280×430 и 281×280) и соседи `poly_sticker`, `poly_sticker_pack`, `keychain` не сдвигаются. `sticker.js` и `showError` не менять, если `catch` уже пишет `detail` в блок срока.
- На проде (Site ops): дубль формы и черновик уже есть (копия 97, товар 2586891). В этой сессии копию не перезаписывать.
- После слияния в `main` и зелёного CI (Site ops, skill `deploy-api`): выкатка API. Затем на копии 97 под админом размер, который не помещается на лист (400×400, RAFLACOAT, тираж 100), показывает в блоке срока «Ошибка: Размер изделия больше допустимого», а не цену одного листа. Боевую форму 22 не переключать.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-sticker` от `main`.

## Файлы

- `wp-plugin/forms/sticker.js` — уже в ветке; в порте ошибки не менялся
- `calc_service/calculators/cut_plotter.py`
- `calc_service/tests/test_calculators/test_cut_plotter.py`
- `calc_service/tests/test_calculators/test_sticker.py`
- `calc_service/calculators/sticker.py` — только если исключение резки перехватывается (в этой правке не менялся)
- WordPress: копия 97 и черновик 2586891 уже есть. После `deploy-api` — проверка копии, без новой записи JS

## Не-scope

- `read_file` и любое переключение боевой формы 22. Выкладка плагина.
- `infra/deploy.sh` в сессии Implementer. Выкатка API — после слияния, skill `deploy-api`.
- `docs/site/forms.md`, `site/forms/22.json`, `todo/forms-batch-switch.md`.
- Цены, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Правка `sticker.py` и `wp-plugin/js/insain-calc-bridge.js`, пока HTTP 400 доходит до уже существующего `showError`.
- Рулонная ветка `cut_plotter`: JS эту ошибку там не бросает.
- Форма 29 CalcStickerPack и остальные формы эпика.
- Расхождение стикера 50×50 VHI80 (JS 1308, Python ~1107) — задача `sticker-vs-js` в `docs/js-runner-cases.md`. В этой задаче цену не выравнивать.
- Удаление копии и черновика.
- Обнуление уже показанной цены в `showError` (общее для форм на API).

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcSticker` — в блоке `calcSticker` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [x] Раннер и `POST https://insain.ru/api/v1/calc/sticker` на эталоне и на дефолте формы 22: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать. Кейс 50×50 VHI80 в эталон не брать.
- [x] `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [x] `Select-String -Path wp-plugin\forms\sticker.js -Pattern "calcApi\('sticker'|syncUrl\(|showResult\("` — все три вхождения есть.
- [x] Копия не на витрине: `wp post get 2586891 --field=post_status` — `draft`; `curl.exe` без cookies на `/?post_type=product&p=2586891` — `404`.
- [x] На копии под админом эталон даёт `POST /api/v1/calc/sticker` → 200. Цена на странице равна `price` API с округлением `showResult` (662.134 → 700 ₽).
- [x] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.
- [x] Листовой RAFLACOAT, тираж 100, сложность 1: 400×400, 281×281 и 280×431 — `CutPlotterCalculator` и `StickerCalculator` бросают `ValueError` `Размер изделия больше допустимого`. 280×430 и 281×280 считаются: стикер `price` / `time_ready` 8417.69 / 17.85 и 7965.69 / 17.69.
- [x] `POST /api/v1/calc/cut_plotter` и `POST /api/v1/calc/sticker` на 400×400 — HTTP 400, `detail` равен этому тексту.
- [x] Новые тесты без `ValueError` падают (`DID NOT RAISE`, HTTP 200). С правкой соседи `poly_sticker`, `poly_sticker_pack`, `keychain` и `test_api.py` остаются зелёными.
- [x] `sticker.js`: `catch` вызывает `showError`. `postCalc` кладёт `detail` в `Error.message`. `showError` пишет `Ошибка: …` во внутренний `div` `.htmTime` (тот же узел, что «Срок …»). Файлы не менялись.
- [ ] После слияния в `main`, зелёный CI, skill `deploy-api`: на копии 97 под админом 400×400 RAFLACOAT в блоке срока «Ошибка: Размер изделия больше допустимого», не цена одного листа. Боевая форма 22 на `calcSticker`. Черновик 2586891 остаётся `draft`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая страница клиентам не меняется. Текст ошибки на копии 97 появится только после `deploy-api`.
- Цены: JSON не править. Расхождение 50×50 VHI80 не выравнивать. Другое расхождение JS и API (rel > 0.001) на боевом калькуляторе — стоп. Ошибка «не помещается на лист» — в scope этой ветки, только листовая ветка `cut_plotter`.
- Формы: id элементов боевой формы 22 не менять. В админке в этой сессии ничего не писать.

## Режим

прод

## Журнал передач

14.11.2026 — Implementer, Grok 4.7 — сверка 0–5б, `wp-plugin/forms/sticker.js` — дальше Site ops
14.11.2026 — Site ops, Grok 4.7 — копия 97 на черновике 2586891, дефолт 700 ₽ — дальше Reviewer
14.11.2026 — Reviewer, Auto — ревью 1 принято — дальше человек (слияние / finish-task)
14.11.2026 — человек — замечание при приёмке копии: при размерах больше размера листа API не возвращает ошибку, показывается неадекватная цена — дальше Implementer
14.11.2026 — Implementer, Grok 4.7 — ошибка размера: JS бросает, API 200 с ценой; правка в `cut_plotter.py` / `sticker.py`, не в `sticker.js` — дальше человек
14.11.2026 — человек — расширить scope form-sticker: портировать ошибку «Размер изделия больше допустимого» в cut_plotter.py/sticker.py — дальше Implementer
14.11.2026 — Implementer, Grok 4.7 — ValueError в cut_plotter, sticker пробрасывает, HTTP 400, тесты — дальше Reviewer, Auto
14.11.2026 — Reviewer, Auto — ревью 2 принято — дальше человек (слияние), затем Site ops (`deploy-api`, копия 97)
14.11.2026 — человек — принято, слияние и выкатка — дальше Site ops

Блокер: копия показывает цену, когда изделие не помещается на лист. Сообщение об ошибке не появляется, потому что `POST /api/v1/calc/sticker` отвечает 200. Исправление не в `wp-plugin/forms/sticker.js`.
Пробовал: раннер `--data current` и боевой API, материал RAFLACOAT, тираж 100, сложность 1, без печати. `calcSticker` / `calcCutPlotter` на 400×400, 281×281 и 280×431 — выход 1, текст `Размер изделия больше допустимого`. На 280×430 — `price` 8417.69, `time_ready` 17.85; на 281×280 — `price` 7965.69, `time_ready` 17.69; те же числа у `StickerCalculator`. `POST https://insain.ru/api/v1/calc/sticker` на 400×400 — HTTP 200, `cost` 18.3, `price` 30.378, `time_ready` 16, `materials` []. Боевая страница формы 22, элемент 629: `catch` ставит `price = 0`, `PriceTotalManager = 0`, `CostTotal = 0` и делает `console.log(err.message)`; в блок срока текст ошибки не пишет.
Гипотеза: `calcCutPlotter.js` при `layoutOnSheet.num == 0` бросает `ICalcError`. `cut_plotter.py` такой лист пропускает и при нуле подходящих размеров возвращает пустой результат (`cost`/`price` 0). `sticker.py` при пустой резке подставляет 1 лист и считает его цену (18.3 × наценка материала). `sticker.js` уже зовёт `showError` только из `catch` неуспешного HTTP; на 200 вызывается `showResult`. `insaincalc.round(30.378, 100)` = 100 ₽.
Вопрос: расширить scope и портировать исключение здесь, завести предпосылку, или принять копию с этим пробелом.
Следующая сессия: человек

## Найдено вне scope

- Ползунок `numDensity` (649): на странице скрыт (`ezfc-hidden`), в инпуте «25%», `factor` 0.01, `calculate_when_hidden` = 0. Плейсхолдер `{{numDensity}}` на дефолте равен 0. В API уходит 0. Поле видно только при сложности 1.7.
- `chkMark` / `isFindMark`: параметра в API `sticker` нет (на `cut_plotter` есть, `sticker.py` его не прокидывает). На дефолте флажок выключен. В `syncUrl` пишется, в `calcApi` не уходит.
- Широкоформатная печать и широкая ламинация — допустимые пропуски `calcPrintWide` / `calcLaminationWide` (`scripts/js_port_gaps_allowed.txt`). В `calcApi` уходит только лазер `KMBizhubC220` и листовая ламинация `dpdRollLaminat`. Широкие принтеры и `dpdRollWideLaminat` — только в URL.
- На живой странице старый JS даёт price 653.134 при тех же материалах (3 листа 320×450 RAFLACOAT). Раннер `--data current` и боевой API — 662.134. `insaincalc.round` обоих — 700. Цены JSON не менялись.
- Боевая страница под админом: старый блок «через менеджера» 800 ₽ и «при заказе с сайта» 700 ₽, срок «2 дня». Копия по `showResult`: «цена» 700 ₽, «со скидкой» 536 ₽, срок «2 дня». Срок совпал. 800 — старое поле, в этой задаче не выравнивается.
- `wp litespeed-purge all` вернул `Error: Something went wrong! Got 400`. `wp cache flush` — `Success`. Превью копии после этого отдало свежий расчёт.
- `showError` не обнуляет уже показанную цену: после успешного расчёта слишком большой размер меняет срок на текст ошибки, сумма в колонке цены остаётся прежней. Общее для форм на API. На копии это изменится только с правкой моста и выкладкой плагина.
- JS бросает ошибку на первом листе с раскладкой 0, даже если следующий размер вмещает. Python пропускает неподходящий размер и берёт следующий подходящий; ошибка — когда не подошёл ни один. В `sheet.json` у листовых материалов один размер, для RAFLACOAT это одно и то же.

## Результат

- Ветка, PR или коммит: `task/form-sticker`, коммита нет. Прод: форма 97 `CalcSticker duplicate`, товар 2586891 «Плоттерная резка (Копировать)», `post_status` `draft`.
- Сделано: дубль формы 22 (строка 97) и черновик 2586891, JS копии с GET. Боевая форма 22 и товар 5601 не менялись. Порт ошибки: листовой `cut_plotter` при раскладке 0 на всех размерах бросает `ValueError('Размер изделия больше допустимого')` вместо пустого результата. `sticker.py` не менялся — вызов резки не в `try`, исключение доходит до `POST /calc/sticker`. `sticker.js` и `showError` не менялись: `catch` уже пишет `detail` во внутренний `div` `.htmTime` как `Ошибка: …`.
- Чем проверено (копия, прошлая сессия): `wp post get 2586891 --field=post_status` — `draft`. `curl.exe` без cookies на `/?post_type=product&p=2586891` — `404`. Превью под админом: `POST /api/v1/calc/sticker` 200, `price` 662.134, на странице 700 ₽. Боевая страница на `calcSticker`.
- Чем проверено (порт): до правки `pytest -k "larger_than_material or just_fits or oversize_sheet_http"` — 8 failed (`DID NOT RAISE`, HTTP 200: cut `price` 0, sticker `price` 30.378), 4 passed (280×430 и 281×280). После правки те же кейсы и соседи — `56 passed`. Раннер `calcCutPlotter` на 400×400 — выход 1, текст ошибки; на 280×430 — `price` 5228, `time_ready` 17.85; на 281×280 — `price` 4776, `time_ready` 17.69. `python scripts/dev.py check` — код 0, 563 + 81.
- Не сделано и почему: боевая форма 22 не переключалась. Выкладка плагина нет. `deploy-api` и проверка копии 97 на 400×400 — после слияния, критерий открыт. `sticker.py` не менялся: подстановка 1 листа не выполняется, потому что резка бросает исключение раньше.
- Требуется решение: нет. Дальше Reviewer (Auto). Незакоммичены `todo/form-sticker.md`, `docs/dashboard.md`, `wp-plugin/forms/sticker.js`, `calc_service/calculators/cut_plotter.py`, `calc_service/tests/test_calculators/test_cut_plotter.py`, `calc_service/tests/test_calculators/test_sticker.py`.
- Как откатить: калькулятор — не сливать ветку. Копию и черновик удалять только с отдельного «да». Бэкап элементов копии: `/tmp/ezfc-copy-97-20261113-190404.json`. После выкатки API откат — автооткат skill `deploy-api`.
- Поля только в URL, не в `calcApi`: `chkMark`; `dpdPrint` кроме `KMBizhubC220`; `dpdRollWideLaminat`. Файл `fluAtrwork` в URL не кладётся.
- Для Reviewer: id в git — боевая форма 22. На копии их подставил `ezfc_copy.py`. Дефолт бьёт в `REF_FORM_DEFAULT`. Порт — замена пустого результата на `ValueError` в листовой ветке `cut_plotter.py` (около прежнего `chosen_size_mm is None`). `sticker.py` без diff. Тест на исключение до правки падал с `DID NOT RAISE`.
- Выбран вариант 1 из блока «Варианты» (14.11.2026).
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока та задача `в работе`): после приёмки копии. Копия 97, черновик 2586891.
- Превью: https://insain.ru/?post_type=product&p=2586891&preview=true

### Варианты

1. Расширить scope и починить здесь (Рекомендуется). Калькулятор `sticker` не на боевой форме API (`docs/site/forms.md`), skill `port-fix-prerequisite` для такого пробела чинит внутри задачи. В `cut_plotter.py` для листового материала при раскладке 0 — `ValueError('Размер изделия больше допустимого')` вместо пустого результата. `sticker.py` вызов не ловит, `POST /calc/sticker` станет 400, текущий `catch` в `sticker.js` покажет `showError`. Эталон с раннера, тест падает без правки, соседи `poly_sticker`, `poly_sticker_pack`, `keychain` не сдвигаются, `make check`. На копии текст появится только после деплоя API.
2. Предпосылка `todo/<fix>.md`: та же правка отдельно, эту задачу не расширять. `form-sticker` ждёт закрытия предпосылки. Имеет смысл, если порт исключения не должен смешиваться с приёмкой копии.
3. Принять копию с пробелом. Цена вместо ошибки остаётся, пока порт не сделают отдельной задачей, не блокирующей слияние `form-sticker`. Боевая форма 22 по-прежнему на `calcSticker` и при непомещении обнуляет цену.
4. Не менять API. В `sticker.js` трактовать пустой `materials` как ошибку и звать `showError`. Боевой `POST` останется 200 с ценой 30.378; текст на копии появится только после перезаписи JS копии. Это не порт JS.

## Ревью 1

**Итог:** принято. Статус `ревью` — слияние и приёмка копии человеком (`finish-task`).

### Критерии (git / локально)

| Критерий | Проверка |
| --- | --- |
| `js_port_gaps.py calcSticker` | `нет в Python:` только `call calcPrintWide`, `call calcLaminationWide` — оба в `scripts/js_port_gaps_allowed.txt` |
| pytest sticker + wp_plugin_forms | `11 passed` (`test_sticker.py`, `test_wp_plugin_forms.py`) |
| `REF_FORM_DEFAULT` | `test_sticker.py` с `# JS, 14.11.2026`, `EXPECTED_FORM_DEFAULT.price` 662.134 — в `main`, в diff задачи не менялся |
| `sticker.js` контракт | `calcApi('sticker'`, `syncUrl(`, `showResult(` — три вхождения; нет формул цены; id полей — форма 22; режим без `\|\| 1`; печать только `KMBizhubC220` + листовая ламинация; широкие и `chkMark` — только URL, согласовано с «Найдено вне scope» |
| `make check` | `python scripts/dev.py check` — код 0, 551 + 81 тест |

### Diff

- Новый файл `wp-plugin/forms/sticker.js` — основной артеfact; **не закоммичен** в ветке (см. замечание).
- `todo/form-sticker.md`, `docs/dashboard.md` — служебные правки статуса/дашборда.

### Критерии на проде

Копия принята в отчёте Site ops (черновик, 404 без cookie, POST 200, GET/share, боевая 22 на `calcSticker`) — повторно на проде не гонялось, по регламенту Reviewer.

### Замечания

- **желательно:** перед слиянием включить в коммит `wp-plugin/forms/sticker.js` (сейчас untracked); иначе в `main` не попадёт источник JS для будущего `deploy-wp-plugin`.
- **желательно:** при `finish-task` перенести строку «Состав пакета» (копия 97, черновик 2586891) в `todo/forms-batch-switch.md`, если та задача не `в работе` (как в Scope).

## Ревью 2

**Итог:** принято. Статус `ревью` — слияние в `main` человеком, затем Site ops: skill `deploy-api` и открытый критерий копии 97 (400×400, текст ошибки в `.htmTime`).

### Критерии (расширение scope, git / локально)

| Критерий | Проверка |
| --- | --- |
| `cut_plotter.py` лист, раскладка 0 на всех размерах | В ветке `else` (лист): `chosen_size_mm is None` → `raise ValueError("Размер изделия больше допустимого")`, текст совпадает с `calcCutPlotter.js:191`. Рулонная ветка по-прежнему `_empty_result` — в scope не-scope |
| `sticker.py` | Diff нет; `cut_calc.calculate(cut_params)` без `try` — исключение пробрасывается |
| Эталоны границ | `pytest -k "larger_than_material or just_fits or oversize_sheet_http"` — 12 кейсов; 280×430 / 281×280: cut `price` 5228 / 4776, sticker `price` 8417.69 / 7965.69, `time_ready` как в задаче |
| HTTP 400 + `detail` | `test_oversize_sheet_http_400` в `test_cut_plotter.py` и `test_sticker.py`; handler `main.py` → `{"detail": str(exc)}` |
| `sticker.js` / мост | В working tree diff порта нет; `catch` → `showError`; `postCalc` кладёт `data.detail` в `Error.message` (`insain-calc-bridge.js:144–145`) |
| Регресс соседей | `test_cut_plotter.py` + `test_sticker.py` — 33 passed; `python scripts/dev.py check` — 563 + 81, код 0 |
| `make check` (Implementer) | Повторно: 563 + 81, код 0 |

### Diff (круг 2)

- `calc_service/calculators/cut_plotter.py` — замена `_empty_result` на `ValueError` только при листовом материале.
- `calc_service/tests/test_calculators/test_cut_plotter.py`, `test_sticker.py` — параметризованный oversize, границы 280×430 / 281×280, HTTP-тесты; комментарии `# JS, 14.11.2026` и команды раннера.
- `todo/form-sticker.md` — scope, критерии, журнал (служебно).
- `wp-plugin/forms/sticker.js` — без изменений в этом круге; файл по-прежнему **не в индексе** (из ревью 1).

### Критерии на проде

- Открыт: после слияния, CI, `deploy-api` — копия 97, 400×400 RAFLACOAT, «Ошибка: Размер изделия больше допустимого» (не цена листа). Локально не проверяется — маршрут Site ops после merge.

### Замечания

- **желательно:** в один коммит/слияние включить все артефакты ветки: `wp-plugin/forms/sticker.js`, правки `cut_plotter.py`, тесты, `todo/form-sticker.md` (и пересобранный `docs/dashboard.md`, если в индексе).
- **желательно:** при `finish-task` — строка «Состав пакета» (копия 97, черновик 2586891), как в ревью 1.
- **вне scope:** расхождение JS/Python при нескольких размерах листа (JS бросает на первом `num==0`, Python — когда ни один не подошёл) — уже в «Найдено вне scope»; для RAFLACOAT один размер, поведение совпадает.
