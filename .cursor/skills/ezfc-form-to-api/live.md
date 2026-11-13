# Боевая форма (шаги 17–24)

Часть skill `ezfc-form-to-api`: общие правила, «SQL через файл» и роли — в `SKILL.md`.

## Боевая форма

После отладки копии — то же на боевой форме. id элементов боевой формы не менять: ни дубля, ни импорта, ни пересоздания элементов. Меняется одна настройка у элемента расчёта — `read_file`.

Боевую форму из снимка не импортировать.

17. Git до прода. Diff `wp-plugin/forms/<slug>.js` прошёл ревью человека, `python scripts/dev.py check` зелёный, ветка смёржена в `main`. Затем плагин выкладывается по skill `deploy-wp-plugin`; в архиве есть `forms/<slug>.js`. Проверка на сервере:

    ```powershell
    ssh insain-prod "ls -l /var/www/insain.ru/wp-content/plugins/insain-calc-bridge/forms/<slug>.js"
    ```

    Ожидается: файл есть. Боевая форма пока считает старым JS — файл без `read_file` ни на что не влияет.

Запросить подтверждение переключения боевой формы `<id>` на `forms/<slug>.js` через `AskQuestion` (готовые варианты: «Переключить форму и проверить (Рекомендуется)» / «Отложить переключение»). Без подтверждения дальше не идти.

18. В админке ezFC (Browser MCP), форма `<id>`. Сначала тот же блок результата, что уже на копии и у формы 79 (раздел «Блок результата» в `docs/ezfc-api-migration.md`): группы цены, срока и материалов. Id полей ввода не менять, форму не импортировать. До `read_file` — флаги цены, SQL через файл, `f_id` = `<id>`:

```sql
SELECT JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) AS name,
  JSON_UNQUOTE(JSON_EXTRACT(data, '$.hidden')) AS hidden,
  JSON_UNQUOTE(JSON_EXTRACT(data, '$.calculate_when_hidden')) AS calc_hidden
FROM wp_insain_ezfc_forms_elements
WHERE f_id = <id>
  AND JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) IN
  ('sbtPriceTotalManager','sbtPriceManager','sbtPriceTotalDiscount','sbtPriceDiscount');
```

Ожидается: у `sbtPriceTotalDiscount` и `sbtPriceDiscount` `hidden` = 1 и `calc_hidden` = 1; у менеджерских полей `hidden` = 0. У скидки `calc_hidden` не 1 — стоп, включить «считать, когда скрыто». Затем у элемента расчёта из шага 5 включить `read_file` (`custom_calculation_function_read_file` = 1), путь `custom_calculation_function_filename`:

    ```text
    {{abspath}}wp-content/plugins/insain-calc-bridge/forms/<slug>.js
    ```

    Сохранить форму. Старый JS в поле элемента не стирать: это откат. Поля ввода не трогать. Проверка, SQL через файл:

    ```sql
    SELECT id, JSON_EXTRACT(data, '$.custom_calculation_function_read_file') AS rf, JSON_UNQUOTE(JSON_EXTRACT(data, '$.custom_calculation_function_filename')) AS fn FROM wp_insain_ezfc_forms_elements WHERE f_id = <id> AND data LIKE '%custom_calculation_function%';
    ```

    Ожидается: id элемента расчёта из шага 5, `rf` = `1` (или `"1"`), `fn` — путь выше. Повторить шаг 5 для полей ввода: их id те же. Новый id допустим у добавленного `htmMaterial`, если такого элемента не было.

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
