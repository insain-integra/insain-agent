# pilot-plaque-form

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: прод и два контура сразу — git и WordPress.
Чат: человек открывает новый чат с моделью из поля Implementer, не с той, что уже открыта «под рукой».

## Цель

Форма 69 CalcPlaque на https://insain.ru/catalog/kalkulyator-nagradnyh-plaketok/ считает через `insaincalc.calcApi('plaque', …)`. Сначала сверка уже существующим скриптом, затем дубль формы на товар, который видит только админ, отладка этой копии на боевом API, затем то же на боевой форме. Если боевой API ещё не отдаёт эталон плакеток, форма остаётся на старом JS.

## Контекст и ссылки

- `todo/skills-recipes.md` и skills `.cursor/skills/ezfc-form-to-api/SKILL.md`, `.cursor/skills/deploy-wp-plugin/SKILL.md` — как делать. Начинать после их merge в `main`.
- `docs/ezfc-api-migration.md` — сбор полей, `calcApi`, `showResult`.
- `docs/site/access-tools.md` — «Принятый режим»: `read_file`, снимок `SELECT … --raw`, обратный импорт запрещён.
- `docs/site/forms.md` — строка формы 69 и сводные числа. Сейчас: старый JS `insaincalc.calcPlaque`, непереведённых 45.
- `calc_service/tests/test_calculators/test_plaque.py` — `REF_PARAMS` и `EXPECTED_REF`: quantity 2, Plaque2330, PVC3, isUVPrint, mode 1, `price` 6205.71. Пометка эталонов `JS, 29.10.2026`.
- `wp-plugin/js/insain-calc-bridge.js` — уже есть `insaincalc.calcApi` и `showResult`. Файл не читать целиком: сигнатура `calcApi(slug, params)`.
- `.cursor/rules/insain-site-autonomous.mdc` — целиком, до первого действия на сервере.
- `docs/refactoring-plan.md` — только пункт 5.5, когда дописывается приписка о прогоне.
- Остальное не открывать. `js_legacy/calc/calcTablets.js` целиком не читать: соответствие полей API берётся из `REF_PARAMS` и схемы, на которую ссылается миграция.

## Scope

Порядок жёсткий. Критерии про форму и плагин выполняются только после записанного в «Результат» вывода ворот и вывода по копии.

1. Ворота боевого API. Тело `{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}` на `POST https://insain.ru/api/v1/calc/plaque`. В ответе `price` равен 6205.71 (допуск 0.02). Другое число, в том числе прежнее расхождение около 4977, или нет slug — стоп: форму не дублировать, плагин не ставить, форму 69 не переключать. Локальные критерии 2 и 3 при стопе всё равно снять в отчёт.
2. До перевода ещё раз локальная сверка тем же скриптом и эталоном. Это проверка, что перенос уже сошёлся. Новые кейсы не писать и скрипт сверкой не подменять дубль.
3. `wp-plugin/forms/plaque.js`. Вызов дословно содержит `insaincalc.calcApi('plaque'`. Параметры API: `quantity`, `plaque_id`, `material_id`, `application`, `mode`. Дальше `insaincalc.showResult`. Id элементов формы снять с формы 69, не выдумывать. В JS нет формул цены.
4. Ревью человека на diff `plaque.js` — до деплоя плагина.
5. Деплой плагина по skill `deploy-wp-plugin` (это в списке «Делай самостоятельно»). Архив с коммита, который прошёл это ревью. В архиве есть `forms/plaque.js`. `infra/deploy.sh` не запускать.
6. Дубль формы 69 в админке ezFC. Копия на черновик или приватный товар, гость permalink копии не открывает. У копии свои id; `get_value_from` в JS копии совпадает с id копии. Перед дублем спросить человека: шаг вне списка «Делай самостоятельно».
7. Отладка копии на боевом API. В «Результат» до правки формы 69 записать: id формы-копии, id товара, `post_status`, код `curl.exe` без cookies на permalink копии, `price` расчёта на копии.
8. То же на боевой форме 69. У элемента расчёта один раз `custom_calculation_function_read_file` = 1 и путь `{{abspath}}wp-content/plugins/insain-calc-bridge/forms/plaque.js`. Id элементов формы 69 не менять. Снимок обратно не импортировать. Перед переключением снова спросить человека.
9. Снимок боевой формы в `site/forms/69.json` (`SELECT … --raw`, файл проходит `json.loads`). В снимке есть `forms/plaque.js` и `custom_calculation_function_read_file`.
10. `docs/site/forms.md`: строка страницы плакеток — slug `plaque`, статус API через `insaincalc.calcApi`, без «старый JS». Форма 69 — один опубликованный товар, поэтому ячейки таблицы итога: API `2` и `2`, старый JS `44` и `46`. Текст: непереведённых **44**, `43 из них на опубликованных товарах`. Строка про привязанные slug содержит `puzzle` и `plaque`. В строке «Не привязаны» — `36 из 38` и нет `plaque`. Другие строки форм не переписывать.
11. Одна строка в `wp-plugin/AGENTS.md`: custom JS переведённых форм лежит в `forms/<slug>.js`.
12. В пункте 5.5 `docs/refactoring-plan.md` дописать, не ставя чекбокс: `прогнаны на форме 69: ezfc-form-to-api, deploy-wp-plugin. new-calculator и json-price-rollout не прогонялись — чекбокс открыт.`

Git-файлы пишет Implementer. Дубль, деплой плагина, `read_file` и проверка страницы — Site ops. Оба чата открываются с моделью из поля Implementer.

## Не-scope

- Остальные формы из 45 непереведённых (после этой задачи их 44). Их строки в реестре не менять, кроме пересчёта сводки.
- Новый калькулятор «чтобы прогнать skill».
- Правка цен, любые файлы в `calc_service/data/`, `calc_service/calculators/plaque.py`, эталоны в `test_plaque.py`.
- Дубль сайта, тестовый контейнер API, `infra/deploy.sh`, пересборка `insain-calc-api`.
- Версия плагина 0.2.3 и `wp-plugin/js/insain-calc-bridge.js`: расчёт идёт через уже существующий `calcApi`.
- Обратный импорт `site/forms/69.json` в ezFC.
- Закрытие чекбокса 5.5 и правки других пунктов плана.

## Критерии приёмки

Команды из корня репозитория, если не сказано иначе. Критерии 4–8 не выполнять, пока критерий 1 не напечатал `6205.71`.

- [ ] Ворота прод-API. Stdout `6205.71`, код выхода 0. Иначе stdout начинается с `STOP` — форму не переключать.

```powershell
@'
import json, sys, urllib.request
payload = b'{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'
req = urllib.request.Request("https://insain.ru/api/v1/calc/plaque", data=payload, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        price = float(json.load(r)["price"])
except Exception as e:
    print("STOP", type(e).__name__, e)
    sys.exit(1)
if abs(price - 6205.71) >= 0.02:
    print("STOP", price)
    sys.exit(1)
print("6205.71")
'@ | python -
```

- [ ] Локальная сверка до перевода. В stdout JSON с `"price": 6205.71`, код выхода 0. Файлы `js_legacy/` и `calc_service/data/` не меняются.

```powershell
node scripts/run_js_calc.mjs calcPlaque --data current --params '{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'
```

- [ ] `python -m pytest calc_service/tests/test_calculators/test_plaque.py -q` — код выхода 0, в конце строка с `passed`.

- [ ] Файл формы в git. Stdout `ok`.

```powershell
@'
from pathlib import Path
t = Path("wp-plugin/forms/plaque.js").read_text(encoding="utf-8")
need = ["insaincalc.calcApi('plaque'", "insaincalc.showResult", "plaque_id", "material_id", "application"]
bad = [s for s in need if s not in t]
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [ ] Копия ещё не на витрине. Подставить id товара копии. Ожидается одна строка с `draft` или `private`, и код HTTP permalink без cookies не `200` (ожидаемо `404`).

```powershell
ssh insain-prod "sudo -u www-data wp post list --post_type=product --post_status=draft,private --fields=ID,post_status,post_name --meta_key=ezfc_form_id --meta_value=ID_КОПИИ --path=/var/www/insain.ru"
curl.exe -sS -o NUL -w "%{http_code}" "PERMALINK_КОПИИ"
```

- [ ] На сервере лежит JS из git. В stdout есть `insaincalc.calcApi('plaque'`.

```powershell
ssh insain-prod "grep calcApi /var/www/insain.ru/wp-content/plugins/insain-calc-bridge/forms/plaque.js"
```

- [ ] Боевая форма 69 читает файл плагина. В выводе шапка `id` и ровно одна строка с числом.

```powershell
ssh insain-prod 'sudo -u www-data wp db query --raw --path=/var/www/insain.ru "SELECT id FROM wp_insain_ezfc_forms_elements WHERE f_id=69 AND data LIKE ''%forms/plaque.js%'' AND data LIKE ''%custom_calculation_function_read_file%''"'
```

- [ ] Снимок, реестр, локальное правило плагина, приписка 5.5. Stdout `ok`.

```powershell
@'
import json
import re
from pathlib import Path
snap = Path("site/forms/69.json").read_text(encoding="utf-8")
json.loads(snap)
assert "forms/plaque.js" in snap
assert re.search(r'custom_calculation_function_read_file"\s*:\s*"?1', snap)
forms = Path("docs/site/forms.md").read_text(encoding="utf-8")
row = next(ln for ln in forms.splitlines() if "kalkulyator-nagradnyh-plaketok" in ln)
assert "| plaque |" in row and "calcApi" in row and "старый JS" not in row
assert "| API через `insaincalc.calcApi` | 2 | 2 |" in forms
assert "| старый JS `insaincalc.calc\u2026` | 44 | 46 |" in forms
assert "Непереведённых форм: **44**" in forms
assert "43 из них на опубликованных товарах" in forms
bound = next(ln for ln in forms.splitlines() if "slug" in ln and "puzzle" in ln)
assert "plaque" in bound
unbound = forms.split("Не привязаны", 1)[1].split("\n", 1)[0]
assert "plaque" not in unbound and "36 из 38" in unbound
plugin = Path("wp-plugin/AGENTS.md").read_text(encoding="utf-8")
assert "forms/<slug>.js" in plugin
plan = Path("docs/refactoring-plan.md").read_text(encoding="utf-8")
assert "- [ ] **5.5." in plan
note = "прогнаны на форме 69: ezfc-form-to-api, deploy-wp-plugin. new-calculator и json-price-rollout не прогонялись — чекбокс открыт."
assert note in plan
print("ok")
'@ | python -
```

- [ ] Витрина плакеток открывается. Stdout `200`.

```powershell
curl.exe -sS -o NUL -w "%{http_code}" "https://insain.ru/catalog/kalkulyator-nagradnyh-plaketok/"
```

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
- [ ] На копии под админом, затем на боевой странице, набор полей эталона (2 шт, Plaque2330, PVC3, УФ-печать, mode 1) даёт `POST /api/v1/calc/plaque` и `price` 6205.71. В «Чем проверено» — код ответа и `price` обоих прогонов. Боевую страницу открывать после записи блока «Копия до боевой формы» в «Результат».

## Риски

- Прод: страница каталога живая. Ворота — первая команда. Несовпадение `price` с 6205.71 — стоп, WordPress и плагин не трогать. Дубль и переключение формы 69 — с подтверждения человека. Деплой плагина откатывается повторной установкой zip предыдущего коммита плагина. API-контейнер не пересобирать.
- Цены: JSON не менять. Чужой `price` на проде не выравнивать правкой прайса.
- Формы: только 69 и одна её копия для админа. Id элементов формы 69 сохраняются. Снимок — история, не источник заливки.

## Режим

прод

## Результат

- Ветка, PR или коммит: `task/pilot-plaque-form` от `main`. Merge fast-forward после ревью. `git push` — спросить. SHA коммита, из которого собран zip плагина:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Как откатить:
