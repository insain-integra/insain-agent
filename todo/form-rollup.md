# form-rollup

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: режим прод и два контура — `wp-plugin/forms/rollup.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 49 CalcRollup на черновике товара считает `POST /api/v1/calc/rollup`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 49 на странице https://insain.ru/catalog/kalkulyator-rollapov/ по-прежнему на `insaincalc.calcRollup`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 49, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, после `form-acrylic-prizes` (закрыто 2026-11-08, `docs/history/log.md`).
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcRollup`.
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_rollup.py` — тираж 1, `Rollup_econom_85`, `BannerFronlitCoat400`, mode 1. Порог `price` — прогон JS против API, не число из файла. Другого эталона в файле нет, тираж ≥ 2 не добавлять. JS: `js_legacy/calc/calcRollup.js`, сигнатура `calcRollup(n, rollupID, materialID, options, modeProduction)`.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- JS и API сошлись — переснять эталон в `test_rollup.py` с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert — `rel=0.001`. Не сошлись — файл не трогать. Новый кейс не добавлять.
- `wp-plugin/forms/rollup.js`: id элементов боевой формы 49, `insaincalc.syncUrl`, `insaincalc.calcApi('rollup'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон тиража 1, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-rollup` от `main`.

Распределение: сверку эталона, `test_rollup.py`, `wp-plugin/forms/rollup.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/rollup.js`
- `calc_service/tests/test_calculators/test_rollup.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 49. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/49.json`.
- Правка `calc_service/calculators/rollup.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Новый эталон с тиражом ≥ 2.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [ ] Порт. В блоке `calcRollup` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcRollup
```

- [ ] Раннер на входе эталона (тираж 1) печатает `price`. Команда — из `docs/js-runner-cases.md` для `calcRollup`. 404 API или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcRollup --data current --args '<args из docs/js-runner-cases.md>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/rollup -ContentType 'application/json' -Body '{"quantity":1,"rollup_id":"Rollup_econom_85","material_id":"BannerFronlitCoat400","mode":1}' | Select-Object price
```

- [ ] `price` раннера и API: абсолютная разница ≤ 0.02 и относительная ≤ 0.001. Подставить оба числа. Stdout начинается с `ok`.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
js = JS_PRICE
api = API_PRICE
abs_d = abs(js - api)
rel = abs_d / max(abs(api), 1e-9)
assert abs_d <= 0.02 and rel <= 0.001, (js, api, abs_d, rel)
print("ok", js, api, abs_d, rel)
'@ | python -
```

- [ ] Эталон в `test_rollup.py` переснят с этого прогона: комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_rollup.py -q
```

- [ ] Файл формы. В выводе есть `insaincalc.calcApi('rollup'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\rollup.js -Pattern "calcApi\('rollup'|syncUrl\(|showResult\("
```

- [ ] Контракт всех `forms/*.js`. Stdout: `passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [ ] Копия не на витрине. Одна строка со статусом `draft` или `private`. HTTP без cookies — `404`.

```powershell
ssh insain-prod "sudo -u www-data wp post get PRODUCT --field=post_status --path=/var/www/insain.ru"
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=PRODUCT"
```

### Критерии перевода формы ezFC на API

- [ ] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/rollup` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [ ] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [ ] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 49 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека: не учтено
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Строка в «Состав пакета» `todo/forms-batch-switch.md` (id копии и товар — после принятия копии):

| 49 CalcRollup | `rollup` | /catalog/kalkulyator-rollapov/ | COPY / PRODUCT (draft) | todo/form-rollup.md |
