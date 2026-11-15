# form-laser

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: человек 15.11.2026 расширил scope на `material_mode` в `laser.py` (радио «не учитывать материал» / «материал заказчика»). Смешанная цепочка: Reviewer по diff, слияние в `main`, `deploy-api`, затем повторная приёмка копии 98. `Reviewer: Auto` — модель не совпадает с Implementer.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 28 CalcLaser на черновике товара считает `POST /api/v1/calc/laser`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 28 на странице https://insain.ru/catalog/lazernaya-gravirovka-i-rezka/ по-прежнему на `insaincalc.calcLaser`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 28, только читать.
- `todo/EPIC-forms-to-api.md` — пачка 3.
- `docs/js-runner-cases.md` — команда раннера для `calcLaser`, если кейс уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): правка `calc_service/calculators/laser.py` по `js_legacy/calc/calcLaser.js` — пустой `material_id` (только время подготовки; вес 0 и пустой `materials`, не NaN), ветка «без резки» (нет `is_cut_laser`: площадь первого размера, без раскладки и без времени реза) и `material_mode` (`js_legacy/calc/calcLaser.js:220-238`). Пустой `{}` по-прежнему включает резку. Эталоны номерков и простой резки при `isMaterial` не сдвигать. Соседи с явным `is_cut_laser` и без своего `material_mode` не сдвигать; `uv_badge.py` передаёт `is_cut_laser: {}`, иначе бейдж попал бы в «без резки».
- `material_mode`: по умолчанию `isMaterial` — основной материал в `materials`, `cost_material` учитывается. `noMaterial` и `isMaterialCustomer` — `cost_material = 0`, основной `material_id` в `materials` не входит, вес по-прежнему считается по материалу. `isMaterialCustomer` — `time_cut` и `time_grave` × 1.25. `badge.py` при печати передаёт `noMaterial` на вторую резку: PVC в её стоимость не входит. Срок и вес `badge.py` к JS не выравнивать.
- `wp-plugin/forms/laser.js`: id элементов боевой формы 28, `insaincalc.syncUrl`, `insaincalc.calcApi('laser'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_laser.py` с пометкой `# JS, 15.11.2026`. Команды раннера — в `docs/js-runner-cases.md`.
- После слияния в `main` снова нужен `deploy-api`: на проде ещё `laser.py` без `material_mode`, радио на копии 98 цену не меняет. Дефолт пустого материала уже выкачен (`ffc23a7`, price 480).
- На проде (Site ops): копия 98 и черновик 2586892 уже есть. После нового `deploy-api` — прогон радио `noMaterial` и `isMaterialCustomer` на копии, не создание второго дубля. Боевую форму не размечать.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-laser` от `main`.

## Файлы

- `calc_service/calculators/laser.py`
- `calc_service/calculators/uv_badge.py` — явный `is_cut_laser: {}`, чтобы цена бейджа не уехала в «без резки»
- `wp-plugin/forms/laser.js`
- `calc_service/tests/test_calculators/test_laser.py`
- `calc_service/tests/test_calculators/test_badge.py` — эталон cost/price после `noMaterial` на второй резке
- `calc_service/tests/test_wp_plugin_forms.py`
- `docs/js-runner-cases.md`
- `scripts/run_js_calc.mjs` — подключить `calcBadge.js`, чтобы команда раннера из критериев выполнялась
- WordPress: копия формы и черновик товара — Site ops после `deploy-api`

## Не-scope

- `read_file` и любое переключение боевой формы 28. Выкладка плагина. `infra/deploy.sh` в этой сессии (его делает Site ops после слияния, skill `deploy-api`).
- `docs/site/forms.md`, `site/forms/28.json`, `todo/forms-batch-switch.md`.
- Цены, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`.
- Переписывать `badge.py` (срок и вес): расхождение `time_ready` 16.55 против JS 17.9 и вес 1.18 против 0.87 остаётся прежним портом, не ценой материала.
- `calcPrintLaser` и вес листовой лазерной печати. Остальные формы эпика.
- Удаление копии и черновика.

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcLaser` — в блоке `calcLaser` единственный пропуск `call calcManualRoll`, он есть в `scripts/js_port_gaps_allowed.txt` (`calcLaser call calcManualRoll`).
- [x] Локальный Python и раннер: номерки price 5631 / `time_ready` 19.05; простая резка AcrylWhite3 23638 / 27.17; «без резки» 1404 / 16.2. Дефолт формы 28 (пустой материал): cost 300, price 480, `time_ready` 16.2, `weight_kg` 0, `materials` пустой. Допуск цены abs ≤ 0.02 и rel ≤ 0.001, срока rel ≤ 0.001. Боевой `POST` дефолта до `deploy-api` — HTTP 400; копию на этом API не принимать.
- [x] `python -m pytest calc_service/tests/test_calculators/test_laser.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, 15.11.2026`. Тесты пустого материала и «без резки» на старом `laser.py` падают.
- [x] `Select-String -Path wp-plugin\forms\laser.js -Pattern "calcApi\('laser'|syncUrl\(|showResult\("` — все три вхождения есть.
- [x] Копия не на витрине: `wp post get 2586892 --field=post_status` — `draft`; `curl.exe` без cookies на `/?post_type=product&p=2586892` — `404`. Боевая страница `200`, в HTML есть `calcLaser`.
- [x] На копии под админом эталон даёт `POST /api/v1/calc/laser` → 200 с выкатанным `laser.py` (`material_id` `AcrylColor3`, `is_grave` 1, `is_grave_fill` [30, 40]). Цена на странице 5 650 ₽ — округление `showResult` от `price` 5631. Дефолт API `price` 480 (`time_ready` 16.2), на странице 500 ₽, не 400. «Без резки» API 1404 / 16.2, на странице 1 500 ₽.
- [x] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой (100 шт., 50×50, материал индекс 1, «без резки», режим 1 → 1 500 ₽).
- [x] `material_mode` по `calcLaser.js:220-238`. Простая резка AcrylWhite3 100 шт. 50×50: `isMaterial` price 23638 / `time_ready` 27.17, в `materials` есть `AcrylWhite3`; `noMaterial` 22465 / 27.17, вес 0.8925, основного материала в `materials` нет; `isMaterialCustomer` 27961 / 29.92, вес тот же, основного материала нет. Номерки `isMaterialCustomer`: price 5708 / `time_ready` 19.77. Допуск цены и срока rel ≤ 0.001. Вес при `noMaterial` и `isMaterialCustomer` не обнуляется. Локальный `POST /api/v1/calc/laser` (TestClient) на этих трёх телах — 200 и те же числа. Без ветки `material_mode` тест `noMaterial` ждал бы 22465 и получил бы 23638.
- [x] `badge` не на боевой форме API (`docs/site/forms.md`). После починки вторая резка с печатью не включает PVC в стоимость: раннер `calcBadge` cost 3335, price 6060.5, `time_hours` 1.35; Python cost 3334.14, price 6061 (rel ≤ 0.001). `time_ready` 16.55 и `weight_kg` 1.18 не сдвинуты. `uv_badge`, `acrylic_prizes`, `tablets` свой `material_mode` не передают, их тесты зелёные.
- [ ] После `deploy-api`: боевой `POST /api/v1/calc/laser` для `noMaterial` (22465) и `isMaterialCustomer` (27961). На копии 98 под админом переключение «Не учитывать материал в цене» и «Материал заказчика» меняет цену. `GET_check` элемента 3675 (`rdoMaterial`) сейчас пустой, а `syncUrl` пишет индекс: если ссылка с GET не восстанавливает радио — выставить `GET_check=index`, боевую форму не трогать.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0 (calc_service 609 passed, bot_service 81 passed)
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: радио на копии 98 заработает только после Reviewer, слияния в `main` и нового `deploy-api`. Боевая страница клиентам не меняется. До выкатки боевой `POST` на `noMaterial` всё ещё считает материал.
- Цены: JSON не править. Эталоны номерков и простой резки при `isMaterial` не сдвигать. `badge` цену сдвигает к JS, срок и вес — нет.
- Формы: id элементов боевой формы 28 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

15.11.2026 — Implementer, Grok 4.7 — блокер: дефолт формы 28 и «без резки» не сходятся с API — дальше человек
15.11.2026 — человек — выбран вариант 1: расширить scope `form-laser` и починить `laser.py` (пустой `material_id` и ветка «без резки» по JS), затем продолжить перевод формы — дальше Implementer
15.11.2026 — Implementer, Grok 4.7 — `laser.py` (пустой материал и «без резки»), `laser.js`, эталоны; `make check` зелёный — дальше Reviewer
15.11.2026 — Reviewer, Auto — принято — дальше человек (слияние, `выкатка`, deploy-api, Site ops)
15.11.2026 — человек — принято для выкатки: слить в main, выкатить API и сделать дубль формы 28 на черновике — выкатка
15.11.2026 — Site ops, Grok 4.7 — API `main` @ `ffc23a7` выкачен, smoke зелёный; копия формы 98 на черновике 2586892, GET и прогон под админом сошлись — дальше человек
15.11.2026 — человек — замечание при приёмке копии 98: не срабатывает переключение radiobutton «Не учитывать материал в цене» / «Материал заказчика»; выбран вариант починить `material_mode` в `laser.py` по JS и перепроверить `badge.py` — дальше Implementer
15.11.2026 — Implementer, Grok 4.7 — `material_mode` в `laser.py` по JS, эталоны laser и cost/price badge, дубль тестов снят; `make check` зелёный — дальше Reviewer
15.11.2026 — Reviewer, Auto — принято (круг 2, `material_mode`) — дальше человек (коммит, слияние, `deploy-api`, Site ops)
15.11.2026 — человек — принято для выкатки (круг 2): слить в main, выкатить API и проверить `material_mode` + GET на копии 98 — выкатка

## Ревью 1

**Итог:** принято.

**Критерии (git / Implementer):**

| Критерий | Вердикт |
| --- | --- |
| `js_port_gaps calcLaser` — только `call calcManualRoll` в допусках | ок: единственный пропуск, строка `calcLaser call calcManualRoll` в `scripts/js_port_gaps_allowed.txt` |
| Эталоны JS/Python: номерки 5631/19.05, простая резка 23638/27.17, «без резки» 1404/16.2, дефолт 300/480/16.2, `weight_kg` 0, `materials` [] | ок: тесты `test_laser_simple_cut_unchanged`, `test_laser_no_cut`, `test_form_default_empty_material`, `test_nomerki_matches_js_tight`; на `laser.py` из HEAD те же три теста — `3 failed` |
| pytest laser + `test_laser_js_calls_laser_api`, `REF_FORM_DEFAULT` `# JS, 15.11.2026` | ок: `9 passed` (laser + wp), `python scripts/dev.py check` — код 0, calc_service 605, bot_service 81 |
| `laser.js`: `calcApi('laser'`, `syncUrl(`, `showResult(` | ок: `Select-String` — три вхождения; без `calcLaser`, `querySelector`, своей `price=` |
| `laser.py`: пустой `material_id`, ветка без `is_cut_laser`, `{}` режет; `uv_badge.py` — `is_cut_laser: {}` | ок по diff; `test_uv_badge.py` — 7 passed, регрессии бейджа нет |
| Копия на проде, GET, приёмка копии | вне этой сессии — Site ops после слияния и `deploy-api` |

**Инварианты AGENTS.md:** обязательные поля ответа и `materials` с `code`/`name`/`title` — в новых тестах; цен/JSON в diff нет; номерки и простая резка не сдвинуты; комментарии по-русски.

**Замечания:**

- `желательно`: в `calc_service/tests/test_calculators/test_laser.py` блок строк 385–517 — полный дубль 250–383 (`JS_REL`, `_assert_js`, те же пять тестов). На сборку не влияет (вторая декларация перекрывает первую), но перед коммитом лучше убрать дубль.

**Найдено вне scope:** без изменений — `material_mode` в `laser.py` не применяется (уже в задаче).

**Дальше:** статус остаётся `ревью`. Человек: коммит на `task/form-laser`, слияние в `main`, статус `выкатка`. Site ops: skill `deploy-api`, затем дубль формы 28 и критерии копии (дефолт price 480 на боевом API).

## Ревью 2

**Итог:** принято.

**Круг 2 (diff после ревью 1):** только `material_mode` в `laser.py`, эталоны в `test_laser.py` / `test_badge.py`, снятие дубля тестов (замечание ревью 1), `calcBadge.js` в раннере. Плагин и боевую форму diff не трогает.

**Критерии (git / Implementer):**

| Критерий | Вердикт |
| --- | --- |
| `material_mode` по `calcLaser.js:220-238`: `isMaterial` — материал в цене и в `materials`; `noMaterial` / `isMaterialCustomer` — `cost_material` 0, основной `material_id` не в `materials`, вес по материалу сохранён | ок: блок после сборки `materials`, до `time_cut`/`cost`; `weight_kg` через `calc_weight` после режима; эталоны `test_laser_material_mode`, `test_laser_nomerki_material_customer` |
| `isMaterialCustomer` — `time_cut` и `time_grave` × 1.25 | ок: множители до расчёта `cost_cut` / `cost_grave`; номерки 5708 / 19.77 |
| Эталоны `isMaterial`: номерки 5631/19.05, простая резка 23638/27.17 | ок: `test_nomerki_matches_js_tight`, `test_laser_simple_cut_unchanged` |
| `badge` — вторая резка с печатью, `noMaterial` на laser2 | ок: `badge.py:206` без правок; `EXPECTED_REF` cost 3335 / price 6060.5 (JS); `time_ready` 16.55 и `weight_kg` 1.18 без сдвига |
| Дубль блока в `test_laser.py` (ревью 1) | ок: второй `JS_REL` / те же пять тестов удалены, −133 строки в diff vs `main` |
| Регресс соседей (`uv_badge`, `acrylic_prizes`, `tablets`) | ок: файлов нет в diff; `30 passed` по их тестам |
| `python scripts/dev.py check` | ок: код 0, calc_service 609, bot_service 81 (повтор ревью) |
| Критерий после `deploy-api` (радио на копии 98, боевой POST) | вне этой сессии — человек + Site ops |

**Инварианты AGENTS.md:** JSON не трогали; обязательные поля и `materials` с `name`/`title` — в новых тестах; комментарии по-русски в `laser.py`.

**Замечания:**

- `желательно`: правки круга 2 в рабочей копии не закоммичены (`git status` — modified без staging); перед слиянием — коммит на `task/form-laser`.

**Найдено вне scope:** элемент 3675 (`rdoMaterial`) на копии 98 — `GET_check` пустой, `syncUrl` пишет индекс; для Site ops после `deploy-api`: при невосстановлении радио из ссылки — `GET_check=index` на копии, боевую форму не трогать.

**Дальше:** статус остаётся `ревью`. Человек: коммит, слияние в `main`, статус `выкатка`. Site ops: skill `deploy-api`, прогон `noMaterial` / `isMaterialCustomer` на копии 98, проверка `GET_check` для 3675.

```text
Блокер: дефолт боевой формы 28 (пустой материал) и опция «без резки» не сходятся с POST /api/v1/calc/laser. Форму не дублировать, laser.js не писать.
Пробовал: js_port_gaps calcLaser — единственный пропуск «call calcManualRoll», он уже в js_port_gaps_allowed.txt. pytest test_laser.py — 3 passed. Раннер и страница: эталон номерков (50 шт., 40×80, AcrylColor3, isGrave 1, isGraveFill [30,40], isCutLaser с нулями) price 5631, time_ready 19.05 — совпал с локальным Python и с POST https://insain.ru/api/v1/calc/laser. Простая резка 100 шт. 50×50 AcrylWhite3 (difficulty 1, sizeItem 50, density 25) — JS и API price 23638, time_ready 27.17. Дефолт страницы: материал «не задан» (data-value пустой), простая резка, режим 1. calcLaser на странице: cost 300, price 480, time 0.2, time_ready 16.2, weight NaN; раннер падает на NaN веса. POST того же тела — HTTP 400 «параметр material_id обязателен». Опция «без резки» (isCutLaser нет, AcrylWhite3): JS price 1404, time_ready 16.2; API price 2596, time_ready 16.67 (rel цены ≈ 0.849, rel срока ≈ 0.029). docs/site/forms.md: форма 28 на старом JS, slug laser ни к одной боевой форме API не привязан.
Гипотеза: порт считает material_id обязательным и при отсутствии is_cut_laser всё равно режет периметр. JS при пустом материале берёт только время подготовки, при «без резки» считает площадь листа без раскладки и без времени реза. Это расхождение не-боевого калькулятора (workflow: чинить в текущей ветке) и одновременно запрет задачи править laser.py (предпосылка port-fix-prerequisite).
Вопрос: чинить порт в task/form-laser или выносить предпосылку и не дублировать форму.
Следующая сессия: человек (AskQuestion), затем Implementer, модель Grok 4.7, либо Analyst, если выбрана предпосылка.
Снято 15.11.2026 (вариант 1): человек расширил scope `form-laser` на правку `laser.py`.
```

## Найдено вне scope

- Копия 98, элемент 3675 `rdoMaterial`: `value` опций `isMaterial` / `noMaterial` / `isMaterialCustomer`, GET-имя `rdoMaterial`, `GET_check` пустой. JS копии читает 3675 и в URL пишет индекс. На живой пересчёт цены это не влияет. Если после `deploy-api` ссылка не восстанавливает радио — `GET_check=index` на копии, боевую форму не трогать.
- `badge.py`: `time_ready` 16.55 против JS 17.9 и вес 1.18 против 0.87. Цена после `noMaterial` сошлась. Срок и вес не чинить в этой задаче.

## Результат

- Ветка, PR или коммит: `task/form-laser`, коммита этой сессии нет. Предыдущая выкатка — `main` @ `ffc23a7` (без `material_mode`). Плагин не выкладывался.
- Сделано: `laser.py` читает `material_mode` по `calcLaser.js:220-238`. Вес по материалу сохраняется. Дубль блока в `test_laser.py` (замечание ревью 1) убран. Эталон `test_badge.py` по cost/price сдвинут к раннеру: вторая резка с печатью больше не включает PVC. `calcBadge.js` подключён к раннеру. `badge.py`, `uv_badge.py`, `acrylic_prizes.py`, `tablets.py` не менялись.
- Было / стало: простая резка AcrylWhite3 при `noMaterial` и `isMaterialCustomer` давала ту же цену, что `isMaterial` (23638). Стало 22465 и 27961, вес 0.8925 в обоих, основного материала в `materials` нет. Номерки `isMaterial` остались 5631 / 19.05; `isMaterialCustomer` — 5708 / 19.77. Бейдж с печатью: cost 3568.14 → 3334.14, price 6509 → 6061 (раннер 3335 / 6060.5). Срок бейджа 16.55 и вес 1.18 те же.
- Чем проверено: раннер `calcLaser` и `calcBadge` (`--data current`); локальный `POST /api/v1/calc/laser` через TestClient — три режима, 200, те же числа. Readonly SQL форм 28 и 98: опции `rdoMaterial` — `isMaterial` / `noMaterial` / `isMaterialCustomer`; JS копии читает элемент 3675, не 1027. `python scripts/dev.py check` — см. критерий проверок.
- Не сделано и почему: прод не писался и API не выкатывался — это Site ops после ревью и слияния. Срок и вес `badge.py` к JS не выравнивались. Боевая форма 28 не менялась.
- Как откатить: не коммитить ветку `task/form-laser` и не сливать. Боевой API остаётся на `ffc23a7`, пока нет нового `deploy-api`.
- Требуется решение: коммит круга 2, слияние, `deploy-api`, приёмка радио на копии 98 (ревью 2 принято).
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока ту задачу не сливают):

| 28 CalcLaser | `laser` | `/catalog/lazernaya-gravirovka-i-rezka/` | 98 / 2586892 (draft) | копия есть, радио `material_mode` ждёт `deploy-api`, `form-laser` |
