# form-acrylic-prizes

Статус: заблокировано: ждёт todo/uv-print-prepare.md
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: режим прод и два контура — `wp-plugin/forms/acrylic_prizes.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 78 CalcAcrilycPrizes на черновике товара считает `POST /api/v1/calc/acrylic_prizes`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 78 на странице https://insain.ru/catalog/kalkulyator-akrilovyh-prizov/ по-прежнему на `insaincalc.calcAcrilycPrizes`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 78, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, после `form-embossing` (закрыто 2026-11-07, `docs/history/log.md`).
- `docs/js-runner-cases.md` — команда раннера и `price` для `calcAcrilycPrizes`.
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_acrylic_prizes.py` — 10 шт., два слоя PVC3 100×100, у верхнего рез лазером и УФ 80×80, mode 1. Порог `price` — прогон JS против API, не число из файла. JS: `js_legacy/calc/calcAcrilycPrizes.js`, сигнатура `calcAcrilycPrizes(n, layers, options, modeProduction)`.
- В вызов УФ у эталона не входят штрихкод, переменные данные и материал заказчика.
- На эталоне `materials` должен быть непустым. Пустой ответ — стоп, `acrylic_prizes.py` не дописывать.
- Остальное не открывать.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` и калькулятор не менять.
- JS и API сошлись — переснять эталон в `test_acrylic_prizes.py` с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert — `rel=0.001`. Не сошлись — файл не трогать. Новый кейс — только один: дефолт формы 78 (100 шт., 2× AcrylTrans3 20×20, рез лазером и УФ на обоих слоях, mode 1), эталон с раннера, та же пометка. Эталон с одним УФ не ловит второй вызов УФ в mode 0.
- До дубля снять поля формы 78. Отдельное поле штрихкода, переменных данных или материала заказчика, от которого старый JS меняет цену, — стоп: в калькулятор этой задачи их не дописывать.
- `wp-plugin/forms/acrylic_prizes.js`: id элементов боевой формы 78, `insaincalc.syncUrl`, `insaincalc.calcApi('acrylic_prizes'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-acrylic-prizes` от `main`.

Распределение: сверку эталона, `test_acrylic_prizes.py`, `wp-plugin/forms/acrylic_prizes.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Снятие полей формы 78, дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `wp-plugin/forms/acrylic_prizes.js`
- `calc_service/tests/test_calculators/test_acrylic_prizes.py`
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета»
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 78. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/78.json`.
- Правка `calc_service/calculators/acrylic_prizes.py`, `uv_print.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcAcrilycPrizes` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcAcrilycPrizes
```

- [x] Раннер на входе эталона печатает `price`. Команда — из `docs/js-runner-cases.md` для `calcAcrilycPrizes`. 404 API или расхождение — стоп, форму не дублировать. Калькулятор и `calc_service/data/` не править.

```powershell
node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '<args из docs/js-runner-cases.md>'
$api = Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/acrylic_prizes -ContentType 'application/json' -Body '{"quantity":10,"layers":[{"materialID":"PVC3","size":[100,100],"isTop":false,"options":{}},{"materialID":"PVC3","size":[100,100],"isTop":true,"options":{"isCutLaser":{},"isUVPrint":{"size":[80,80]}}}],"mode":1}'
$api | Select-Object price
$api.materials.Count
```

- [x] `price` раннера и API: абсолютная разница ≤ 0.02 и относительная ≤ 0.001. Подставить оба числа. Stdout начинается с `ok`. На этом же ответе API `materials` не пустой. Пустой список — стоп, `acrylic_prizes.py` не дописывать.

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

- [x] Эталон в `test_acrylic_prizes.py` переснят с этого прогона: комментарий `# JS, ДД.ММ.ГГГГ` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Расхождение JS и Python — стоп, файл не менять.

```powershell
python -m pytest calc_service/tests/test_calculators/test_acrylic_prizes.py -q
```

- [ ] Дефолт формы 78 (УФ на двух слоях): `price` раннера `calcAcrilycPrizes` и боевого `POST /api/v1/calc/acrylic_prizes` — разница ≤ 0.02 и `rel ≤ 0.001` (тот же скрипт, что выше). Кейс дефолта в `test_acrylic_prizes.py`, stdout `passed`. Только после выкатки `todo/uv-print-prepare.md`; до неё было JS 8977.92 / API 9559.92. Приёмка копии 91 — после этого пункта.

- [x] Файл формы. В выводе есть `insaincalc.calcApi('acrylic_prizes'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\acrylic_prizes.js -Pattern "calcApi\('acrylic_prizes'|syncUrl\(|showResult\("
```

- [x] Контракт всех `forms/*.js`. Stdout: `passed`.

```powershell
python -m pytest calc_service/tests/test_wp_plugin_forms.py -q
```

- [x] Копия не на витрине. Одна строка со статусом `draft` или `private`. HTTP без cookies — `404`.

```powershell
ssh insain-prod "sudo -u www-data wp post get 2586884 --field=post_status --path=/var/www/insain.ru"
curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=2586884"
```

### Критерии перевода формы ezFC на API

- [x] На копии под админом (`https://insain.ru/?post_type=product&p=2586884&preview=true`) эталон даёт `POST /api/v1/calc/acrylic_prizes` → 200, в теле коды материалов, не `0`. Цена на странице равна `price` API с округлением `showResult`. В «Результат» — код ответа и обе цены.
- [x] На эталоне в ответе API `materials` не пустой: на странице есть `name` или `title`, внутреннего `code` нет. Смена каждого dropdown меняет цену и эту таблицу. Пустой `materials` — стоп и эскалация. `acrylic_prizes.py` в этой задаче не дописывать. Есть вес и срок с подсказкой дат. Перезагрузка не меняет режим и срок.
- [x] URL обновляется GET-именами формы (имя параметра = имя элемента). Ссылка с этими GET открывает копию с теми же значениями и той же ценой. У dropdown с кодом в `data-value` — `GET_check=index`. У radio со значениями `1`/`2` — `GET_check=value`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Расхождение JS и Python (локальный расчёт и боевой API, rel > 0.001) — стоп и эскалация, калькулятор не править.
- Формы: id элементов боевой формы 78 не менять. В админке пишется только копия. Поля штрихкода, переменных данных или материала заказчика на форме — стоп.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

- 2026-11-07 — Implementer, Opus 5.5 — шаги 0–5б + `wp-plugin/forms/acrylic_prizes.js`, эталон переснят, `python scripts/dev.py check` зелёный; статус `в работе` — дальше Site ops (дубль после «да» человека)
- 2026-11-07 — Site ops, Opus 5.5 — шаги 6–16: копия **91** / товар **2586884** (draft, гость 404); JS копии + GET; прогон AcrylTrans3 API `price=4344.72` / страница `4400`; боевую 78 не трогал; статус `ревью` — дальше человек (приёмка копии), затем Reviewer
- 2026-11-07 — Site ops, Opus 5.5 — человек: копия не принята (боевая ≠ копия). Диагностика: дефолт формы (100 шт, 2× AcrylTrans3 20×20, УФ на обоих слоях) — боевая/JS `price=8977.92`→9000, API/копия `9559.92`→9600; `d_cost≈365` стабильно при УФ на двух слоях, при УФ только на верхнем — совпадение. Эталон PVC3 и AcrylTrans3 с одним УФ — 0. Статус `заблокировано: исполнитель` — дальше Implementer (сверка `acrylic_prizes` / УФ на не-top слое; форму/JSON в этой задаче не править по AGENTS)
- 2026-11-07 — Implementer, Opus 5.5 — сверка дефолта формы: расхождение не в маппинге формы и не в `isTop`. Блокер Analyst. Копию 91 / плагин не трогал.

```
Блокер: на дефолте формы (УФ на двух слоях) JS≠API; критерий «копия = боевая» и сдача формы на API невыполнимы, пока второй УФ в economy даёт чужую цену. Править `uv_print` / `acrylic_prizes` в этой задаче нельзя (Не-scope).
Пробовал:
1) Раннер JS vs local/prod API, слои как форма (Stella top→Bazis base), qty=100, 2×AcrylTrans3 20×20, cut+UV оба, mode=1: JS cost/price 5599.45/8977.92; API 5963.45/9559.92 (Δcost=364, Δprice=582).
2) Матрица: noUV и один УФ (top или base) — JS=API 3867.45/6205.92 и 4915.45/7882.92; оба УФ — только API дороже. Порядок top-first / base-first на сумму не влияет.
3) Прямой `calcUVPrint` 100×[20,20]: JS mode1=1048/1677, mode0=684/1095; Python `UVPrintCalculator` mode0=mode1=1048/1677. Второй слой в `acrylic_prizes` как в JS сбрасывает mode_uv→0; Python УФ mode=0 не дешевеет из‑за `time_prepare *= max(1, mode.value)` в `uv_print.py:235` (JS: `timePrepare * modeProduction`, при 0 → 0).
Гипотеза: баг порта `uv_print` (economy), не формы и не порядка слоёв. Первый УФ mode=1 совпадает → эталон с одним УФ зелёный и маскирует дыру.
Вопрос: завести предпосылку (починить `uv_print` mode=0 → как JS; тест mode0≠mode1 на 20×20) и поставить этой задаче `заблокировано: ждёт todo/<имя>.md`, или расширить scope `form-acrylic-prizes` на `uv_print.py` (+тест)? Копию 91 не трогать, пока JS=API на дефолте.
Следующая сессия: Analyst, модель из шапки / человек выбирает
```

- 2026-11-07 — Analyst, Opus 5.5 — блокер разобран: предпосылка `todo/uv-print-prepare.md` (mode 0 и `timePrepareAround` в `uv_print`, деплой API); здесь разрешён кейс дефолта формы и добавлен критерий JS = API на нём; статус `заблокировано: ждёт todo/uv-print-prepare.md` — дальше Implementer `uv-print-prepare`; после её закрытия — Implementer этой задачи (кейс дефолта), затем Site ops (перепрогон копии 91)

## Найдено вне scope

- `calc_service/calculators/uv_print.py`: `time_prepare *= max(1, mode.value)` (plain и non-plain) — при `mode=0` готовит как mode=1; JS `calcUVPrint` умножает на `modeProduction` (0 → 0). Ломает второй УФ в `acrylic_prizes` после сброса `mode_uv`. Вынесено в `todo/uv-print-prepare.md`.
- В `acrylic_prizes.py` при гравировке читается `is_grave_fill`, а боевой cjsCalc/JS кладут `isGraveFill` — через API площадь заливки гравировки может не доходить до лазера. В эту задачу калькулятор не править.
- В dropdown формы 77 `dpdMaterial` нет кода `PVC3` (эталон git/API); на странице для проверки брать материал из списка формы и сверять цену с `POST` на тех же слоях.
- При дубле формы 78 создались две копии **90** и **91**; рабочая — **91**. Форма **90** лишняя, удаление — только с подтверждения человека.

## Результат

- Ветка: `task/form-acrylic-prizes` (калькулятор/`data`/копию 91 в этой сессии не менял)
- Сделано (Implementer, сверка блокера Site ops):
  - Подтверждены числа человека/Site ops: JS `8977.92`, API `9559.92` на дефолте (оба УФ)
  - Локализовано: не `isTop` и не маппинг `acrylic_prizes.js`; второй вызов УФ после `mode_uv=0` — JS `+684/+1095`, Python `+1048/+1677`
  - Корень: `uv_print.py` `max(1, mode.value)` vs JS `* modeProduction`
- Чем проверено: `run_js_calc.mjs calcAcrilycPrizes` / `calcUVPrint`; local `AcrylicPrizesCalculator` + `UVPrintCalculator`; `POST https://insain.ru/api/v1/calc/acrylic_prizes`
- Не сделано: правка `uv_print`/`acrylic_prizes` — Не-scope; приёмка копии 91 — пока JS≠API на дефолте; строка в `forms-batch-switch` — после принятия
- Решение Analyst (07.11.2026): отдельная todo `uv-print-prepare`, эта задача ждёт её закрытия
- Предыдущий отчёт Site ops (копия 91 / 2586884) без изменений
