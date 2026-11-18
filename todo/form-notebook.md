# form-notebook

Статус: черновик
Сложность: низкая
Implementer: Grok 4.7
Reviewer: не нужен
Site ops: Grok 4.7
Почему: калькулятор `notebook` уже в API, пропусков `calcNotebook` в `js_port_gaps_allowed.txt` нет; копия формы по skill `ezfc-form-to-api`.

## Цель

Копия формы 45 CalcNotebook на черновике товара считает `POST /api/v1/calc/notebook`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-bloknotov/ остаётся на `insaincalc.calcNotebook`. В пакет `forms-batch-switch` форма 45 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента.
- `docs/site/forms.md` — строка формы 45, только читать.
- `calc_service/calculators/notebook.py`, `calc_service/tests/test_calculators/test_notebook.py`.
- `todo/EPIC-forms-to-api.md` — пачка 4.
- Остальное не открывать.

## Scope

- В git (Implementer): шаги 0–5б и `wp-plugin/forms/notebook.js`. `REF_FORM_DEFAULT` в `test_notebook.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- Калькулятор не на боевой форме API. Расхождение дефолта чинить в `notebook.py`, не в `print_sheet.py` и не в `print_offset.py`. Если без их правки дефолт не сходится — стоп, `заблокировано: аналитик`.
- На проде (Site ops): дубль формы 45 на черновик после совпадения дефолта с боевым API. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 45 не переключать.
- Строка для будущего пакета — в «Результат», не в `todo/forms-batch-switch.md`.

## Файлы

- `wp-plugin/forms/notebook.js`
- `calc_service/calculators/notebook.py`
- `calc_service/tests/test_calculators/test_notebook.py`
- WordPress: только копия формы 45 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`, новые строки в `scripts/js_port_gaps_allowed.txt`
- `print_sheet.py`, `print_offset.py`, их тесты и `wp-plugin/forms/print_sheet.js`, `print_offset.js`
- Боевая форма 45, выкладка плагина, JSON цен, `calc_service/calculators/__init__.py`

## Критерии приёмки

- [x] `python scripts/js_port_gaps.py calcNotebook` — в блоке `calcNotebook` строка `нет в Python` пустая, либо каждый пропуск уже есть и в docstring, и в `scripts/js_port_gaps_allowed.txt`.
- [x] `python -m pytest calc_service/tests/test_calculators/test_notebook.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Есть `REF_FORM_DEFAULT` с `# JS,`.
- [x] Боевой `POST /api/v1/calc/notebook` на теле `REF_FORM_DEFAULT`: `price` 16062, `time_ready` 22.61 (после выкатки `cc68867`). `REF_PARAMS`: `price` 20800, `time_ready` 58.15.
- [x] `Select-String -Path wp-plugin\forms\notebook.js -Pattern "calcApi\('notebook'|syncUrl\(|showResult\("` — все три есть. Своей `price` и `querySelector` нет.
- [x] Копия не на витрине: товар 2586897 `draft`, гость без cookies — `404`.
- [x] На копии под админом дефолт даёт `POST /api/v1/calc/notebook` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] URL копии обновляется GET-именами формы 45. Ссылка с этими GET открывает те же значения и ту же цену.
- [x] Боевая страница в HTML содержит `calcNotebook`, не `calcApi`.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: боевая форма 45 не меняется. Запись в формы не параллельно с `todo/ezfc-options-source-reset.md`.
- Цены: JSON не менять. Чужие калькуляторы печати не двигать.
- Формы: id боевой 45 не менять.

## Режим

прод

## Журнал передач

19.11.2026 — Analyst, Grok 4.7 — задача заведена, пачка 4 — дальше Implementer

19.11.2026 — Implementer, Grok 4.7 — шаги 0–5б и `wp-plugin/forms/notebook.js` в ветке, без коммита. Локальный дефолт совпал с JS страницы, боевой API ещё старый — дальше человек

Блокер: копию формы 45 нельзя ставить, пока боевой `POST /api/v1/calc/notebook` на `REF_FORM_DEFAULT` не совпадёт с JS. Сейчас бой `price` 11869, JS 16061.69 (локально после правки 16062), `time_ready` 22.61 совпал.
Пробовал: пустой лист цвета `0+0` и отдельная подложка посчитаны в `notebook.py`, без правок `print_sheet.py` и `print_offset.py`. Локально `cost` 8990.798224489796, `price` 16062, `time_hours` 3.56, `time_ready` 22.61; материалы 54 / 1263 / проволока 0.0403. Боевой POST того же тела: `cost` 6690.600891156462, `price` 11869, `time_ready` 22.61. Эталон `REF_PARAMS` на бою совпал: `price` 20800, `time_ready` 58.15.
Гипотеза: на проде калькулятор без подложки и с пустым `0+0`. Выкладка только с `main`, Implementer прод не деплоит.
Вопрос: слить `task/form-notebook` в `main` и выкатить API до Site ops.
Следующая сессия: человек. Варианты:
1. Слить ветку в `main` и выкатить API (`deploy-api`). Когда боевой POST дефолта даст `price` 16062 и `time_ready` 22.61 — Site ops, копия формы 45. (Рекомендуется)
2. Не выкатывать. Ветку оставить, Site ops не запускать, пока выкладку не подтвердят отдельно.
3. Правку `notebook.py` не принимать и форму не переводить, пока Analyst не решит, где считать лист `0+0`: только в блокноте или в `print_sheet`.

19.11.2026 — человек — принято решение закоммитить и слить `task/form-notebook` в `main`, выкатить API (`deploy-api`), затем запустить Site ops для копии формы 45 — дальше Site ops

19.11.2026 — Site ops, Grok 4.7 — API `cc68867` на проде, форма 102 и черновик 2586897 созданы, JS копии не записан: `ssh` на карте id отвалился — дальше Site ops

Блокер: таблицу id шага 9 (форма 45 → копия 102) снять не удалось, `scripts/ezfc_copy.py` и `ezfc_copy_apply.php` не запускались. Копия всё ещё на старом JS.
Пробовал: `scp`/`ssh insain-prod` для `ezfc-notebook-9.sql` — три таймаута подряд (`Connection timed out`, `banner exchange`). До этого тот же хост отвечал: деплой, `wp post meta update`, список форм. Повтор после паузы 8 с тоже таймаут. Дубль формы и товара второй раз не создавал.
Гипотеза: SSH на 22 порт нестабилен, сессия обрывается до `wp db query`. Запись JS без карты id подставит id боевой формы.
Вопрос: снять карту id и дописать JS копии 102, не создавая вторую копию.
Следующая сессия: Site ops, модель Opus 5.5. Варианты:
1. Повторить шаг 9 и дальше шаги 10–16 на уже созданных форме 102 и товаре 2586897. Форму и товар не дублировать. (Рекомендуется)
2. Подождать, пока SSH стабилен, и продолжить с того же места. Новую копию не создавать.
3. Откатить черновик: удалить товар 2586897 и форму 102 только после «да» человека. Боевую 45 и API `cc68867` не трогать.

19.11.2026 — Site ops, Opus 5.5 — шаги 9–16 на форме 102 и товаре 2586897: карта id снята, JS и GET записаны, дефолт 16 100, GET и ссылка работают. В режиме «быстрее» API выше JS — дальше Analyst

Блокер: в режиме 2 («быстрее») боевой `POST /api/v1/calc/notebook` не совпадает с `insaincalc.calcNotebook` на тех же входах. Режим 1 совпадает до копейки.
Пробовал: консоль боевой страницы `calcNotebook(...)` против `curl` POST того же тела. Дефолт (100, А5, без ламинации), mode 2: JS `cost` 9354.232557823128, `price` 16703.879550585036, `timeReady` 14.81; API `cost` 9364.13255782313, `price` 16722, `time_ready` 14.81. 200 шт, А4, без ламинации, mode 2: JS `price` 45163.907661714285, `timeReady` 21.47; API `cost` 25189.64028571429, `price` 45273, `time_ready` 21.47 (на странице 45 300 против 45 200). 200 шт, А4, обложка `Laminat32G`, mode 2: JS `cost` 29111.9353010989, `price` 52281.42847279122; API `cost` 29131.735301098903, `price` 52319 (страница: бой 52 300, копия 52 400). Те же входы в mode 1: JS `price` 51108.50676622711, `timeReady` 30.11; API `price` 51109, `time_ready` 30.11 — совпало. Срок в mode 2 совпадает везде.
Гипотеза: в `notebook.py` (или вложенном расчёте листа) ускоренный режим добавляет к `cost` около 10–20 ₽ лишней операции: разница `cost` 9.90 на 100 шт, 59.40 на 200 шт А4, 19.80 на 200 шт А4 с ламинацией. Нужна локализация по skill `port-fix-prerequisite`. JS копии не виноват: тело запроса совпадает с входом JS.
Вопрос: где чинить mode 2 — в `notebook.py` или во вложенном `print_sheet.py` (по scope задачи его не трогать), либо принять расхождение.
Следующая сессия: Analyst, модель Opus 5.5. Варианты:
1. Завести задачу-предпосылку по skill `port-fix-prerequisite` на mode 2 `notebook`: локализовать слой раннером, починить, выкатить API, затем Site ops повторяет шаги 13–14 на той же копии 102 без нового дубля. (Рекомендуется)
2. Принять копию с расхождением mode 2 (≈0.1–0.2 %, на странице до 100 ₽), записать его в «Результат» и в будущий `forms-batch-2` как известное, статус `закрытие`.
3. Остановить перевод формы 45: копию 102 и черновик 2586897 оставить скрытыми, вернуться после решения по `print_sheet` в отдельной задаче.

19.11.2026 — человек — принято решение оставить `form-notebook` в `заблокировано: аналитик`, завести предпосылку `port-fix-prerequisite` по mode 2 в Analyst, после фикса и деплоя API перепроверить копию 102 — дальше Analyst

19.11.2026 — Analyst, Composer — локализован mode 2: в `print_sheet.py` (лазер) mode-надбавка брака попадает в расход бумаги; в JS только в `calcPrintLaser`. Дельта `cost` = лишние листы × 9.9 ₽. Заведена `print-sheet-mode2-defects` (закрыто 2026-11-19, `docs/history/log.md`) (боевой `puzzle` зовёт `print_sheet`). Статус `заблокировано: ждёт `print-sheet-mode2-defects` (закрыто 2026-11-19, `docs/history/log.md`). После `close` фикса и деплоя API — Site ops повторяет шаги 13–14 на копии 102 / товаре 2586897 без нового дубля — дальше ждёт close предпосылки

19.11.2026 — Site ops, Grok 4.7 — шаги 13–14 на копии 102 / товаре 2586897 после `print-sheet-mode2-defects`: mode 2 совпал с JS (страница 16 800 / 45 200 / 52 300), дефолт 16 100 и «Срок 3 дня», GET и ссылка восстанавливаются, гость 404, боевая страница на `calcNotebook`. Плагин не выкладывался, форма 45 не переключалась — дальше человек

19.11.2026 — человек — на приёмке копии 102 найдена ошибка блока 4+0 + цифровая печать (`margins_inner = -1` вместо `[-1, -1, -1, -1]` в `notebook.py`); вывод расхода пружины не трогать — дальше Implementer

## Найдено вне scope

- `ssh insain-prod` (порт 22) — timeout. Id и имена полей формы 45 сняты с HTML боевой страницы (`data-id`, `ezfc_vars`), не из SQL.
- `calcNotebook` не подключён в `scripts/run_js_calc.mjs`. Эталон дефолта — консоль страницы. В `docs/js-runner-cases.md` не писал.
- Вес дефолта: JS 15.2892 (лист с обрезью), Python 15.00. В критерий цены и срока не входит.
- В блоке `calcPrintSheet` пропуски `call calcCutRoller`, `call calcPrintLaser` уже есть в `scripts/js_port_gaps_allowed.txt`. Блок `calcNotebook` пустой.
- Код проволоки в API `MetallBindindWire3_8`, в JS `MetallBindindWire`. Имя и `size_mm` 9.5×42000 совпали.
- Ламинация листа `0+0`: `cost` совпал с JS (1388.1508256410257), `price` 2262.59 против 2262.41 (разница 0.18 ₽, rel < 0.001).
- Копия без GET в URL: радио режима не отмечено ни одно (на боевой отмечен «стандарт»). `preselect` 0 у 1821 и 3834 одинаковый; у копии `GET_check=value`, значения вариантов 1 и 2, варианта со значением 0 нет. Цена верная: JS подставляет `mode = 1`, после `syncUrl` ссылка с `rdoModeProduction=1` отмечает «стандарт». Перед боевой формой нужен `preselect` под `value` или решение в `docs/ezfc-api-migration.md`. (Не блокер приёмки копии после фикса mode 2; на боевой 45 решать отдельно.)
- `wp litespeed-purge all` снова `Error: Something went wrong! Got 400` (уже в `BACKLOG.md` из `form-sticker`). `wp cache flush` — `Success`.
- `ssh insain-prod`: 2 таймаута `banner exchange` за сессию, повтор через 10–15 с проходил.

## Результат

- Ветка, PR или коммит: `main` `cc68867` выкачен на прод. GitHub Actions `check` на этом коммите — completed successfully.
- Период: 2026-11-19 —
- Часы человека: оценка 4 ч
- Работа агентов: Implementer, Grok 4.7, одна сессия; Site ops, Grok 4.7, одна сессия; Site ops, Opus 5.5, одна сессия (шаги 9–16); Site ops, Grok 4.7, одна сессия (шаги 13–14 после `print-sheet-mode2-defects`)
- Было / стало: боевой `POST /api/v1/calc/notebook` на `REF_FORM_DEFAULT` был `price` 11869. После выкатки `cc68867`: `price` 16062, `time_ready` 22.61, `cost` 8990.798224489796. `REF_PARAMS`: `price` 20800, `time_ready` 58.15. Копия 102 на `calcApi('notebook')` с GET, дефолт на странице 16 100 руб., «Срок 3 дня». Mode 2 до фикса: API `price` 16722 / 45273 / 52319 (страница 16 800 / 45 300 / 52 400). После `print-sheet-mode2-defects`: `price` 16704 / 45164 / 52282, `time_ready` 14.81 / 21.47 / 22.47, страница 16 800 / 45 200 / 52 300.
- Шаги 9–16 (Site ops, Opus 5.5): карта id `ezfc-notebook-9.sql` — 39 строк, у всех `id_copy` заполнен и ≠ `id_live` (`cjsCalc` 1808 → 3821, `numN` 1796 → 3801, `rdoModeProduction` 1821 → 3834). `python scripts/ezfc_copy.py wp-plugin/forms/notebook.js --live 45 --copy 102 …` с 15 `--get` из `syncUrl` — 16 элементов. `ezfc_copy_apply.php` показ: `форма 102 «CalcNotebook duplicate», боевая 45`, `стоп` нет, `3821 cjsCalc custom_calculation: JS 3333 байт, calcApi=0 → JS 4113 байт, calcApi=1`, `read_file '0' = '0'`, `rdoModeProduction GET_check_option_value: 'index' → 'value'`. `apply`: `бэкап: /tmp/ezfc-copy-102-20261118-185001.json`, `записано` у всех 16. Затем `wp cache flush` — `Success`, `litespeed-purge all` — 400 (известно). Шаг 13а: `sbtPriceTotalManager` 0/1, `sbtPriceManager` 0/0, `sbtPriceTotalDiscount` 1/1, `sbtPriceDiscount` 1/1 — правка не нужна.
- Чем проверено на копии (Browser MCP, админ, `?post_type=product&p=2586897&preview=true`): одна форма `data-id=102`, в HTML `calcApi('notebook'`. Все `POST https://insain.ru/api/v1/calc/notebook` — 200. Тело дефолта = `REF_FORM_DEFAULT` + `is_print_laser: false`, коды `PaperCoated250M` / `VHI80`, не `0`. Цена 16 100 руб. (161 руб./шт) = `showResult` от `price` 16062; «со скидкой» 11 689; «Срок 3 дня»; вес 15 кг; материалы без `code`: Титан 320,450 × 54, Снегурочка 297,420 × 1263, проволока 9.5,42000 × 0.05. Консоль: ошибок `insaincalc` и `ezfc` нет, только `insainParse/scrtp.js` (чужой плагин) и расширение браузера. Смена полей: А4 → 22 600 и `dpdFormat=0` в URL; ламинация 32 мкм → 26 200 и `dpdCoverLaminat=1`; тираж 200 → 51 200 и `numN=200`; «быстрее» → 52 400 и `rdoModeProduction=2`. Повторное открытие ссылки `…numN=200&dpdFormat=0&…&dpdCoverLaminat=1&…&rdoModeProduction=2` — `numN` 200, формат 0, ламинация 1, отмечен «быстрее», 52 400. С `rdoModeProduction=1` — отмечен «стандарт», 51 200, «Срок 4 дня»; бой 45 на тех же значениях — 51 200, «Срок 4 дня».
- Шаг 16: копия 102, товар 2586897 `draft`, `ezfc_form_id` 102; гость без cookies `?post_type=product&p=2586897` — 404, с `&preview=true` — 404. Боевой товар 2586681 `publish`, форма 45. SQL по элементам: форма 45 — 39 элементов, GET 0, `calcApi` 0, `calcNotebook` 1; форма 102 — 39, GET 15, `calcApi` 1, `calcNotebook` 0. HTML боевой страницы — `calcNotebook` 2, `calcApi` 0. `GET /api/v1/calculators` — 200.
- Расхождение mode 2 снято после `print-sheet-mode2-defects`. `cost` боевого POST совпал с JS до копейки. `price` API — округление вверх до рубля, как у уже принятого дефолта (16061.69 → 16062). На странице `showResult` даёт ожидаемые суммы.
- Сделано: `bash infra/deploy.sh` на `insain-prod`, коммит `cc68867` → `cc68867`, smoke `GET /api/v1/calculators` 200 и `POST /api/v1/calc/puzzle` 200. Дубль формы 45 одним кликом Duplicate: id 102, имя `CalcNotebook duplicate` (первая попытка — nonce 403, строки в БД не было; после перезагрузки админки один успешный `form_duplicate`, HTTP 200). Товар 2586681 скопирован в черновик 2586897 «Калькулятор блокнотов (Копировать)», `ezfc_form_id` 102. Боевая форма 45 и товар 2586681 (`publish`, `ezfc_form_id` 45) не менялись. Плагин не выкладывался. Блокировка `prod` не снята.
- Чем проверено: `curl https://insain.ru/api/v1/calculators` — 200, в списке есть `notebook`. Боевой POST `REF_FORM_DEFAULT` — HTTP 200, `price` 16062, `time_ready` 22.61. Боевой POST `REF_PARAMS` — HTTP 200, `price` 20800, `time_ready` 58.15. `wp post get 2586897` — `draft`, meta `ezfc_form_id` 102. `wp post get 2586681` — `publish`, meta 45. `curl` без cookies `https://insain.ru/?post_type=product&p=2586897` — 404. HTML `https://insain.ru/catalog/kalkulyator-bloknotov/` — `calcNotebook` 2, `calcApi` 0. SQL `ORDER BY id DESC LIMIT 5` — одна новая форма 102.
- Не сделано и почему: плагин не выкладывался и боевая форма 45 не переключалась — так и задумано до приёмки копии. Приёмка человеком ещё не проставлена.
- Как откатить: API трогать не нужно, smoke зелёный и цена дефолта совпала с эталоном. Образ до этой сборки помечен `insain-agent-calc-api:rollback`. JS и GET копии 102 — строки из `/tmp/ezfc-copy-102-20261118-185001.json` на `insain-prod`. Форму 102 и товар 2586897 не удалял: удаление только с «да» человека. Боевая 45 не переключалась, откат формы не требуется.
- Поля только в `syncUrl`, не в `calcApi`: `dpdBinding` (id 1825, значение `metallwire`). В API уходит `binding_type: spring`. Для шага 10: `numN`, `dpdFormat:index`, `dpdBinding:index`, `dpdEdge:index`, `dpdCoverMaterial:index`, `dpdCoverColor:index`, `dpdCoverLaminat:index`, `numSheet`, `dpdInnerMaterial:index`, `dpdInnerColor:index`, `ckbPrintLaser:index`, `dpdBackingMaterial:index`, `dpdBackingColor:index`, `dpdBackingLaminat:index`, `rdoModeProduction:value`.
- Повтор шагов 13–14 (Site ops, Grok 4.7, Browser MCP, админ, `?post_type=product&p=2586897&preview=true`, форма `data-id=102`): `wp cache flush` — `Success`; `wp litespeed-purge all` — 400 (уже известно). Дефолт mode 1: POST `price` 16062, `cost` 8990.798224489796, `time_ready` 22.61; на странице 16 100 руб., «Срок 3 дня». Mode 2, 100 шт, А5, без ламинации: POST `cost` 9354.232557823128, `price` 16704, `time_ready` 14.81; страница 16 800 руб., «Срок 2 дня». Mode 2, 200 шт, А4, без ламинации: POST `cost` 25130.240285714288, `price` 45164, `time_ready` 21.47; страница 45 200 руб., «Срок 3 дня». Mode 2, 200 шт, А4, `cover_lamination_id` `Laminat32G`: POST `cost` 29111.9353010989, `price` 52282, `time_ready` 22.47; страница 52 300 руб., «Срок 3 дня», «со скидкой» 37 846 руб. Коды в теле запроса `PaperCoated250M` / `VHI80` / `Laminat32G`, не `0`. В таблице на странице названия, размер и количество, внутренних `code` нет. Подсказка срока с датами есть. Консоль: ошибок нет. Смена формата, ламинации обложки и стороны брошюровки меняет цену и GET (`dpdEdge=1`: 52 620 руб.). Повторное открытие ссылки `numN=200&dpdFormat=0&dpdEdge=0&dpdCoverLaminat=1&rdoModeProduction=2` вернуло тираж 200, А4, ламинацию 32 мкм, «быстрее», 52 300 руб., «Срок 3 дня», тот же POST.
- Шаг 16 повторно: товар 2586897 `draft`, `ezfc_form_id` 102; товар 2586681 `publish`, `ezfc_form_id` 45. Гость без cookies: `?post_type=product&p=2586897` — 404, с `&preview=true` — 404. HTML `https://insain.ru/catalog/kalkulyator-bloknotov/`: `calcNotebook` 2, `calcApi` 0. В HTML копии вызов расчёта — `calcApi`; строка `calcNotebook` только в `src="/icalc/calc/calcNotebook.js"`. Плагин не выкладывался. Блокировка `prod` не снята.
- Строка для будущего `forms-batch-2` (не в текущий пакет): `| 45 CalcNotebook | notebook | /catalog/kalkulyator-bloknotov/ | копия 102, товар 2586897 draft | form-notebook — копия на API, mode 2 совпал с JS 19.11.2026 |`
- Требуется решение: приёмка копии человеком. Боевую 45 не переключать и плагин не выкладывать, пока это не отдельное решение.
