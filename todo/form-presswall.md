# form-presswall

Статус: заблокировано: ждёт todo/presswall-banner-options.md
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: режим прод и два контура — `wp-plugin/forms/presswall.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 46 CalcPresswall на черновике товара считает `POST /api/v1/calc/presswall`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 46 на странице https://insain.ru/catalog/kalkulyator-pressvolov/ по-прежнему на `insaincalc.calcPresswall`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 46, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, после `todo/form-rollup.md`.
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcPresswall`.
- Эталон: кейсы с креплением в `calc_service/tests/test_calculators/test_presswall.py` от `todo/presswall-banner-options.md` — тираж 1, `Joker30_20_eyelet`, `BannerFronlitCoat400`, каркас да, аренда 0; люверсы `is_eyelet [300,300,300,300]` (mode 1 и 2), карман `is_pocket [1,0,1,0]` + `is_cutting [0,1,0,1]`, люверсы с чехлом `bag160`. `REF_PARAMS` без крепления на форме недостижим (dpdAttachment всегда даёт одну из опций) — для сверки формы не годится. Порог `price` — прогон JS против API, не число из файла. Тираж ≥ 2 не добавлять. JS: `js_legacy/calc/calcPresswall.js`, сигнатура `calcPresswall(n, presswallID, materialID, options, modeProduction)`.
- Форма 46, cjsCalc 1862: dpdAttachment = люверсы — `options.isEyelet = [300,300,300,300]`; карман — `isPocket = [1,0,1,0]` и `isCutting = [0,1,0,1]`.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- Сверка JS и API — на кейсе дефолта формы 46 (значения полей при открытии страницы, крепление из dpdAttachment). Совпал с кейсом `presswall-banner-options` — `test_presswall.py` не трогать. Не совпал — один кейс дефолта с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert: `cost`, `price`, `time_ready` — `rel=0.001`, `weight_kg` — `abs=0.02` (`print_roll` отдаёт вес баннера, округлённый до 0.01: раннер 9.79, API 9.78). Не сошлись — файл не трогать.
- `wp-plugin/forms/presswall.js`: id элементов боевой формы 46, `insaincalc.syncUrl`, `insaincalc.calcApi('presswall'`, `insaincalc.showResult`. Крепление в `calcApi`: dpdAttachment люверсы — `is_eyelet: [300,300,300,300]`; карман — `is_pocket: [1,0,1,0]` и `is_cutting: [0,1,0,1]`, как cjsCalc 1862. Чехол dpdBag — `is_bag`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон тиража 1, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-presswall` от `main`.

Распределение: сверку эталона, `test_presswall.py`, `wp-plugin/forms/presswall.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/presswall.js`
- `calc_service/tests/test_calculators/test_presswall.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 46. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/46.json`.
- Правка `calc_service/calculators/presswall.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Новый эталон с тиражом ≥ 2.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [ ] Порт. В блоке `calcPresswall` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcPresswall
```

- [ ] Раннер на кейсе дефолта формы 46 (тираж 1, с креплением) печатает `price`. Ниже — образец на люверсах, mode 1 (08.11.2026: 13914.624); поля подставить из дефолта формы, команды других кейсов — `docs/js-runner-cases.md`. 404 API, API без `is_eyelet` в `tool_schema` или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300]},1]'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/presswall -ContentType 'application/json' -Body '{"quantity":1,"presswall_id":"Joker30_20_eyelet","material_id":"BannerFronlitCoat400","is_presswall":true,"is_rent":0,"is_eyelet":[300,300,300,300],"mode":1}' | Select-Object price, time_ready
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

- [ ] Эталон дефолта формы в `test_presswall.py` — кейс с креплением: уже есть от `presswall-banner-options` или добавлен с этого прогона (комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом, `price` равен цене раннера). Допуск assert: `cost`, `price`, `time_ready` — `rel=0.001`, `weight_kg` — `abs=0.02`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_presswall.py -q
```

- [ ] Файл формы. В выводе есть `insaincalc.calcApi('presswall'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`, а также `is_eyelet`, `is_pocket`, `is_cutting` и `is_bag` — крепление и чехол уходят в `calcApi`.

```powershell
Select-String -Path wp-plugin\forms\presswall.js -Pattern "calcApi\('presswall'|syncUrl\(|showResult\(|is_eyelet|is_pocket|is_cutting|is_bag"
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

- [ ] На копии под админом (`https://insain.ru/?post_type=product&p=PRODUCT&preview=true`) эталон даёт `POST /api/v1/calc/presswall` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [ ] Люверсы и карман в dpdAttachment дают разные `price`, каждая равна раннеру на том же входе (rel ≤ 0.001).
- [ ] Смена каждого dropdown меняет цену и таблицу материалов. В таблице нет внутренних `code`. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [ ] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 46 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

08.11.2026 — Implementer, Opus 5.5 — стоп на сверке (skill verify, шаги 5а–5б): крепление баннера из формы 46 в API не уходит, файлы не менялись — дальше Analyst

```
Блокер: поле dpdAttachment (1845, «люверсы» / «карман») боевой формы 46 влияет на цену, а у POST /api/v1/calc/presswall параметра для него нет — форму на API не перевести без недооценки.
Пробовал: js_port_gaps calcPresswall — блок calcPresswall пуст (calcPrintRoll call calcLaminationWide есть в allowed); эталон REF_PARAMS: раннер price 11453.624, боевой API 11453.624, проверка abs/rel — ok. cjsCalc 1862 (SELECT): при dpdAttachment=isEyelet ставит options isEyelet [300,300,300,300], при isPocket — isPocket [1,0,1,0] и isCutting [0,1,0,1]; у dropdown только эти две опции, т.е. одна из них всегда в options. calcPresswall передаёт options в calcPrintRoll баннера. Раннер, тираж 1, Joker30_20_eyelet, BannerFronlitCoat400, каркас: с люверсами price 13914.624 / time_ready 19.94; с карманом 12659.624 / 19.12; без крепления 11453.624 / 18.3. API на том же входе (лишний is_eyelet игнорируется) — 11453.624. tool_schema presswall: quantity, presswall_id, material_id, is_presswall, is_rent, is_bag, mode — крепления нет; presswall.py вызывает PrintRollCalculator без опций. Без баннера (material_id "") JS и API сходятся: 7006.624.
Гипотеза: порт calcPresswall потерял проброс options в calcPrintRoll; js_port_gaps его не видит, потому что смотрит только options.has() самой функции. REF_PARAMS (баннер без крепления) на форме недостижим.
Вопрос: завести задачу-предпосылку по skill port-fix-prerequisite — параметр крепления (люверсы / карман) в presswall API с пробросом в print_roll, эталоны раннера на обоих вариантах; эту задачу — `заблокировано: ждёт todo/<предпосылка>.md`, эталон в test_presswall.py переснять на кейсе с креплением.
Следующая сессия: Analyst, модель Opus 5.5
```

08.11.2026 — Analyst, Opus 5.5 — задача-предпосылка `todo/presswall-banner-options.md` (крепление, плюс найденные раннером люверсы `calc_eyelet`, режим баннера, чехол); эталон — кейс с креплением, `forms/presswall.js` передаёт крепление и чехол, допуск веса `abs=0.02` — дальше человек: после закрытия предпосылки `черновик`, Implementer — `git rebase main`

## Найдено вне scope

- `weight_kg` presswall на эталоне: раннер 9.79, Python и боевой API 9.78 (rel 0.00102) — presswall.py суммирует вес баннера, уже округлённый print_roll до 0.01. Учтено: допуск `abs=0.02` в assert веса.
## Результат

- Ветка, PR или коммит: `task/form-presswall` (от `main` 56a618e), без коммитов; изменён только этот файл
- Период: 08.11.2026
- Часы человека: не учтено
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему: эталон в `test_presswall.py` и `wp-plugin/forms/presswall.js` — стоп на сверке, блокер в «Журнал передач». Поля формы 46 для будущего `forms/presswall.js`: numN 1843, dpdPresswall 1844, dpdAttachment 1845, dpdBanner 1879, dpdBag 1880, numDays 1882, rdoPresswal 1883 (isPresswall / isRent / noPresswall — «свой прессвол» в API: is_presswall=false, is_rent=0), rdoModeProduction 1875, cjsCalc 1862.
- Требуется решение: нет — ждёт `todo/presswall-banner-options.md`.
- Строка в «Состав пакета» `todo/forms-batch-switch.md` (id копии и товар — после принятия копии):

| 46 CalcPresswall | `presswall` | /catalog/kalkulyator-pressvolov/ | COPY / PRODUCT (draft) | todo/form-presswall.md |
