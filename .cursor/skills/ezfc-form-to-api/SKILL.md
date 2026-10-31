---
name: ezfc-form-to-api
description: Перевод одной формы ezFC на сайте insain.ru со старого JS (insaincalc.calcXxx) на расчёт через API — insaincalc.calcApi и insaincalc.showResult. Порядок — сверка расчётов, дубль формы на черновик или приватный товар, отладка копии на боевом API, затем то же на боевой форме через read_file и forms/<slug>.js в плагине. Применять, когда калькулятор формы уже есть в calc_service и выкачен на прод.
---

# Перевод формы ezFC на API

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.

Дубль формы и переключение боевой формы — вне списка «Делай самостоятельно» в .cursor/rules/insain-site-autonomous.mdc: перед ними спросить человека.

Одна форма за проход. Обозначения: `<id>` — id боевой формы, `<slug>` — калькулятор API, `<copy>` — id копии формы, `<product>` — id товара с копией. Реестр форм и страниц — `docs/site/forms.md`. Как собирать поля и вызывать API — `docs/ezfc-api-migration.md`.

Запросы к базе ezFC. В Windows PowerShell 5.1 кавычки внутри аргумента `ssh` теряются, поэтому SQL идёт файлом:

```powershell
Set-Content -Encoding ascii -Path $env:TEMP\ezfc.sql -Value "<SQL>"
scp $env:TEMP\ezfc.sql insain-prod:/tmp/ezfc.sql
ssh insain-prod "sudo -u www-data wp db query --skip-column-names --path=/var/www/insain.ru < /tmp/ezfc.sql 2>/dev/null"
```

Ниже «SQL через файл» — эти три команды с нужным `<SQL>`. Только `SELECT`. Запись в таблицы `wp_insain_ezfc_*` идёт через админку ezFC (Browser MCP), не SQL.

## Сверка до перевода

Сверка скриптом scripts/run_js_calc.mjs и эталонами в calc_service/tests/test_calculators/ делается до перевода и не заменяет дубль, отладку на боевом API и переключение боевой формы.

0. Порт полон: `python scripts/js_port_gaps.py <calcX>` для JS-функции калькулятора формы печатает её и всю цепочку вызовов. Если строка `нет в Python` хоть в одном блоке не пустая и этот пропуск не записан в «не перенесено» (docstring модуля и файл допустимых пропусков рядом со скриптом) — стоп, порт не полон, форму не переводить.

1. Эталоны калькулятора зелёные локально:

   ```powershell
   python -m pytest calc_service/tests/test_calculators/test_<slug>.py -q
   ```

   Ожидается: `passed`, `failed` нет. Выбрать один эталон с тиражом ≥ 2 — его вход и `price` нужны в шагах 3, 13 и 20.

2. Если калькулятор подключён в `scripts/run_js_calc.mjs` (сейчас только `calcPlaque`), старый JS на том же входе даёт ту же цену. В PowerShell 5.1 кавычки JSON экранируются `\"`:

   ```powershell
   node scripts/run_js_calc.mjs calcPlaque --data current --params '{\"quantity\":2,\"plaque_id\":\"Plaque2330\",\"material_id\":\"PVC3\",\"application\":\"isUVPrint\",\"mode\":1}'
   ```

   Ожидается: `price` равна эталону из шага 1 (допуск 0.02). Не подключён — сверка только эталонами из теста; новый кейс в скрипт ради перевода формы не добавлять.

3. Боевой API отдаёт тот же эталон:

   ```powershell
   Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/<slug> -ContentType 'application/json' -Body '<json входа эталона>' | Select-Object cost, price, unit_price
   ```

   Ожидается: `price` равна эталону (допуск 0.02). Другое число или 404 — стоп: калькулятор на проде не тот (выкатка — `bash infra/deploy.sh` с `main`), форму не дублировать и не переключать.

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

## Дубль формы

Спросить человека: дубль формы `<id>` и черновик товара для него. Без ответа «да» дальше не идти.

6. В админке ezFC (Browser MCP) у формы `<id>` — «Duplicate». Id копии, SQL через файл:

   ```sql
   SELECT id, name FROM wp_insain_ezfc_forms ORDER BY id DESC LIMIT 1;
   ```

   Ожидается: новая строка с именем формы-источника — это `<copy>`.

7. Товар для копии: черновик или приватный товар, который видит только админ. В админке WooCommerce у товара с боевой формой — «Копировать» (создаётся черновик), затем форма копии на него:

   ```powershell
   ssh insain-prod "sudo -u www-data wp post meta update <product> ezfc_form_id <copy> --path=/var/www/insain.ru"
   ssh insain-prod "sudo -u www-data wp post get <product> --field=post_status --path=/var/www/insain.ru"
   ```

   Ожидается: `Success: Updated custom field 'ezfc_form_id'.` и `draft` (или `private`). Статус `publish` — сразу вернуть в черновик, копия не должна быть видна покупателям.

8. Гость копию не видит:

   ```powershell
   curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=<product>"
   ```

   Ожидается: `404`. `200` — товар открыт гостям, стоп, вернуть статус шага 7.

9. Id копии. Шаг 5 с `f_id = <copy>`.

   У копии свои id элементов. Ссылки `get_value_from(N)` в старом JS копии указывают на элементы боевой формы — этот JS в копии не отлаживать. Сопоставить id боевой формы и копии по `name`.

10. JS формы по шаблону `cjsCalc` из `docs/ezfc-api-migration.md`: чтение полей (`{{numN}}`, `ezfc_functions.get_value_from`), `insaincalc.syncUrl`, затем `insaincalc.calcApi('<slug>', {…})`, в `.then` — `insaincalc.showResult(calcCost, qty, __form_id__)`, в `.catch` — `insaincalc.showError`. Формул цены, чтения через DOM и своего вывода цены в JS нет.

    Источник правды — `wp-plugin/forms/<slug>.js` в ветке задачи, с id **боевой** формы. Для копии — тот же текст с id копии по таблице шага 9; он вставляется в элемент расчёта копии в админке как обычный custom JS, без `read_file`.

    ```powershell
    Select-String -Path wp-plugin\forms\<slug>.js -Pattern "insaincalc.calcApi\('<slug>'|insaincalc.showResult|get_value_from\(\d+"
    ```

    Ожидается: вызов `calcApi('<slug>'`, `showResult` и только id боевой формы из шага 5.

## Отладка на боевом API

Копия ходит в боевой API `https://insain.ru/api/v1`: `apiBase` плагина — `/api/v1` на том же домене. Тестовый контейнер API не поднимать.

11. Открыть черновик под админом (Browser MCP): `https://insain.ru/?post_type=product&p=<product>&preview=true`.

12. Network и консоль. Ожидается: `POST https://insain.ru/api/v1/calc/<slug>` — 200; в теле запроса коды материалов из `data-value`, а не `0`; в консоли нет ошибок `insaincalc` и `ezfc`.

13. Ввести вход эталона из шага 1. Ожидается: цена на странице равна `price` эталона (с учётом округления вывода), есть вес, срок с подсказкой дат, таблица материалов без внутренних `code`.

14. Поведение формы по чеклисту `docs/ezfc-api-migration.md`: смена каждого dropdown меняет цену и материалы; URL обновляется GET-именами формы; перезагрузка страницы не меняет режим и срок.

15. Нашлась ошибка — правка в `wp-plugin/forms/<slug>.js` (id боевой формы), затем тот же текст с id копии снова в копию, шаги 12–14 заново. Правка, сделанная только в админке копии, в git не попадает и считается потерянной.

16. Записать в отчёт: `<copy>`, `<product>`, `post_status`, код шага 8, `price` из шага 13.

## Боевая форма

После отладки копии — то же на боевой форме. id элементов боевой формы не менять: ни дубля, ни импорта, ни пересоздания элементов. Меняется одна настройка у элемента расчёта — `read_file`.

Боевую форму из снимка не импортировать.

17. Git до прода. Diff `wp-plugin/forms/<slug>.js` прошёл ревью человека, `python scripts/dev.py check` зелёный, ветка смёржена в `main`. Затем плагин выкладывается по skill `deploy-wp-plugin`; в архиве есть `forms/<slug>.js`. Проверка на сервере:

    ```powershell
    ssh insain-prod "ls -l /var/www/insain.ru/wp-content/plugins/insain-calc-bridge/forms/<slug>.js"
    ```

    Ожидается: файл есть. Боевая форма пока считает старым JS — файл без `read_file` ни на что не влияет.

Спросить человека: переключение боевой формы `<id>` на `forms/<slug>.js`. Без ответа «да» дальше не идти.

18. В админке ezFC (Browser MCP), форма `<id>`, элемент расчёта из шага 5: включить `read_file` (`custom_calculation_function_read_file` = 1), путь `custom_calculation_function_filename`:

    ```text
    {{abspath}}wp-content/plugins/insain-calc-bridge/forms/<slug>.js
    ```

    Сохранить форму. Старый JS в поле элемента не стирать: это откат. Других полей и элементов не трогать. Проверка, SQL через файл:

    ```sql
    SELECT id, JSON_EXTRACT(data, '$.custom_calculation_function_read_file') AS rf, JSON_UNQUOTE(JSON_EXTRACT(data, '$.custom_calculation_function_filename')) AS fn FROM wp_insain_ezfc_forms_elements WHERE f_id = <id> AND data LIKE '%custom_calculation_function%';
    ```

    Ожидается: id элемента расчёта из шага 5, `rf` = `1` (или `"1"`), `fn` — путь выше. Повторить шаг 5: тот же список id, что до переключения.

19. Сброс кэша:

    ```powershell
    ssh insain-prod "sudo -u www-data wp litespeed-purge all --path=/var/www/insain.ru"
    ```

    Ожидается: `Success`.

20. Боевая страница (Browser MCP), шаги 12–14 на ней. Ожидается: `POST /api/v1/calc/<slug>` — 200, цена на входе эталона равна цене копии из шага 16. Гостем:

    ```powershell
    curl.exe -s https://insain.ru/<путь страницы>/ | Select-String -SimpleMatch "calcApi('<slug>'"
    ```

    Ожидается: строка с вызовом `calcApi('<slug>'`.

21. Снимок в `site/forms/<id>.json`. SQL через файл, но ответ сохраняется на сервере и забирается `scp` (вывод в консоль PowerShell портит кириллицу):

    ```powershell
    Set-Content -Encoding ascii -Path $env:TEMP\ezfc.sql -Value "SELECT JSON_OBJECT('form', (SELECT JSON_OBJECT('id', id, 'name', name, 'data', data) FROM wp_insain_ezfc_forms WHERE id = <id>), 'elements', (SELECT JSON_ARRAYAGG(JSON_OBJECT('id', id, 'e_id', e_id, 'position', position, 'data', data)) FROM wp_insain_ezfc_forms_elements WHERE f_id = <id>), 'options', (SELECT JSON_ARRAYAGG(JSON_OBJECT('o_id', o_id, 'value', value)) FROM wp_insain_ezfc_forms_options WHERE f_id = <id>));"
    scp $env:TEMP\ezfc.sql insain-prod:/tmp/ezfc.sql
    ssh insain-prod "sudo -u www-data wp db query --raw --skip-column-names --path=/var/www/insain.ru < /tmp/ezfc.sql 2>/dev/null | grep '^{' > /tmp/ezfc-form-<id>.json; wc -c /tmp/ezfc-form-<id>.json"
    New-Item -ItemType Directory -Force site\forms | Out-Null
    scp insain-prod:/tmp/ezfc-form-<id>.json site/forms/<id>.json
    ```

    `--raw` обязателен: без него mysql-клиент удваивает обратные слэши и JSON ломается. Ожидается: `wc -c` больше нуля, файл скачан.

22. Снимок читаемый и стабильный для diff: вложенные JSON-строки `data` раскрываются, элементы сортируются по `position`. Блок копируется без отступов: `'@` должен стоять в начале строки.

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
@'
import json
from pathlib import Path
p = Path("site/forms/<id>.json")
snap = json.loads(p.read_text(encoding="utf-8"))
def inner(v):
    try:
        return json.loads(v) if isinstance(v, str) else v
    except ValueError:
        return v
snap["form"]["data"] = inner(snap["form"]["data"])
for el in snap["elements"]:
    el["data"] = inner(el["data"])
snap["elements"].sort(key=lambda e: (int(e["position"]), int(e["id"])))
snap["options"].sort(key=lambda o: int(o["o_id"]))
text = json.dumps(snap, ensure_ascii=False, indent=2) + "\n"
p.write_text(text, encoding="utf-8")
print(len(snap["elements"]), len(snap["options"]), "forms/<slug>.js" in text, "custom_calculation_function_read_file" in text)
'@ | python -
```

    Ожидается: число элементов, число опций, `True True`. `$OutputEncoding` нужен, иначе PowerShell 5.1 отдаёт Python кириллицу как `???`.

23. Реестр `docs/site/forms.md`. Одна форма бывает на нескольких товарах (61 — на трёх, 64 — на двух), и `read_file` переключает их все. Поэтому slug `<slug>` и статус «API через `insaincalc.calcApi`» ставятся во всех строках с формой `<id>`, остальные строки не трогать. Затем раздел «Итог» пересчитывается по таблице, не прибавлением единицы:

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
@'
from pathlib import Path
import re
rows = []
for line in Path("docs/site/forms.md").read_text(encoding="utf-8").splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 4 and re.match(r"\d+ \S", c[1]):
        rows.append((c[0], c[1].split()[0], c[2], c[3]))
groups = [("API через `insaincalc.calcApi`", "API"), ("старый JS `insaincalc.calc…`", "старый JS"), ("не калькулятор", "не калькулятор")]
for title, pref in groups:
    g = [r for r in rows if r[3].startswith(pref)]
    print(f"| {title} | {len({r[1] for r in g})} | {sum(r[0].startswith('http') for r in g)} |")
print("Форм ezFC:", len({r[1] for r in rows}), "Опубликованных товаров с формой:", sum(r[0].startswith("http") for r in rows))
old = [r for r in rows if r[3].startswith("старый JS")]
print("Непереведённых форм:", len({r[1] for r in old}), "на опубликованных товарах:", len({r[1] for r in old if r[0].startswith("http")}))
print("slug через calcApi:", sorted({r[2] for r in rows if r[3].startswith("API")}))
'@ | python -
```

    Ожидается: три строки таблицы «Итог» (форм — число разных id формы, страниц — число строк с URL), всего форм и товаров без изменений, число непереведённых форм и список slug через `calcApi` с `<slug>`. Эти числа переносятся в таблицу «Итог», в абзацы «Непереведённых форм», «К форме через `calcApi` привязан…» и «Не привязаны ни к одной форме» (из последнего списка убрать `<slug>`, число в скобках — длина оставшегося списка). Всего форм или товаров изменилось — значит, правка задела чужие строки. Коммит снимка и реестра — по просьбе человека.

24. Копия. Форма `<copy>` и черновик `<product>` больше не нужны; удаление — только с подтверждения человека. Без подтверждения оставить черновиком и записать id в отчёт.

Откат боевой формы: в админке ezFC у элемента расчёта выключить `read_file`, сохранить, шаг 19. Форма снова считает старым JS из поля элемента. Плагин и файл `forms/<slug>.js` при этом не трогать.

Отчёт: вывод шагов 3, 8, 16, 18, 20, 22; коммиты; что осталось на сайте (копия, черновик); как откатить.
