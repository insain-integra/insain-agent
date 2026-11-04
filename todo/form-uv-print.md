# form-uv-print

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: режим прод и два контура — `wp-plugin/forms/uv_print.js` в git и WordPress (дубль, GET на копии, прогон под админом).
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 26 CalcUVPrint на черновике товара считает `POST /api/v1/calc/uv_print`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 26 на странице https://insain.ru/catalog/uf-pechat-na-suveniry/ по-прежнему на `insaincalc.calcUVPrint`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 26, только читать.
- `todo/forms-batch-switch.md` — в конце одна строка в «Состав пакета».
- `todo/EPIC-forms-to-api.md` — очередь, параллельно `todo/js-runner-forms.md`. Раннер для `calcUVPrint` уже есть.
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_uv_print.py` — 50 шт., 100×150, resolution 0, `4+0`, plain, mode 1. Порог `price` — прогон JS против API, не число из файла. Сигнатура JS: `calcUVPrint(n, size, sizeItem, materialID, options, modeProduction)` в `js_legacy/calc/calcUVPrint.js`. Файл уже в `scripts/run_js_calc.mjs`.
- Калькулятор материал каталога не применяет: ответ `materials` пустой. Таблицу на форме не требовать.
- Остальное не открывать.

## Scope

- Сверка эталона со старым JS: `node scripts/run_js_calc.mjs calcUVPrint --data current`. Позиционные аргументы собирает Implementer из `REF_PARAMS` по сигнатуре. Новый кейс в скрипт не добавлять. Если `--data current` не подменяет прайс, который читает эта функция, в список подмены можно дописать только этот JSON. `calc_service/data/` не менять.
- JS и API сошлись — переснять эталон в `test_uv_print.py` с пометкой `JS, ДД.ММ.ГГГГ`, как в `test_tablets.py`. Допуск assert — `rel=0.001`. Не сошлись — файл не трогать.
- До дубля снять поля формы 26 (SQL из skill, шаг 5). По решению человека: дописать `isBarcode`/`isVariables`/`isNumber` в Python. Материал заказчика в API — `is_customer_material`. Строка `calcUVPrint call calcLayoutOnSheet` в `scripts/js_port_gaps_allowed.txt` стопом не является: раскладка уже в `_layout_on_printer`.
- `wp-plugin/forms/uv_print.js`: id элементов боевой формы 26, `insaincalc.syncUrl`, `insaincalc.calcApi('uv_print'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-uv-print` от `main`.

## Не-scope

- `read_file` и любое переключение боевой формы 26. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/26.json`.
- Правка цен, `calc_service/data/` (кроме закрытия port-gaps строк после порта опций).
- Удаление копии и черновика.
- Формы 41, 85, 78, 49, 46, 73, 55 — свои задачи эпика.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcUVPrint` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [x] Раннер на входе эталона печатает `price`. JS и API сошлись.
- [x] `price` раннера и API: abs ≤ 0.02 и rel ≤ 0.001.
- [x] Эталон в `test_uv_print.py` переснят (`JS, 04.11.2026`, `rel=0.001`).
- [x] Файл формы: `calcApi('uv_print'`, `syncUrl(`, `showResult(`.
- [x] Контракт всех `forms/*.js`.
- [x] Копия не на витрине: draft + guest 404.
- [x] На копии под админом POST 200; цена = API с округлением showResult; dropdown меняет цену; materials пустой; вес/срок; GET-URL.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать.
- Формы: id элементов боевой формы 26 не менять. В админке пишется только копия.

## Режим

прод

## Результат

- Ветка, PR или коммит: `task/form-uv-print` → merge в `main` + деплой API (по запросу 04.11.2026)
- Период: 04.11.2026
- Часы человека: не учтено
- Работа агентов: Implementer (Opus 5.5)
- Было / стало: в Python дописаны `is_number`/`is_barcode`/`is_variables`; эталон JS `price=3888`; копия **87** на черновике **2586881** считает через `calcApi('uv_print')`
- Сделано:
  - сверка JS/API: `ok 3888 3888 0 0.0`; `materials=[]` (таблица на форме оставлена пустой)
  - опции в `uv_print.py` по формулам JS; `js_port_gaps_allowed.txt` — остался только `calcUVPrint call calcLayoutOnSheet`
  - `test_uv_print.py` — `# JS, 04.11.2026`, `rel=0.001`, тест опций
  - `wp-plugin/forms/uv_print.js` (id боевой 26)
  - дубль формы **87**; товар **2586881** draft; guest 404
  - GET на копии; custom JS копии с id 87
  - прогон: POST 200; смена цвета 4+0→4+1: API 5090→8519, страница 5100→8550; URL sync; GET-ссылка; срок с датами; materials tbody пуст
- Чем проверено:
  - `python scripts/js_port_gaps.py calcUVPrint` / `--check`
  - JS vs Python (base/number/barcode/variables/customer/all) — цены совпали
  - `python scripts/dev.py check` → exit 0 (499 passed, 2 skipped + bot)
  - `wp post get 2586881 --field=post_status` → draft; curl guest → 404
  - Browser MCP: https://insain.ru/?post_type=product&p=2586881&preview=true
- Не сделано и почему:
  - боевая 26 / `read_file` / деплой плагина — вне scope
  - строка в `forms-batch-switch.md` — ждёт принятия копии
  - UI `dpdResolution` только 1/2: эталон resolution=0 с формы недоступен (при индексе 0 уходит value=1 → 5090/5100); REF 3888 проверен JS+API
  - (закрыто) прод-API без опций — merge + deploy
- Требуется решение: —
- Строка в «Состав пакета»:

| 26 CalcUVPrint | `uv_print` | /catalog/uf-pechat-na-suveniry/ | 87 / 2586881 (draft) | todo/form-uv-print.md |
