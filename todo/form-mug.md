# form-mug

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: режим прод и два контура — `wp-plugin/forms/mug.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 41 CalcMug на черновике товара считает `POST /api/v1/calc/mug`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 41 на странице https://insain.ru/catalog/kalkulyator-sublimaczionnoj-pechati-na-kruzhki/ по-прежнему на `insaincalc.calcMug`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 41, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, параллельно `todo/js-runner-forms.md`. Раннер для `calcMug` уже есть. На форму 26 не завязана.
- Эталон: `REF_PARAMS_10` в `calc_service/tests/test_calculators/test_mug.py`, пометка «JS, 01.11.2026». Вызов `calcMug(10, 'MugStandartWhite', {}, 1)`. Порог `price` — прогон JS против API. Файл `js_legacy/calc/calcMug.js` уже в `scripts/run_js_calc.mjs`.
- Кружка зовёт термопресс с `transfer_type=sublimation`. Строки `calcHeatPress` в `scripts/js_port_gaps_allowed.txt` — плёнка, DTF, сабельный резак.
- Остальное не открывать.

## Scope

- Сверка эталона со старым JS командой ниже. Новый кейс в скрипт не добавлять. `calc_service/data/` не менять.
- JS и API сошлись и цена совпала с уже помеченным эталоном «JS, 01.11.2026» — `test_mug.py` не переписывать. Сошлась с API и не совпала с файлом — переснять эталон и сменить дату пометки. Не сошлась с API — файл не трогать.
- `wp-plugin/forms/mug.js`: id элементов боевой формы 41, `insaincalc.syncUrl`, `insaincalc.calcApi('mug'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон 10 шт. `MugStandartWhite`, mode 1, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-mug` от `main`.

## Не-scope

- `read_file` и любое переключение боевой формы 41. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/41.json`.
- Правка `calc_service/calculators/mug.py`, `calc_service/calculators/heat_press.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`.
- Ветки термопресса кроме сублимации на кружку (плёнка, DTF, сабельный резак).
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [ ] Порт. В блоке `calcMug` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`. Дыры в блоке `calcHeatPress` этой проверкой не чинятся.

```powershell
python scripts/js_port_gaps.py calcMug
```

- [ ] Раннер на входе эталона печатает `price`. 404 API или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcMug --data current --args '[10,\"MugStandartWhite\",{},1]'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/mug -ContentType 'application/json' -Body '{"quantity":10,"mug_id":"MugStandartWhite","is_packing":false,"mode":1}' | Select-Object price
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

- [ ] Если цена JS совпала с эталоном «JS, 01.11.2026», `test_mug.py` не переписан. Если совпала с API и не совпала с файлом — эталон переснят, пометка `JS, ДД.ММ.ГГГГ` этой даты, `price` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_mug.py -q
```

- [ ] Файл формы. В выводе есть `insaincalc.calcApi('mug'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\mug.js -Pattern "calcApi\('mug'|syncUrl\(|showResult\("
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

- [ ] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/mug` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [ ] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [ ] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 41 не менять. В админке пишется только копия.

## Режим

прод

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

| 41 CalcMug | `mug` | /catalog/kalkulyator-sublimaczionnoj-pechati-na-kruzhki/ | COPY / PRODUCT (draft) | todo/form-mug.md |
