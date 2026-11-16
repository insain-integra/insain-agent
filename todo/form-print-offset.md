# form-print-offset

Статус: закрытие
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

- [x] `python scripts/js_port_gaps.py calcPrintOffsetPromo` — в блоке `calcPrintOffsetPromo` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.
- [x] Раннер и `POST https://insain.ru/api/v1/calc/print_offset` на эталоне и на дефолте формы 82: `price` abs ≤ 0.02 и rel ≤ 0.001, `time_ready` rel ≤ 0.001. Иначе стоп, форму не дублировать.
- [x] `python -m pytest calc_service/tests/test_calculators/test_print_offset.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`, `failed` нет. В тесте есть `REF_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`.
- [x] `Select-String -Path wp-plugin\forms\print_offset.js -Pattern "calcApi\('print_offset'|syncUrl\(|showResult\("` — все три вхождения есть.
- [x] Копия не на витрине: `wp post get 2586895 --field=post_status` — `draft`; `curl.exe` без cookies на `/?post_type=product&p=2586895` — `404`.
- [x] На копии под админом эталон даёт `POST /api/v1/calc/print_offset` → 200. Цена на странице равна `price` API с округлением `showResult`.
- [x] URL обновляется GET-именами формы. Ссылка с этими GET открывает копию с теми же значениями и той же ценой.

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

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
17.11.2026 — Implementer, Grok 4.7 — сверка сошлась (дефолт mode 1, price 4244.4, time_ready 48), `print_offset.js` и `REF_FORM_DEFAULT` в ветке, `make check` зелёный — дальше Site ops
17.11.2026 — Site ops, Grok 4.7 — копия формы 100 на черновике 2586895, GET и прогон на боевом API, боевая 82 не тронута — дальше Reviewer
17.11.2026 — Reviewer, Auto — принято: `print_offset.js`, `REF_FORM_DEFAULT`, отчёт Site ops по копии; в ветке ещё нет коммита с кодом — дальше человек (слияние и `close`)
- 17.11.2026 — человек — принято — закрытие

## Найдено вне scope

- `GET /api/v1/tool_schema/print_offset` по-прежнему помечает `width`, `height`, `color` как required. На форме 82 таких полей нет. Боевой `POST` без них на промо-коде уже отдаёт цену (закрытый `print-offset-promo` и эта сверка). Схему не менял: `print_offset.py` в «Не-scope».
- Радио «стандарт»: HTML `value` 0, `data-value` 1. Боевой `get_value_from(3221)` без `true` суммирует `parseFloat(data-value)` и даёт 1, не 0. Срок на странице «6 дней» (48 ч). В калькулятор это не переносил: цена от режима не зависит.
- Имя `GET` у `numN`, `dpdFormat`, `rdoModeProduction` в базе боевой формы пустое. `GET_check` у формата и режима на боевой уже `index` (не пусто). На копии Site ops прописал имена GET; у формата оставил `index`, у режима сменил на `value`. Боевую не менял.
- В `docs/js-runner-cases.md` строка дефолта формы 82 всё ещё с mode 0 (`time_ready` 56). Файл общий, не правил. Актуальная команда — в «Результат».

## Результат

- Ветка, PR или коммит: ветка `task/form-print-offset`, коммита нет. Файлы: `wp-plugin/forms/print_offset.js`, `calc_service/tests/test_calculators/test_print_offset.py`, `todo/form-print-offset.md`.
- Сделано: сверка шагов 0–5б. Порт `calcPrintOffsetPromo` полный (`нет в Python:` пусто). Дефолт боевой страницы https://insain.ru/catalog/listovki-po-akczii/ : тираж 1000, А5 `OffsetPromoА51000` (индекс 1), режим `get_value_from(3221)` = 1. `wp-plugin/forms/print_offset.js` вызывает `syncUrl`, `calcApi('print_offset'` и `showResult`; своих формул и чтения DOM нет. Id боевой формы: `3188 numN`, `3189 dpdFormat`, `3221 rdoModeProduction`, `3208 cjsCalc`. `REF_FORM_DEFAULT` — `# JS, 17.11.2026`. Эталон обычного офсета `REF_PARAMS` не сдвигал. В `calcApi` не уходят поля, которых нет в схеме: лишних полей формы нет. `width` / `height` / `color` форма не шлёт — промо берёт их из каталога.
- Чем проверено: `python scripts/js_port_gaps.py calcPrintOffsetPromo` — exit 0, во всех блоках `нет в Python:` пусто. Раннер `--data current`: `[1000,"OffsetPromoА51000",1]` → cost 2250, price 4244.4, time_hours 0, time_ready 48, weight_kg 3.5742; `[2000,"OffsetPromoА51000",1]` → cost 4050, price 7592.4, time_ready 48, weight_kg 7.1484. `POST https://insain.ru/api/v1/calc/print_offset` теми же телами без width/height/color — 200, те же price и time_ready (abs 0, rel 0). Страница под админом: «4 700 руб.», «Срок 6 дней», вес 3.57 кг, материал «Листовки А5, 4+4, сборный тираж на офсет, 1000шт», размер 148,210, количество 1000 — как `materials` API (`size_mm` [148, 210]). `python -m pytest calc_service/tests/test_calculators/test_print_offset.py calc_service/tests/test_wp_plugin_forms.py -q` — 20 passed. `Select-String` — `syncUrl(`, `calcApi('print_offset'`, `showResult(` есть. `python scripts/dev.py check` — см. журнал, код выхода 0.
- Не сделано и почему: боевую форму 82 и страницу https://insain.ru/catalog/listovki-po-akczii/ не переключал. `read_file` не включал. Плагин не выкладывал. `docs/js-runner-cases.md`, `docs/site/forms.md`, `todo/forms-batch-switch.md`, `todo/EPIC-*.md`, `STATUS.md`, `BACKLOG.md` не правил. Удаление копии и черновика — не-scope.
- Требуется решение: нет. Дальше Reviewer.
- Для Reviewer: у радио «стандарт» HTML value 0 и data-value 1, у «быстрее» HTML value 1 и data-value 2. `GET_check=value` на копии сверяет параметр с data-value: ссылка `rdoModeProduction=1` отмечает «стандарт», в API уходит mode 1. Боевая форма по-прежнему с `GET_check=index` у режима — это шаг переключения боевой, его не было. Срок дефолта 48 ч, не 56. Журнал 16.11 ошибочно считал режим 0. На странице копии дефолт «4 300 руб.», не «4 700 руб.»: `showResult` округляет 4244.4 при тираже 1000 до 4300. «4 700 руб.» пишет старый JS боевой формы.
- Строка раннера для слияния в `docs/js-runner-cases.md` (файл общий, сейчас там mode 0): `node scripts/run_js_calc.mjs calcPrintOffsetPromo --data current --args '[1000,"OffsetPromoА51000",1]'` → price 4244.4, time_ready 48. Эталон тиража ≥ 2, его можно ввести на форме (шаг слайдера 1000): `[2000,"OffsetPromoА51000",1]` → price 7592.4, time_ready 48.
- Строка в «Состав пакета» (`todo/forms-batch-switch.md` не правил; статус того файла `черновик`, перенос при слиянии после приёмки копии человеком): `| 82 CalcPrintPromo | print_offset | /catalog/listovki-po-akczii/ | 100 / 2586895 (draft) | копия на ревью 17.11.2026, form-print-offset |`

### Site ops, шаги 6–16

- Сделано: одна копия формы, id 100, имя `CalcPrintPromo duplicate` (до дубля последняя была 99). Товар 2586895 «Листовки по акции (Копировать)», `post_status=draft`, `ezfc_form_id=100`. Гость: `curl.exe` на `/?post_type=product&p=2586895` — `404`. На копию записан JS из `wp-plugin/forms/print_offset.js` с id копии, `custom_calculation_function_read_file=0`. GET: `numN` без суффикса (элемент 3757), `dpdFormat` = `index` (3758), `rdoModeProduction` = `value` (3772). Элемент расчёта 3759, `calcApi=1`. Бэкап `/tmp/ezfc-copy-100-20261116-170327.json`. Флаги шага 13а уже как у эталона: скидка `hidden=1`, `calc_hidden=1`; менеджерские `hidden=0`. Блок результата не пересобирал: колонки цены в одной строке, режим внутри группы срока, подсказка дат на месте, таблица материалов без внутренних `code`, с размером и количеством.
- Чем проверено: боевая форма 82 после записи — `GET` пустой, у `cjsCalc` 3208 нет `calcApi`; товар 2586806 `publish`, `ezfc_form_id=82`, `post_modified` 2025-02-16. `curl` страницы https://insain.ru/catalog/listovki-po-akczii/ находит `calcPrintOffsetPromo`. Под админом превью `/?post_type=product&p=2586895&preview=true`. Дефолт: тираж 1000, А5 `OffsetPromoА51000`, «стандарт» (data-value 1). `POST /api/v1/calc/print_offset` 200, тело `{"num_sheet":1000,"material_id":"OffsetPromoА51000","mode":1}`, ответ price 4244.4, time_ready 48, weight_kg 3.5742. На странице «4 300 руб.», «Срок 6 дней», вес 3.57 кг, материал «Листовки А5, 4+4, сборный тираж на офсет, 1000шт», размер 148,210, количество 1000. Смена формата на А4: URL `dpdFormat=0`, POST `OffsetPromoА41000`, цена на странице «7 500 руб.», материал А4, размер 210,297. Тираж 2000, снова А5 и mode 1: URL `numN=2000&dpdFormat=1&rdoModeProduction=1`, POST `{"num_sheet":2000,"material_id":"OffsetPromoА51000","mode":1}` 200; отдельный `curl` того же тела — price 7592.4, time_ready 48, weight_kg 7.1484. На странице «7 600 руб.», «Срок 6 дней», вес 7.15 кг, количество 2000. Повторное открытие этой ссылки восстанавливает тираж 2000, А5, отмеченный «стандарт», ту же цену «7 600 руб.» и тот же POST. Консоль: ошибок `insaincalc` и `ezfc` нет. `wp cache flush` — Success. `wp litespeed-purge all` — `Error: Something went wrong! Got 400`; страница копии после этого отдала новый JS и GET, повторно не гонял.
- Как откатить: боевая форма и боевой товар не менялись, откат витрины не нужен. Копия — вернуть `data` элементов 3759, 3757, 3758, 3772 из `/tmp/ezfc-copy-100-20261116-170327.json`. Черновик 2586895 и форму 100 не удалял.

## Ревью 1

**Итог:** принято.

**Критерии (diff + отчёт Site ops, без повторного прогона копии):**

| Критерий | Статус |
| --- | --- |
| `js_port_gaps.py calcPrintOffsetPromo` — порт полный | ok — в «Результат» Implementer, `нет в Python:` пусто |
| Раннер и боевой POST на эталоне/дефолте (mode 1, 4244.4 / 48) | ok — отчёт Implementer; `REF_FORM_DEFAULT` с `# JS, 17.11.2026`, mode 1 |
| pytest `test_print_offset.py` + `test_wp_plugin_forms.py` | ok — локально 20 passed (14.5 s) |
| `print_offset.js`: `syncUrl`, `calcApi('print_offset'`, `showResult` | ok — `Select-String`, своих формул/DOM-цены нет; id 3189/3221, тираж `{{numN}}` |
| Копия draft / 404 гостю | ok — Site ops: 2586895 `draft`, curl без cookies → 404 |
| Копия: POST 200, цена = API ± `showResult` | ok — дефолт 4244.4 → «4 300 руб.»; 2000 → 7592.4 → «7 600 руб.»; А4 кейс 7500 |
| GET `numN` / `dpdFormat=index` / `rdoModeProduction=value` | ok — ссылка `numN=2000&dpdFormat=1&rdoModeProduction=1` восстанавливает поля и цену |
| Боевая 82 не переключена | ok — Site ops: у 3208 нет `calcApi`, страница на `calcPrintOffsetPromo` |

**Инварианты:** цен в JS нет; в API уходят только `num_sheet`, `material_id`, `mode`; scope соблюдён (боевую/`read_file`/калькулятор/общие доки не трогали).

**Замечания:**

- `желательно` — `wp-plugin/forms/print_offset.js`, правка `test_print_offset.py` и актуальная задача только в рабочем дереве: на `task/form-print-offset` закоммичен лишь hold-коммит; перед merge — один коммит с реализацией.
- `желательно` — при слиянии дописать строку раннера из «Результат» в `docs/js-runner-cases.md` (mode 1, 48 ч) и строку «Состав пакета» в `todo/forms-batch-switch.md`.

**Вне scope (без блокеров):** схема `tool_schema` и радио value/data-value на боевой — уже в «Найдено вне scope».
