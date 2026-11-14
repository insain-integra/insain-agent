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
- После `close` `sticker-print-wide` (закрыто 2026-11-14, `docs/history/log.md`) (статус этой задачи станет `черновик`): в `wp-plugin/forms/sticker.js` передавать в `calcApi` широкие `printer_code` (`Technojet160ECO`, `HPLatex335`, `TechnojetXR720`) с `color` `4+0`; для `Technojet160ECO` — `lamination_id` из `dpdRollWideLaminat` (1064), если не `No`; свериться с формой 22 (элемент 811 / 1064). Перезаписать custom JS копии 97 тем же текстом. На копии сверить кейсы интерьерной печати с раннером / API. Бой 22 не переключать.
- В git (Implementer, расширение 15.11.2026): запасная ветка рулона в `calc_service/calculators/cut_plotter.py`, когда изделие не помещается на плоттер (обе стороны больше ширины плоттера 603 мм). Длина как в `js_legacy/calc/calcCutPlotter.js`: `(maxSize * numWithDefects * numBondPlotter + numSheet * (margins[0]+margins[2])) * numBondMaterial`. Ширина рулона — та, у которой стоимость материала меньше, не первый размер. `wp-plugin/forms/sticker.js` не менять. Эталоны с раннера `# JS, 15.11.2026`: ORAJET3640, density 0, difficulty 1, mode 1, size_item 50. 1000×1000 — 1 шт и 100 шт (ширина 1260, длина 1.3866666666666665 м и 72.8 м). 604×604 1 шт — ширина 1520, длина 0.5152 м. Контроль, короткая сторона ≤ 603 мм: 500×500 и 1000×500 1 шт — цена и длина не сдвигаются. Соседи `poly_sticker`, `poly_sticker_pack`, `keychain` и `test_api.py` не сдвигаются. Команды раннера — в `docs/js-runner-cases.md`.
- После слияния в `main` и зелёного CI (Site ops, skill `deploy-api`): выкатка API, потому что правка `cut_plotter.py` меняет ответ. Затем на копии 97 под админом ORAJET3640, 1 шт, 1000×1000, без печати: `POST /api/v1/calc/sticker` `price` 890.06336 (не 1934.19008), расход около 1.39 м, не 4.16 м. На странице округление `showResult` от этой цены (900 ₽), не от тройного расхода. 500×500 остаётся `price` 421.77376. Боевую форму 22 не переключать. Черновик 2586891 остаётся `draft`.

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
- Цены, `calc_service/data/`. Порт `calcPrintWide` / `calcLaminationWide` / модуль `lamination_wide` / `scripts/js_port_gaps_allowed.txt` / `scripts/run_js_calc.mjs` — задача `sticker-print-wide` (закрыто 2026-11-14, `docs/history/log.md`).
- Правка `sticker.py` в этой задаче (кроме уже сделанного проброса ошибки резки): широкая печать — в предпосылке.
- `wp-plugin/js/insain-calc-bridge.js`, пока HTTP 400 доходит до уже существующего `showError`.
- Рулонная ветка `cut_plotter`: ошибку «Размер изделия больше допустимого» JS там не бросает, здесь тоже не бросать. Коэффициент `numBondMaterial` и выбор ширины — scope расширения 15.11.2026, только когда изделие не помещается на плоттер.
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
- [x] ORAJET3640, size_item 50, density 0, difficulty 1, mode 1. Запасная ветка (обе стороны > 603): `CutPlotterCalculator` и `StickerCalculator`. 1000×1000 1 шт — cut `cost` / `price` / `time_ready` 230 / 368 / 16.13, материал `[1260, 0]` × 1.3866666666666665 м; sticker `price` 890.06336, `time_ready` 16.13. 100 шт — cut 7548 / 12077 / 20.25, 72.8 м; sticker `price` 39485.3264, `time_ready` 20.25. 604×604 1 шт — ширина 1520, 0.5152 м; cut 201 / 322 / 16.12; sticker `price` 555.9914752, `time_ready` 16.12. Пометка `# JS, 15.11.2026`. Допуск `cost` / `price` / `time_ready` rel ≤ 0.001. У 604×604 `time_ready` Python на 0.01 ч ниже (`round` против `Math.ceil`) — в допуске.
- [x] Контроль, короткая сторона ≤ 603 мм, 1 шт: 500×500 и 1000×500. Sticker `price` 421.77376 и 674.54752, `time_ready` 16.08 и 16.1, ширина 1260, длина 0.52 м и 1.04 м. Cut `price` 226 и 283. Не сдвигаются.
- [x] Новые тесты запасной ветки без правки `cut_plotter.py` падают (длина ×3, на 604×604 ширина 1260 вместо 1520). Контроль 500×500 и 1000×500 при этом зелёный. С правкой соседи `poly_sticker`, `poly_sticker_pack`, `keychain` и `test_api.py` остаются зелёными.
- [ ] После слияния в `main`, зелёный CI, skill `deploy-api`: на копии 97 под админом ORAJET3640 1000×1000 1 шт без печати — POST `price` 890.06336, не 1934.19008; на странице 900 ₽, не цена тройного расхода. 500×500 — POST `price` 421.77376. Боевая форма 22 на `calcSticker`. Черновик 2586891 — `draft`. `sticker.js` в этом круге не менялся.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая страница клиентам не меняется. Текст ошибки на копии 97 появится только после `deploy-api`.
- Цены: JSON не править. Расхождение 50×50 VHI80 не выравнивать. Другое расхождение JS и API (rel > 0.001) на боевом калькуляторе — стоп. Ошибка «не помещается на лист» — только листовая ветка `cut_plotter`. Запасная ветка рулона (15.11.2026) меняет цену и метры, когда обе стороны больше 603 мм: на копии 97 новая цена появится только после `deploy-api`. `sticker` и `cut_plotter` не стоят на боевой форме API.
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
14.11.2026 — Analyst, Grok 4.7 — оформлена `sticker-print-wide` (закрыто 2026-11-14, `docs/history/log.md`); статус ждёт предпосылку — дальше закрытие `sticker-print-wide`, затем Implementer этой задачи
15.11.2026 — Implementer, Grok 4.7 — `sticker.js`: широкие `printer_code` и `lamination_id` из 1064; тест без правки падал — дальше Site ops (перезапись JS копии 97, сверка интерьерной печати). Боевую форму 22 не переключать.
15.11.2026 — Site ops, Grok 4.7 — custom JS копии 97 перезаписан из рабочей копии `sticker.js`; интерьерная печать на копии сходится с боевым POST — дальше Reviewer, Auto
15.11.2026 — Reviewer, Auto — ревью 3 принято — дальше человек (слияние / finish-task)
15.11.2026 — человек — замечание при приёмке копии: расчёт для размера 1000×1000 мм не сходится, расход по материалу неадекватный — дальше Implementer
15.11.2026 — Implementer, Grok 4.7 — 1000×1000 рулон: цена и метры плёнки в 3 раза выше JS, причина в `cut_plotter.py`, не в `sticker.js` — дальше человек
15.11.2026 — человек — выбран вариант 1: расширить scope `form-sticker` и починить коэффициент длины рулона (`numBondMaterial`) и выбор ширины в `cut_plotter.py` — дальше Implementer
15.11.2026 — Implementer, Grok 4.7 — `numBondMaterial` и ширина рулона по минимальной стоимости в `cut_plotter.py`, эталоны с раннера — дальше Reviewer, Auto
15.11.2026 — Reviewer, Auto — ревью 4 принято — дальше человек (слияние в `main`, `deploy-api`, Site ops: критерий копии 97 на 1000×1000)
15.11.2026 — человек — принято для выкатки, слить в main и выкатить API — выкатка

Блокер: на рулоне ORAJET3640 при 1000×1000 мм локальный `StickerCalculator` и боевой `POST /api/v1/calc/sticker` дают цену и расход плёнки ровно в 3 раза выше старого JS. Резка как операция совпадает (cost/price плоттера те же). Листовой RAFLACOAT на 1000×1000 и JS, и API уже отвечают ошибкой «Размер изделия больше допустимого». `wp-plugin/forms/sticker.js` размеры не портит.
Пробовал: раннер `node scripts/run_js_calc.mjs calcSticker|calcCutPlotter --data current` и тот же вызов локально / `POST https://insain.ru/api/v1/calc/sticker`. Поля как у копии 97: `quantity`, `width`, `height`, `size_item`, `density` 0, `difficulty` 1, `mode` 1. ORAJET3640, 1 шт, size_item 50 и 1000 — одно и то же. Без печати JS `price` 890.06336, материал `[1260, 0]` × 1.3866666666666665 м; Python и бой `price` 1934.1900800000003, 4.16 м (4.16 / 1.3866… = 3). 100 шт: JS 39485.3264 и 72.8 м, бой 57081.12 и 218.4 м (тоже ×3). Плоттер с обеих сторон: 1 шт cost 230 / price 368; 100 шт 7548 / 12077. Печать не причина дельты: `Technojet160ECO` добавляет к цене 402 и в JS (1292.06336), и в API (2336.19008); `HPLatex335` добавляет 2173 с обеих сторон; ламинация `LaminatDLCLAM` добавляет 753. Контроль, где изделие помещается на плоттер (короткая сторона ≤ 603): 500×500 и 1000×500 — price совпадает (421.77376 и 674.54752). 604×604, обе стороны больше ширины плоттера — снова расходится (JS 555.9914752, Python 1291.833088). Лист RAFLACOAT, 1 и 100 шт — раннер выход 1 с текстом ошибки, POST HTTP 400, тот же `detail`.
Гипотеза: изделие 1000×1000 не входит в ширину плоттера Graphtec CE5000-60 (`maxSize` 603). JS уходит в ветку «разбиваем на куски» (`calcCutPlotter.js`, иначе после `layoutOnPlotter.length == 0`) и умножает длину на `numBondMaterial` = 1/3. `cut_plotter.py` в этом запасном расчёте при рулоне шире плоттера умножает длину на 1, поэтому 4160 мм вместо 4160/3. `sticker.py` берёт эту длину как расход и стоимость плёнки. Ширина рулона в этом кейсе уже 1260 и там, и там. `size_item` при density 0 на длину не влияет. Копия шлёт `width`/`height` отдельно от `size_item` — подмена полей тут ни при чём.
Вопрос: расширить scope и поправить коэффициент длины (и выбор ширины рулона по минимальной стоимости, как в JS) в `cut_plotter.py` в этой задаче, оформить предпосылку, или принять копию с пробелом.
Следующая сессия: человек
Снято 15.11.2026 (вариант 1): человек расширил scope `form-sticker` на правку `cut_plotter.py`.
Варианты:
1. Расширить scope и починить здесь (Рекомендуется). `sticker` и `cut_plotter` не стоят ни на одной боевой форме API (`docs/site/forms.md`). В запасной ветке рулона, когда изделие не помещается на плоттер, длина как в JS: `(maxSize * numWithDefects * numBondPlotter + numSheet * (margins[0]+margins[2])) * numBondMaterial`, ширина рулона — та, у которой стоимость меньше, не только первый размер. Эталон с раннера, тест падает без правки. 500×500, 1000×500, 50×50 и листовая ошибка не сдвигаются. `sticker.js` не менять. На копии 97 новая цена появится только после `deploy-api`.
2. Предпосылка `todo/<fix>.md` на ту же правку `cut_plotter.py`. `form-sticker` ждёт. Копию по 1000×1000 не принимать, форму 22 не переключать.
3. Принять копию с пробелом. Пока порт не сделают отдельно, рулон при обеих сторонах больше 603 мм остаётся в 3 раза дороже и длиннее старого JS. Боевая форма 22 на `calcSticker` считает 890.06336 и 1.39 м.
4. Не менять Python. В `sticker.js` это не лечится: при 1000×1000 в API уже уходят `width` 1000, `height` 1000, `quantity` и `size_item`. Подмена расхода в JS копии разойдётся с телом POST.

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
Снято оформлением `sticker-print-wide` (закрыто 2026-11-14, `docs/history/log.md`) 14.11.2026 (вариант 1).

## Найдено вне scope

- Ползунок `numDensity` (649): на странице скрыт (`ezfc-hidden`), в инпуте «25%», `factor` 0.01, `calculate_when_hidden` = 0. Плейсхолдер `{{numDensity}}` на дефолте равен 0. В API уходит 0. Поле видно только при сложности 1.7.
- `chkMark` / `isFindMark`: параметра в API `sticker` нет (на `cut_plotter` есть, `sticker.py` его не прокидывает). На дефолте флажок выключен. В `syncUrl` пишется, в `calcApi` не уходит.
- `chkMark` по-прежнему только в URL. Широкие принтеры и `dpdRollWideLaminat` с 15.11.2026 уходят в `calcApi` из git и с той же даты — из custom JS копии 97.
- На живой странице старый JS даёт price 653.134 при тех же материалах (3 листа 320×450 RAFLACOAT). Раннер `--data current` и боевой API — 662.134. `insaincalc.round` обоих — 700. Цены JSON не менялись.
- Боевая страница под админом: старый блок «через менеджера» 800 ₽ и «при заказе с сайта» 700 ₽, срок «2 дня». Копия по `showResult`: «цена» 700 ₽, «со скидкой» 536 ₽, срок «2 дня». Срок совпал. 800 — старое поле, в этой задаче не выравнивается.
- `wp litespeed-purge all` вернул `Error: Something went wrong! Got 400`. `wp cache flush` — `Success`. Превью копии после этого отдало свежий расчёт.
- 1000×1000, рулон и широкая печать: `calcPrintWide` делит площадь на `material.size[0]`. У ORAJET3640 это `[1260, 0]`, частное `NaN`, `mergeMaps` затирает метры резки. Раннер на 1 шт + `Technojet160ECO` отдаёт quantity `null`. Дельта цены печати (+402) при этом совпадает с API. В порт `null` не переносить: после правки длины в таблице остаётся расход резки.
- Рулон + лазер `KMBizhubC220`: раннер `calcSticker` падает (`reading 'density'`), API считает как без печати. К замечанию про 1000×1000 не относится: там есть цена и метры, не обнуление.
- `showError` не обнуляет уже показанную цену: после успешного расчёта слишком большой размер меняет срок на текст ошибки, сумма в колонке цены остаётся прежней. Общее для форм на API. На копии это изменится только с правкой моста и выкладкой плагина.
- JS бросает ошибку на первом листе с раскладкой 0, даже если следующий размер вмещает. Python пропускает неподходящий размер и берёт следующий подходящий; ошибка — когда не подошёл ни один. В `sheet.json` у листовых материалов один размер, для RAFLACOAT это одно и то же.
- Рулон ORAJET3640, 100 шт 50×50, без печати: на 14.11.2026 раннер `price` 577.368832, боевой `POST /api/v1/calc/sticker` 558.59224. Оба `insaincalc.round(..., 100)` дают 600. Перепроверено 15.11.2026: тот же боевой POST — `price` 577.368832, на копии страница 600 ₽. Расхождение 558 на проде больше не воспроизводится.

## Факты: интерьерная печать

Снято 14.11.2026. Боевая форма 22 и копия 97, элемент печати. `sticker.py` и `scripts/js_port_gaps_allowed.txt` не менялись. С 15.11.2026 `wp-plugin/forms/sticker.js` шлёт широкие принтеры в `calcApi`. Копия 97 перезаписана тем же текстом 15.11.2026 (Site ops). Таблица и абзац ниже — снимок до этой перезаписи.

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

До перезаписи 15.11.2026 `wp-plugin/forms/sticker.js` и тот же текст на копии 97 (элемент 3646, `read_file=0`): в `calcApi` печать и ламинация уходили только при `printerId === 'KMBizhubC220'`. Широкий принтер и `dpdRollWideLaminat` писались в URL и в POST не входили. После перезаписи копия шлёт широкие `printer_code`, `color` `4+0` и `lamination_id` для `Technojet160ECO`, если value не `No`.

Абзац ниже — снимок 14.11.2026, до закрытия `sticker-print-wide`. На 15.11.2026 боевой POST уже считает широкую печать; числа — в «Результате».

В `calc_service/calculators/` на 14.11.2026: `print_wide.py` (`PrintWideCalculator`, slug `print_wide`) есть, из `sticker.py` не вызывается. `print_roll.py` вызывает `print_wide` для своего калькулятора. `lamination.py` — это `calcLamination` (ламинатор `FGKFM360`). Файла широкой ламинации нет. `sticker.py` печатает только при `color` и листовом материале, всегда через `PrintLaserCalculator`; исключение печати глотается. В `scripts/js_port_gaps_allowed.txt` для этого пропуска три строки: `calcLaminationWide module`, `calcSticker call calcPrintWide`, `calcSticker call calcLaminationWide`.

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

### 15.11.2026 — Implementer, запасная ветка рулона

- Ветка: `task/form-sticker`. Коммит не создавался.
- Сделано: в `cut_plotter.py` запасная ветка, когда изделие не входит в ширину плоттера (обе стороны > 603 мм). Длина `(maxSize * numWithDefects * numBondPlotter + numSheet * (margins[0]+margins[2])) * numBondMaterial`. Ширина рулона — с меньшей стоимостью материала, как в `calcCutPlotter.js:170–186` и `214–219` (при равной стоимости остаётся более ранняя). `sticker.js` и `sticker.py` не менялись. Команды раннера дописаны в `docs/js-runner-cases.md`.
- Чем проверено (раннер `--data current`, 15.11.2026): ORAJET3640, size_item 50, density 0, difficulty 1, mode 1. 1000×1000 1 шт — sticker `price` 890.06336, `[1260, 0]` × 1.3866666666666665 м; cut `cost` / `price` / `time_ready` 230 / 368 / 16.13. 100 шт — sticker `price` 39485.3264, 72.8 м; cut 7548 / 12077 / 20.25. 604×604 1 шт — ширина 1520, 0.5152 м; sticker `price` 555.9914752; cut 201 / 322 / 16.12. Контроль 500×500 и 1000×500 — sticker `price` 421.77376 и 674.54752.
- Чем проверено (тесты): без правки `cut_plotter.py` (`git stash push -- calc_service/calculators/cut_plotter.py`) `test_roll_bond_when_wider_than_plotter` — 6 failed (1000×1000 длина 4.16 и 218.4 м вместо 1.39 и 72.8; 604×604 ширина 1260 вместо 1520; sticker `cost` 1173.488 / 57081.12 / 785.2368), 4 passed (контроль 500×500 и 1000×500 у cut и sticker). После `stash pop` те же тесты и соседи `test_cut_plotter.py` `test_sticker.py` `test_poly_sticker.py` `test_poly_sticker_pack.py` `test_keychain.py` `test_api.py` — `77 passed`. `python scripts/dev.py check` — код 0, 599 + 81.
- Сходимость после правки: 100 шт и 604×604 sticker `price` совпали с раннером. 1 шт 1000×1000 sticker `price` 890.063485 против 890.06336: длина в ответе округляется до 6 знаков (1.386667), rel < 0.001. У 604×604 `time_ready` Python 16.11 против JS 16.12 (`round` против `Math.ceil`), rel < 0.001. Контроль 500×500 и 1000×500 не сдвинулся.
- Не сделано и почему: выкладка API и проверка копии 97 — после слияния в `main`, skill `deploy-api`, Site ops. Боевая форма 22 не переключалась. Коммит не создавался.
- Требуется решение: нет. Дальше Reviewer.
- Для Reviewer: diff этого круга — `cut_plotter.py`, тесты `test_cut_plotter.py` и `test_sticker.py`, `docs/js-runner-cases.md`, `todo/form-sticker.md`. `sticker.js` и `test_wp_plugin_forms.py` в рабочей копии с прошлого круга (ревью 3), в этой сессии не менялись. Открытый критерий копии 97 (1000×1000 → 890.06336) локально не проверяется.

### 15.11.2026 — Implementer, 1000×1000

- Ветка: `task/form-sticker`. Коммит не создавался. `sticker.js`, `sticker.py`, `cut_plotter.py` в этой сессии не менялись.
- Сделано: сверка 1000×1000. Причина не в `wp-plugin/forms/sticker.js`. Копия шлёт `quantity`, `width`, `height`, `size_item` раздельно; при density 0 `size_item` 50 и 1000 дают одни числа. Расхождение — запасная раскладка рулона в `cut_plotter.py`, когда обе стороны больше ширины плоттера 603 мм: длина без коэффициента `numBondMaterial` (1/3), расход и цена плёнки ×3. Печать и широкая ламинация к этой дельте не добавляют своего расхождения. Лист RAFLACOAT уже ошибка и в JS, и в API.
- Чем проверено: раннер `--data current` (`calcSticker`, `calcCutPlotter`), локальные `StickerCalculator` / `CutPlotterCalculator`, `POST https://insain.ru/api/v1/calc/sticker`. Числа — в блокере журнала от 15.11.2026. Бой совпал с локальным Python.
- Не сделано и почему: правку `cut_plotter.py` не вносил. Рулонная раскладка вне scope этой задачи; предыдущие такие расширения шли через решение человека. `make check` не запускался: кода калькулятора нет.
- Требуется решение: вариант из блока «Варианты» в журнале (расширить scope / предпосылка / принять пробел / не трогать Python).

### 15.11.2026 — Site ops, перезапись JS копии 97

- Сделано: custom JS элемента 3646 (`cjsCalc`) формы 97 перезаписан из рабочей копии `wp-plugin/forms/sticker.js` (ветка `task/form-sticker`, не из HEAD). Id `get_value_from` подставлены картой 22 → 97. `--get` не передавался. Форма заново не дублировалась. Боевая форма 22 не читалась на запись и не переключалась. Плагин не выкладывался, `deploy-api` не запускался. Черновик 2586891 остался `draft`.
- Пакет: только элемент 3646, `custom_calculation` 4224 → 4891 байт, `calcApi=1`, `read_file` `0` = `0`. В JS копии id 3632, 3633, 3636, 3638, 3639, 3640, 3641, 3642, 3643, 3644, 3660. Id боевой формы в `get_value_from` нет. Три строки карты без id копии (`sbtPrice` 640, `sbtPriceTotal` 639, `grpPriceCustomer` 637) в пакет не входили: этих элементов на копии нет, в `sticker.js` они не читаются. GET без изменений: `numN`, `dpdMaterial`/`dpdPrint`/`dpdRollLaminat`/`dpdRollWideLaminat` = `index`, `rdoModeProduction` = `value`.
- Чем проверено (бой API, `curl`): ORAJET3640, 100 шт, 50×50, size_item 50, density 0, difficulty 1, mode 1. Без печати `price` 577.368832 (не 558.59224). `Technojet160ECO` 979.368832. Тот же принтер и `LaminatDLCLAM` 1732.368832. `HPLatex335` 2750.368832. `TechnojetXR720` 1003.368832. RAFLACOAT без печати 662.134. RAFLACOAT и каждый из трёх широких принтеров — HTTP 400, `detail` `Широкоформатная печать доступна только на рулонном материале`.
- Чем проверено (копия 97, превью 2586891 под админом): те же входы. Страница: без печати на рулоне 600 ₽; экосольвент 1 000 ₽; экосольвент и глянцевая широкая ламинация (`LaminatDLCLAM`) 1 800 ₽; латекс 2 800 ₽, в POST ламинации нет; сольвент и УФ (оба value `TechnojetXR720`) 1 100 ₽. Срок на этих ответах «Срок 2 дня». Лист RAFLACOAT и `Technojet160ECO`, `HPLatex335`, `TechnojetXR720` — POST 400, в `.htmTime` «Ошибка: Широкоформатная печать доступна только на рулонном материале», не расчёт без печати. Дефолт RAFLACOAT без печати: POST `price` 662.134, на странице 700 ₽ и «Срок 2 дня». После ошибки возврат на «Без печати» снова даёт 700 ₽.
- Чем проверено (форма не уехала на витрину): `wp post get 2586891 --field=post_status` — `draft`. `curl.exe` без cookies на `/?post_type=product&p=2586891` — `404`. Элемент 629 формы 22 — `calcSticker`, не `calcApi`. Страница https://insain.ru/catalog/plotternaya-rezka/ содержит `calcSticker`, вызова `calcApi('sticker'` нет. `wp litespeed-purge all` — `Got 400` (как раньше). `wp cache flush` — `Success`.
- Не сделано и почему: плагин не выкладывался, API не деплоился, боевая форма 22 не переключалась — так в задаче этой сессии. Коммит не создавался.
- Как откатить: бэкап элемента 3646 `/tmp/ezfc-copy-97-20261114-200212.json`. Предыдущий бэкап копии `/tmp/ezfc-copy-97-20261113-190404.json`. Копию и черновик не удалять.
- Требуется решение: нет.
- Для Reviewer: diff `sticker.js` не закоммичен, источник — рабочая копия ветки. Id в git — боевая форма 22. На копии их подставил `ezfc_copy.py`. Колонка цены при HTTP 400 остаётся от прошлого успешного расчёта (`showError` её не обнуляет) — уже в «Найдено вне scope».

### 15.11.2026 — широкая печать в JS

- Ветка: `task/form-sticker`, коммит не создавался. Поверх `a3775c2` (закрытие `sticker-print-wide`).
- Сделано: `wp-plugin/forms/sticker.js` передаёт в `calcApi` `printer_code` `Technojet160ECO`, `HPLatex335`, `TechnojetXR720` и `color` `4+0`. Для `Technojet160ECO`, если value элемента 1064 не `No`, — `lamination_id`. Лазер `KMBizhubC220` и листовая ламинация 1063 без изменений. Id — боевая форма 22 (811 / 1063 / 1064). Формул цены нет. `catch` по-прежнему вызывает `showError`.
- Чем проверено: до правки `python -m pytest calc_service/tests/test_wp_plugin_forms.py::test_sticker_js_posts_wide_print -q` — `1 failed` (нет `get_value_from(1064, true)[0]`). После правки `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — `29 passed`. `python scripts/dev.py check` — код 0, 589 + 81. `Select-String` по `calcApi('sticker'`, `syncUrl(`, `showResult(` — три вхождения (строки 44, 88, 89). Value элементов 811/1064 сверены с разделом «Факты» от 14.11.2026; повторный SELECT на проде не делался.
- Не сделано в сессии Implementer: custom JS копии 97 — это был Site ops, перезаписан в разделе выше. Боевая форма 22 не переключалась. Плагин не выкладывался. `sticker.py` не менялся.
- Требуется решение: нет.
- Для Site ops, рулон ORAJET3640, 100 шт, 50×50, size_item 50, density 0, difficulty 1, mode 1. `price` из `test_sticker.py`: без печати 577.368832; `Technojet160ECO` 979.368832; тот же принтер и `LaminatDLCLAM` 1732.368832; `HPLatex335` 2750.368832; `TechnojetXR720` 1003.368832. Лист RAFLACOAT и любой из трёх широких принтеров — HTTP 400, `detail` `Широкоформатная печать доступна только на рулонном материале` (в блоке срока «Ошибка: …», не цена без печати). Дефолт без печати: 662.134, на странице 700 ₽.

### Ранее (до широкой печати в JS)

- Ветка, PR или коммит: `main` @ `73a52f6` (CI `completed success`). Прод API выкачен этим коммитом с `7c88dfb`. Форма 97 `CalcSticker duplicate`, товар 2586891 «Плоттерная резка (Копировать)», `post_status` `draft`.
- Сделано: дубль формы 22 (строка 97) и черновик 2586891, JS копии с GET. Боевая форма 22 и товар 5601 не менялись. Порт ошибки: листовой `cut_plotter` при раскладке 0 на всех размерах бросает `ValueError('Размер изделия больше допустимого')` вместо пустого результата. `sticker.py` не менялся — вызов резки не в `try`, исключение доходит до `POST /calc/sticker`. `sticker.js` и `showError` не менялись: `catch` уже пишет `detail` во внутренний `div` `.htmTime` как `Ошибка: …`. API `73a52f6` выкачен на прод skill `deploy-api`; копия 97 показывает ошибку размера, боевая форма 22 осталась на `calcSticker`.
- Чем проверено (копия, прошлая сессия): `wp post get 2586891 --field=post_status` — `draft`. `curl.exe` без cookies на `/?post_type=product&p=2586891` — `404`. Превью под админом: `POST /api/v1/calc/sticker` 200, `price` 662.134, на странице 700 ₽. Боевая страница на `calcSticker`.
- Чем проверено (порт): до правки `pytest -k "larger_than_material or just_fits or oversize_sheet_http"` — 8 failed (`DID NOT RAISE`, HTTP 200: cut `price` 0, sticker `price` 30.378), 4 passed (280×430 и 281×280). После правки те же кейсы и соседи — `56 passed`. Раннер `calcCutPlotter` на 400×400 — выход 1, текст ошибки; на 280×430 — `price` 5228, `time_ready` 17.85; на 281×280 — `price` 4776, `time_ready` 17.69. `python scripts/dev.py check` — код 0, 563 + 81.
- Чем проверено (выкатка 14.11.2026): `bash infra/deploy.sh` на VDS — fast-forward `7c88dfb` → `73a52f6`, smoke скрипта `GET /api/v1/calculators` 200 и `POST /api/v1/calc/puzzle` 200, контейнер healthy. `POST /api/v1/calc/sticker` дефолт (100 шт, 50×50, RAFLACOAT) — HTTP 200, `price` 662.134. Oversize 400×400 RAFLACOAT тираж 100 — HTTP 400, `detail` `Размер изделия больше допустимого`. Превью копии под админом: тот же POST 400, `.htmTime` — `Ошибка: Размер изделия больше допустимого`; возврат 50×50 — POST 200, `price` 662.134, на странице `700 руб.` и `Срок 2 дня`. `wp post get 2586891 --field=post_status` — `draft`. Боевая страница https://insain.ru/catalog/plotternaya-rezka/ содержит `insaincalc.calcSticker(`, вызова `calcApi` нет. Копия и форма 22 не перезаписывались.
- Не сделано и почему: боевая форма 22 не переключалась (так и задумано). Выкладка плагина нет — вне scope. `sticker.py` не менялся: подстановка 1 листа не выполняется, потому что резка бросает исключение раньше.
- Требуется решение: нет. Выбрана предпосылка `sticker-print-wide` (закрыто 2026-11-14, `docs/history/log.md`). `finish-task` не запускать, пока широкая ветка не сойдётся на копии 97 после возобновления этой задачи.
- Как откатить: перед выкаткой `deploy.sh` сохранил предыдущий образ как `insain-agent-calc-api:rollback` (сервер был на `7c88dfb`). Копию и черновик не удалять. Бэкап элементов копии: `/tmp/ezfc-copy-97-20261113-190404.json`.
- Поля только в URL, не в `calcApi`: `chkMark`. Файл `fluAtrwork` в URL не кладётся. С 15.11.2026 широкие `dpdPrint` и `dpdRollWideLaminat` (если не `No` и принтер `Technojet160ECO`) уходят в `calcApi` из git и из custom JS копии 97.
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

## Ревью 3

**Итог:** принято. Статус `ревью` — `sticker.js` и тест широкой печати ещё не в `main`; дальше человек: коммит/слияние ветки `task/form-sticker`, затем `finish-task` (без переключения боевой формы 22).

### Критерии (широкая печать в JS, git / локально)

| Критерий | Проверка |
| --- | --- |
| Scope §32: широкие `printer_code` | `Technojet160ECO`, `HPLatex335`, `TechnojetXR720` → `params.color` `4+0` и `params.printer_code` в ветке `else if` (строки 80–85 `sticker.js`) |
| `Technojet160ECO` + ламинация 1064 | `wideLaminat` из `get_value_from(1064, …)`; `lamination_id` только если value не `No` (83–85) |
| Лазер без регрессии | `KMBizhubC220` + листовая 1063 — без изменения логики |
| Id формы 22 | 811 / 1063 / 1064 в git; на копии 97 — подстановка `ezfc_copy.py` (отчёт Site ops 15.11.2026) |
| Контракт формы | `calcApi('sticker'`, `syncUrl(`, `showResult(` — три вхождения; `catch` → `showError`; `\bprice\s*=` в файле нет |
| Тест контракта | `test_sticker_js_posts_wide_print` в `test_wp_plugin_forms.py` — читает `sticker.js`, падает без правки (проверено по diff) |
| pytest | `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_wp_plugin_forms.py -q` — **28 passed** |
| `make check` | `python scripts/dev.py check` — код 0, 589 + 81 |

### Diff (круг 3, рабочая копия)

- `wp-plugin/forms/sticker.js` — широкая печать и `lamination_id` из 1064; комментарии; **modified, не закоммичен**.
- `calc_service/tests/test_wp_plugin_forms.py` — новый `test_sticker_js_posts_wide_print`.
- `todo/form-sticker.md`, `docs/dashboard.md` — служебно (журнал, Site ops, ревью).

`sticker.py`, `cut_plotter.py`, мост — без diff в этом круге (широкий расчёт на API — предпосылка `sticker-print-wide`, уже в проде).

### Сверка с Site ops 15.11.2026

Повторного прогона копии 97 / превью 2586891 не делалось (регламент Reviewer после приёмки копии).

| Заявление Site ops | Diff / локально |
| --- | --- |
| Custom JS копии 97 = рабочая копия `sticker.js`, карта 22→97, бой 22 не трогали | Соответствует: id в git — форма 22; на копии — `ezfc_copy.py` |
| ORAJET3640 + широкие принтеры: `price` API 577.37 / 979.37 / 1732.37 / 2750.37 / 1003.37; страница 600 / 1000 / 1800 / 2800 / 1100 ₽ | JS шлёт `printer_code`, `color` `4+0`, ламинацию для экосольвента — условие совпадает с отчётом |
| RAFLACOAT + широкий принтер → HTTP 400, `.htmTime` «Ошибка: Широкоформатная печать…» | POST с полями из diff; не подменяется цена «без печати» (700 ₽) |
| Дефолт без печати 662.134 / 700 ₽; черновик `draft`; форма 22 — `calcSticker` | Вне diff круга 3; в отчёте зафиксировано, противоречий с diff нет |
| Плагин не выкладывали, `deploy-api` не запускали | Согласовано с ограничениями задачи |

### Замечания

- **желательно:** в слиянии — один коммит с `wp-plugin/forms/sticker.js`, `test_wp_plugin_forms.py` и служебными правками задачи; до merge файл остаётся только в рабочей копии ветки.
- **желательно:** при `finish-task` — строка «Состав пакета» (копия 97 / 2586891), как в ревью 1–2.
- **вне scope:** `showError` не обнуляет колонку цены после успешного расчёта — в «Найдено вне scope»; Site ops подтвердил на HTTP 400.

## Ревью 4

**Итог:** принято. Статус `ревью` — слияние ветки `task/form-sticker` в `main` (человек), затем skill `deploy-api` и открытый критерий копии 97 (ORAJET3640 1000×1000 → `price` 890.06336). Прод в этом ревью не гонялось.

### Критерии (расширение 15.11.2026, git / локально)

| Критерий | Проверка |
| --- | --- |
| Запасная ветка рулона, обе стороны > 603 мм | `layout_on_roll` на ширине плоттера пустой → `_bond_roll_layout` + перебор `roll_sizes`; формула длины с `numBondMaterial` (стр. 72–109, 308–336 `cut_plotter.py`) совпадает с `calcCutPlotter.js:157–168` |
| Ширина рулона | `_roll_piece_cost` + `_tier_price_js` (170–186 JS); выбор `min cost`, при равенстве остаётся более ранняя ширина — кейс 604×604 → 1520 мм |
| `sticker.js` / `sticker.py` | В круге 4 без diff; цена стикера тянет метры из `cut_plotter` |
| Эталоны `# JS, 15.11.2026` | `test_roll_bond_when_wider_than_plotter` в `test_cut_plotter.py` и `test_sticker.py`: 1000×1000 (1 и 100 шт), 604×604, контроль 500×500 и 1000×500 |
| Тест без правки падает | `git stash` только `cut_plotter.py` → **6 failed** (длина ×3, 604×604 ширина 1260), **4 passed** (контроль) — повторено Reviewer |
| Регресс соседей | `pytest` cut_plotter + sticker + poly_sticker + poly_sticker_pack + keychain + test_api — **77 passed** |
| Листовая ошибка и границы 14.11 | Не в diff круга 4; логика `ValueError` на листе не тронута |
| `make check` | `python scripts/dev.py check` — код **0**, **599 + 81** (повторно после `stash pop`) |
| `docs/js-runner-cases.md` | Строки ORAJET3640 1000×1000 / 604×604 и сноска 15.11.2026 — в diff круга |

### Diff (круг 4)

- `calc_service/calculators/cut_plotter.py` — `_bond_roll_layout`, `_tier_price_js`, `_roll_piece_cost`, ветка `not plotter_fits`.
- `calc_service/tests/test_calculators/test_cut_plotter.py`, `test_sticker.py` — `test_roll_bond_when_wider_than_plotter`.
- `docs/js-runner-cases.md`, `todo/form-sticker.md` — служебно.
- `wp-plugin/forms/sticker.js`, `test_wp_plugin_forms.py` — из ревью 3, в круге 4 не менялись (всё ещё **не закоммичено** в git).

### Критерии на проде

- Открыт: после merge, CI, `deploy-api` — копия 97, ORAJET3640 1000×1000 1 шт без печати, POST `price` 890.06336 и ~900 ₽ на странице; 500×500 — 421.77376. Маршрут Site ops, не Reviewer.

### Замечания

- **желательно:** одно слияние/коммит со всеми артефактами ветки: `cut_plotter.py`, тесты круга 4, `sticker.js` и `test_wp_plugin_forms.py` (круг 3), `docs/js-runner-cases.md`, `todo/form-sticker.md`.
- **желательно:** при `finish-task` — строка «Состав пакета» (копия 97 / 2586891), как в ревью 1–3.
- **желательно:** без `deploy-api` новый расчёт 1000×1000 на проде останется ×3 — ожидаемо до выкатки API.
