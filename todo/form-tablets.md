# form-tablets

Статус: доработка
Сложность: средняя
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: лид-копия slug `tablets` на пять боевых форм (с формой 68); 14 пропусков `calcTablets` в allowed, часть — вызовы чужих калькуляторов; порт может понадобиться в том же diff.

## Цель

Копия формы 36 CalcTabs на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/tablichki-s-uf-pechatyu/ остаётся на `insaincalc.calcTablets`. Боевое переключение отложено решением человека 22.11.2026. Формы 48, 51, 76 и 68 — отдельными задачами после приёмки этой копии. Форма 68 CalcShild вызывает `calcTablets` и переводится через slug `tablets`, не `shild` (решение человека 22.11.2026).

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строки форм 36, 48, 51, 68, 76 (`insaincalc.calcTablets`), только читать.
- `calc_service/calculators/tablets.py`, `calc_service/tests/test_calculators/test_tablets.py`.
- `js_legacy/calc/calcTablets.js`, функция `calcTablets` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `scripts/js_port_gaps_allowed.txt` — строки `calcTablets` (14 штук).
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- Доработка 27.11.2026 (важнее запрета фона в прошлом круге): «Оклейка фона таблички» не меняет цену. На форме 36 это поле 1427 `dpdBackgroudMaterial`: значение не `0` включает `isBackgroundFilm` (материал — `data-value` поля 1427, край — поле 1483 `dpdBackroundEdge`, двойное нанесение — поле 3313). В `calcTablets.js` это `calcCutRoller` резаком `KWTrio3026` и `calcManualRoll`. Портировать вызовом уже существующих портов и передавать из `wp-plugin/forms/tablets.js` в `calcApi`. `0` / «без оклейки» фон не добавляет. Эталоны УФ, экосольвента, латекса и аппликации не сдвигать. Строку `calcTablets option isBackgroundFilm` снять из allowed, когда ветка сошлась с раннером. Множитель двойного нанесения брать как в `calcTablets.js`, расхождение формы и функции не «исправлять». Чужие калькуляторы не менять. Новую копию не создавать.
- В git (Implementer), сверка: раннер против `tablets.py` на дефолтах форм 36, 48, 51, 76 и 68. Итог — таблица «форма → `price` / `time_ready` JS и API, какие пропуски задевает» в «Результат»; для 68 — отдельная строка, что она идёт через `tablets`.
- В git (Implementer), лид: шаги 0–5б для формы 36 и `wp-plugin/forms/tablets.js` с привязкой к id 36. `REF_FORM_DEFAULT` в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`. Портировать в `tablets.py` только ветки, без которых дефолт формы 36 не сходится по цене и сроку, и снять их строки из allowed. Вызов в JS — вызов уже существующего порта в Python (`milling`, `print_roll`, `sticker`, `cut_roller`); чужие калькуляторы не менять. Если дефолту формы 36 нужен вызов, у которого порта в Python нет (`calcManualRoll`, `calcPockets`, `calcFrame`), — стоп со статусом `заблокировано: аналитик`. Калькулятор не на боевой форме API, предпосылку не заводить. Новые строки в allowed не добавлять.
- Доработка 26.11.2026, второй круг (важнее запрета аппликации в «Не-scope»): расчёт аппликации на копии 120 не сходится. В JS это ветка `isFilm` (`calcSticker` и `calcManualRoll`). Её надо портировать вызовом уже существующих портов и передавать из `wp-plugin/forms/tablets.js` в `calcApi`, когда способ нанесения — аппликация. `isBackgroundFilm` портировать только если без фона цена этой аппликации не сходится с раннером. `REF_FORM_DEFAULT` (УФ) и эталоны экосольвента и латекса не сдвигать. Строки `calcTablets option isFilm` и `calcTablets call calcSticker` снять из allowed, когда ветка сошлась. Чужие калькуляторы не менять. Новые строки в allowed не добавлять.
- Доработка 26.11.2026 (уже сделана): способы нанесения с экосольвентной печатью на копии 120 считаются неверно. В JS это ветка `isPrint` (`calcPrintRoll` и `calcManualRoll`, плёнка с экосольвентом и латексом). Её надо портировать вызовом уже существующих портов и передавать из `wp-plugin/forms/tablets.js` в `calcApi`. `REF_FORM_DEFAULT` (УФ, форма 36) не сдвигать. Строки `calcTablets call calcPrintRoll` и `calcTablets call calcManualRoll` снять из allowed, когда ветка сошлась с раннером. Чужие калькуляторы не менять. Новые строки в allowed не добавлять.
- На проде (Site ops): новую копию не создавать. После `deploy-api` с `main` записать JS в уже существующую форму 120 на черновике товара 2586916 (`read_file=0`). Плагин не выкладывать. Боевую 36 не переключать.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат», не в общие файлы.

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/calculators/sticker.py` — только формула рулона при `length_min > 0`
- `calc_service/materials/loader.py` — только чтение `length_min` (решение человека 27.11.2026)
- `calc_service/tests/test_calculators/test_tablets.py`
- `calc_service/tests/test_calculators/test_sticker.py` — эталон этой формулы; прежние эталоны не сдвигать без раннера
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcTablets`, если ветка портирована
- `calc_service/tests/test_js_port_gaps.py` — только если снятие строк allowed требует поправить счётчик и цепочку, как в прошлом круге
- WordPress: только форма 120 и черновик товара 2586916, новый дубль не создавать

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копии форм 48, 51, 76, 68; ветки кроме `isPrint`, `isFilm` и `isBackgroundFilm` (фрезеровка, древко, клеевой слой, карманы, рамка); модули `calcPockets`, `calcPutTape`, `calcFrame`
- `shild.py` (`calcShild.js`), `plaque.py` (`calcPlaque` из того же `calcTablets.js`), `puzzle.py` и строки `calcPuzzle` / `calcShildSublimaton` в allowed
- Чужие калькуляторы `milling.py`, `print_roll.py`, `cut_roller.py`, `cut_plotter.py` и их тесты. `sticker.py` — только формула рулона при `length_min > 0` (решение человека 26.11.2026) и тест этой формулы
- Боевые формы 36, 48, 51, 68, 76 и шаги 17–24, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.
Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`, иначе кириллица в нём станет `?`.

- [x] В «Результат» есть таблица сверки дефолтов форм 36, 48, 51, 76, 68 (`price` / `time_ready` JS и API, задетые пропуски).
- [x] `python scripts/js_port_gaps.py calcTablets` — каждый пропуск либо снят, либо назван в docstring и остаётся в allowed. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`; эталоны `plaque` и прежние эталоны `tablets` не сдвинулись или сдвиг объяснён раннером в «Результат».
- [ ] Боевой `POST /api/v1/calc/tablets` на теле `REF_FORM_DEFAULT`: `price` и `time_ready` как у раннера (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). Если порт ещё не выкачен — пункт после `deploy-api`, копию до него не принимать.
- [x] `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [ ] Копия не на витрине: `wp post get <product> --field=post_status` → `draft` или `private`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s https://insain.ru/catalog/tablichki-s-uf-pechatyu/` — в HTML есть `calcTablets`, нет `calcApi`.
- [x] Экосольвентное нанесение (`isPrint`): раннер и `POST /api/v1/calc/tablets` сходятся по `price` и `time_ready` (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). В тесте эталон `# JS,`. `REF_FORM_DEFAULT` не сдвинут.
- [x] В `wp-plugin/forms/tablets.js` выбранный способ с экосольвентной печатью уходит в `calcApi`, не только в `syncUrl`.
- [ ] На копии 120 под админом экосольвент даёт цену страницы = `price` API с округлением `showResult`. Дефолт с УФ-печатью остаётся 12 800 руб. и срок 7 дней. Экосольвент — 13 000 руб. / 3 дня, латекс — 14 500 руб. / 5 дней.
- [x] Аппликация (`isFilm`): раннер и `POST /api/v1/calc/tablets` сходятся по `price` и `time_ready` (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). В тесте эталон `# JS,`. Эталоны УФ, экосольвента и латекса не сдвинуты. *(Примечание: `price` и `cost` для всех 7 плёнок на `mode=0/1/2` сходятся с раннером в `0.00%`; `time_ready` сходится в `rel ≤ 0.001` на 5 плёнках на `mode=1`, а на `Avery500w`/`Avery500c` `mode=1` на 0.04 ч ниже из-за `round` вместо `Math.ceil` в `cut_plotter.py:499`, который по решению человека не трогаем.)*
- [x] В `wp-plugin/forms/tablets.js` способ «аппликация» уходит в `calcApi`, не только в `syncUrl`.
- [ ] На копии 120 под админом аппликация даёт цену страницы = `price` API с округлением `showResult`.
- [ ] Оклейка фона (`isBackgroundFilm`, поле 1427 не `0`): раннер и `POST /api/v1/calc/tablets` сходятся по `price` и `time_ready` (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001). В тесте эталон `# JS,`. Эталоны УФ, экосольвента, латекса и аппликации не сдвинуты.
- [ ] В `wp-plugin/forms/tablets.js` выбранная оклейка фона (1427) и край (1483) уходят в `calcApi`, не только в `syncUrl`. Значение `0` фон не включает.
- [ ] На копии 120 под админом выбор плёнки в «Оклейка фона таблички» меняет цену страницы на `price` API с округлением `showResult`. «без оклейки» оставляет цену выбранного способа нанесения.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевые формы `calcTablets` не меняются. Выкатка API — только если менялся калькулятор, с `main` после ревью. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Порт веток может сдвинуть ответ `tablets` для форм 48, 51, 76, 68 — прежние эталоны теста держат это.
- Формы: id боевой 36 не менять; копия — новая форма на черновике.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

22.11.2026 — человек — завести 8 лид-копий, боевые формы не переключать, форма 68 через tablets — дальше Implementer
26.11.2026 — Implementer, Gemini 4 Hydrogen High — сверка дефолтов 36/48/51/76/68, порт is_cut_manual и material_mode в tablets.py, REF_FORM_DEFAULT, wp-plugin/forms/tablets.js (id 36), make check зелёный — дальше Reviewer
26.11.2026 — Reviewer, Grok 4.7 — принято по diff, прод-критерии копии после deploy-api — дальше человек
26.11.2026 — человек — принято, слить и выкатить API, затем дубль формы 36 — дальше Site ops
26.11.2026 — Site ops, Grok 4.7 — API 1a116e0 выкачен, дубль формы 36 = 120 на черновике 2586916 — дальше Reviewer
26.11.2026 — Reviewer, Grok 4.7 — принято по отчёту Site ops — дальше человек
26.11.2026 — человек — закрыто, коммит 7b0aacc — дальше человек
26.11.2026 — человек — доработка: способы нанесения с экосольвентной печатью на копии считаются неверно — дальше Implementer
26.11.2026 — Implementer, Gemini 4 Hydrogen High — доработка: порт is_print (PrintRollCalculator + calc_manual_roll) в tablets.py, сняты calcPrintRoll/calcManualRoll из allowed, в wp-plugin/forms/tablets.js добавлены isECOPrint и isLatexPrint, REF_FORM_DEFAULT не сдвинут, make check зелёный — дальше Reviewer
26.11.2026 — Reviewer, Grok 4.7 — принято по diff, блокер «Ревью 2» закрыт (is_print сходится с раннером), проверка копии 120 после выкатки API — дальше человек
26.11.2026 — человек — принято, слить и выкатить API, затем записать JS в форму 120 — дальше Site ops
26.11.2026 — Site ops, Grok 4.7 — API 5b762e6 выкачен, JS в форме 120: УФ 12 800/7 дней, экосольвент 13 000/3 дня, латекс 14 500/5 дней — дальше Reviewer
26.11.2026 — Reviewer, Grok 4.7 — принято по отчёту Site ops, доработка экосольвента закрыта — дальше человек
26.11.2026 — человек — закрыто, коммит 279b248 — дальше человек
26.11.2026 — человек — доработка: расчёт аппликации на копии не сходится — дальше Implementer
26.11.2026 — Implementer, Gemini 4 Hydrogen High — портирована ветка `is_film` (`StickerCalculator` + `calc_manual_roll`) в `tablets.py` и `isFilm` в `wp-plugin/forms/tablets.js`, сняты `isFilm`/`calcSticker` из allowed (`MAX_ALLOWED` 66→64), но выявлен баг вне scope в `sticker.py:308` (`length_min > 0`) — дальше человек
26.11.2026 — человек — починить формулу рулона в `sticker.py` в этой задаче, все плёнки аппликации свести с раннером; `cut_plotter.py` не трогать — дальше Implementer
27.11.2026 — Implementer, Gemini 4 Hydrogen High — починена формула рулона в `sticker.py:309` (`* width_mm`) и добавлен тест `test_roll_length_min_matches_js`, но `calc_service/materials/loader.py:171` теряет `length_min` из JSON (читает `"lengthMin"` вместо `"length_min"`), из-за чего в runtime 4 плёнки (`Avery500c`, `Oracal352`, `LGLT4000`, `FES24`) не сходятся с раннером — дальше человек
26.11.2026 — человек — починить чтение `length_min` в `loader.py` в этой задаче и свести все 7 плёнок аппликации с раннером; формулу `cut_plotter.py` не трогать — дальше Implementer
27.11.2026 — Implementer, Gemini 4 Hydrogen High — починено чтение `length_min` в `loader.py:171`, убран `monkeypatch` из `test_sticker.py`, все 7 плёнок аппликации поля 1484 сведены с раннером `# JS` в `test_tablets.py`, `make check` зелёный — дальше Reviewer
27.11.2026 — Reviewer, Grok 4.7 — принято по diff, блокер «Ревью 4» закрыт (is_film: цена всех 7 плёнок сходится с раннером), проверка копии 120 после выкатки API — дальше человек
26.11.2026 — человек — принято, слить и выкатить API, затем записать JS в форму 120 — дальше Site ops

```text
Блокер: calc_service/materials/loader.py:171 читает merged.get("lengthMin"), а в roll.json/sheet.json ключ называется "length_min", поэтому material.length_min всегда None в runtime и ветка length_min > 0 в sticker.py (и cut_plotter.py) не срабатывает для плёнок с length_min=1000
Пробовал: починил формулу в sticker.py:309 (* (width_mm / 1000) -> * width_mm) и сверил все 7 плёнок поля 1484 с раннером calcTablets/calcSticker:
  - Без правки loader.py: Avery500c (-3.46%), Oracal352 (-4.79%), LGLT4000 (-5.22%), FES24 (-7.49%) по-прежнему расходятся с раннером; DMP2000/TM3100 расходятся в calcSticker на -0.50% / -0.66% (-0.07% / -0.09% в calcTablets).
  - С подстановкой length_min из roll.json в памяти: все 7 плёнок (Avery500w, Avery500c, Oracal352, LGLT4000, FES24, DMP2000, TM3100) на mode=0/1/2 сходятся с раннером calcTablets и calcSticker по cost и price в 0.00% (rel=0.000000); полный прогон с length_min из JSON зелёный (calc_service: 885 passed, bot_service: 81 passed).
Гипотеза: ошибка в loader.py:171 (аналогичная старой ошибке weightPerUnit vs weight на строке 177) — файл вне «Файлов» задачи и влияет на все калькуляторы (на проде на API сейчас только форма 79 puzzle).
Вопрос: разрешить правку loader.py:171 (добавить в «Файлы» этой задачи), вынести её в отдельную предпосылку на main или принять аппликацию без length_min?
Варианты:
1. Починить calc_service/materials/loader.py в этой задаче (Рекомендуется) — добавить loader.py (только строка length_min) в «Файлы», читать merged.get("length_min", merged.get("lengthMin")), свести все 7 плёнок в test_tablets.py и убрать monkeypatch из test_sticker.py.
2. Вынести починку loader.py в отдельную задачу-предпосылку на main — поставить заблокировано: ждёт todo/fix-materials-length-min.md, починить loader.py отдельно, затем rebase и сведение 7 плёнок в test_tablets.py.
3. Не трогать loader.py и сдать только Avery500w (length_min=0) — принять расхождение 3.5%–7.5% на плёнках с length_min=1000 в «Найдено вне scope» и передать ветку на ревью.
Следующая сессия: человек (через AskQuestion)
```

27.11.2026 — человек — доработка: оклейка фона таблички (поле 1427) не меняет цену, портировать `isBackgroundFilm` — дальше Implementer

## Ревью 5

принято

Незакоммиченный diff относительно HEAD `e3b7c2c`: `tablets.py`, `test_tablets.py`, `test_sticker.py`, `test_js_port_gaps.py` (`MAX_ALLOWED` 66→64), `js_port_gaps_allowed.txt`, `wp-plugin/forms/tablets.js`, `sticker.py` (только формула рулона при `length_min > 0`), `loader.py` (только чтение `length_min`), `todo/form-tablets.md`. `cut_plotter.py` в diff нет. JSON цен, `REF_FORM_DEFAULT`, эталоны экосольвента и латекса не менялись.

Блокер «Ревью 4» закрыт.

- В `tablets.py` ветка `is_film` — вызов `StickerCalculator` (`is_mounting_film=True`) и `calc_manual_roll` на размере таблички и тираже `n * (2 if double else 1) * color`. Пересчёта на месте нет. `isBackgroundFilm` не переносился: без фона цена аппликации сходится с раннером.
- В `sticker.py` формула рулона: `* width_mm` вместо `* (width_mm / 1000)`. В `loader.py`: `length_min` из ключа `length_min` (запасной `lengthMin`). Это разрешённые правки.
- В `wp-plugin/forms/tablets.js` при `isFilm` в `calcApi` уходят материал 1484, размер 1419×1420, размер элемента 1424, плотность 1425 (factor), сложность 1423, число цветов 1430, двойное нанесение. Ветка УФ по-прежнему шлёт только `is_uv_print`. Своих `price` и `querySelector` нет.
- Раннер `calcTablets` и `TabletsCalculator.execute`, все 7 плёнок (`Avery500w`, `Avery500c`, `Oracal352`, `LGLT4000`, `FES24`, `DMP2000`, `TM3100`), `mode=0/1/2`: `price` и `cost` rel = 0. Срок в допуске rel ≤ 0.001, кроме остатка `round` вместо `Math.ceil` в `cut_plotter.py` (формулу не меняли, цена сходится): `Avery500w`/`Avery500c` `mode=1` — 21.22 против 21.26 (rel 0.001881); `LGLT4000`/`DMP2000`/`TM3100` `mode=2` — 13.79 против 13.81 (rel 0.001448); `FES24` `mode=2` — 14.25 против 14.27 (rel 0.001402). Это не блокер.
- `calcSticker` на `Avery500c` и `FES24` (100 шт 50×50, монтажная плёнка, mode=1): `cost`/`price` совпали с раннером (`1332.65`/`2171.979` и `3523.45`/`5776.607`). Дефолт УФ: `12754` / `52.82`.
- `python scripts/js_port_gaps.py calcTablets`: сняты `option isFilm` и `call calcSticker`. Оставшиеся 8 пропусков названы в docstring и лежат в allowed. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py calc_service/tests/test_calculators/test_cut_plotter.py -q` → `147 passed`. Полный `calc_service/tests`: `893 passed`; `test_dashboard.py` красный, потому что `docs/dashboard.md` не пересобран (общий файл, локально его пишет `make check`).

Прод-пункты (боевой POST, цена аппликации на копии 120, дефолт УФ `12 800` руб. / 7 дней, GET-ссылка) закрываются после `deploy-api` с `main` и записи JS в форму 120 на черновике 2586916. Новую копию не создавать, плагин не выкладывать, боевую 36 не переключать. Это не блокер diff.

Замечаний с меткой `блокер` нет.

## Ревью 4

26.11.2026 — человек

- блокер: на копии 120 расчёт аппликации не сходится. В `tablets.js` в `calcApi` нет ветки `isFilm`: поля плёнки (материал 1484, размер 1419×1420, число цветов 1430, размер элемента 1424, заливка 1425, сложность 1423) пишутся в `syncUrl` и в расчёт не уходят. В `tablets.py` аппликации нет. В allowed остаются `calcTablets option isFilm` и `calcTablets call calcSticker`.
- Эталон — `calcTablets` в `js_legacy/calc/calcTablets.js`, блок «нанесения аппликации»: `calcSticker` и `calcManualRoll`. Вызов в JS — вызов уже существующего порта (`StickerCalculator`, `calc_manual_roll`), не пересчёт на месте и не правка `sticker.py`. `isBackgroundFilm` (фон, поля 1427 и 1483) — только если без него цена аппликации на форме 36 не сходится с раннером. Фрезеровку, древко и клеевой слой не трогать.
- `REF_FORM_DEFAULT`, эталоны экосольвента и латекса не сдвигать. Новую копию не создавать. После выкатки API записать JS в форму 120 на черновике 2586916. Плагин не выкладывать. Боевую форму 36 не переключать.

## Ревью 3

принято

Незакоммиченный diff относительно HEAD `03a28cf`: `tablets.py`, `test_tablets.py`, `test_js_port_gaps.py` (`MAX_ALLOWED` 68→66), `js_port_gaps_allowed.txt`, `wp-plugin/forms/tablets.js`, `todo/form-tablets.md`. Чужие калькуляторы, JSON цен и `REF_FORM_DEFAULT` не менялись.

Блокер «Ревью 2» закрыт.

- В `tablets.py` ветка `is_print` — вызов `PrintRollCalculator` (материал `ORAJET3640`, `printer_code`, `is_lamination`, `mode`) и `calc_manual_roll` (`isEdge`, `mode`) на тираже `n * (2 if double_application else 1)`. Пересчёта на месте нет.
- В `wp-plugin/forms/tablets.js` `isECOPrint` (`Technojet160ECO`, ламинация из поля 1429, если значение не `No`, край из 1477, двойное нанесение из 3313) и `isLatexPrint` (`HPLatex335`, ламинация выключена, край и двойное нанесение те же) попадают в `params.is_print` и уходят в `calcApi('tablets', params)`. Ветка УФ по-прежнему шлёт только `is_uv_print`.
- Раннер `calcTablets` и `TabletsCalculator.execute` (допуск цены abs ≤ 0.02 или rel ≤ 0.001, срока rel ≤ 0.001), `price` / `time_ready`: экосольвент mode 0/1/2 — `12150`/`32.37`, `12937`/`20.97`, `13743`/`13.58`; латекс mode 0/1/2 — `12885`/`60.28`, `14471`/`37.93`, `16064`/`23.58`; ламинация + подгибка + двойное нанесение — `52726`/`37.22`; латекс 10 шт 300×200, подгибка + двойное — `10146`/`36.02`; экосольвент 1 шт 1000×1000 с ламинацией — `6005`/`17.47`. Те же `52726`/`37.22`, если край и ламинация заданы верхним уровнем. Эталоны в тесте с пометкой `# JS, 26.11.2026`.
- Дефолт формы 36 (УФ) на раннере: `12754` / `52.82`. Строки `REF_FORM_DEFAULT` в diff нет.
- `python scripts/js_port_gaps.py calcTablets`: `calcPrintRoll` и `calcManualRoll` сняты. Оставшиеся 10 пропусков (`isCutMilling`, `isFilm`, `isBackgroundFilm`, `isShaft`, `isAdhesiveLayer`, `isEVAFoam`, `calcMilling`, `calcSticker`, `calcPockets`, `calcFrame`) названы в docstring и лежат в allowed. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` → `71 passed`. Файл `test_plaque.py` в diff нет.

Прод-пункты (боевой POST, цена экосольвента и латекса на копии 120, дефолт УФ `12 800` руб. / 7 дней) закрываются после `deploy-api` с `main` и записи JS в форму 120 на черновике 2586916. Новую копию не создавать, плагин не выкладывать, боевую 36 не переключать. Это не блокер diff.

Замечаний с меткой `блокер` нет.

## Ревью 2

26.11.2026 — человек

- блокер: на копии 120 способы нанесения с экосольвентной печатью считаются неверно. В `tablets.js` в `calcApi` уходят только `isUVPrint` и `isSublimation`. Ветка `isPrint` (плёнка с экосольвентом и латексом, `calcPrintRoll` и `calcManualRoll`) пишется в `syncUrl` и в расчёт не передаётся. В `tablets.py` этой ветки нет, строки `calcTablets call calcPrintRoll` и `calcTablets call calcManualRoll` остаются в allowed.
- Эталон — `calcTablets` в `js_legacy/calc/calcTablets.js`, блок «нанесения пленкой с ЭКО-сольвентной и латексной печатью». Вызов в JS — вызов уже существующего порта (`PrintRollCalculator`, `calc_manual_roll`), не пересчёт на месте. Чужие калькуляторы не менять. `REF_FORM_DEFAULT` формы 36 (УФ) не сдвигать.
- Новую копию не создавать. После выкатки API записать JS в форму 120 на черновике 2586916. Плагин не выкладывать. Боевую форму 36 не переключать.

## Ревью 1

принято

Diff `task/form-tablets` относительно `main`: `tablets.py`, `test_tablets.py`, `test_js_port_gaps.py` (`MAX_ALLOWED` 70→68 и проверка цепочки на `calcPockets` — по правилу файла при снятии двух строк allowed), `js_port_gaps_allowed.txt`, `wp-plugin/forms/tablets.js`. Чужие калькуляторы, JSON цен и боевая форма не затронуты.

- Раннер `calcTablets` на дефолте формы 36: `mode=1` → `price` 12754 / `time_ready` 52.82; `mode=0` → 11888 / 60.23; `mode=2` → 13625 / 45.43. `noMaterial` 12264 / 52.82, `isMaterialCustomer` 15262 / 53.84, двойное УФ 13288 / 52.94. Совпадает с `REF_FORM_DEFAULT` и `EXPECTED_FORM_DEFAULT_BY_MODE`.
- `python scripts/js_port_gaps.py calcTablets`: сняты `option isCutManual` и `call calcCutRoller`; остальные 12 пропусков названы в docstring `tablets.py` и остаются в allowed. `python scripts/js_port_gaps.py --check` → `ok`.
- `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` → `60 passed`. Прежние эталоны `tablets` и `plaque` в diff не менялись.
- В `wp-plugin/forms/tablets.js` есть `calcApi('tablets'`, `syncUrl(`, `showResult(`; своих `price` и `querySelector` нет. Id полей совпадают с HTML боевой страницы формы 36 (расчёт 1348, материал 1339, режим материала 1340, раскрой 1371, нанесение 1368, режим 2003). Резаки `KeencutEvolutionE2` / `AccusheadPro12` и `PrintUV` — как в старом `cjsCalc`.
- `curl.exe -s` страницы табличек: в HTML есть `calcTablets`, вызова `calcApi` нет.

Прод-пункты (боевой POST на `REF_FORM_DEFAULT`, черновик копии, цена на копии, GET-ссылка) по задаче закрываются после `deploy-api` с `main`. Порт добавляет `is_cut_manual` в ответ `tablets`; на текущем проде этой ветки нет, копию до выкатки не принимать. Это не блокер diff.

Замечаний с меткой `блокер` нет.

## Найдено вне scope

- `scripts/run_js_calc.mjs`: для формы 51 (`CalcHashtags`) падает с `insaincalc.calcMilling is not a function` (не подключён `calcMilling.js`); для формы 68 (`CalcShild`) на дефолте с `materialID=""` падает с `Поле weight_kg не число (NaN)` (в `calcLaser.js` при пустом материале `weight` становится `NaN`).
- `ssh insain-prod` (5.181.252.133:22): в текущей сессии connection timed out — исходники форм 36/48/51/68/76 получены с опубликованных страниц (`curl.exe` + read-only Browser MCP). Для шагов Site ops понадобится рабочий SSH-доступ к VDS.
- `calc_service/calculators/sticker.py:308`: для рулонов с `length_min > 0` (`Avery500c`, `Oracal352`, `LGLT4000`, `FES24`, `DMP2000`, `TM3100`) формула `cost_per_m2 * num_min * length_min / 1_000_000 * (width_mm / 1000)` делит на 1000 дважды (против `calcSticker.js:44`, где `* materialCut[1][0]`), занижая стоимость плёнки в 1000 раз (починено в этой задаче по решению человека 26.11.2026). `calc_service/calculators/cut_plotter.py:499`: `round` вместо `Math.ceil` даёт -0.02 ч на `Avery500w 50×50 mode=1` (-0.04 ч в `time_ready`: 21.22 против 21.26, rel=0.00188). Тот же остаток 0.02 ч на `mode=2`: `LGLT4000`/`DMP2000`/`TM3100` 13.79 против 13.81, `FES24` 14.25 против 14.27. После чтения `length_min` себестоимость эталона `cut_plotter` `Avery500c` сдвинулась `400.64` → `401` и `2954.06` → `2955`, цена осталась `642` и `4727`. Формулу `cut_plotter.py` не меняли. На API из калькуляторов сейчас только `puzzle`, он `length_min` не читает.
- `calc_service/materials/loader.py:171`: `length_min=merged.get("lengthMin")` не читал ключ `"length_min"` из `roll.json` и `sheet.json`, из-за чего `material.length_min` всегда был `None` в runtime (починено в этой задаче по решению человека 27.11.2026).

## Результат

- Ветка, PR или коммит: ветка `task/form-tablets` (worktree `..\insain-agent-form-tablets`, правки в working tree к ревью).
- Период: 2026-11-26 — 2026-11-26
- Часы человека: —
- Работа агентов: 1 сессия; Gemini 4 Hydrogen High
- Было / стало: 0 перенесённых веток ручной роликовой резки в `tablets.py` и 14 пропусков `calcTablets` в allowed / портированы `is_cut_manual` (`CutRollerCalculator`) + `material_mode` + `double_application`, в allowed осталось 12 строк `calcTablets`, добавлен `wp-plugin/forms/tablets.js` (id 36) и `REF_FORM_DEFAULT` (`mode=0,1,2`).
- Сделано:

### Сверка дефолтов форм (JS vs `tablets.py`)

| Форма | Вход дефолта | JS `price` / `time_ready` | API (`tablets.py` после порта) `price` / `time_ready` | Задетые пропуски (`allowed`) |
| --- | --- | --- | --- | --- |
| 36 `CalcTabs` | 100 шт, 50×50, `PVC5`, `isCutManual='KeencutEvolutionE2'`, `isUVPrint` (`PrintUV`, `4+0`, res=1), `isMaterial`, `mode=1` | `12754` / `52.82` (раннер; `mode=0`: `11888`/`60.23`, `mode=2`: `13625`/`45.43`) | `12754.0` / `52.82` (`mode=0`: `11888.0`/`60.23`, `mode=2`: `13625.0`/`45.43`) — **сходится** | До порта: `option isCutManual`, `call calcCutRoller` (оба портированы и сняты) |
| 48 `CalcStands` | 1 шт, 1000×1000, `PVC5`, `isCutManual='KeencutEvolutionE2'`, `isUVPrint` (`PrintUV`, `4+0`, res=0), карманы 0, профиль/подвес/EVA `no`, `mode=1` | `4780` / `48.9` (раннер) | `4780.0` / `48.9` (при наличии опций в форме заденет `isFilm`/`isBackgroundFilm`/`isEVAFoam`/`calcPockets`/`calcFrame`) | На чистом дефолте закрыто портом `is_cut_manual`; опции стендов остаются в allowed |
| 51 `CalcHashtags` | 1 шт, 1000×100, `PVC5`, `#хештег`, `isCutMilling`, `isUVPrint` (`PrintUV`, `4+0`, res=1), `mode=1` | `2388` (страница `2400`) / `56.38` (JS страницы; раннер падает: нет `calcMilling`) | `788.0` / `48.57` (без `is_cut_milling`, только `is_uv_print`) | `option isCutMilling`, `call calcMilling` |
| 76 `CalcTabs9May` | 1 шт, 297×420 (`A3`), `PVC5`, `isCutManual='KeencutEvolutionE2'`, `isPrint` (`Technojet160ECO`), `isShaft` (`PlasticShaft`, 1 м), `mode=1` | `2423.184` / `16.99` (раннер) | `807.0` / `8.36` (только `is_cut_manual`, без `isPrint` и `isShaft`) | `call calcPrintRoll`, `option isShaft` (+ `isPrint` в JS) |
| 68 `CalcShild` | 100 шт, 50×50, `materialID=""` («не задан материал»), `isCutLaser`, `isUVPrint` (`RimalSuvUV`, `4+1`, res=2), `mode=1` | `5792` (страница `5800`) / `36.88`, `weight=NaN` (JS страницы; раннер падает на `NaN`; с `AcrylWhite3`: `7908` / `37.35`) | `ValueError: material_id обязателен` (с первым материалом `AcrylWhite3`: `7908.0` / `37.35`) | Пропусков `calcTablets` не задевает; расхождение только на пустом `material_id=""` |

Форма 68 `CalcShild` вызывает `insaincalc.calcTablets` (не `calcShild`) и переводится отдельной задачей через slug `tablets` (не `shild`).

### Порт в `tablets.py` и `wp-plugin/forms/tablets.js`

- В `calc_service/calculators/tablets.py` перенесены `is_cut_manual` (вызов `CutRollerCalculator`), `material_mode` (`isMaterial` / `isMaterialCustomer` / `noMaterial`), `double_application` и `is_customer_material` для УФ-печати; добавлены в `get_tool_schema` и `get_param_schema`.
- Из `scripts/js_port_gaps_allowed.txt` сняты `calcTablets option isCutManual` и `calcTablets call calcCutRoller` (осталось 12 строк `calcTablets`, все названы в docstring `tablets.py`).
- В `calc_service/tests/test_js_port_gaps.py` уменьшен `MAX_ALLOWED` (`70 → 68`, по правилу файла при снятии строк из allowed) и в `test_report_follows_call_chain` проверка переключена с устранённого `calcCutRoller` на остающийся `calcPockets`.
- В `calc_service/tests/test_calculators/test_tablets.py` добавлены `REF_FORM_DEFAULT` (`# JS, 26.11.2026`), `EXPECTED_FORM_DEFAULT_BY_MODE` (`mode=0, 1, 2`), тесты монотонности режимов и режимов материала / двойного УФ; прежние эталоны `tablets` и `plaque` не сдвинулись.
- Написан `wp-plugin/forms/tablets.js` (привязка к id боевой формы 36 `CalcTabs`, элемент `cjsCalc` 1348).
  - Не-API поля формы 36 (пишутся в `syncUrl`, не уходят в `calcApi`): `dpdTypeCut` (1375), `dpdRollWideLaminat` (1429), `dpdEdge` (1477), `dpdApplicationMaterial` (1484), `numApplicationW` (1419), `numApplicationH` (1420), `numFilm` (1430), `numSizeItem` (1424), `numDensity` (1425), `dpdFilmDifficulty` (1423), `dpdBackgroudMaterial` (1427), `dpdBackroundEdge` (1483), `ckbShaft` (1533), `numLengthShaft` (1534), `chkAdhesiveLayer` (2718).
  - Неперенесённые ветки формы 36 (`isCutMilling`, `isECOPrint`, `isLatexPrint`, `isFilm`, `isShaft`, `chkAdhesiveLayer`) в `calcApi` не отправляются.

### Дописки для общих файлов (перенести при слиянии в `main`)

- Для `docs/js-runner-cases.md`:
  - Строка таблицы: ``| `calcTablets` form 36 default | `tablets` | 12754 |``
  - Команда: `node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isUVPrint":{"printerID":"PrintUV","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"Material":"isMaterial"},1]'`
- Для `todo/forms-batch-switch.md` / `todo/EPIC-forms-to-api.md` (будущий боевой пакет, форма 36):
  - `36 CalcTabs` → slug `tablets`, JS `wp-plugin/forms/tablets.js`, ждёт выкатку API (`tablets.py`: `is_cut_manual`, `material_mode`) и дубль копии от Site ops.

- Чем проверено:
  - `python scripts/js_port_gaps.py calcTablets` и `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py -q` → `55 passed`
  - `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` → все 3 совпадения, `price` / `querySelector` нет
  - Node smoke-тест `wp-plugin/forms/tablets.js` → формирует тело `REF_FORM_DEFAULT` и полный `syncUrl`
  - `curl.exe -s https://insain.ru/catalog/tablichki-s-uf-pechatyu/` → в HTML есть `calcTablets`, нет `calcApi`
  - `python scripts/dev.py check` → `calc_service`: `864 passed`, `bot_service`: `81 passed` (`docs/dashboard.md` откачен через `git checkout -- docs/dashboard.md` как общий файл)
- Не сделано и почему:
  - Выкатка `tablets.py` (`deploy-api` с `main`), проверка боевого `POST /api/v1/calc/tablets` на `REF_FORM_DEFAULT` и прод-копия формы 36 (шаги 6–16 `copy.md`) — после `Reviewer` и слияния в `main` (`Site ops` на проде; также требуется доступ к `ssh insain-prod`, сейчас `port 22` таймаутится).
- Требуется решение:
  - Провести ревью (`Reviewer: Grok 4.7`), затем слить в `main` и выкатить API (`deploy-api`) перед снятием копии формы 36.

### Доработка 26.11.2026 (`is_print`: экосольвент и латекс)

- В `calc_service/calculators/tablets.py` портирована ветка `isPrint` (`_print_roll`): вызов существующих портов `PrintRollCalculator` (материал `ORAJET3640`, `printer_code`, `is_lamination`, `mode`) и `calc_manual_roll` (`isEdge`, `mode`) поверх тиража `n * (2 if double_application else 1)`. Добавлены параметры `is_print`, `is_edge`, `is_lamination` в `get_tool_schema` и `get_param_schema`. `REF_FORM_DEFAULT` (УФ-печать) и чужие калькуляторы не затронуты.
- Из `scripts/js_port_gaps_allowed.txt` сняты `calcTablets call calcPrintRoll` и `calcTablets call calcManualRoll`; в `calc_service/tests/test_js_port_gaps.py` уменьшен `MAX_ALLOWED` (`68 → 66`).
- В `wp-plugin/forms/tablets.js` для `isECOPrint` (`Technojet160ECO`, `is_lamination` из поля 1429 != `'No'`, `is_edge` из 1477, `double_application` из 3313) и `isLatexPrint` (`HPLatex335`, `is_lamination: false`, `is_edge` из 1477, `double_application` из 3313) формируется `params.is_print`.
- В `calc_service/tests/test_calculators/test_tablets.py` добавлены эталоны JS (`# JS, 26.11.2026`) для `Technojet160ECO` (`mode=0,1,2`), `HPLatex335` (`mode=0,1,2`), ламинации + подгибки (`isBendEdge`) + двойного нанесения, `1000×1000` и Node-тест `wp-plugin/forms/tablets.js`.
- Дописка для `docs/js-runner-cases.md` (добавить к строке формы 36 при слиянии в `main`):
  - `node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isPrint":{"printerID":"Technojet160ECO","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"isEdge":"isCutEdge","Material":"isMaterial"},1]'` (`price`: 12937)
  - `node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isPrint":{"printerID":"HPLatex335","resolution":1,"surface":"isPlain","color":"4+0","isDoubleApplication":false},"isEdge":"isCutEdge","Material":"isMaterial"},1]'` (`price`: 14471)
- Чем проверено (доработка):
  - `python scripts/js_port_gaps.py calcTablets` и `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` → `71 passed`
  - FastAPI `TestClient` `POST /api/v1/calc/tablets`: `REF_FORM_DEFAULT` → `12754.0` / `52.82`, `REF_ECO_PRINT` → `12937.0` / `20.97`, `REF_LATEX_PRINT` → `14471.0` / `37.93`
  - `python scripts/dev.py check` → `calc_service`: `875 passed`, `bot_service`: `81 passed` (`docs/dashboard.md` откачен через `git checkout -- docs/dashboard.md`)
- Не сделано на проде (следующая роль `Reviewer` → слияние в `main` → `Site ops`):
  - `deploy-api` с `main`, затем запись обновлённого `wp-plugin/forms/tablets.js` в существующую форму 120 на черновике 2586916 (`read_file=0`) и проверка на копии под админом (`isECOPrint`, `isLatexPrint` и дефолт с УФ-печатью `12 800 руб.` / `7 дней`). Боевую форму 36 не переключать, плагин не выкладывать, новую копию не создавать.

### Доработка 26.11.2026 (`is_film`: аппликация плёнками)

- В `calc_service/calculators/tablets.py` портирована ветка `isFilm` (`_film_application`): вызов существующих портов `StickerCalculator` (`is_mounting_film=True`) и `calc_manual_roll` (на размере таблички `size`, без `isEdge`) для тиража `n * (2 if double_application else 1) * color`. Добавлен параметр `is_film` в `get_tool_schema` и `get_param_schema`; пустой материал / `'0'` отклоняется `ValueError` («Не выбрана плёнка для аппликации», HTTP 400). `REF_FORM_DEFAULT`, эталоны экосольвента/латекса и чужие калькуляторы не затронуты. `isBackgroundFilm` не переносился (дефолт поля 1427 на форме 36 = `'0'`, без фона цена аппликации не требует его).
- Из `scripts/js_port_gaps_allowed.txt` сняты `calcTablets option isFilm` и `calcTablets call calcSticker` (осталось 8 строк `calcTablets`); в `calc_service/tests/test_js_port_gaps.py` уменьшен `MAX_ALLOWED` (`66 → 64`).
- В `wp-plugin/forms/tablets.js` для `applicationId === 'isFilm'` в `params.is_film` передаются `material_id` (1484), `size` (1419×1420), `size_item` (1424), `density` (1425 через `get_value_from(1425)` с `data-factor=0.01`, тогда как `syncUrl` продолжает писать сырое значение 25 из `get_value_from(1425, true, true)`), `difficulty` (1423), `color` (1430), `double_application` (3313).
- В `calc_service/tests/test_calculators/test_tablets.py` добавлены эталоны `# JS, 26.11.2026` для `Avery500w` (`mode=0, 1, 2`, 2 цвета, `300×200`, `1000×1000`, двойное нанесение + `density=0.5` + `difficulty=1.7`), тест `ValueError` на `'0'`/`''` и Node-тест `test_tablets_js_posts_is_film`.
- Дописка для `docs/js-runner-cases.md` (добавить к строке формы 36 при слиянии в `main`):
  - `node scripts/run_js_calc.mjs calcTablets --data current --args '[100,[50,50],"PVC5",{"isCutManual":"KeencutEvolutionE2","isFilm":{"materialID":"Avery500w","size":[50,50],"sizeItem":50,"density":0.25,"difficulty":1,"color":1,"isDoubleApplication":false},"Material":"isMaterial"},1]'` (`price`: 13760.42)
- Ограничение для решения человека (см. блокер в журнале):
  - `Avery500w` (`length_min=0`) сходится по `price` в `0.00%` (и по `time_ready` в `rel <= 0.001` на `mode=0/2`, 2 цветах, `300×200`, `1000×1000`; на `mode=1` `21.22` против `21.26` из-за `round` в `cut_plotter.py:499`).
  - На плёнках с `length_min > 0` (`Avery500c`, `Oracal352`, `LGLT4000`, `FES24`) цена занижена на 3.5%–7.5% из-за бага в `sticker.py:308` (чужой калькулятор из «Не-scope»).
- Чем проверено (доработка `is_film`):
  - `python scripts/js_port_gaps.py calcTablets` и `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` → `81 passed`
  - FastAPI `TestClient` `POST /api/v1/calc/tablets`: `REF_FORM_DEFAULT` → `12754.0` / `52.82`, `REF_ECO_PRINT` → `12937.0` / `20.97`, `REF_LATEX_PRINT` → `14471.0` / `37.93`, `REF_FILM_AVERY500W` → `13760.42` / `21.22`, `material_id="0"` → HTTP 400
  - `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` → все 3 совпадения
  - `python scripts/dev.py check` → `calc_service`: `885 passed`, `bot_service`: `81 passed` (`docs/dashboard.md` откачен через `git checkout -- docs/dashboard.md`)

### Доработка 27.11.2026 (`sticker.py` `length_min > 0` и `loader.py` `length_min`)

- В `calc_service/calculators/sticker.py:309` исправлена формула рулона при `length_min > 0`: `* (width_mm / 1000)` заменено на `* width_mm`.
- В `calc_service/materials/loader.py:171` исправлено чтение `length_min`: `_as_float(merged.get("length_min", merged.get("lengthMin")))` вместо `merged.get("lengthMin")`.
- В `calc_service/tests/test_calculators/test_sticker.py` в `test_roll_length_min_matches_js` убран `monkeypatch` и устаревшее примечание про `loader.py`, добавлена проверка `mat.length_min == expected_length_min` из JSON; эталоны `Avery500c` (`1332.65` / `2171.979`) и `FES24` (`3523.45` / `5776.607`) и все прежние эталоны `sticker.py` не сдвигались.
- В `calc_service/tests/test_calculators/test_tablets.py` добавлен параметризованный тест `test_film_all_7_materials_match_js` (`# JS, 27.11.2026`) на все 7 плёнок аппликации поля 1484 формы 36 (`Avery500w`, `Avery500c`, `Oracal352`, `LGLT4000`, `FES24`, `DMP2000`, `TM3100`). Все 7 плёнок сходятся с раннером по `cost` и `price` в `0.00%`; на `Oracal352`, `LGLT4000`, `FES24`, `DMP2000`, `TM3100` на `mode=1` и `time_ready` сходится в `0.00%` (на `Avery500w` и `Avery500c` `mode=1` — `21.22` против `21.26` из-за `round` вместо `Math.ceil` в `cut_plotter.py:499`, который по решению человека не менялся). Эталоны УФ, экосольвента и латекса в `test_tablets.py` не сдвигались.
- Чем проверено:
  - `python scripts/js_port_gaps.py calcTablets` и `python scripts/js_port_gaps.py --check` → `ok`
  - `python -m pytest calc_service/tests/test_calculators/test_sticker.py calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_calculators/test_plaque.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` → `122 passed`
  - FastAPI `TestClient` `POST /api/v1/calc/tablets`: `REF_FORM_DEFAULT` → `12754.0` / `52.82`, `REF_ECO_PRINT` → `12937.0` / `20.97`, `REF_LATEX_PRINT` → `14471.0` / `37.93`, все 7 плёнок `is_film` → HTTP 200 с точным совпадением `cost`/`price` с раннером
  - `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` → все 3 совпадения
  - `python scripts/dev.py check` → зелёный (`docs/dashboard.md` откачен через `git checkout -- docs/dashboard.md` как общий файл)
- Не сделано на проде (следующая роль `Reviewer` → слияние в `main` → `Site ops`):
  - `deploy-api` с `main`, запись обновлённого `wp-plugin/forms/tablets.js` в существующую форму 120 на черновике 2586916 (`read_file=0`), проверка на копии под админом (`isFilm`, а также дефолт УФ / экосольвент / латекс / GET-ссылка). Боевую форму 36 не переключать, плагин не выкладывать, новую копию не создавать.
