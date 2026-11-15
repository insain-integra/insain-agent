# form-print-offset

Статус: черновик
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Копия формы 82 CalcPrintPromo на черновике товара считает `POST /api/v1/calc/print_offset`. URL копии пишется GET-именами элементов. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая форма 82 на странице https://insain.ru/catalog/listovki-po-akczii/ по-прежнему на `insaincalc.calcPrintOffsetPromo`.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md` — порядок. Боевая форма (шаги 17–24 skill) в эту задачу не входит.
- `docs/ezfc-api-migration.md` — шаблон `cjsCalc`, GET = имя элемента, `GET_check`: dropdown с кодом — `index`, radio `1`/`2` — `value`.
- `docs/site/forms.md` — строка формы 82, только читать.
- `todo/EPIC-forms-to-api.md` — пачка 3. Форма 83 CalcCardPromo на том же slug — отдельная задача после принятия этой копии.
- JS формы — `calcPrintOffsetPromo` в `js_legacy/calc/calcPrintOffset.js`, не `calcPrintOffset`. Slug API — `print_offset`.
- `docs/js-runner-cases.md` — команда раннера для `calcPrintOffsetPromo`, если кейс уже есть.
- Остальное не открывать.

## Scope

- В git (Implementer): сверка по skill `verify.md` (порт `calcPrintOffsetPromo`, эталон, `REF_FORM_DEFAULT`, раннер, боевой API). `wp-plugin/forms/print_offset.js`: id элементов боевой формы 82, `insaincalc.syncUrl`, `insaincalc.calcApi('print_offset'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет. Кейс дефолта — в `test_print_offset.py` с пометкой `# JS, ДД.ММ.ГГГГ`, после `close` `print-offset-promo` (закрыто 2026-11-16, `docs/history/log.md`): до этого эталоны promo пишет она, и путь теста в «Файлы» этой задачи не входит. После close путь вернуть в «Файлы» и дописать только `REF_FORM_DEFAULT`. Команду раннера дописать одной строкой в `docs/js-runner-cases.md`; файл общий для пачки, в «Файлы» его нет. Если строку в файл не вносили — она в «Результат», вносят при слиянии.
- На проде (Site ops): дубль формы и черновик товара — только после «да» человека. На копию — тот же JS с id копии, без `read_file`. GET на копии: имя параметра = имя элемента. Боевую форму не размечать. Прогон копии под админом: эталон, смена полей, ссылка с GET.
- После принятия копии человеком строка для «Состава пакета» пишется в «Результат», не в `todo/forms-batch-switch.md`. В файл пакета её переносят при слиянии, если та задача не в статусе `в работе`.
- Ветка `task/form-print-offset` от `main`.

## Файлы

- `wp-plugin/forms/print_offset.js`
- `calc_service/tests/test_calculators/test_print_offset.py`
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 82. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/82.json`, `todo/forms-batch-switch.md`.
- Правка `calc_service/calculators/print_offset.py`, цен, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`.
- Форма 83 CalcCardPromo и остальные формы эпика.
- Функция `calcPrintOffset` (не promo) и slug `print_wide`.
- Удаление копии и черновика.

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPrintOffsetPromo` — в блоке `calcPrintOffsetPromo` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [ ] Раннер и `POST https://insain.ru/api/v1/calc/print_offset` на эталоне и на дефолте формы 82: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_print_offset.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [ ] `Select-String -Path wp-plugin\forms\print_offset.js -Pattern "calcApi\('print_offset'|syncUrl\(|showResult\("` — все три вхождения есть.
- [ ] Копия не на витрине: `wp post get PRODUCT --field=post_status` — `draft` или `private`; `curl.exe` без cookies на `/?post_type=product&p=PRODUCT` — `404`.
- [ ] На копии под админом эталон даёт `POST /api/v1/calc/print_offset` → 200. Цена на странице равна `price` API с округлением `showResult`.
- [ ] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Расхождение JS и API (rel > 0.001) — стоп, калькулятор не править, предпосылка по skill `port-fix-prerequisite`. Порт `calcPrintOffset` не заменяет проверку `calcPrintOffsetPromo`.
- Формы: id элементов боевой формы 82 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

16.11.2026 — Implementer, Grok 4.7 — порт `calcPrintOffsetPromo` отсутствует, боевой API на дефолте формы отдаёт price 0 при JS 4244.4 — дальше человек
16.11.2026 — человек — выбран вариант 1: предпосылка через Analyst (порт `calcPrintOffsetPromo` в `print_offset` с mode 0, 4244.4 ₽ / 56 ч) — дальше Analyst
16.11.2026 — Analyst, Grok 4.7 — на main заведена `todo/print-offset-promo.md` (коммит `2c125b2`), эталон mode 0 — дальше ждёт закрытия предпосылки
17.11.2026 — Orchestrator — rebase на main после закрытия `print-offset-promo`, статус `черновик` — дальше Implementer

Блокер: форму 82 нельзя переводить на `POST /api/v1/calc/print_offset`. Функции `calcPrintOffsetPromo` в Python нет, схема API требует ширину, высоту и цветность, которых на форме нет, цена и срок с JS не сходятся.
Пробовал: `python scripts/js_port_gaps.py calcPrintOffsetPromo` → `calcPrintOffsetPromo -> нет порта`, `нет в Python: module` (строка `calcPrintOffsetPromo module` уже в `scripts/js_port_gaps_allowed.txt`). Штатный `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` → `Калькулятор не подключён: calcPrintOffsetPromo` (`js_legacy/calc/calcPrintOffset.js` в список файлов раннера не входит; файл раннера не менял). Тот же раннер с временной подгрузкой этого файла, `--data current`: тираж 1000, код `OffsetPromoА51000` (кириллическая А) — mode 0/1/2 дают cost 2250, price 4244.4, time_hours 0, weight_kg 3.5742, time_ready 56/48/40. Тираж 2000, mode 1 — cost 4050, price 7592.4, time_ready 48, weight_kg 7.1484. `POST https://insain.ru/api/v1/calc/print_offset` с телом `{num_sheet:1000,width:148,height:210,color:"4+4",material_id:"OffsetPromoА51000",mode:1}` → 200, cost 0, price 0, time_ready 8, materials []. rel цены и срока много больше 0.001. Повторный POST обычного эталона `PaperCoated115M` в этой сессии не дождался ответа (timeout), на вывод по промо не влияет: промо-вызов уже вернул 200.
Гипотеза: `PrintOffsetCalculator.calculate` (`calc_service/calculators/print_offset.py`, строки 100–104) ищет `material_id` только в каталоге sheet и на неизвестном коде уходит в `_empty` (срок из `baseTimeReady` [24, 8, 1], для mode 1 это 8). Промо живёт в `calcPrintOffset.js` строки 89–106: `findMaterial('sheet', offsetpromoID)`, набор по `numSheet` материала, доставка `calcShipment(..., 'Luch')`, наценка `marginOffsetPromo`, срок `baseTimeReadyPrintOffsetPromo`. В `PORTS` (`scripts/js_port_gaps.py`) записан только `calcPrintOffset`, не promo. Данные `offset_promo.json` и ключ срока в `common.json` калькулятор не читает. Поля формы 82: `3188 numN` (дефолт 1000), `3189 dpdFormat` (выбран индекс 1, `OffsetPromoА51000`; опции А4/А5/А6/евро, визиток нет), `3221 rdoModeProduction` («стандарт» value=0 data-value=1, «быстрее» value=1 data-value=2), расчёт `3208 cjsCalc`. Боевой JS: `get_value_from(3189, true)[0]` в код, режим — `get_value_from(3221)` без `true`. Без `true` ezFC берёт value, `Math.ceil` даёт режим 0, срок 56 ч при подписи «стандарт». Цена от режима не зависит.
Вопрос: какой путь разблокирует форму — предпосылка на порт с эталоном режима 0 (как боевая страница), предпосылка с режимом 1 (как data-value «стандарт»), порт в этой же ветке, или форму не переводить.
Следующая сессия: человек (варианты ниже), затем Analyst либо Implementer по выбранному пути.

## Найдено вне scope

- Штатный раннер не загружает `js_legacy/calc/calcPrintOffset.js`. Подключать его в этой задаче нельзя: файл в «Не-scope».
- Радио «стандарт» на форме 82: value 0 и data-value 1. Боевой расчёт читает value, подпись и срок расходятся. Цену это не меняет. В JS формы и в калькулятор не переносил.
- `GET` у `numN`, `dpdFormat`, `rdoModeProduction` сейчас пустой (`GET_check` у формата и режима в базе — `index`). Это шаг копии, до совпадения цены не делать.

## Результат

- Ветка, PR или коммит: ветка `task/form-print-offset`. В git только `todo/form-print-offset.md`: блокер сверки и статус «ждёт `todo/print-offset-promo.md`». `wp-plugin/forms/print_offset.js` не создан.
- Сделано: сверка шагов 0–5б skill `ezfc-form-to-api` до стопа. Порт promo — допустимый пропуск `module`, отдельной реализации нет. Дефолт боевой страницы https://insain.ru/catalog/listovki-po-akczii/ снят с HTML: тираж 1000, формат А5 `OffsetPromoА51000`, режим с value 0. Id полей совпадают с `get_value_from` в `cjsCalc`. Команду раннера в `docs/js-runner-cases.md` не писал (общий файл). Строка для слияния, когда раннер начнёт грузить `calcPrintOffset.js`: `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",0]'` → price 4244.4, time_ready 56.
- Чем проверено: `python scripts/js_port_gaps.py calcPrintOffsetPromo` (exit 0, `нет в Python: module`). Штатный раннер — exit 1, `Калькулятор не подключён`. Временный прогон того же скрипта с подгрузкой `calcPrintOffset.js` — числа выше. `POST https://insain.ru/api/v1/calc/print_offset` на промо-код — 200, price 0, time_ready 8. `make check` не запускался: код калькулятора и JS формы не менялись, критерий цены не выполнен.
- Не сделано и почему: `forms/print_offset.js`, `REF_FORM_DEFAULT`, дубль формы. Skill `port-fix-prerequisite` шаг 5: при расхождении копию и плагин не трогать. `print_offset.py` в «Не-scope». Критерий приёмки: price abs ≤ 0.02 и rel ≤ 0.001, time_ready rel ≤ 0.001 — на дефолте 4244.4 против 0 и 56 против 8.
- Требуется решение:
  1. (Рекомендуется) Analyst заводит предпосылку на порт `calcPrintOffsetPromo` в slug `print_offset`. Эталон дефолта: тираж 1000, `OffsetPromoА51000`, mode 0 — cost 2250, price 4244.4, time_hours 0, time_ready 56, weight_kg 3.5742. Второй кейс: тираж 2000, mode 0, ожидание снять тем же раннером (на mode 1 уже есть price 7592.4, time_ready 48). Размер и цветность брать из `offset_promo.json`, обязательные width/height/color для промо не требовать. Эталон обычного офсета не сдвигать. В раннер добавить загрузку `calcPrintOffset.js`. После деплоя API эта задача снова `черновик`.
  2. Та же предпосылка, но «стандарт» = mode 1 (data-value), time_ready 48 при цене 4244.4. Срок на будущей копии короче, чем сейчас на боевой странице. Боевую форму 82 не переключать.
  3. Снять запрет на правку `calc_service/calculators/print_offset.py` и портировать промо в ветке `task/form-print-offset` эталоном варианта 1. Калькулятор ни на одной боевой форме API не стоит (`docs/site/forms.md`).
  4. Форму 82 оставить на `insaincalc.calcPrintOffsetPromo`. Задачу закрыть без копии и без порта.
- Строка в «Состав пакета» (в `todo/forms-batch-switch.md` не писать, пока та задача `в работе`): нет, копия не принята.
