# form-laser

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: человек 15.11.2026 расширил scope на правку `laser.py` (пустой материал и «без резки»). Смешанная цепочка: Reviewer по diff, слияние в `main`, `deploy-api`, затем копия формы. `Reviewer: Auto` — модель не совпадает с Implementer.
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

- В git (Implementer): правка `calc_service/calculators/laser.py` по `js_legacy/calc/calcLaser.js` — пустой `material_id` (только время подготовки; вес 0 и пустой `materials`, не NaN) и ветка «без резки» (нет `is_cut_laser`: площадь первого размера, без раскладки и без времени реза). Пустой `{}` по-прежнему включает резку. Эталоны номерков и простой резки не сдвигать. Соседи с явным `is_cut_laser` не сдвигать; `uv_badge.py` передаёт `is_cut_laser: {}`, иначе бейдж попал бы в «без резки».
- `wp-plugin/forms/laser.js`: id элементов боевой формы 28, `insaincalc.syncUrl`, `insaincalc.calcApi('laser'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_laser.py` с пометкой `# JS, 15.11.2026`. Команды раннера — в `docs/js-runner-cases.md`.
- После слияния в `main` нужен `deploy-api` до приёмки копии на боевом API: `laser.py` меняется, без выкатки дефолт формы на проде остаётся HTTP 400 вместо price 480.
- На проде (Site ops): дубль формы и черновик товара — после Reviewer, слияния и `deploy-api`, не в этой сессии. На копию — тот же JS с id копии, без `read_file`. GET на копии: имя параметра = имя элемента. Боевую форму не размечать. Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-laser` от `main`.

## Файлы

- `calc_service/calculators/laser.py`
- `calc_service/calculators/uv_badge.py` — явный `is_cut_laser: {}`, чтобы цена бейджа не уехала в «без резки»
- `wp-plugin/forms/laser.js`
- `calc_service/tests/test_calculators/test_laser.py`
- `calc_service/tests/test_wp_plugin_forms.py`
- `docs/js-runner-cases.md`
- WordPress: копия формы и черновик товара — Site ops после `deploy-api`

## Не-scope

- `read_file` и любое переключение боевой формы 28. Выкладка плагина. `infra/deploy.sh` в этой сессии (его делает Site ops после слияния, skill `deploy-api`).
- `docs/site/forms.md`, `site/forms/28.json`, `todo/forms-batch-switch.md`.
- Цены, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Ветка `material_mode` (`isMaterialCustomer` / `noMaterial`): в `laser.py` по-прежнему не применяется. Включать её нельзя в этой задаче: `badge.py` передаёт `noMaterial` и ждёт текущую цену.
- `calcPrintLaser` и вес листовой лазерной печати. Остальные формы эпика.
- Удаление копии и черновика.

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcLaser` — в блоке `calcLaser` единственный пропуск `call calcManualRoll`, он есть в `scripts/js_port_gaps_allowed.txt` (`calcLaser call calcManualRoll`).
- [x] Локальный Python и раннер: номерки price 5631 / `time_ready` 19.05; простая резка AcrylWhite3 23638 / 27.17; «без резки» 1404 / 16.2. Дефолт формы 28 (пустой материал): cost 300, price 480, `time_ready` 16.2, `weight_kg` 0, `materials` пустой. Допуск цены abs ≤ 0.02 и rel ≤ 0.001, срока rel ≤ 0.001. Боевой `POST` дефолта до `deploy-api` — HTTP 400; копию на этом API не принимать.
- [x] `python -m pytest calc_service/tests/test_calculators/test_laser.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, 15.11.2026`. Тесты пустого материала и «без резки» на старом `laser.py` падают.
- [x] `Select-String -Path wp-plugin\forms\laser.js -Pattern "calcApi\('laser'|syncUrl\(|showResult\("` — все три вхождения есть.
- [ ] Копия не на витрине — Site ops после слияния и `deploy-api`: `wp post get PRODUCT --field=post_status` — `draft` или `private`; `curl.exe` без cookies на `/?post_type=product&p=PRODUCT` — `404`.
- [ ] На копии под админом эталон даёт `POST /api/v1/calc/laser` → 200 уже с выкатанным `laser.py`. Цена на странице равна `price` API с округлением `showResult`. Дефолт — 480, не 400.
- [ ] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0 (calc_service 605 passed, bot_service 81 passed)
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только после Reviewer, слияния в `main` и `deploy-api`. Боевая страница клиентам не меняется. Копию на старом боевом API не принимать: дефолт там 400, не 480.
- Цены: JSON не править. Эталоны номерков и простой резки не сдвигать.
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

```text
Блокер: дефолт боевой формы 28 (пустой материал) и опция «без резки» не сходятся с POST /api/v1/calc/laser. Форму не дублировать, laser.js не писать.
Пробовал: js_port_gaps calcLaser — единственный пропуск «call calcManualRoll», он уже в js_port_gaps_allowed.txt. pytest test_laser.py — 3 passed. Раннер и страница: эталон номерков (50 шт., 40×80, AcrylColor3, isGrave 1, isGraveFill [30,40], isCutLaser с нулями) price 5631, time_ready 19.05 — совпал с локальным Python и с POST https://insain.ru/api/v1/calc/laser. Простая резка 100 шт. 50×50 AcrylWhite3 (difficulty 1, sizeItem 50, density 25) — JS и API price 23638, time_ready 27.17. Дефолт страницы: материал «не задан» (data-value пустой), простая резка, режим 1. calcLaser на странице: cost 300, price 480, time 0.2, time_ready 16.2, weight NaN; раннер падает на NaN веса. POST того же тела — HTTP 400 «параметр material_id обязателен». Опция «без резки» (isCutLaser нет, AcrylWhite3): JS price 1404, time_ready 16.2; API price 2596, time_ready 16.67 (rel цены ≈ 0.849, rel срока ≈ 0.029). docs/site/forms.md: форма 28 на старом JS, slug laser ни к одной боевой форме API не привязан.
Гипотеза: порт считает material_id обязательным и при отсутствии is_cut_laser всё равно режет периметр. JS при пустом материале берёт только время подготовки, при «без резки» считает площадь листа без раскладки и без времени реза. Это расхождение не-боевого калькулятора (workflow: чинить в текущей ветке) и одновременно запрет задачи править laser.py (предпосылка port-fix-prerequisite).
Вопрос: чинить порт в task/form-laser или выносить предпосылку и не дублировать форму.
Следующая сессия: человек (AskQuestion), затем Implementer, модель Grok 4.7, либо Analyst, если выбрана предпосылка.
Снято 15.11.2026 (вариант 1): человек расширил scope `form-laser` на правку `laser.py`.
```

## Найдено вне scope

- `material_mode` (`isMaterial` / `noMaterial` / `isMaterialCustomer`, поле 1027) форма шлёт в API, `laser.py` его не применяет. Не чинить здесь: `badge.py` при печати передаёт `noMaterial` и тесты бейджа держат текущую цену.

## Результат

- Ветка, PR или коммит: `task/form-laser`, коммита нет.
- Сделано: `laser.py` — пустой `material_id` не даёт 400 (cost 300, price 480, `time_ready` 16.2, `weight_kg` 0, `materials` []); нет `is_cut_laser` — площадь первого листа без времени реза (AcrylWhite3 cost 857, price 1404, `time_ready` 16.2). Пустой `{}` по-прежнему режет. `uv_badge.py` передаёт `is_cut_laser: {}`. `wp-plugin/forms/laser.js` на id формы 28. Эталоны и строка раннера записаны. `material_mode` не трогал.
- Чем проверено: раннер `calcLaser` 15.11.2026 — номерки 5631 / 19.05, простая резка 23638 / 27.17, «без резки» 1404 / 16.2. Дефолт формы раннер не печатает (`weight` NaN); числа 300 / 480 / 16.2 — со страницы, локальный Python их повторяет. `python scripts/js_port_gaps.py calcLaser` — пропуск только `call calcManualRoll` (есть в допусках). `python -m pytest` laser + uv_badge + badge + tablets + acrylic_prizes + test_wp_plugin_forms — `49 passed`. На `laser.py` из HEAD те же новые тесты: `3 failed` (ValueError на пустом материале, cost «без резки» 1596 ≠ 857). `python scripts/dev.py check` — код 0, calc_service `605 passed`, bot_service `81 passed`.
- Не сделано и почему: дубль формы, GET на копии, `deploy-api`. Боевой API ещё без этой правки `laser.py` (дефолт 400). Копию до выкатки не проверять.
- Требуется решение: нет, маршрут смешанной цепочки. `Reviewer: Auto` и правка Python: сначала Reviewer по diff `task/form-laser`. После `принято` — человек сливает в `main` и ставит `выкатка`, Site ops делает `deploy-api`, затем дубль формы 28 на уже обновлённом боевом API. Site ops до выкатки не идёт: на текущем проде дефолт не сойдётся.
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока та задача `в работе`): нет, копия не делалась.
