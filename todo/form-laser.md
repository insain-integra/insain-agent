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
- Клеевой слой в `laser.py` по `js_legacy/calc/calcLaser.js:241-260`: листы `Sheet3M7952` (`AdhesiveLayer50`) и `Sheet3M7955` (`AdhesiveLayer130`) из каталога `tape`, накатка через `calc_manual_roll`, число листов `numWithDefects * (ширина+5) * (высота+5) / размер листа`. В накатку — `ceil` листов и размер листа скотча. `laser.js` не менять, новый радиоэлемент не заводить. Пустой `material_id` со слоем не даёт NaN и не остаётся ценой дефолта 480.
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
- `calc_service/materials/loader.py` — поле `weight` в каталоге (граммы единицы, как `material.weight` в JS)
- `scripts/js_port_gaps_allowed.txt` — снять `calcLaser call calcManualRoll`, вызов в `laser.py` реальный
- `calc_service/tests/test_js_port_gaps.py` — `MAX_ALLOWED` на единицу меньше
- `calc_service/tests/test_calculators/test_badge.py` — эталон cost/price после `noMaterial` на второй резке
- `calc_service/tests/test_wp_plugin_forms.py`
- `docs/js-runner-cases.md`
- `scripts/run_js_calc.mjs` — подключить `calcBadge.js`, чтобы команда раннера из критериев выполнялась
- WordPress: копия формы и черновик товара — Site ops после `deploy-api`

## Не-scope

- `read_file` и любое переключение боевой формы 28. Выкладка плагина. `infra/deploy.sh` в этой сессии (его делает Site ops после слияния, skill `deploy-api`).
- `docs/site/forms.md`, `site/forms/28.json`, `todo/forms-batch-switch.md`.
- Цены и `calc_service/data/`. Новые строки в `scripts/js_port_gaps_allowed.txt` не добавлять: снята только `calcLaser call calcManualRoll`, потому что вызов уже есть в `laser.py`.
- Переписывать `badge.py` (срок и вес): расхождение `time_ready` 16.55 против JS 17.9 и вес 1.18 против 0.87 остаётся прежним портом, не ценой материала.
- `calcPrintLaser` и вес листовой лазерной печати. Остальные формы эпика.
- Удаление копии и черновика.

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcLaser` — в блоке `calcLaser` строка `нет в Python` пустая: `calc_manual_roll` импортирован, строка `calcLaser call calcManualRoll` снята из `scripts/js_port_gaps_allowed.txt`. `python scripts/js_port_gaps.py --check` печатает `ok`.
- [x] Локальный Python и раннер: номерки price 5631 / `time_ready` 19.05; простая резка AcrylWhite3 23638 / 27.17; «без резки» 1404 / 16.2. Дефолт формы 28 (пустой материал): cost 300, price 480, `time_ready` 16.2, `weight_kg` 0, `materials` пустой. Допуск цены abs ≤ 0.02 и rel ≤ 0.001, срока rel ≤ 0.001. Боевой `POST` дефолта до `deploy-api` — HTTP 400; копию на этом API не принимать.
- [x] `python -m pytest calc_service/tests/test_calculators/test_laser.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, 15.11.2026`. Тесты пустого материала и «без резки» на старом `laser.py` падают.
- [x] `Select-String -Path wp-plugin\forms\laser.js -Pattern "calcApi\('laser'|syncUrl\(|showResult\("` — все три вхождения есть.
- [x] Копия не на витрине: `wp post get 2586892 --field=post_status` — `draft`; `curl.exe` без cookies на `/?post_type=product&p=2586892` — `404`. Боевая страница `200`, в HTML есть `calcLaser`.
- [x] На копии под админом эталон даёт `POST /api/v1/calc/laser` → 200 с выкатанным `laser.py` (`material_id` `AcrylColor3`, `is_grave` 1, `is_grave_fill` [30, 40]). Цена на странице 5 650 ₽ — округление `showResult` от `price` 5631. Дефолт API `price` 480 (`time_ready` 16.2), на странице 500 ₽, не 400. «Без резки» API 1404 / 16.2, на странице 1 500 ₽.
- [x] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой (100 шт., 50×50, материал индекс 1, «без резки», режим 1 → 1 500 ₽).
- [x] `material_mode` по `calcLaser.js:220-238`. Простая резка AcrylWhite3 100 шт. 50×50: `isMaterial` price 23638 / `time_ready` 27.17, в `materials` есть `AcrylWhite3`; `noMaterial` 22465 / 27.17, вес 0.8925, основного материала в `materials` нет; `isMaterialCustomer` 27961 / 29.92, вес тот же, основного материала нет. Номерки `isMaterialCustomer`: price 5708 / `time_ready` 19.77. Допуск цены и срока rel ≤ 0.001. Вес при `noMaterial` и `isMaterialCustomer` не обнуляется. Локальный `POST /api/v1/calc/laser` (TestClient) на этих трёх телах — 200 и те же числа. Без ветки `material_mode` тест `noMaterial` ждал бы 22465 и получил бы 23638.
- [x] `badge` не на боевой форме API (`docs/site/forms.md`). После починки вторая резка с печатью не включает PVC в стоимость: раннер `calcBadge` cost 3335, price 6060.5, `time_hours` 1.35; Python cost 3334.14, price 6061 (rel ≤ 0.001). `time_ready` 16.55 и `weight_kg` 1.18 не сдвинуты. `uv_badge`, `acrylic_prizes`, `tablets` свой `material_mode` не передают, их тесты зелёные.
- [x] После `deploy-api`: боевой `POST /api/v1/calc/laser` для эталона резки (size_item 50, density 25, difficulty 1, mode 1) — `isMaterial` 23638 / 27.17, `noMaterial` 22465 / 27.17, `isMaterialCustomer` 27961 / 29.92; номерки `isMaterial` 5631 / 19.05, `isMaterialCustomer` 5708 / 19.77. На копии 98 под админом переключение радио меняет `material_mode`, цену и таблицу материалов. `GET_check` элемента 3675 уже `index`, ссылка с `rdoMaterial=1` и `=2` открывает выбранную опцию. Боевая форма не менялась.
- [x] Клеевой слой по JS, каталог `tape`, `calc_manual_roll`. Простая резка AcrylWhite3 100 шт. 50×50 (`size_item` 50, `density` 25, `difficulty` 1, `mode` 1): `AdhesiveLayer50` cost 15959, price 25626, `time_ready` 27.44, `weight_kg` 0.9389; `AdhesiveLayer130` cost 16152, price 25946, `time_ready` 27.44, `weight_kg` 0.9852; `noMaterial` + `AdhesiveLayer130` price 24772, `time_ready` 27.44. Допуск цены abs ≤ 0.02 и rel ≤ 0.001, срока rel ≤ 0.001. Без слоя 23638 / 27.17 не сдвинут. В `materials` есть лист скотча (`name`/`title` из каталога). Стоимость листа — скаляр `get_cost(1.0)`, в `tape.json` тиров нет. Вес — `weight` листа (граммы) × число листов / 1000.
- [x] Пустой `material_id` и `AdhesiveLayer50`: не NaN и не price 480. Слой входит в цену (cost 1512, price 2468, `time_ready` 16.47), вес изделия 0 плюс вес скотча, в `materials` только `Sheet3M7952`. На `laser.py` из HEAD тест `test_laser_adhesive_layer_matches_js` — `KeyError` `Sheet3M7952` / `Sheet3M7955`.
- [x] Соседи `badge`, `uv_badge`, `acrylic_prizes`, `tablets` после вызова `calc_manual_roll` зелёные. Прод этой сессией не трогали.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0 (calc_service 613 passed, bot_service 81 passed)
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: радио на копии 98 заработает только после Reviewer, слияния в `main` и нового `deploy-api`. Боевая страница клиентам не меняется. До выкатки боевой `POST` на `noMaterial` всё ещё считает материал.
- Цены: JSON не править. Эталоны номерков и простой резки при `isMaterial` не сдвигать. `badge` цену сдвигает к JS, срок и вес — нет.
- Клеевой слой на копии 98 заработает только после Reviewer, слияния в `main` и нового `deploy-api`. До выкатки `POST` с `is_adhesive_layer` на боевом API падает.
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
15.11.2026 — Site ops, Grok 4.7 — API `main` @ `5aa08e9` выкачен, smoke зелёный; боевой POST эталона совпал; на копии 98 радио меняет цену, `GET_check` 3675 уже `index` и ссылка восстанавливает радио — дальше Reviewer
15.11.2026 — Reviewer, Auto — принято (круг 3, отчёт Site ops и `material_mode` на проде) — дальше человек (приёмка копии, закрытие задачи)
15.11.2026 — человек — замечание при приёмке копии 98: не срабатывает radiobutton выбора клеевого слоя — дальше Implementer
15.11.2026 — Implementer, Grok 4.7 — блокер: клеевой слой в `laser.py` падает и не сходится с JS; на форме 28/98 нет радио 50/130, только чекбокс `chkAdhesiveLayer` — дальше человек
15.11.2026 — человек — выбран вариант 1: починить порт клеевого слоя в `laser.py` здесь (каталог `tape`, `calc_manual_roll`, формула JS) — дальше Implementer
15.11.2026 — Implementer, Grok 4.7 — клеевой слой в `laser.py`: каталог `tape`, `calc_manual_roll`, эталоны; `make check` зелёный — дальше Reviewer
15.11.2026 — Reviewer, Auto — принято (круг 4, клеевой слой) — дальше человек (коммит, слияние, `deploy-api`, чекбокс на копии 98)
15.11.2026 — человек — принято для выкатки (круг 4): слить в main, выкатить API и проверить чекбокс «Клеевой слой» на копии 98 — выкатка

```text
Блокер: чекбокс «Клеевой слой» не может сменить цену, потому что порт is_adhesive_layer в laser.py падает. Радио AdhesiveLayer50/AdhesiveLayer130 на формах 28 и 98 нет.
Пробовал: readonly wp db query форм 28 и 98 (элементы, опции, GET, cjsCalc 992 и 3691). Раннер calcLaser --data current и LaserCalculator.execute на простой резке AcrylWhite3 100 шт. 50×50. Подмена каталога misc → tape в памяти процесса (файл не менялся) — следующий вызов падает на tool._items.
Гипотеза: замечание человека про «radiobutton» — это чекбокс 2630/3689. Старый и новый JS уже пишут AdhesiveLayer50. Цена не меняется, потому что API не доходит до числа: лист скотча лежит в tape, а laser.py ищет его в misc и дальше читает несуществующее поле оборудования.
Вопрос: чинить порт клеевого слоя в task/form-laser (по JS, с вызовом calc_manual_roll) или выносить предпосылку и не трогать копию 98.
Следующая сессия: человек (AskQuestion), затем Implementer, модель Grok 4.7, либо отдельная задача, если выбрана предпосылка.
Снято 15.11.2026 (вариант 1): человек расширил scope на правку клеевого слоя в `laser.py`.
```

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

## Ревью 3

**Итог:** принято.

**Круг 3:** сверка «Результат» Site ops с последним критерием приёмки (`deploy-api`, копия 98, боевой POST). Diff в git не пересматривался (круги 1–2 приняты, прод на `5aa08e9`).

**Критерий после `deploy-api` (Site ops):**

| Проверка | Вердикт |
| --- | --- |
| Боевой `POST` резки: `size_item` 50, `density` 25 — `isMaterial` 23638/27.17, `noMaterial` 22465/27.17, `isMaterialCustomer` 27961/29.92 | ок: совпадает с отчётом Site ops; локально TestClient на `main` @ `5aa08e9` — те же числа (прод не дергали) |
| Номерки: `isMaterial` 5631/19.05, `isMaterialCustomer` 5708/19.77 | ок: отчёт Site ops и TestClient |
| Копия 98: радио 3675 меняет `material_mode`, цену и таблицу материалов | ок: отчёт (2 600 / 1 500 / 1 700 ₽ на экране — от другого тела, см. ниже) |
| `GET_check` 3675 = `index`, ссылка `rdoMaterial=1`/`2` | ок: отчёт, перепись не делалась |
| Черновик `draft`, копия 404 без cookies, боевая `calcLaser`, плагин не выкладывали | ок: отчёт |

**Почему копия шлёт `size_item` 0 и `density` 0 (вне блокера критерия):**

В `wp-plugin/forms/laser.js` размер и плотность берутся не через `get_value_from`, а плейсхолдерами ezFC `{{numSizeItem}}` и `{{numDensity}}` (строки 20–21). При `calculate_when_hidden=0` у скрытых полей сложности «простая резка» (типичный дефолт формы 28) подстановка даёт 0, хотя в разметке могут быть `defaultValue` 50 и 25% — тот же класс проблем, что у `sticker.js` / `form-sticker` в `BACKLOG.md`. В API при `difficulty` 1 и нулевых `size_item`/`density` `laser.py` не добавляет внутренний периметр (`if size_item:` в `len_cut`), эталон 23638 не применим к такому телу. Локальный POST 100×50×50 AcrylWhite3 с нулями: `isMaterial` 2596 / 16.67, `noMaterial` 1422, `isMaterialCustomer` 1658 — совпадает с перехватом Site ops и округлением `showResult`. Для номерок тест портирования как раз с `size_item`/`density` 0 (`test_laser.py` REF номерков). Исправление — отдельная задача (чтение полей в `laser.js` или `calculate_when_hidden` на копии), не входит в критерий круга 3.

**Инварианты:** прод и diff не трогали; `material_mode` на боевом API подтверждён отчётом и локальным эталонным телом.

**Замечания:** без `блокер`.

**Найдено вне scope:** строка в «Состав пакета» в «Результат» — для человека при закрытии. Расхождение цен простой резки на копии из-за нулей в POST — в `Найдено вне scope` задачи, не держит закрытие `material_mode` и deploy.

**Дальше:** статус `закрытие`. Человек: визуальная приёмка копии 98 (радио и GET), затем `python scripts/dev.py close form-laser` по желанию; выкладка плагина и боевая форма 28 — вне scope.

## Ревью 4

**Итог:** принято.

**Круг 4 (diff после ревью 3):** клеевой слой — `laser.py` (каталог `tape`, `calc_manual_roll`, `num_with_defects`, слой без обязательного `material_id`), `loader.py` (`weight` → `weight_per_unit`), эталоны в `test_laser.py`, снятие `calcLaser call calcManualRoll`, `MAX_ALLOWED` 71. `wp-plugin/forms/laser.js` и прод в diff нет.

**Критерии (локально):**

| Критерий | Вердикт |
| --- | --- |
| `js_port_gaps calcLaser` — `нет в Python` пусто; строка `calcManualRoll` снята; `--check` → `ok` | ок |
| AdhesiveLayer50: 15959 / 25626 / 27.44 / 0.9389; AdhesiveLayer130: 16152 / 25946 / 27.44 / 0.9852; `noMaterial` + 130 → price 24772, `time_ready` 27.44 | ок: `test_laser_adhesive_layer_matches_js`, `test_laser_adhesive_no_material` |
| Без слоя 23638 / 27.17 | ок: `test_laser_simple_cut_unchanged` |
| Пустой `material_id` + AdhesiveLayer50: cost 1512, price 2468, `time_ready` 16.47, не 480/NaN; в `materials` только `Sheet3M7952` | ок: `test_laser_adhesive_empty_material` |
| На `laser.py` из HEAD тест клея — `KeyError` `Sheet3M7952` / `Sheet3M7955` | ок: 2 failed, файл восстановлен |
| `python scripts/dev.py check` | ок: код 0, calc_service 613, bot_service 81 |
| Регресс `badge`, `uv_badge`, `acrylic_prizes`, `tablets`, `test_js_port_gaps` | ок: 41 passed по выборке соседей |
| Чекбокс клея на копии 98 после `deploy-api` | вне этой сессии — человек + Site ops после выкатки |

**Инварианты AGENTS.md:** JSON не трогали; ответ со всеми обязательными полями; лист скотча в `materials` с `name`/`title` из каталога, не голый `code`; `calc_manual_roll` — порт, не пересчёт на месте; комментарии по-русски.

**Замечания:**

- `желательно`: правки круга 4 не закоммичены (`git status` — modified без staging); перед слиянием — коммит на `task/form-laser`.

**Найдено вне scope:** без нового.

**Дальше:** статус остаётся `ревью`. Человек: коммит, слияние в `main`, `deploy-api` (skill `deploy-api`), затем приёмка чекбокса «Клеевой слой» на копии 98 (до выкатки боевой `POST` с `is_adhesive_layer` падает). `laser.js` и радио 50/130 по-прежнему вне scope — форма шлёт `AdhesiveLayer50` через чекбокс.

```text
Блокер: дефолт боевой формы 28 (пустой материал) и опция «без резки» не сходятся с POST /api/v1/calc/laser. Форму не дублировать, laser.js не писать.
Пробовал: js_port_gaps calcLaser — единственный пропуск «call calcManualRoll», он уже в js_port_gaps_allowed.txt. pytest test_laser.py — 3 passed. Раннер и страница: эталон номерков (50 шт., 40×80, AcrylColor3, isGrave 1, isGraveFill [30,40], isCutLaser с нулями) price 5631, time_ready 19.05 — совпал с локальным Python и с POST https://insain.ru/api/v1/calc/laser. Простая резка 100 шт. 50×50 AcrylWhite3 (difficulty 1, sizeItem 50, density 25) — JS и API price 23638, time_ready 27.17. Дефолт страницы: материал «не задан» (data-value пустой), простая резка, режим 1. calcLaser на странице: cost 300, price 480, time 0.2, time_ready 16.2, weight NaN; раннер падает на NaN веса. POST того же тела — HTTP 400 «параметр material_id обязателен». Опция «без резки» (isCutLaser нет, AcrylWhite3): JS price 1404, time_ready 16.2; API price 2596, time_ready 16.67 (rel цены ≈ 0.849, rel срока ≈ 0.029). docs/site/forms.md: форма 28 на старом JS, slug laser ни к одной боевой форме API не привязан.
Гипотеза: порт считает material_id обязательным и при отсутствии is_cut_laser всё равно режет периметр. JS при пустом материале берёт только время подготовки, при «без резки» считает площадь листа без раскладки и без времени реза. Это расхождение не-боевого калькулятора (workflow: чинить в текущей ветке) и одновременно запрет задачи править laser.py (предпосылка port-fix-prerequisite).
Вопрос: чинить порт в task/form-laser или выносить предпосылку и не дублировать форму.
Следующая сессия: человек (AskQuestion), затем Implementer, модель Grok 4.7, либо Analyst, если выбрана предпосылка.
Снято 15.11.2026 (вариант 1): человек расширил scope `form-laser` на правку `laser.py`.
```

## Найдено вне scope

- Копия 98 шлёт в `POST` `size_item: 0` и `density: 0`, хотя поле «Размер элементов» показывает 50, а «Плотность элементов» — `25%` (defaultValue `25`). Цена на странице поэтому 2 600 / 1 500 / 1 700 ₽, не округление эталона 23638 / 22465 / 27961. `material_mode` при этом уходит верный. Не чинилось: вне списка правок этой сессии (только `GET_check` 3675, и только если ссылка не восстанавливает радио).
- `badge.py`: `time_ready` 16.55 против JS 17.9 и вес 1.18 против 0.87. Цена после `noMaterial` сошлась. Срок и вес не чинить в этой задаче.

## Результат

- Ветка, PR или коммит: `task/form-laser`, коммита этой сессии нет (человек не просил). Предыдущая выкатка — `main` @ `5aa08e9`, в этой сессии прод не трогали.
- Сделано: клеевой слой в `laser.py` берёт `Sheet3M7952` / `Sheet3M7955` из каталога `tape`. Накатка — `calc_manual_roll(ceil(листов), размер листа)`. Число листов — `numWithDefects * (ширина+5) * (высота+5) / (609*900)`. Стоимость листа — скаляр `get_cost(1.0)` (`tape.json` без тиров, это `material.cost` в JS). Вес — поле `weight` листа в граммах (загрузчик пишет его в `weight_per_unit`) × число листов / 1000. Пустой `material_id` со слоем больше не отбрасывает слой: price 2468, не 480 и не NaN, в `materials` только лист скотча. Строка `calcLaser call calcManualRoll` снята из допусков: `js_port_gaps calcLaser` показывает пустое `нет в Python`, `--check` — `ok`.
- Было / стало: на HEAD `is_adhesive_layer` падал `KeyError` (`misc.get('Sheet3M7952')`), затем на `tool._items`. Стало: простая резка AcrylWhite3 100 шт. 50×50 — `AdhesiveLayer50` cost 15959, price 25626, `time_ready` 27.44, `weight_kg` 0.9389; `AdhesiveLayer130` cost 16152, price 25946, `time_ready` 27.44, `weight_kg` 0.9852; `noMaterial` + `AdhesiveLayer130` price 24772, `time_ready` 27.44. Без слоя 23638 / 27.17.
- Чем проверено: тест `test_laser_adhesive_layer_matches_js` на `laser.py` из HEAD — 2 failed, `KeyError` `Sheet3M7952` и `Sheet3M7955`; файл после прогона восстановлен. После правки `pytest` laser 16 passed; соседи `badge`, `uv_badge`, `acrylic_prizes`, `tablets` вместе с `test_js_port_gaps` и `test_materials` — 63 passed. `python scripts/js_port_gaps.py calcLaser` — `нет в Python` пусто; `--check` — `ok`. `python scripts/dev.py check` — см. «Проверки».
- Не сделано и почему: прод, `laser.js` и новый радиоэлемент не трогались — так в задаче. Коммит не делался.
- Требуется решение: Reviewer (`Auto`) по diff. После приёмки — человек: коммит, слияние, `deploy-api`, затем повторная проверка чекбокса клеевого слоя на копии 98. До выкатки боевой `POST` со слоем по-прежнему падает.
- Предыдущая выкатка `material_mode` (`5aa08e9`) и строка пакета ниже не отменяются этой сессией. Отчёт Site ops — в «Ревью 3».
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока ту задачу не сливают):

| 28 CalcLaser | `laser` | `/catalog/lazernaya-gravirovka-i-rezka/` | 98 / 2586892 (draft) | API `5aa08e9`, радио `material_mode` на копии меняет цену, GET `rdoMaterial` восстанавливается, боевая на `calcLaser` |
