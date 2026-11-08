# form-rollup

Статус: выкатка
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: типовая форма серии по skill `ezfc-form-to-api`, калькулятор уже на API; прод — только копия формы по шагам skill.
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
- Эталон: `REF_PARAMS` в `calc_service/tests/test_calculators/test_rollup.py` — тираж 1, `Rollup_econom_85`, `ScrollPaper200`, mode 1. Порог — раннер против локального Python, `rel=0.001`. Сверка с боевым API — после выкатки API. Тираж ≥ 2 не добавлять. Дефолт формы (без постера) — `REF_FORM_DEFAULT`. JS: `js_legacy/calc/calcRollup.js`, сигнатура `calcRollup(n, rollupID, materialID, options, modeProduction)`.
- Остальное не открывать.

## Решение человека (09.11.2026)

Явное указание: Analyst не нужен, scope расширен на `calc_service/calculators/rollup.py` и его тест.

- Полчаса установки — только при непустом материале постера, как в JS. Окончательно.
- Печать для сверки считать как в JS (в `calcPrintRoll` всегда mode 1), затем вернуть `mode.value`. Окончательно в печать уходит режим роллапа. Отличие mode 2 от старого JS — осознанное, в «Требуется решение» не выносить.
- Эталон сменить на `ScrollPaper200`.

## Scope

- Раннер готов (`js-runner-forms` закрыта 05.11.2026). Кейс и команда раннера — из `docs/js-runner-cases.md`. `calc_service/data/` не менять.
- `calc_service/calculators/rollup.py`: полчаса установки только при непустом постере; в печать передаётся `mode.value`.
- Эталон в `test_rollup.py` переснять раннером: `ScrollPaper200`, mode 1, пометка `JS, ДД.ММ.ГГГГ`, допуск `rel=0.001`. Дефолт без постера — отдельный кейс `REF_FORM_DEFAULT` (срок как в JS). Тираж ≥ 2 не добавлять.
- `wp-plugin/forms/rollup.js`: id элементов боевой формы 49, `insaincalc.syncUrl`, `insaincalc.calcApi('rollup'`, `insaincalc.showResult`. Своих формул цены и чтения через DOM нет.
- Дубль формы и черновик товара — после выкатки API и «да» человека. До выкатки дефолт без постера на боевом API ещё со старым сроком, копию не дублировать. На копию — тот же JS с id копии, без `read_file`.
- GET на копии: имя параметра = имя элемента. Боевую форму не размечать.
- Прогон копии под админом: эталон тиража 1, смена полей, ссылка с GET.
- После принятия копии человеком — одна строка в таблицу «Состав пакета» `todo/forms-batch-switch.md`. Ветка `task/form-rollup` от `main`.

Распределение: сверку эталона, `test_rollup.py`, `wp-plugin/forms/rollup.js` и строку в `todo/forms-batch-switch.md` делает Implementer. Дубль и черновик товара, JS и GET на копии, прогон под админом — Site ops; расхождение на копии возвращается Implementer.

## Файлы

- `calc_service/calculators/rollup.py`
- `wp-plugin/forms/rollup.js`
- `calc_service/tests/test_calculators/test_rollup.py`
- `docs/js-runner-cases.md` — команда и `price` эталона `ScrollPaper200` и дефолта без постера
- `todo/forms-batch-switch.md` — общий для задач эпика: одна строка в «Состав пакета» после принятия копии
- WordPress: только копия формы и черновик товара

## Не-scope

- `read_file` и любое переключение боевой формы 49. Выкладка плагина. `infra/deploy.sh`.
- `docs/site/forms.md`, `site/forms/49.json`.
- Цены, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`, `scripts/run_js_calc.mjs`. Выкатка API (`infra/deploy.sh`, skill `deploy-api`) — после merge в `main`, не в сессии Implementer.
- Новый эталон с тиражом ≥ 2.
- Удаление копии и черновика.
- Остальные формы эпика — свои задачи.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `COPY` и `PRODUCT` — id копии и черновика из отчёта. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`, как в skill.

- [x] Порт. В блоке `calcRollup` строка `нет в Python:` пустая или каждая позиция уже есть в `scripts/js_port_gaps_allowed.txt`.

```powershell
python scripts/js_port_gaps.py calcRollup
```

- [x] Раннер эталона (тираж 1, `ScrollPaper200`, mode 1) печатает `price` 7910 и `time_ready` 24.95. Дефолт без постера: `price` 4482, `time_hours` 0, `time_ready` 24. Сверка с боевым API — после выкатки, форму до неё не дублировать.

```powershell
node scripts/run_js_calc.mjs calcRollup --data current --args '[1,\"Rollup_econom_85\",\"ScrollPaper200\",{},1]'
node scripts/run_js_calc.mjs calcRollup --data current --args '[1,\"Rollup_econom_85\",\"\",{},1]'
```

- [x] Эталон в `test_rollup.py` переснят с этого прогона: комментарий `# JS, 09.11.2026` и вызов раннера рядом с эталоном, в docstring та же пометка, `price` в `EXPECTED_*` равен цене раннера, допуск assert — `rel=0.001`. Stdout: `passed`, `failed` нет. Эталон mode 1 и дефолт без постера сходятся с раннером. Режим 2 с постером с JS не сходится — решение человека, не стоп.

```powershell
python -m pytest calc_service/tests/test_calculators/test_rollup.py -q
```

- [x] Файл формы. В выводе есть `insaincalc.calcApi('rollup'`, `insaincalc.syncUrl(` и `insaincalc.showResult(`.

```powershell
Select-String -Path wp-plugin\forms\rollup.js -Pattern "calcApi\('rollup'|syncUrl\(|showResult\("
```

- [x] Контракт всех `forms/*.js`. Stdout: `passed`.

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

- [x] `python scripts/dev.py check` — код выхода 0
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль и GET только с подтверждения человека. Боевая страница клиентам не меняется.
- Цены: JSON не править. Чужой `price` на проде не выравнивать. Режим 2 в печать — `mode.value`, не выравнивать под старый JS. Боевой API до выкатки на дефолте без постера отдаёт старый срок (`time_ready` 24.5).
- Формы: id элементов боевой формы 49 не менять. В админке пишется только копия.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

2026-11-09 — Implementer, Grok 4.7 — эталон mode 1 с баннером сошёлся, дефолт формы и режим 2 расходятся со старым JS; калькулятор и плагин не трогал — дальше аналитик

```
Блокер: порт calcRollup расходится с JS на дефолте боевой формы (пустой постер) по сроку и на режиме 2 по цене
Пробовал: раннер calcRollup и POST /api/v1/calc/rollup; вложенный calcPrintRoll на 850×2000 сходится с POST /api/v1/calc/print_roll на mode 1 и 2. Эталон задачи (тираж 1, Rollup_econom_85, BannerFronlitCoat400, mode 1): JS и API cost 5086, price 8321, time_hours 0.98, time_ready 24.98; проверка price — ok 8321 8321 0 0.0. Дефолт страницы (тот же роллап, material_id пустой, mode 1): price 4482 с обеих сторон, time_ready JS 24 / API 24.5 (rel 0.020), time_hours JS 0 / API 0.5. Режим 2 и ScrollPaper200 (единственный постер формы): price JS 7910 / API 8699. Режим 2 и BannerFronlitCoat400: price JS 8321 / API 9148. python scripts/js_port_gaps.py calcRollup — в блоке calcRollup строка «нет в Python» пустая.
Гипотеза: расхождение во внешнем calcRollup, не в печати. JS ставит costInstall.time = 0.5 только при непустом materialID (js_legacy/calc/calcRollup.js:34–37) и вызывает calcPrintRoll с modeProduction = 1 (строка 36). Python держит time_install = 0.5 всегда (calc_service/calculators/rollup.py:188) и передаёт в печать mode.value (строка 200).
Вопрос: предпосылка по skill port-fix-prerequisite или расширить scope form-rollup?
Следующая сессия: Analyst
```

2026-11-09 — Implementer, Grok 4.7 — полчаса установки только при постере, эталон ScrollPaper200 mode 1 сходится с JS, печать `mode.value` (режим 2 отличается от старого JS — решение человека 09.11.2026), `forms/rollup.js`; копию не дублировать до выкатки API — дальше Reviewer

2026-11-09 — Reviewer, Auto — принято по diff (rollup.py, test_rollup.py, rollup.js, js-runner-cases); копия и прод вне круга — дальше человек

## Ревью 1

- Вердикт: принято (git-часть; копия формы и прод в этот круг не входят).
- Калькулятор: установка 0.5 ч только с постером; в печать `mode.value`. Режим 2 отличается от старого JS — решение человека 09.11.2026.
- Эталон (тираж 1, `Rollup_econom_85`, `ScrollPaper200`, mode 1) и дефолт без постера сверены с раннером 09.11.2026, допуск `rel=0.001`.
- `forms/rollup.js` по шаблону API-форм, `test_wp_plugin_forms` зелёный.
- желательно: включить в коммит неотслеживаемый `wp-plugin/forms/rollup.js`.
- Чем проверено: `python scripts/js_port_gaps.py calcRollup` — «нет в Python» пусто; раннер эталона и дефолта совпал с `EXPECTED_*`; pytest `test_rollup.py` и `test_wp_plugin_forms.py` — 10 passed.

## Найдено вне scope

- В списках формы есть сочетания, которых нет в `calc_service/data/materials/presswall.json`: `Rollup_econom_150`, `Rollup_econom_200`, `Rollup_standart_200`. На цену эталона и дефолта не влияет.
- У элемента 2024 `options_source` — URL `http://vm-57d1b2fc.na4u.ru/calc/js/paper_test.json`. На странице в селекте значения `econom` / `standart` / `premium` из `data.options`.

## Результат

- Ветка, PR или коммит: `task/form-rollup` от `main`, коммита нет.
- Период: 2026-11-09
- Часы человека: не учтено
- Работа агентов: Implementer, Grok 4.7 — правка `rollup.py`, эталон, `forms/rollup.js`
- Было / стало: форма 49 на странице по-прежнему на `insaincalc.calcRollup`. Локальный расчёт: полчаса установки только при непустом постере; в печать уходит `mode.value`. Эталон — тираж 1, `Rollup_econom_85`, `ScrollPaper200`, mode 1, `price` 7910.
- Сделано: порт `calcRollup` без пропусков. Временная сверка печати mode 1 (как JS) против раннера: mode 1 и 2, с `ScrollPaper200` и без постера, `price` и `time_ready` rel 0. Затем в печать возвращён `mode.value`. `test_rollup.py` и `wp-plugin/forms/rollup.js` (id боевой формы 49: 2019, 2024, 2020, 2043, 2039, расчёт 2026). GET на копии, когда до неё дойдёт Site ops: `dpdRollup`, `dpdSize`, `dpdPoster` — index; `rdoModeProduction` — value.
- Чем проверено: раннер `--data current` — эталон `price` 7910, `time_ready` 24.95; дефолт без постера `price` 4482, `time_hours` 0, `time_ready` 24. Временная печать mode 1 против этого раннера (mode 1 и 2, с постером и без): `price` и `time_ready` rel 0. После возврата `mode.value` эталон mode 1 и дефолт без постера те же. `python scripts/js_port_gaps.py calcRollup` — в блоке `calcRollup` строка «нет в Python» пустая. `Select-String` по `rollup.js` — `calcApi`, `syncUrl`, `showResult`. `python -m pytest calc_service/tests/test_calculators/test_rollup.py calc_service/tests/test_wp_plugin_forms.py -q` — 10 passed. `python scripts/dev.py check` — код выхода 0 (539 passed, 81 passed).
- Не сделано и почему: строка в `todo/forms-batch-switch.md` — после принятия копии. Дубль формы, GET и прогон — Site ops, и только после выкатки API. Боевой API до выкатки на дефолте без постера ещё отдаёт старый срок (`time_hours` 0.5, `time_ready` 24.5). Эталон с постером и mode 1 этой правкой не сдвигается, но skill запрещает дубль, пока дефолт не сойдётся. Выкатка API — не этот шаг: нужен merge в `main` и skill `deploy-api`.
- Требуется решение: нет.
- Строка в «Состав пакета» `todo/forms-batch-switch.md` (id копии и товар — после принятия копии):

| 49 CalcRollup | `rollup` | /catalog/kalkulyator-rollapov/ | COPY / PRODUCT (draft) | todo/form-rollup.md |
