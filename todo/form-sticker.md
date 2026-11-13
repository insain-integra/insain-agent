# form-sticker

Статус: заблокировано: ждёт todo/sticker-print-wide.md
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
- После `close` `todo/sticker-print-wide.md` (статус этой задачи станет `черновик`): в `wp-plugin/forms/sticker.js` передавать в `calcApi` широкие `printer_code` (`Technojet160ECO`, `HPLatex335`, `TechnojetXR720`) с `color` `4+0`; для `Technojet160ECO` — `lamination_id` из `dpdRollWideLaminat` (1064), если не `No`; свериться с формой 22 (элемент 811 / 1064). Перезаписать custom JS копии 97 тем же текстом. На копии сверить кейсы интерьерной печати с раннером / API. Бой 22 не переключать.

## Файлы

- `wp-plugin/forms/sticker.js` — уже в ветке; после предпосылки — широкая печать и `dpdRollWideLaminat` в POST
- `calc_service/calculators/cut_plotter.py`
- `calc_service/tests/test_calculators/test_cut_plotter.py`
- `calc_service/tests/test_calculators/test_sticker.py` — эталоны формы; широкая ветка правит `sticker-print-wide`
- WordPress: копия 97 и черновик 2586891 уже есть. После предпосылки — перезапись JS копии 97

## Не-scope

- `read_file` и любое переключение боевой формы 22. Выкладка плагина — только если после правки `sticker.js` нужна выкатка моста (отдельно решить при возобновлении).
- `infra/deploy.sh` в сессии Implementer. Выкатка API широкой ветки — в `sticker-print-wide` / skill `deploy-api`.
- `docs/site/forms.md`, `site/forms/22.json`, `todo/forms-batch-switch.md`.
- Цены, `calc_service/data/`. Порт `calcPrintWide` / `calcLaminationWide` / модуль `lamination_wide` / `scripts/js_port_gaps_allowed.txt` / `scripts/run_js_calc.mjs` — задача `todo/sticker-print-wide.md`.
- Правка `sticker.py` в этой задаче (кроме уже сделанного проброса ошибки резки): широкая печать — в предпосылке.
- `wp-plugin/js/insain-calc-bridge.js`, пока HTTP 400 доходит до уже существующего `showError`.
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
- [x] После слияния в `main`, зелёный CI, skill `deploy-api`: на копии 97 под админом 400×400 RAFLACOAT в блоке срока «Ошибка: Размер изделия больше допустимого», не цена одного листа. Боевая форма 22 на `calcSticker`. Черновик 2586891 остаётся `draft`.

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
14.11.2026 — Site ops, Grok 4.7 — API `73a52f6` выкачен (skill `deploy-api`); копия 97: 400×400 «Ошибка: Размер изделия больше допустимого», возврат 50×50 — 700 руб. и «Срок 2 дня»; форма 22 на `calcSticker`, черновик `draft` — дальше человек (finish-task)
14.11.2026 — человек — замечание при приёмке копии: не сходятся расчёты при выборе интерьерной печати — дальше Implementer
14.11.2026 — Implementer, Grok 4.7 — интерьерная печать: `sticker.js` не шлёт широкий принтер, но и прокидывание в API не считает `calcPrintWide` / `calcLaminationWide`; `sticker.py` и `js_port_gaps_allowed.txt` не менялись — дальше человек
14.11.2026 — человек — оформлять отдельную задачу-предпосылку на порт `calcPrintWide` и `calcLaminationWide` в `sticker.py` — дальше аналитик
14.11.2026 — Analyst, Grok 4.7 — оформлена `todo/sticker-print-wide.md`; статус ждёт предпосылку — дальше закрытие `sticker-print-wide`, затем Implementer этой задачи

Блокер: копия показывает цену, когда изделие не помещается на лист. Сообщение об ошибке не появляется, потому что `POST /api/v1/calc/sticker` отвечает 200. Исправление не в `wp-plugin/forms/sticker.js`.
Пробовал: раннер `--data current` и боевой API, материал RAFLACOAT, тираж 100, сложность 1, без печати. `calcSticker` / `calcCutPlotter` на 400×400, 281×281 и 280×431 — выход 1, текст `Размер изделия больше допустимого`. На 280×430 — `price` 8417.69, `time_ready` 17.85; на 281×280 — `price` 7965.69, `time_ready` 17.69; те же числа у `StickerCalculator`. `POST https://insain.ru/api/v1/calc/sticker` на 400×400 — HTTP 200, `cost` 18.3, `price` 30.378, `time_ready` 16, `materials` []. Боевая страница формы 22, элемент 629: `catch` ставит `price = 0`, `PriceTotalManager = 0`, `CostTotal = 0` и делает `console.log(err.message)`; в блок срока текст ошибки не пишет.
Гипотеза: `calcCutPlotter.js` при `layoutOnSheet.num == 0` бросает `ICalcError`. `cut_plotter.py` такой лист пропускает и при нуле подходящих размеров возвращает пустой результат (`cost`/`price` 0). `sticker.py` при пустой резке подставляет 1 лист и считает его цену (18.3 × наценка материала). `sticker.js` уже зовёт `showError` только из `catch` неуспешного HTTP; на 200 вызывается `showResult`. `insaincalc.round(30.378, 100)` = 100 ₽.
Вопрос: расширить scope и портировать исключение здесь, завести предпосылку, или принять копию с этим пробелом.
Следующая сессия: человек
Снято 14.11.2026 выкаткой `73a52f6`: `POST /api/v1/calc/sticker` на 400×400 — HTTP 400, на копии 97 в блоке срока текст ошибки.

Блокер: при «интерьерной» печати копия 97 считает ту же цену, что без печати. Старый JS формы 22 либо обнуляет цену (листовой материал), либо добавляет `calcPrintWide` и, для рулона с ламинацией, `calcLaminationWide`. Правка только `wp-plugin/forms/sticker.js` цену не сближает: `sticker.py` эти две функции не вызывает. `sticker.py` и `scripts/js_port_gaps_allowed.txt` в Не-scope, в этой сессии не менялись.
Пробовал: форма 22, элемент 811 `dpdPrint` — «Интерьерная экосольвентная» = `Technojet160ECO` (открывает 1064 `dpdRollWideLaminat`), «Интерьерная латексная» = `HPLatex335` (ламинацию не открывает). Старый cjsCalc 629 кладёт любой принтер кроме `No` в `isPrint` и для `Technojet160ECO` ламинацию из 1064. Раннер `--data current`, 100 шт, 50×50, size_item 50, density 0, difficulty 1, mode 1. RAFLACOAT + `Technojet160ECO` / `HPLatex335` — выход 1, `Cannot read properties of undefined (reading 'name')` (`calcPrintWide` ищет материал только в roll). ORAJET3640 без печати — `price` 577.368832; + экосольвент — 979.368832; + экосольвент и `LaminatDLCLAM` — 1732.368832; + латекс — 2750.368832. `POST https://insain.ru/api/v1/calc/sticker` как копия 97 (без `color` / `printer_code`): RAFLACOAT `price` 662.134; ORAJET3640 `price` 558.59224. Тот же POST с `color` `4+0` и `printer_code` широкого принтера — те же 662.134 и 558.59224. С `lamination_id` `LaminatDLCLAM` API даёт 1382.134 (лист) и 1024.59224 (рулон) — это `LaminationCalculator`, не `calcLaminationWide`, и копия это поле не шлёт.
Гипотеза: дыра порта, уже записанная в `scripts/js_port_gaps_allowed.txt` (`calcSticker call calcPrintWide`, `calcSticker call calcLaminationWide`, `calcLaminationWide module`). `print_wide.py` есть и в реестре, из `sticker.py` не вызывается. Модуля широкой ламинации нет. `sticker.py` печатает только лист через `PrintLaserCalculator` и только если передан `color`.
Вопрос: предпосылка на порт этих двух вызовов, расширить scope здесь, или принять копию без переключения боя и вынести широкую ветку в отдельную задачу до переключения формы 22.
Следующая сессия: закрытие `sticker-print-wide`, затем Implementer `form-sticker`
Снято оформлением `todo/sticker-print-wide.md` 14.11.2026 (вариант 1).

## Найдено вне scope

- Ползунок `numDensity` (649): на странице скрыт (`ezfc-hidden`), в инпуте «25%», `factor` 0.01, `calculate_when_hidden` = 0. Плейсхолдер `{{numDensity}}` на дефолте равен 0. В API уходит 0. Поле видно только при сложности 1.7.
- `chkMark` / `isFindMark`: параметра в API `sticker` нет (на `cut_plotter` есть, `sticker.py` его не прокидывает). На дефолте флажок выключен. В `syncUrl` пишется, в `calcApi` не уходит.
- Широкоформатная печать и широкая ламинация — допустимые пропуски `calcPrintWide` / `calcLaminationWide` (`scripts/js_port_gaps_allowed.txt`). В `calcApi` уходит только лазер `KMBizhubC220` и листовая ламинация `dpdRollLaminat`. Широкие принтеры и `dpdRollWideLaminat` — только в URL. Числа, почему это уже не даёт принять копию, — раздел «Факты: интерьерная печать».
- На живой странице старый JS даёт price 653.134 при тех же материалах (3 листа 320×450 RAFLACOAT). Раннер `--data current` и боевой API — 662.134. `insaincalc.round` обоих — 700. Цены JSON не менялись.
- Боевая страница под админом: старый блок «через менеджера» 800 ₽ и «при заказе с сайта» 700 ₽, срок «2 дня». Копия по `showResult`: «цена» 700 ₽, «со скидкой» 536 ₽, срок «2 дня». Срок совпал. 800 — старое поле, в этой задаче не выравнивается.
- `wp litespeed-purge all` вернул `Error: Something went wrong! Got 400`. `wp cache flush` — `Success`. Превью копии после этого отдало свежий расчёт.
- `showError` не обнуляет уже показанную цену: после успешного расчёта слишком большой размер меняет срок на текст ошибки, сумма в колонке цены остаётся прежней. Общее для форм на API. На копии это изменится только с правкой моста и выкладкой плагина.
- JS бросает ошибку на первом листе с раскладкой 0, даже если следующий размер вмещает. Python пропускает неподходящий размер и берёт следующий подходящий; ошибка — когда не подошёл ни один. В `sheet.json` у листовых материалов один размер, для RAFLACOAT это одно и то же.
- Рулон ORAJET3640, 100 шт 50×50, без печати: раннер `price` 577.368832, боевой `POST /api/v1/calc/sticker` 558.59224. Оба `insaincalc.round(..., 100)` дают 600. К замечанию про интерьерную печать не относится: там расхождение — сама печать.

## Факты: интерьерная печать

Снято 14.11.2026. Боевая форма 22 и копия 97, элемент печати. `sticker.py` и `scripts/js_port_gaps_allowed.txt` не менялись.

`dpdPrint` формы 22 (элемент 811; на копии 97 это 3641, те же value):

| index | value | Подпись | Что открывается |
| --- | --- | --- | --- |
| 0 | `No` | Без печати | — |
| 1 | `KMBizhubC220` | Цифровая лазерная печать | листовая ламинация `dpdRollLaminat` (1063 / на копии 3642) |
| 2 | `Technojet160ECO` | Интерьерная экосольвентная | широкая ламинация `dpdRollWideLaminat` (1064 / 3643): «нет», «глянцевая», «матовая». Глянец и мат — оба value `LaminatDLCLAM` |
| 3 | `HPLatex335` | Интерьерная латексная | ламинация не открывается |
| 4 | `TechnojetXR720` | Широкоформатная сольвентная | ламинация не открывается |
| 5 | `TechnojetXR720` | Широкоформатная УФ-печать | тот же value, что у строки 4 |

Старый cjsCalc формы 22 (элемент 629): любой принтер кроме `No` → `options.isPrint = {printerID, color: '4+0'}`. Ламинация: `KMBizhubC220` читает 1063, `Technojet160ECO` читает 1064, остальные принтеры ламинацию не ставят. `calcSticker.js`: `KMBizhubC220` → `calcPrintLaser`; `Technojet160ECO`, `HPLatex335`, `TechnojetXR720` → `calcPrintWide(1, размер_расхода_резки, materialID, printerID, …)`. Если ламинация задана и расход резки — рулон (высота 0) → `calcLaminationWide(1, тот же размер)` с зашитым `LaminatDLCLAM`. Если лист → `calcLamination` с id из списка. `catch` ставит `price = 0`.

`wp-plugin/forms/sticker.js` и тот же текст на копии 97 (элемент 3646, `read_file=0`): в `calcApi` печать и ламинация уходят только при `printerId === 'KMBizhubC220'`. Широкий принтер и `dpdRollWideLaminat` пишутся в URL и в POST не входят.

В `calc_service/calculators/`: `print_wide.py` (`PrintWideCalculator`, slug `print_wide`) есть, из `sticker.py` не вызывается. `print_roll.py` вызывает `print_wide` для своего калькулятора. `lamination.py` — это `calcLamination` (ламинатор `FGKFM360`). Файла широкой ламинации нет. `sticker.py` печатает только при `color` и листовом материале, всегда через `PrintLaserCalculator`; исключение печати глотается. В `scripts/js_port_gaps_allowed.txt` для этого пропуска три строки: `calcLaminationWide module`, `calcSticker call calcPrintWide`, `calcSticker call calcLaminationWide`.

Кейс дефолта формы, 100 шт, 50×50, size_item 50, density 0, difficulty 1, mode 1. Раннер `node scripts/run_js_calc.mjs calcSticker --data current`. Боевой `POST /api/v1/calc/sticker` — то тело, которое шлёт копия. «На странице» — `insaincalc.round(price, 100)`. Срок на всех этих `time_ready` ≈ 16 ч — «2 дня» (`Math.round(time/8) = 2`). Число широкой ламинации снято раннером с подгруженными `calcLamination.js` и `laminat.json` текущего прайса: штатный `run_js_calc.mjs` каталог ламината не грузит, без него вызов падает на `insaincalc.laminat`.

| Кейс | Старый JS `price` / страница | Копия 97 / POST `price` / страница |
| --- | --- | --- |
| RAFLACOAT, без печати | 662.134 / 700 ₽ | 662.134 / 700 ₽ |
| RAFLACOAT, экосольвент или латекс, с широкой ламинацией и без | выход 1, `reading 'name'` (`calcPrintWide` не находит листовой материал в roll). Форма 22 ставит цену 0 | 662.134 / 700 ₽. POST с `color` `4+0` и `printer_code` `Technojet160ECO` или `HPLatex335` — те же 662.134 |
| ORAJET3640, без печати | 577.368832 / 600 ₽ | 558.59224 / 600 ₽ |
| ORAJET3640, экосольвент, ламинация «нет» | 979.368832 / 1000 ₽, `time_ready` 16.32 | 558.59224 / 600 ₽. POST с `printer_code` `Technojet160ECO` и `color` `4+0` — те же 558.59224 |
| ORAJET3640, экосольвент + `LaminatDLCLAM` | 1732.368832 / 1800 ₽, `time_ready` 16.33 | копия поле не шлёт, остаётся 558.59224 / 600 ₽. Если передать `lamination_id` вручную — 1024.59224 / 1100 ₽ (`LaminationCalculator`, не `calcLaminationWide`) |
| ORAJET3640, латекс | 2750.368832 / 2800 ₽, `time_ready` 16.68 | 558.59224 / 600 ₽ |

Вывод: причина не только в `sticker.js`. Прокинуть `printer_code` и `lamination_id` можно, но текущий `sticker.py` от этого не вызывает `calcPrintWide` и `calcLaminationWide`. Чтобы сойтись со старым JS, нужен порт этих двух вызовов (широкая ламинация — новый модуль: в Python его нет).

## Результат

- Ветка, PR или коммит: `main` @ `73a52f6` (CI `completed success`). Прод API выкачен этим коммитом с `7c88dfb`. Форма 97 `CalcSticker duplicate`, товар 2586891 «Плоттерная резка (Копировать)», `post_status` `draft`.
- Сделано: дубль формы 22 (строка 97) и черновик 2586891, JS копии с GET. Боевая форма 22 и товар 5601 не менялись. Порт ошибки: листовой `cut_plotter` при раскладке 0 на всех размерах бросает `ValueError('Размер изделия больше допустимого')` вместо пустого результата. `sticker.py` не менялся — вызов резки не в `try`, исключение доходит до `POST /calc/sticker`. `sticker.js` и `showError` не менялись: `catch` уже пишет `detail` во внутренний `div` `.htmTime` как `Ошибка: …`. API `73a52f6` выкачен на прод skill `deploy-api`; копия 97 показывает ошибку размера, боевая форма 22 осталась на `calcSticker`.
- Чем проверено (копия, прошлая сессия): `wp post get 2586891 --field=post_status` — `draft`. `curl.exe` без cookies на `/?post_type=product&p=2586891` — `404`. Превью под админом: `POST /api/v1/calc/sticker` 200, `price` 662.134, на странице 700 ₽. Боевая страница на `calcSticker`.
- Чем проверено (порт): до правки `pytest -k "larger_than_material or just_fits or oversize_sheet_http"` — 8 failed (`DID NOT RAISE`, HTTP 200: cut `price` 0, sticker `price` 30.378), 4 passed (280×430 и 281×280). После правки те же кейсы и соседи — `56 passed`. Раннер `calcCutPlotter` на 400×400 — выход 1, текст ошибки; на 280×430 — `price` 5228, `time_ready` 17.85; на 281×280 — `price` 4776, `time_ready` 17.69. `python scripts/dev.py check` — код 0, 563 + 81.
- Чем проверено (выкатка 14.11.2026): `bash infra/deploy.sh` на VDS — fast-forward `7c88dfb` → `73a52f6`, smoke скрипта `GET /api/v1/calculators` 200 и `POST /api/v1/calc/puzzle` 200, контейнер healthy. `POST /api/v1/calc/sticker` дефолт (100 шт, 50×50, RAFLACOAT) — HTTP 200, `price` 662.134. Oversize 400×400 RAFLACOAT тираж 100 — HTTP 400, `detail` `Размер изделия больше допустимого`. Превью копии под админом: тот же POST 400, `.htmTime` — `Ошибка: Размер изделия больше допустимого`; возврат 50×50 — POST 200, `price` 662.134, на странице `700 руб.` и `Срок 2 дня`. `wp post get 2586891 --field=post_status` — `draft`. Боевая страница https://insain.ru/catalog/plotternaya-rezka/ содержит `insaincalc.calcSticker(`, вызова `calcApi` нет. Копия и форма 22 не перезаписывались.
- Не сделано и почему: боевая форма 22 не переключалась (так и задумано). Выкладка плагина нет — вне scope. `sticker.py` не менялся: подстановка 1 листа не выполняется, потому что резка бросает исключение раньше.
- Требуется решение: нет. Выбрана предпосылка `todo/sticker-print-wide.md`. `finish-task` не запускать, пока широкая ветка не сойдётся на копии 97 после возобновления этой задачи.
- Как откатить: перед выкаткой `deploy.sh` сохранил предыдущий образ как `insain-agent-calc-api:rollback` (сервер был на `7c88dfb`). Копию и черновик не удалять. Бэкап элементов копии: `/tmp/ezfc-copy-97-20261113-190404.json`.
- Поля только в URL, не в `calcApi`: `chkMark`; `dpdPrint` кроме `KMBizhubC220`; `dpdRollWideLaminat`. Файл `fluAtrwork` в URL не кладётся.
- Для Reviewer: id в git — боевая форма 22. На копии их подставил `ezfc_copy.py`. Дефолт бьёт в `REF_FORM_DEFAULT`. Порт — замена пустого результата на `ValueError` в листовой ветке `cut_plotter.py` (около прежнего `chosen_size_mm is None`). `sticker.py` без diff. Тест на исключение до правки падал с `DID NOT RAISE`.
- Выбран вариант 1 из блока «Варианты» (14.11.2026).
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать в этой сессии; статус пакета `черновик`, строку переносит `finish-task`): | 22 CalcSticker | `sticker` | `/catalog/plotternaya-rezka/` | 97 / 2586891 (draft) | копия принята 14.11.2026, `form-sticker` |
- Период: 2026-11-14 — 2026-11-14 (1 дн.) по чатам Cursor (`hours_from_chats`); git-история файла 2026-11-12 — 2026-11-14 (3 дн.)
- Часы человека: 24 сообщ. в чатах Cursor; активно 3.8 ч (ходы агента > 30 мин — с коэфф. 0.5)
- Работа агентов: 13 чатов Cursor, 24 сообщ. человека, 3.8 ч активных; Implementer — Grok 4.7; Reviewer — Auto; Site ops — Grok 4.7
- Было / стало: до выкатки API (`7c88dfb`) `POST /api/v1/calc/sticker` на 400×400 RAFLACOAT тираж 100 отвечал HTTP 200 с `price` 30.378 (цена одного листа), копия показывала цену / после `73a52f6` тот же запрос — HTTP 400, `detail` «Размер изделия больше допустимого»; на копии 97 в блоке срока «Ошибка: Размер изделия больше допустимого»; дефолт 50×50 — `price` 662.134, на странице 700 руб. и «Срок 2 дня». Боевая форма 22 по-прежнему на `calcSticker`, черновик 2586891 — `draft`.
- Превью: https://insain.ru/?post_type=product&p=2586891&preview=true

### Варианты

1. Расширить scope и починить здесь (Рекомендуется). Калькулятор `sticker` не на боевой форме API (`docs/site/forms.md`), skill `port-fix-prerequisite` для такого пробела чинит внутри задачи. В `cut_plotter.py` для листового материала при раскладке 0 — `ValueError('Размер изделия больше допустимого')` вместо пустого результата. `sticker.py` вызов не ловит, `POST /calc/sticker` станет 400, текущий `catch` в `sticker.js` покажет `showError`. Эталон с раннера, тест падает без правки, соседи `poly_sticker`, `poly_sticker_pack`, `keychain` не сдвигаются, `make check`. На копии текст появится только после деплоя API.
2. Предпосылка `todo/<fix>.md`: та же правка отдельно, эту задачу не расширять. `form-sticker` ждёт закрытия предпосылки. Имеет смысл, если порт исключения не должен смешиваться с приёмкой копии.
3. Принять копию с пробелом. Цена вместо ошибки остаётся, пока порт не сделают отдельной задачей, не блокирующей слияние `form-sticker`. Боевая форма 22 по-прежнему на `calcSticker` и при непомещении обнуляет цену.
4. Не менять API. В `sticker.js` трактовать пустой `materials` как ошибку и звать `showError`. Боевой `POST` останется 200 с ценой 30.378; текст на копии появится только после перезаписи JS копии. Это не порт JS.

### Варианты (интерьерная печать, 14.11.2026)

Числа — в разделе «Факты: интерьерная печать». Боевую форму 22 ни один вариант не переключает.

1. Отдельная задача-предпосылка на порт интерьерной и широкоформатной ветки в `sticker.py` (Рекомендуется). `print_wide` уже есть: вызов как в JS (`n = 1`, размер расхода резки, принтеры `Technojet160ECO`, `HPLatex335`, `TechnojetXR720`). `calcLaminationWide` в Python нет — порт функции, сейчас это строка `calcLaminationWide module` в `scripts/js_port_gaps_allowed.txt`. Эталон с раннера: лист RAFLACOAT (JS падает на `name`) и рулон с широкой ламинацией (ORAJET3640 + `LaminatDLCLAM`, JS `price` 1732.368832). Две строки `calcSticker call …` снимаются в той задаче. `form-sticker` ждёт, копию по интерьерной печати не принимать, форму 22 не переключать.
2. Расширить scope `form-sticker` и портировать те же два вызова здесь. `sticker.py`, модуль широкой ламинации, тесты, правки `scripts/js_port_gaps_allowed.txt`. Боевую форму не переключать, пока копия не сойдётся с раннером на этих кейсах.
3. Принять копию для «без печати» и лазера `KMBizhubC220`. Боевую форму 22 не переключать. Широкую ветку (интерьерная, широкоформатная, `dpdRollWideLaminat`) вынести в отдельную задачу до переключения боя. На копии интерьерная печать останется ценой без печати: дефолт RAFLACOAT — 700 ₽, у старой формы при том же выборе цена 0.
4. Не портировать расчёт. В `sticker.js` при широком принтере не показывать цену резки как итог с печатью (ошибка или пустая цена). Это не сходимость: на ORAJET3640 старый JS даёт 1000 / 1800 / 2800 ₽. Имеет смысл только если интерьер на копии до отдельной задачи не нужен и нельзя оставлять цену «без печати».

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
