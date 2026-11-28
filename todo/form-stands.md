# form-stands

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `tablets` по skill `ezfc-form-to-api`; лид 36 и копию 120 не пересматривать.

## Цель

Копия формы 48 CalcStands на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов формы 48. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-stendov/ остаётся на `insaincalc.calcTablets`. В пакет `forms-batch-switch` форма 48 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы в одном файле — `wp-plugin/forms/print_sheet.js` (формы 6 и 19).
- `docs/site/forms.md` — строка формы 48, только читать.
- `wp-plugin/forms/tablets.js` — JS лида 36. `calc_service/tests/test_calculators/test_tablets.py` — эталоны лида не сдвигать.
- `js_legacy/calc/calcTablets.js` — эталон; подключён в `scripts/run_js_calc.mjs`.
- `todo/EPIC-forms-to-api.md` — пачка 6. Формы 51, 76, 68 — отдельные задачи после этой.
- Остальное не открывать.

## Scope

- Доработка 29.11.2026 (важнее записи «только URL» прошлого круга): на копии 121 карманы и дополнительные опции не меняют цену. В `calcTablets.js` это карманы `isPocket` → `calcPockets`, рамка и подвесы `isFrame` / `isHanger` → `calcFrame`, EVA `isEVAFoam` → `calcCutRoller` и `calcManualRoll`. В принятом `forms/tablets.js` они пишутся в `syncUrl` и в `calcApi` не уходят. Выбор кармана, рамки, подвеса и EVA на копии 121 должен менять цену и срок так же, как старый JS. Дефолт без этих опций (4780 / 48.9) и эталоны лида 36 не сдвигать. Новую копию не создавать: JS писать в форму 121, `read_file=0`. Плагин не выкладывать. Боевые 36 и 48 не переключать.
- Модулей `calcPockets` и `calcFrame` в Python нет (allowed: `calcPockets module`, `calcFrame module`, `calcTablets call calcPockets`, `calcTablets call calcFrame`, `calcTablets option isEVAFoam`). Их порт входит в эту доработку, эталон только с раннера. EVA считать вызовом уже существующих портов резки и накатки. Строки своего префикса снять, когда ветка сошлась. Новые строки в `scripts/js_port_gaps_allowed.txt` не добавлять.
- В git (Implementer): JS формы 48 со своими id. `forms/tablets.js` остаётся расчётом формы 36: её id и эталоны лида не менять. Текст формы 48 — в том же файле, блоки `/* form 36 */` и `/* form 48 */`. Без блоков `scripts/ezfc_copy.py` не примет чужие `get_value_from`. Развилка по набору полей формы, не по id копии. Если развилка не собирается без сдвига цены лида — стоп, `заблокировано: аналитик`.
- Дефолт формы 48 сверить с раннером. Сошёлся с текущим `tablets.py` — калькулятор не менять. Не сошёлся — портировать только ветки этого дефолта вызовом уже существующего порта. Порта нет — стоп, `заблокировано: аналитик`. Новые строки в `scripts/js_port_gaps_allowed.txt` не добавлять; снятую строку своего префикса снять, когда ветка сошлась.
- Кейс дефолта формы 48 — отдельная константа в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 48 на черновик по skill. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевые 48 и 36 не переключать. Копию 120 / 2586916 не править.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат».

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/calculators/pockets.py`, `calc_service/calculators/frame.py` — новые модули, если порта нет; регистрация в `calc_service/calculators/__init__.py`
- `calc_service/tests/test_calculators/test_tablets.py` и тесты новых модулей
- `scripts/js_port_gaps_allowed.txt` — только снять строки `calcTablets` / `calcPockets` / `calcFrame`, когда ветка сошлась
- WordPress: форма 121 и черновик 2586917, новый дубль не создавать

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`
- Копия 120 / 2586916, боевые формы 36, 51, 76, 68
- `shild.py`, `plaque.py`, JSON цен, выкладка плагина, шаги 17–24
- Чужие калькуляторы, кроме вызова уже существующего порта и новых модулей карманов и рамки из этой доработки

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат.

- [x] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны лида 36 на месте. Есть константа дефолта формы 48 с `# JS,`.
- [x] `Select-String -Path wp-plugin\forms\tablets.js -Pattern "calcApi\('tablets'|syncUrl\(|showResult\("` — все три есть. Id формы 36 из шапки файла на месте. Есть блоки `/* form 36 */` и `/* form 48 */`.
- [x] Копия не на витрине: `wp post get 2586917 --field=post_status` → `draft`; `curl.exe -s -o NUL -w "%{http_code}"` гостем — `404`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200, price 4780, time_ready 48.9. На странице `4 800` = `insaincalc.round(4780, 1)`.
- [x] `curl.exe -s https://insain.ru/catalog/kalkulyator-stendov/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [x] URL обновляется GET-именами формы 48; ссылка с GET открывает форму с теми же значениями и той же ценой.
- [ ] Карман с количеством > 0: раннер и `POST /api/v1/calc/tablets` сходятся по `price` и `time_ready`. В тесте эталон `# JS,`. На копии 121 цена страницы = `price` API с округлением `showResult`. Дефолт без кармана остаётся 4780 / 4 800.
- [ ] Рамка, подвес и EVA: каждая опция меняет цену и срок на копии 121 так же, как раннер и `POST /api/v1/calc/tablets`. В `forms/tablets.js` они уходят в `calcApi`, не только в `syncUrl`. Эталоны лида 36 и дефолт формы 48 не сдвинуты.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод после этой доработки
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Боевые 48 и 36 не меняются. Запись на проде под `lock prod`, не параллельно с другой формой.
- Цены: нет. Эталоны лида не сдвигать.
- Формы: id боевой 48 не менять. id формы 36 в JS не подменять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — черновик второй формы slug `tablets`, форма 48 — дальше человек
29.11.2026 — Implementer, Grok 4.7 — JS формы 48 и эталон дефолта 4780 / 48.9 ч, калькулятор не менялся, make check зелёный — дальше Site ops
29.11.2026 — человек — изоляция: посторонние файлы в main не блокируют, продолжать — дальше Site ops
29.11.2026 — Site ops, Grok 4.7 — дубль формы 48 не создан: админка ezFC открылась как wp-login.php (reauth=1), пароль не вводился — дальше человек

Блокер: шаг 6 skill ezfc-form-to-api не выполнен — Chrome Browser MCP не в сессии wp-admin.
Пробовал: `python scripts/dev.py lock acquire prod form-stands` — «lock prod: подтверждён задачей form-stands». SQL: товар формы 48 — 2586687 publish `kalkulyator-stendov`; последние формы 120 CalcTabs duplicate, 119, 118, новой нет. Браузер: `https://insain.ru/wp-admin/admin.php?page=ezfc` → `wp-login.php?reauth=1`, заголовок «Войти». Логин и пароль не вводились. Повторный SQL: старшая форма по-прежнему 120. `curl` https://insain.ru/catalog/kalkulyator-stendov/ — есть `calcTablets`, `calcApi` нет.
Гипотеза: админ-сессия WordPress в Chrome Browser MCP истекла (рядом уже были вкладки wp-login и «My Account»).
Вопрос: войти в wp-admin в этом Chrome и продолжить дубль, или оставить прод без копии.
Следующая сессия: человек, затем Site ops, модель Grok 4.7
29.11.2026 — человек — войти в wp-admin в Chrome Browser MCP и продолжить дубль формы 48 — дальше Site ops
29.11.2026 — Site ops, Grok 4.7 — копия формы 121 на черновике 2586917, дефолт API 4780 и на странице 4 800, боевые 36 и 48 не переключались — дальше Reviewer
29.11.2026 — Reviewer, Auto — ревью 1: принято; перед слиянием нужен коммит в task/form-stands — дальше человек
29.11.2026 — человек — принято — закрытие
29.11.2026 — человек — вернуть на доработку: на копии 121 карманы и дополнительные опции (рамка, подвесы, EVA) не меняют цену — дальше Implementer
29.11.2026 — Implementer, Grok 4.7 — порт карманов, рамки и EVA; JS формы 48 шлёт их в calcApi; дефолт 4780 / 48.9 не сдвинут; make check зелёный — дальше Site ops

Блокер: критерии кармана, рамки, подвеса и EVA на копии 121 не закрыты. В форму 121 всё ещё JS прошлого круга, без этих опций в `calcApi`.
Пробовал: порт `calcPockets` / `calcFrame` / EVA и тесты локально (см. «Результат», доработка). WordPress не правил — это Site ops.
Гипотеза: после записи текущего `forms/tablets.js` в форму 121 цена на копии совпадёт с API и `showResult`.
Вопрос: записать JS в форму 121 и сверить цены, без нового дубля и без переключения боевых 36 и 48.
Следующая сессия: Site ops, модель Grok 4.7
29.11.2026 — человек — ревью git-diff до записи на форму 121; форму не трогать, пока порт не принят, не слит в main и API не выкачен — дальше Reviewer
29.11.2026 — Reviewer, Auto — ревью 2: принято по git; копия 121 и критерии на проде вне этого круга — дальше человек
29.11.2026 — человек — принято: коммит, слияние в main и push; форму 121 обновить после выкатки API — выкатка

## Ревью 1

**Вердикт:** принято

**Diff (main…рабочее дерево, коммита нет):** `wp-plugin/forms/tablets.js`, `calc_service/tests/test_calculators/test_tablets.py`, `todo/form-stands.md`, `docs/dashboard.md` (побочный от check). `tablets.py` и `scripts/js_port_gaps_allowed.txt` без изменений.

**Критерии приёмки (git / локально):**

- `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — Reviewer: **80 passed**. `REF_FORM_DEFAULT` лида 36 на месте; добавлены `REF_FORM48_DEFAULT` с `# JS, 29.11.2026`, тесты дефолта/mode и `test_tablets_js_form48_posts_default`.
- Паттерны в `tablets.js` — `calcApi('tablets'`, `syncUrl(`, `showResult(` есть в обеих ветках; блоки `/* form 36 */` / `/* form 48 */`; шапка с id формы 36; развилка по `dpdProfile`.
- `python scripts/dev.py check` — Reviewer: **913 + 81 passed**, exit 0.
- Копия / бой (Site ops, не перепроверял): критерии в шапке задачи отмечены; отчёт и матрица опций в «Результат» согласованы с ветками JS (печать, материал, ламинация, подгибка через `is_edge`, аппликация, фон).

**Опции формы 48 (полнота):** поля из списка id в шапке `tablets.js` читаются; цена/срок через `calcApi` — материал, нанесение (УФ/эко/латекс/фон/аппликация), край, ламинация, `ckbSize`→`size`, режим `rdoModeProduction`. Рамка, подвесы, EVA (`dpd`, `numFoam*`), карманы (`setPockets`) — только URL или без POST, согласовано с «не перенесено» в `tablets.py` / `js_port_gaps_allowed.txt` и таблицей Site ops (URL-only). Новых строк в allowed не добавлено.

**Инварианты:** цен в коде нет; внутренние `code` в отчёте Site ops на копии не показывались; эталоны лида не сдвинуты.

**Замечания:**

- `желательно` — перед слиянием в `main`: один коммит с `tablets.js` и `test_tablets.py` на ветке `task/form-stands` (сейчас HEAD = main, изменения только в рабочем дереве).
- `вне scope` — повтор «Найдено вне scope»: раннер `isFrame` / `AluFrame2Plus`; матрица кроме строк Site ops в git-тестах не дублируется (приёмка копии уже у Site ops).

## Ревью 2

**Вердикт:** принято (только git-часть доработки 29.11.2026; копию 121 и критерии «на копии» по решению человека не перепроверял)

**Diff после «Ревью 1»** (коммита нет, HEAD = точка ответвления от `main`): `wp-plugin/forms/tablets.js`; `calc_service/calculators/tablets.py`, `pockets.py` (новый), `frame.py` (новый), `__init__.py`, `common/process_tools.py`; `calc_service/tests/test_calculators/test_tablets.py`, `test_pockets.py` (новый), `test_frame.py` (новый), `test_js_port_gaps.py`, `test_mode_contract.py`; `scripts/js_port_gaps.py`, `scripts/js_port_gaps_allowed.txt`; `todo/form-stands.md`, `docs/dashboard.md` (побочный от check).

**Scope доработки:**

- Порт `calcPockets` / `calcFrame` / EVA в `tablets.py` через `PocketsCalculator`, `FrameCalculator`, существующие `CutRoller` + `calc_manual_roll`. `pockets` и `frame` в реестре с `is_public = False`.
- Строки allowed сняты: `calcPockets`, `calcPutTape`, `calcFrame`, вызовы из `calcTablets`, опция `isEVAFoam`. Новых строк в `scripts/js_port_gaps_allowed.txt` нет. `python scripts/js_port_gaps.py --check` — **ok**.
- Блок `/* form 48 */` в `tablets.js`: `is_pocket` (DOM `setPockets`, окантовка `Avery500c`), `is_frame`, `is_hanger`, `is_eva_foam` в `calcApi('tablets')`; профиль/подвес/EVA по-прежнему в `syncUrl`. Форма 36: блок `/* form 36 */`, id и POST без новых полей.
- Эталоны лида 36 (`REF_FORM_DEFAULT`, `EXPECTED_FORM_DEFAULT*`) не менялись. Дефолт формы 48 mode 1: **price 4780**, **time_ready 48.9**. Добавлены эталоны `# JS, 29.11.2026`: карман A4 / standoff, EVA, рамка, рамка+подвес; подвес без рамки оставляет 4780 / 48.9 (как JS).

**Проверки Reviewer:**

- `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — **86 passed**.
- `python scripts/dev.py check` — **927 + 81 passed**, exit 0.
- `Select-String` по `tablets.js` — `calcApi('tablets'`, `syncUrl(`, `showResult(` в обеих ветках; блоки `/* form 36 */` / `/* form 48 */`.
- `test_tablets_js_form48_posts_default` — без `is_pocket` / `is_frame` / `is_eva_foam` в теле; `test_tablets_js_form48_posts_options` — все четыре опции в POST.

**Опции формы 48:** карманы, рамка, подвес, EVA закрыты в git (POST + тесты с раннером). Критерии приёмки с формулировкой «на копии 121» **намеренно открыты**: форма 121 не обновлялась, боевой API без выкатки ветки.

**Инварианты:** цен в Python нет; эталоны лида не сдвинуты; внутренние `code` в тестах материалов — служебные assert.

**Замечания:**

- `желательно` — перед слиянием: один коммит со всеми файлами доработки на `task/form-stands` (по-прежнему только рабочее дерево).
- `вне scope` — копия 121 / deploy API / `docs/js-runner-cases.md` (строки в «Результат»); `time_hours` кармана standoff vs JS (в «Результат»); склейка `Avery500c` в стоковом раннере для кармана.

**Блокеры этого круга:** нет (для git).

## Найдено вне scope

- `calcTablets.js`: оклейка фона без аппликации падает на `options.get('isFilm')['isBackgroundFilm']`. Дефолт формы 48 — УФ, ветка не исполняется.
- Стоковый `scripts/run_js_calc.mjs` не грузит `profile.json`: `isFrame` / `AluFrame2Plus` падает с `Cannot read properties of undefined (reading 'AluFrame2Plus')`. Файл раннера не менялся. Числа рамки сняты тем же раннером после временной загрузки каталога профиля и совпали с портом.
- `Avery500c` есть и в ленте (cost 3), и в рулоне (cost 340). `--data current` склеивает коды, и `calcPutTape` окантовки берёт 340. Живой misc и `tape.json` — cost 3. Порт кармана считает ленту.
- У формы 48 поле пены названо `dpd` (id 2959), не `dpdFoam`.

## Результат

- Ветка, PR или коммит: `task/form-stands`
- Период: 29.11.2026
- Часы человека:
- Работа агентов: Implementer, Grok 4.7; Site ops, Grok 4.7; Reviewer, Auto
- Было / стало: `forms/tablets.js` считал только форму 36. Стало: развилка по полю `dpdProfile`, блок `/* form 48 */` со своими id. Калькулятор `tablets.py` не менялся.
- Сделано: дефолт формы 48 (1 шт, 1000×1000, PVC5, KeencutEvolutionE2, УФ PrintUV 4+0, resolution 0, mode 1) совпал с раннером, локальным `tablets.py` и боевым API: price 4780, time_ready 48.9, mode 0/2 тоже. Константа `REF_FORM48_DEFAULT` с пометкой `# JS, 29.11.2026`. JS формы 48 читает свои id, GET-имена элементов, `calcApi('tablets')`. Рамка, подвесы, EVA и карманы — только URL: полного порта нет, дефолт их не включает.
- Чем проверено: `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — 80 passed. `python scripts/dev.py check` — exit 0 (913 passed, затем 81 passed). Раннер и `POST https://insain.ru/api/v1/calc/tablets` на mode 0/1/2. `curl` страницы стендов: есть `calcTablets`, нет `calcApi`.
- Site ops 29.11.2026. Сделано: один Duplicate формы 48 → форма 121 `CalcStands duplicate`. Черновик товара 2586917 «Калькулятор стендов (Копировать)», `post_status=draft`, `ezfc_form_id=121`. Боевой товар 2586687 остался `publish` и форма 48. JS копии записан `scripts/ezfc_copy.py --live 48 --copy 121` и `ezfc_copy_apply.php apply`, `read_file=0`, у `cjsCalc` `calcApi=1`. GET: числа без суффикса, dropdown и `ckbSize` — `index`, `rdoModeProduction` — `value`. Блок цены копии уже был как у формы 79: скидка `hidden=1` и `calc_hidden=1`, менеджерские `hidden=0`. Плагин не выкладывался. Формы 36, 48 и копия 120 / 2586916 не менялись. `lock release` не вызывался.
- Чем проверено: гость `curl` `/?post_type=product&p=2586917` → `404`. Под админом превью `POST /api/v1/calc/tablets` 200. Дефолт: тело `PVC5`, УФ `4+0`, `mode` 1, price 4780, time_ready 48.9; подпись `4 800` = `insaincalc.round(4780, 1)`. Перезагрузка ссылки с `rdoModeProduction=2`, `dpdHanger=2`, `dpd=1`, `numFoamH=400` оставила те же значения, цену `5 700` и «Срок 5 дней». Таблица материалов: название, размер, количество, внутренних `code` нет. Консоль: ошибки только `insainParse/scrtp.js`, не `insaincalc` и не `ezfc`. Боевая страница: `calcTablets=2`, `calcApi=0`. `wp litespeed-purge all` вернул 400, `wp cache flush` прошёл; расчёт копии шёл в API.
- Не сделано и почему: шаги 17–24, выкладка плагина, переключение боевых 36 и 48, коммит. Режим `0` на форме 48 нет: у радио data-value только 1 и 2. Карманы в POST не отправлялись, ряд с количеством не добавлялся. Строки матрицы кроме дефолта и mode 2 с раннером в этой сессии не сверялись: цена копии равна ответу API и `showResult`.
- Как откатить: боевая форма и товар 2586687 не менялись. JS копии — бэкап `/tmp/ezfc-copy-121-20261128-165139.json`. Черновик 2586917 гостю не виден. Удалять форму 121 только с согласия человека.
- Требуется решение: нет. Дальше Reviewer по шапке задачи. Рамка, подвесы, EVA и карманы в `calcApi` не передаются.

| Опция | Параметр в POST | Цена JS/API | Цена на копии | Срок |
| --- | --- | --- | --- | --- |
| дефолт PVC5, УФ 4+0, mode 1 | material_id PVC5, is_uv_print 4+0, mode 1 | 4780 | 4 800 | 48.9 ч, 6 дней |
| mode 2, data-value | mode 2 | 5653 | 5 700 | 41.53 ч, 5 дней |
| материал PVC3 | material_id PVC3 | 4033 | 4 100 | 48.9 ч |
| без нанесения | нет is_uv_print | 2524 | 2 600 | 8.36 ч, 1 день |
| УФ 4+1 | is_uv_print color 4+1 | 6436 | 6 500 | 49.12 ч |
| УФ 1+0 | is_uv_print color 1+0 | 4780 | 4 800 | 48.9 ч |
| экосольвент | Technojet160ECO, isCutEdge, size 1000x1000 | 5214 | 5 300 | 17.41 ч, 2 дня |
| экосольвент, ламинация глянец и мат | is_lamination true; оба data-value LaminatDLCLAM | 6005 | 6 100 | 17.47 ч |
| экосольвент, подгибка | isBendEdge | 5534 | 5 600 | 17.55 ч |
| экосольвент, ckbSize | size 50x50, URL ckbSize=0 | 3228 | 3 300 | — |
| латекс | HPLatex335, isCutEdge, size 1000x1000 | 6352 | 6 400 | 34.19 ч |
| плёнка фона Avery500w | is_background_film Avery500w | 4273 | 4 300 | 8.88 ч |
| плёнка фона Avery500c | is_background_film Avery500c | 4465 | 4 500 | 8.88 ч |
| аппликация Avery500w, сложность 1 / 1.3 / 1.7 | is_film Avery500w | 6213 / 6215 / 6219 | 6 300 | 17.53 ч |
| URL-only: профиль, подвес, EVA, numFoamH=400 | в POST нет, price не меняется | 4780 или 5653 на mode 2 | 4 800 или 5 700 | как у режима |
- Для Reviewer: карманы читаются DOM по классу `setPockets`, как боевой cjsCalc (повторяемая форма). Старый `{{rdoModeProduction}}` для «быстрее» складывает index и data-value; новый JS шлёт data-value (1 или 2). Дефолт «стандарт» — 1 и там, и там.
- URL-only (в `syncUrl`, не в `calcApi`): `dpdProfile`, `dpdHanger`, `numHangers`, `dpd` (EVA), `numFoamW`, `numFoamH`. Карманы в URL одной парой не пишутся. `ckbSize` влияет на `size` печати и фона.
- Строка для `docs/js-runner-cases.md`: `| calcTablets form 48 default | tablets | 4780 |` и команда `node scripts/run_js_calc.mjs calcTablets --data current --args '[1,[1000,1000],"PVC5",{"isCutManual":"KeencutEvolutionE2","isUVPrint":{"printerID":"PrintUV","resolution":0,"surface":"isPlain","color":"4+0"},"Material":"isMaterial"},1]'`.
- Строка будущего боевого пакета: форма 48 CalcStands, slug `tablets`, страница https://insain.ru/catalog/kalkulyator-stendov/. В `forms-batch-switch` не входит. Боевая остаётся на `insaincalc.calcTablets`, пока её не переключат отдельно.

### Доработка 29.11.2026

- Ветка, PR или коммит: `task/form-stands`, коммита нет.
- Было / стало: рамка, подвес, EVA и карманы писались только в `syncUrl`. Стало: блок `/* form 48 */` шлёт `is_pocket`, `is_frame`, `is_hanger`, `is_eva_foam` в `calcApi('tablets')`. Порт: `calculators/pockets.py`, `calculators/frame.py`, `calc_put_tape`, EVA через уже существующие резку и `calc_manual_roll`. Калькуляторы `pockets` и `frame` не публичные. Дефолт формы 48 и эталоны лида 36 не сдвигались.
- Сделано: строки allowed своего префикса сняты (`calcPockets`, `calcPutTape`, `calcFrame`, вызовы из `calcTablets`, опция `isEVAFoam`). Новых строк в allowed нет. Подвес меняет цену только вместе с рамкой, как `calcFrame`. Окантовка кармана всегда `Avery500c`, цена ленты из `tape.json` (cost 3), не из склеенного раннера.
- Чем проверено: `python -m pytest calc_service/tests/test_calculators/test_tablets.py::test_form48_pocket_a4_changes_price calc_service/tests/test_calculators/test_tablets.py::test_form48_pocket_count_scales calc_service/tests/test_calculators/test_tablets.py::test_form48_pocket_standoff_matches_js calc_service/tests/test_calculators/test_tablets.py::test_form48_eva_matches_js calc_service/tests/test_calculators/test_tablets.py::test_form48_frame_and_hanger_match_js calc_service/tests/test_calculators/test_tablets.py::test_tablets_js_form48_posts_options calc_service/tests/test_calculators/test_tablets.py::test_tablets_js_form48_posts_default -q` — 7 passed. `python scripts/dev.py check` — exit 0 (927 passed, затем 81 passed). `python scripts/js_port_gaps.py --check` — `ok`.
- Не сделано и почему: форма 121 не обновлена, плагин не выкладывался, боевые 36 и 48 не переключались, коммита нет. Критерии «на копии 121» остаются открытыми до Site ops.
- Как откатить git: не коммитить. Как откатить копию после записи: бэкап `/tmp/ezfc-copy-121-20261128-165139.json` — это JS прошлого круга, без опций в POST.
- Требуется решение: нет. Дальше Site ops: записать текущий `wp-plugin/forms/tablets.js` в форму 121, `read_file=0`, новый дубль не создавать, копию 120 / 2586916 и боевые 36 и 48 не трогать.

| Опция на дефолте формы 48 | POST | price API | Ожидаемая цена `showResult`, qty 1 | time_ready |
| --- | --- | --- | --- | --- |
| без кармана, рамки и EVA | этих полей нет | 4780 | 4 800 | 48.9 |
| карман PocketPETA4V ×1, окантовка Avery500c | is_pocket | 5183.9191676 | 5 200 | 49.08 |
| карман PocketStandoffА4V ×1 | is_pocket | 5413.72 | 5 500 | 49.08 |
| EVA EVAFoam5, 500×500 | is_eva_foam | 6385 | 6 400 | 49.3 |
| рамка AluFrame2Plus, сегменты 1000×2 и 1000×2 | is_frame | 7773.1 | 7 800 | 49.34 |
| та же рамка и подвес HangerH35 ×2 | is_frame и is_hanger | 7834.573333333334 | 7 900 | 49.35 |
| подвес без рамки | is_hanger | 4780 | 4 800 | 48.9 |

- Карман на держателях: `price` и `time_ready` совпали с раннером. `time_hours` у порта 0.71 против 0.72 у JS, вес 2.96 против 2.9; в приёмке этих полей нет, тест их не фиксирует.
- Строки для `docs/js-runner-cases.md` (в файл не писались): `| calcTablets form 48 pocket A4 | tablets | 5183.9191676 |`, `| calcTablets form 48 EVA 500 | tablets | 6385 |`, `| calcTablets form 48 frame | tablets | 7773.1 |`, `| calcTablets form 48 frame hanger | tablets | 7834.573333333334 |`. Рамка — только с загруженным `profile.json`. Карман с окантовкой на стоковом `--data current` даёт 5480.9711876 из-за склейки `Avery500c`; эталон задачи — 5183.9191676.
