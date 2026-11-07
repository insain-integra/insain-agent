# form-embossing

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: режим прод и два контура — `wp-plugin/forms/embossing.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 85 CalcEmbossing на черновике товара считает `POST /api/v1/calc/embossing`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 85 на странице https://insain.ru/catalog/kalkulyator-tisneniya/ по-прежнему на `insaincalc.calcEmbossing`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 85, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь; `js-runner-forms` закрыта 05.11.2026.
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcEmbossing`.
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_embossing.py` — 500 шт., клише 50×30, foil, diary, mode 1. Порог `price` — прогон JS против API, не число из файла. JS: `js_legacy/calc/calcEmbossing.js`, сигнатура `calcEmbossing(n, size, materialID, embossingID, itemID, sizeItem, options, modeProduction)`.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- JS и API сошлись — переснять эталон в `test_embossing.py` с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert — `rel=0.001`. Не сошлись — файл не трогать. Новый кейс не добавлять.
- `wp-plugin/forms/embossing.js`: id элементов боевой формы 85, `insaincalc.syncUrl`, `insaincalc.calcApi('embossing'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-embossing` от `main`.

Распределение: сверку эталона, `test_embossing.py`, `wp-plugin/forms/embossing.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/embossing.js`
- `calc_service/tests/test_calculators/test_embossing.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 85. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/85.json`.
- Правка `calc_service/calculators/embossing.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcEmbossing` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcEmbossing
```

- [x] Раннер на входе эталона печатает `price`. Команда — из `docs/js-runner-cases.md` для `calcEmbossing`. 404 API или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcEmbossing --data current --args '<args из docs/js-runner-cases.md>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/embossing -ContentType 'application/json' -Body '{"quantity":500,"cliche_width_mm":50,"cliche_height_mm":30,"embossing_type":"foil","item_type":"diary","is_cliche":true,"mode":1}' | Select-Object price
```

- [x] `price` раннера и API: абсолютная разница ≤ 0.02 и относительная ≤ 0.001. Подставить оба числа. Stdout начинается с `ok`.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
js = 14046.000000000002
api = 14046.000000000002
abs_d = abs(js - api)
rel = abs_d / max(abs(api), 1e-9)
assert abs_d <= 0.02 and rel <= 0.001, (js, api, abs_d, rel)
print("ok", js, api, abs_d, rel)
'@ | python -
```

- [x] Эталон в `test_embossing.py` переснят с этого прогона: комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_embossing.py -q
```

- [x] Файл формы. В выводе есть `insaincalc.calcApi('embossing'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\embossing.js -Pattern "calcApi\('embossing'|syncUrl\(|showResult\("
```

- [x] Контракт всех `forms/*.js`. Stdout: `passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [x] Копия не на витрине. Одна строка со статусом `draft` или `private`. HTTP без cookies — `404`.

```powershell
ssh insain-prod "sudo -u www-data wp post get 2586883 --field=post_status --path=/var/www/insain.ru"
# draft
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586883"
# 404
```

### Критерии перевода формы ezFC на API

- [x] На копии под админом (`https://insain.ru/?post_type=product&p=2586883&preview=true`) эталон даёт `POST /api/v1/calc/embossing` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
  - Тело: `quantity=500, cliche 50×30, foil, diary, is_cliche=true, mode=1` → 200; страница `14 050` (API 14046, округление `showResult`).
- [x] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
  - foil→blind: 14050→12400; материалы «Клише 50,30»; срок с `data-bs-original-title`; reload `rdoModeProduction=2` → mode 2, цена 14650.
- [x] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.
  - GET: `numN,numW,numH,numItemW,numItemH,dpdEmbossing,dpdPreset,dpdSurfaceMaterial,ckbCliche,ckbPacking,ckbMaterialCustomer,rdoModeProduction`; режим `GET_check=value`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 85 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

- 07.11.2026 — Implementer, Opus 5.5 — сверка JS=API price 14046, `embossing.js` + эталон `test_embossing.py` (rel=0.001), `make check` зелёный; дубль не делал (ждёт «да») — дальше Reviewer (код); после «да» — Site ops (дубль/GET/прогон копии)
- 07.11.2026 — Site ops, Opus 5.5 — копия 89 / draft 2586883, JS+GET на копии, прогон эталона под админом (POST 200, цена 14050); боевую 85 не трогал — дальше Reviewer (Grok 4.7); после принятия копии человеком — строка в `forms-batch-switch`
- 07.11.2026 — человек — копия 89 / 2586883 принята; строка в `forms-batch-switch` — дальше Reviewer (Grok 4.7), затем merge
- 07.11.2026 — Reviewer, Grok 4.7 — принято — дальше человек: коммит и слияние

## Найдено вне scope

- Старый cjsCalc формы 85 читает `ckbMaterialCustomer` с id 3291 (`ckbCliche`), а не 3311 — баг боевого JS; в `embossing.js` исправлено на 3311.
- `dpdSurfaceMaterial`, `ckbPacking`, `ckbMaterialCustomer` есть на форме, в API `embossing` не входят (как `materialID` в старом `calcEmbossing` не используется); в `syncUrl` пишутся, в `calcApi` не уходят.
- У `rdoModeProduction` формы 85 только значения `1`/`2` (опции «дешевле»/0 нет).

## Результат

- Ветка, PR или коммит: `task/form-embossing` (коммит после Ревью 1)
- Период: 07.11.2026
- Часы человека: не учтено
- Работа агентов: Implementer + Site ops (Opus 5.5)
- Было / стало: формы `embossing.js` не было → `calcApi`+`syncUrl`+`showResult` с id боевой 85; эталон `rel=0.001`; на WP — копия 89 на draft 2586883
- Сделано:
  - git: `wp-plugin/forms/embossing.js`, эталон `test_embossing.py`, `make check` зелёный
  - WP: форма **89** `CalcEmbossing duplicate`, товар **2586883** `draft`, `ezfc_form_id=89`, гость 404
  - на копии: custom JS с id 89 (`cjsCalc` 3417), GET = имена, dropdown `GET_check=index`, `rdoModeProduction` `GET_check=value`, `read_file=0`
  - блок результата уже как у 79 (htmCost «со скидкой», htmTime с `<a>`, htmMaterial table)
  - боевая 85 / https://insain.ru/catalog/kalkulyator-tisneniya/ — по-прежнему `insaincalc.calcEmbossing`
- Чем проверено:
  - `wp post get 2586883` → `draft`; curl гость → `404`
  - под админом эталон: `POST /api/v1/calc/embossing` 200, body foil/50×30/diary; цена страницы `14 050` (API 14046)
  - foil→blind меняет цену 14050→12400; материалы без `code`; срок с датами; mode=2 → URL `rdoModeProduction=2`, цена 14650; reload сохраняет режим
  - live-страница: `calcEmbossing`, не `calcApi('embossing'`
- Не сделано и почему: merge в `main` — по просьбе человека; выкладка плагина и `read_file` боевой 85 — не-scope (`forms-batch-switch`)
- Требуется решение: слияние `task/form-embossing` → `main`?
- Откат копии: удалить форму 89 и товар 2586883 (только с подтверждения); боевая не менялась
- Строка в «Состав пакета» `todo/forms-batch-switch.md`:

| 85 CalcEmbossing | `embossing` | /catalog/kalkulyator-tisneniya/ | 89 / 2586883 (draft) | копия принята 07.11.2026, todo/form-embossing.md |

## Ревью 1

принято. Статус остаётся `ревью`. Дальше человек: коммит рабочего дерева и слияние в `main`. Выкладка плагина и `read_file` боевой формы 85 в эту задачу не входят.

Повторно 07.11.2026:

- Порт: `python scripts/js_port_gaps.py calcEmbossing` — в блоке `calcEmbossing` строка `нет в Python:` пустая.
- Раннер и боевой API: оба `price` = 14046.000000000002, абсолютная разница 0.
- Эталон в `test_embossing.py`: `# JS, 07.11.2026`, команда раннера из `docs/js-runner-cases.md`, `EXPECTED_REF["price"]` = 14046.0, допуск assert `rel=0.001`. `calculators/embossing.py` и `calc_service/data/` не менялись.
- `wp-plugin/forms/embossing.js`: есть `calcApi('embossing'`, `syncUrl(`, `showResult(`. Id — боевая форма 85 (cjsCalc 3294, dpdEmbossing 3280, dpdPreset 3279, dpdSurfaceMaterial 3287, rdoModeProduction 3307, ckbCliche 3291, ckbPacking 3292, ckbMaterialCustomer 3311). Своих формул цены и чтения через DOM нет.
- `python scripts/dev.py check` — код выхода 0: calc_service 510 passed, 2 skipped; bot_service 81 passed. В том числе `test_embossing.py` и `test_wp_plugin_forms.py`.
- Копия не на витрине: товар 2586883 `draft`, гость `404`, `ezfc_form_id=89`. Форма 89, элемент 3417: `read_file=0`, `calcApi('embossing'`, id копии (3408, 3405, 3430, 3414). GET = имя элемента. У dropdown `GET_check_option_value=index`, у `rdoModeProduction` = `value`.
- Боевая 85: `read_file=0`, cjsCalc 3294 по-прежнему `calcEmbossing`, GET-имена пустые, у режима `GET_check_option_value` остался `index`. На https://insain.ru/catalog/kalkulyator-tisneniya/ в HTML есть `calcEmbossing`, вызова `calcApi('embossing'` нет.
- Цена страницы `14 050` сходится с `insaincalc.round(14046, 500)` = 14050. Смена foil→blind (14050→12400), mode 2 (14650) и reload — по отчёту Site ops; копию принял человек.
- Строка 85 CalcEmbossing есть в «Состав пакета» `todo/forms-batch-switch.md`.
- `docs/dashboard.md` — статус `ревью` для `test_dashboard_file_matches_render`. Калькулятор, цены и боевая форма не затронуты.

Блокеров нет. В коммит: `wp-plugin/forms/embossing.js`, `test_embossing.py`, `todo/forms-batch-switch.md`, `todo/form-embossing.md`, `docs/dashboard.md`.
