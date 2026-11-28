# form-hashtags

Статус: выкатка
Сложность: низкая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: вторая форма уже выкатанного slug `tablets`; дефолт формы 51 на лиде расходился из-за фрезеровки. Ждёт доработку `form-stands`, те же файлы.

## Цель

Копия формы 51 CalcHashtags на черновике товара считает `POST /api/v1/calc/tablets`. URL копии пишется GET-именами элементов формы 51. Ссылка с этими GET открывает ту же копию с теми же значениями и той же ценой. Боевая страница https://insain.ru/catalog/kalkulyator-heshtegov/ остаётся на `insaincalc.calcTablets`. В пакет `forms-batch-switch` форма 51 не попадает.

## Контекст и ссылки

- `.cursor/skills/ezfc-form-to-api/SKILL.md`, этапы `verify.md` и `copy.md`. Шаги 17–24 не входят.
- `docs/ezfc-api-migration.md` — GET = имя элемента. Образец второй формы — `wp-plugin/forms/print_sheet.js`.
- `docs/site/forms.md` — строка формы 51, только читать.
- `wp-plugin/forms/tablets.js` и `calc_service/tests/test_calculators/test_tablets.py` — блоки и эталоны уже принятых форм не сдвигать.
- `js_legacy/calc/calcTablets.js` — эталон. На сверке лида дефолт формы 51 звал `calcMilling`; раннер без этого вызова падал.
- `todo/EPIC-forms-to-api.md` — пачка 6.
- Остальное не открывать.

## Scope

- В git (Implementer): JS формы 51 со своими id, блок `/* form 51 */` в `forms/tablets.js`. Блоки уже принятых форм и их эталоны не менять. Развилка по набору полей, не по id копии. Если развилка не собирается без сдвига цены принятой формы — стоп, `заблокировано: аналитик`.
- Дефолт формы 51 сверить с раннером. Сошёлся — `tablets.py` не менять. Не сошёлся — портировать только ветки этого дефолта вызовом уже существующего порта (`milling`, если он есть). Порта нет — стоп, `заблокировано: аналитик`. Новые строки в allowed не добавлять.
- Кейс дефолта формы 51 — отдельная константа в `test_tablets.py` с пометкой `# JS, ДД.ММ.ГГГГ`.
- На проде (Site ops): дубль формы 51 на черновик. JS копии в элементе (`read_file=0`). Плагин не выкладывать. Боевую 51 не переключать. Копию 120 и копии предыдущих задач slug не править.
- Строка для будущего боевого пакета и дописка для `docs/js-runner-cases.md` — в «Результат».

## Файлы

- `wp-plugin/forms/tablets.js`
- `calc_service/calculators/tablets.py`
- `calc_service/tests/test_calculators/test_tablets.py`
- WordPress: только новая копия формы 51 и её черновик

## Не-scope

- `todo/forms-batch-switch.md`, `docs/site/forms.md`, `docs/js-runner-cases.md`
- Копия 120 / 2586916, боевые формы 36, 48, 76, 68 и их копии
- `shild.py`, JSON цен, выкладка плагина, шаги 17–24

## Критерии приёмки

- [x] `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py -q` — `passed`. Эталоны уже принятых форм на месте. Есть константа дефолта формы 51 с `# JS,`.
- [x] В `wp-plugin/forms/tablets.js` есть `calcApi('tablets'`, `syncUrl(`, `showResult(` и блок `/* form 51 */`. Id уже принятых форм на месте.
- [ ] Копия не на витрине: статус черновика `draft` или `private`, гость получает не `200`.
- [ ] На копии под админом дефолт даёт `POST /api/v1/calc/tablets` → 200. Цена на странице = `price` API с округлением `showResult`.
- [x] `curl.exe -s https://insain.ru/catalog/kalkulyator-heshtegov/` — в HTML есть `calcTablets`, нет `calcApi`.

### Критерии перевода формы ezFC на API

- [ ] URL обновляется GET-именами формы 51; ссылка с GET открывает форму с теми же значениями и той же ценой.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль только этой копии. Запись под `lock prod`.
- Цены: нет. Эталоны принятых форм не сдвигать.
- Формы: дефолт может требовать фрезеровку. id боевой 51 не менять.

## Режим

прод

## Журнал передач

27.11.2026 — человек — завести задачи на оставшиеся формы, реализацию не начинать — дальше Analyst
27.11.2026 — Analyst, Grok 4.7 — задача формы 51, ждёт `form-stands` — дальше человек
29.11.2026 — человек — `form-stands` возвращена на доработку, ожидание снова — дальше человек
29.11.2026 — человек — `form-stands` закрыта, ожидание снято — дальше Implementer
29.11.2026 — Implementer, Grok 4.7 — блок формы 51 и порт фрезы дефолта в tablets, make check зелёный; копию не дублировать, пока API с этой ветки не на проде — дальше Reviewer
29.11.2026 — человек — dashboard.md на main оставить (чужой коммит факт-листа), Reviewer в worktree — дальше Reviewer
29.11.2026 — Reviewer, Auto — принято diff git (блок 51, is_cut_milling, эталоны); копия/GET — после слияния и выкатки API — дальше человек
29.11.2026 — человек — принято: слить в main, запушить, статус выкатка; API и дубль формы 51 после зелёного CI — дальше Site ops

## Ревью 1

**Вердикт:** принято

**Критерии (git):** `python scripts/dev.py check` — 933 + 81 passed (повтор Reviewer). `pytest` tablets + wp_plugin_forms + js_port_gaps — 97 passed. В `tablets.js` — `/* form 51 */`, ветка `inpText`, `calcApi`/`syncUrl`/`showResult`; id 1339 и 1924 форм 36/48 на месте, их блоки и эталоны `REF_FORM48_*` в diff не трогались. `REF_FORM51_DEFAULT` с `# JS, 29.11.2026`, режимы 0–1–2 и `test_tablets_js_form51_posts_default`. `tablets.py`: `MillingCalculator` только при `is_cut_milling`; из `js_port_gaps_allowed.txt` сняты `calcMilling`/`isCutMilling`, `MAX_ALLOWED` 29, тест цепочки обновлён. Инварианты AGENTS: цены из JSON, обязательные поля ответа в `_assert_js`, scope без JSON/прод-копии.

**Критерии приёмки (прод-копия):** пункты про черновик, POST на копии и GET-ссылку не закрыты — по scope и отчёту Implementer дубль намеренно отложен до выкатки API с `is_cut_milling`; не блокер ревью git.

**Замечания:** `желательно` — перед слиянием закоммитить diff в `task/form-hashtags` (сейчас только рабочее дерево).

## Найдено вне scope

- `scripts/run_js_calc.mjs` не грузит `calcMilling.js` и `milling.json`: стоковый раннер на дефолте формы 51 падает с `insaincalc.calcMilling is not a function`. Скрипт не менялся. Эталон снят тем же раннером с этими двумя файлами.

## Результат

- Ветка, PR или коммит: `task/form-hashtags`, worktree `D:\Projects\insain-agent-form-hashtags`, коммита нет
- Период: 29.11.2026
- Часы человека: —
- Работа агентов: Implementer, Grok 4.7
- Было / стало: боевая форма 51 считает `insaincalc.calcTablets`; в git у `tablets.js` появился блок `/* form 51 */`, дефолт (ПВХ 5 мм, фреза) считается через `MillingCalculator`. Боевая страница не менялась.
- Сделано: развилка по полю `inpText` (не по id копии). Дефолт формы 51: тираж 1, 1000×100, материал `PVC5`, текст `#хештег` (условный `select_option` ставит `isCutMilling`), без УФ, mode 1. Длина реза `(100 + 1000/7) * 2 * 7 * 1.3 = 4420`. `REF_FORM51_DEFAULT` и режимы 0/1/2. Эталоны форм 36 и 48 не сдвигались. Id 1339 и 1924 на месте.
- Чем проверено: `python scripts/dev.py check` — 933 passed, затем 81 passed, код 0. До этого `python -m pytest calc_service/tests/test_calculators/test_tablets.py calc_service/tests/test_wp_plugin_forms.py calc_service/tests/test_js_port_gaps.py -q` — 97 passed. Стоковый раннер на дефолте: `insaincalc.calcMilling is not a function`. Боевой `POST /api/v1/calc/tablets` с `is_cut_milling` len_cut 4420 — `price` 0 (ветки на проде нет). `curl` страницы хештегов: в HTML есть `calcTablets`, нет `calcApi`.
- Не сделано и почему: дубль формы, JS копии и отладка на копии — Site ops, шаги 6–16. Копию не создавать, пока эта ветка не выкатана: боевой API без `is_cut_milling` отдаёт 0, дефолт с JS не сойдётся (шаг 3 skill). Плагин не выкладывался, боевая 51 не переключалась. `docs/site/forms.md`, `docs/js-runner-cases.md`, `todo/forms-batch-switch.md` не правились.
- Требуется решение: нет. После приёмки diff — слияние в `main`, выкатка API, затем Site ops (дубль формы 51).
- Для Reviewer: id `get_value_from` боевого `cjsCalc` (2100, 2101, 2148, 2102, 2106, 2109, 2111, 2099, 2143) совпали с элементами формы 51. Чужих id нет.
- URL-only и не в API: `fluAtrwork` (файл, в URL не кладётся), `Set` (служебный). `inpText` на цену влияет, в API уходит уже как `is_cut_milling.len_cut`, в URL пишется текстом.
- Строка будущего боевого пакета (в текущий `forms-batch-switch` не добавлять; копии ещё нет): `| 51 CalcHashtags | tablets | /catalog/kalkulyator-heshtegov/ | копия не создана | form-hashtags |`
- Дописка `docs/js-runner-cases.md`: `| calcTablets form 51 default | tablets | 1944 |`. Команда (стоковый раннер падает, пока в него не подключены `calcMilling.js` и `milling.json`): `node scripts/run_js_calc.mjs calcTablets --data current --args '[1,[1000,100],"PVC5",{"isCutMilling":{"sizeItem":100,"density":0,"difficulty":1,"lenCut":4420}},1]'`. Режимы того же входа: mode 0 — price 1544, time_ready 72; mode 1 — 1944 и 56.1; mode 2 — 2668.9071642857148 и 40.2. Цена на странице после `showResult` при тираже 1 — 1944.

```text
Reviewer. todo/form-hashtags.md, ветка task/form-hashtags

Рабочая папка: D:\Projects\insain-agent-form-hashtags. Основную папку D:\Projects\insain-agent на main не трогай. Общие файлы (docs/site/forms.md, todo/EPIC-*.md, todo/forms-batch-switch.md, docs/js-runner-cases.md, STATUS.md, BACKLOG.md) не правь.

Прочитай и выполняй только роль Reviewer: D:\Projects\insain-agent-form-hashtags\docs\agents\roles\reviewer.md. Задача: D:\Projects\insain-agent-form-hashtags\todo\form-hashtags.md. Модель сессии — из поля Reviewer.

Смотри diff ветки task/form-hashtags: блок /* form 51 */ в wp-plugin/forms/tablets.js, порт is_cut_milling через MillingCalculator в tablets.py, константа REF_FORM51_DEFAULT. Эталоны форм 36 и 48 не сдвигать. Копию на проде не создавать: боевой POST дефолта сейчас price 0, дубль — после выкатки API с main.
```
