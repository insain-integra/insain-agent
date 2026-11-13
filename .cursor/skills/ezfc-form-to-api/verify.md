# Сверка до перевода (шаги 0–5б)

Часть skill `ezfc-form-to-api`: общие правила, «SQL через файл» и роли — в `SKILL.md`.

## Сверка до перевода

Сверка скриптом scripts/run_js_calc.mjs и эталонами в calc_service/tests/test_calculators/ делается до перевода и не заменяет дубль, отладку на боевом API и переключение боевой формы.

0. Порт полон: `python scripts/js_port_gaps.py <calcX>` для JS-функции калькулятора формы печатает её и всю цепочку вызовов. Если строка `нет в Python` хоть в одном блоке не пустая и этот пропуск не записан в «не перенесено» (docstring модуля и файл допустимых пропусков рядом со скриптом) — стоп, порт не полон, форму не переводить.

1. Эталоны калькулятора зелёные локально:

   ```powershell
   python -m pytest calc_service/tests/test_calculators/test_<slug>.py -q
   ```

   Ожидается: `passed`, `failed` нет. Выбрать один эталон с тиражом ≥ 2 — его вход и `price` нужны в шагах 3, 13 и 20. Эталон собран только из значений, которые есть в списках боевой формы (код материала есть в её dropdown) — иначе его не ввести на странице.

1а. Кейс дефолта формы. Вход — значения, с которыми открывается боевая страница (Browser MCP, только чтение) или `value` / выбранные опции элементов шага 5. Эталон с одной опцией прячет баги повторных вызовов: если форма повторяет операцию (несколько слоёв, УФ или лазер на каждом ряду, опции по рядам), кейс должен её повторять — дефолт без повтора дополняется вторым кейсом с повтором. Эталон — раннером (шаг 2), в `test_<slug>.py` как `REF_FORM_DEFAULT` / `EXPECTED_FORM_DEFAULT` с пометкой `# JS, ДД.ММ.ГГГГ`, assert `cost`, `price`, `time_hours`, `time_ready` с `rel=0.001`; команда раннера — строкой в `docs/js-runner-cases.md`. Наличие `REF_FORM_DEFAULT` проверяет `calc_service/tests/test_wp_plugin_forms.py`.

2. Если калькулятор подключён в `scripts/run_js_calc.mjs`, старый JS на том же входе даёт ту же цену. `calcPlaque` — по `--params`, остальные загруженные функции — по `--args` (JSON-массив позиционных аргументов). В PowerShell 5.1 кавычки JSON экранируются `\"`:

   ```powershell
   node scripts/run_js_calc.mjs calcPlaque --data current --params '{\"quantity\":2,\"plaque_id\":\"Plaque2330\",\"material_id\":\"PVC3\",\"application\":\"isUVPrint\",\"mode\":1}'
   node scripts/run_js_calc.mjs calcPrintInkJet --data current --args '[1,[297,420],1,\"4+0\",\"PaperSublimation128\",\"EPSONWF7610\",1]'
   ```

   Ожидается: `price` равна эталону из шага 1, `time_ready` — тоже (`rel ≤ 0.001`). Допуск цены: abs ≤ 0.02 или `rel ≤ 0.001` при одинаковом `insaincalc.round` вывода (решение 11.11.2026: 0.18 ₽ на 5976 при равной `cost`). Расхождение срока — такой же стоп, как цены, а не строка «вне scope». Не подключён — сверка только эталонами из теста; новый кейс в скрипт ради перевода формы не добавлять.

   Функция подключена, но раннер падает на части расчёта (пример: ламинация у `calcPennantPaper`, нет `laminat.json`) — эталон тем же вызовом `insaincalc.<calcX>(...)` в консоли боевой страницы (Browser MCP, только чтение), пометка `# JS страницы, ДД.ММ.ГГГГ`. `scripts/run_js_calc.mjs` в задаче формы не правится, пробел раннера — строка в «Найдено вне scope».

3. Боевой API отдаёт тот же эталон и кейс дефолта. Тело запроса — из `REF_*` теста, не набирать руками (`<REF>` — `REF_PARAMS`, `REF_FORM_DEFAULT`):

   ```powershell
   python -c "import sys,json; sys.path[:0]=['calc_service','calc_service/tests/test_calculators']; import test_<slug> as t; print(json.dumps(t.<REF>))" | Set-Content -Encoding ascii $env:TEMP\body.json
   Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/<slug> -ContentType 'application/json' -Body (Get-Content -Raw $env:TEMP\body.json) | Select-Object cost, price, unit_price, time_ready
   ```

   Ожидается: `price` равна раннеру (допуск шага 2), `time_ready` — `rel ≤ 0.001`, на обоих кейсах. `weight_kg` в цепочках `calcPrintSheet` с JS не сверяется: JS считает лист с обрезью, Python — изделие; верный вес и вес в эталоне — Python (решение 11.11.2026). Другое число или 404 — стоп:
   - если калькулятор ещё **не используется на боевых формах API** (`docs/site/forms.md`) — починить расхождение сразу в текущей ветке с эталоном из раннера и проверкой тестов соседей, без создания отдельной задачи-предпосылки;
   - если калькулятор **уже работает на боевой форме API** (или на проде старый код) — либо выкатка `bash infra/deploy.sh` с `main`, либо `заблокировано: аналитик` + задача-предпосылка по skill `port-fix-prerequisite`. Форму не дублировать до совпадения дефолта.

3а. Таблица материалов на кейсе дефолта. На боевой странице — `showMaterials` (Browser MCP, только чтение): имя, размер, количество. В ответе боевого API — `materials[].name`, `size_mm`, `quantity`.

   Ожидается: тот же состав, те же количества, у каждой строки с размером на боевой — `size_mm` в API (`showResult` берёт размер только оттуда). Порядок строк может отличаться. Нет `size_mm` или другой состав — стоп, как в шаге 3: предпосылка на калькулятор, `size_mm` в `forms/<slug>.js` не подставлять. Тот же класс, что уже закрытая соседняя задача (пример: `pennant-materials-size-mm`, `flag-materials-size-mm`) — в блокере Analyst указать образец; Analyst заводит быструю предпосылку по skill `port-fix-prerequisite`, раздел «Быстрый путь».

4. Параметры API:

   ```powershell
   Invoke-RestMethod https://insain.ru/api/v1/tool_schema/<slug> | ConvertTo-Json -Depth 8
   ```

   Ожидается: список параметров. Каждому параметру найдётся поле формы в шаге 5.

5. Поля боевой формы. SQL через файл:

   ```sql
   SELECT id, e_id, position, JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) AS name FROM wp_insain_ezfc_forms_elements WHERE f_id = <id> ORDER BY position;
   ```

   Ожидается: строки `id  e_id  position  name`. Выписать id и имена полей ввода и элемент расчёта (`cjsCalc`, тип custom calculation). Id не выдумывать.

5а. Поля формы и схема API. Сопоставить имена из шага 5 с параметрами шага 4.
   - Поле есть, параметра в API нет (материал заказчика, упаковка, поверхность и т. п.) — в `syncUrl` пишется, в `calcApi` не уходит. Список таких полей — в «Результат».
   - Параметр API обязателен, а поля нет — стоп: форма и калькулятор не сходятся, `заблокировано: аналитик`.

5б. Старый JS боевой формы. Выписать все `get_value_from(N)` из `cjsCalc` и сверить N с таблицей шага 5.
   - Id не того поля (пример: форма 85 читала «материал заказчика» из `ckbCliche` 3291 вместо 3311) — это баг боевого JS, запись в «Найдено вне scope».
   - Поле влияет на цену (уходит в `calcApi`) — стоп, `заблокировано: человек`: исправление меняет цену для клиентов. Не влияет — в `forms/<slug>.js` правильный id и строка «для Reviewer» в «Результат».
