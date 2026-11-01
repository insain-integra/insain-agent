# pilot-plaque-form

Статус: в работе
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: прод и два контура сразу — git и WordPress.
Чат: человек открывает новый чат с моделью из поля Implementer, не с той, что уже открыта «под рукой».

## Цель

Форма 69 CalcPlaque на https://insain.ru/catalog/kalkulyator-nagradnyh-plaketok/ считает через `insaincalc.calcApi('plaque', …)`. Сначала сверка уже существующим скриптом, затем дубль формы на товар, который видит только админ, отладка этой копии на боевом API, затем то же на боевой форме.

## Контекст и ссылки

- Эпик `todo/EPIC-calc-port-structure.md` закрыт (`tablets-for-plaque`, `plaque-thin-wrapper` в `main`, прод-API выкачен). Форма 69 переводится со всеми нанесениями, включая сублимацию. Ворота API: УФ 6205.71, сублимация 4018.24 / 2564.31.
- Skills `.cursor/skills/ezfc-form-to-api/SKILL.md`, `.cursor/skills/deploy-wp-plugin/SKILL.md` — как делать.
- `docs/ezfc-api-migration.md` — сбор полей, `calcApi`, `showResult`.
- `docs/site/access-tools.md` — «Принятый режим»: `read_file`, снимок `SELECT … --raw`, обратный импорт запрещён.
- `docs/site/forms.md` — строка формы 69 и сводные числа. До переключения 69: старый JS `insaincalc.calcPlaque`, непереведённых **45**. После перевода — **44** (см. Scope п.10).
- `calc_service/tests/test_calculators/test_plaque.py` — `REF_PARAMS` / `EXPECTED_REF` (УФ PVC3 → 6205.71) и `SUBLIMATION_CASES` (AluminiumSU055 → 4018.24 / 2564.31).
- `wp-plugin/js/insain-calc-bridge.js` — уже есть `insaincalc.calcApi` и `showResult`. Файл не читать целиком: сигнатура `calcApi(slug, params)`.
- `.cursor/rules/insain-site-autonomous.mdc` — целиком, до первого действия на сервере.
- `docs/refactoring-plan.md` — только пункт 5.5, когда дописывается приписка о прогоне.
- Остальное не открывать. `js_legacy/calc/calcTablets.js` целиком не читать: соответствие полей API берётся из `REF_PARAMS` и схемы, на которую ссылается миграция.

## Scope

Порядок жёсткий. Критерии про форму и плагин выполняются только после записанного в «Результат» вывода ворот и вывода по копии с **тремя** нанесениями. Факт на 02.11.2026:

| # | Шаг | Статус |
| --- | --- | --- |
| 1 | Ворота прод-API (УФ 6205.71) | сделано |
| 2 | Локальная сверка JS эталона | сделано |
| 3 | `wp-plugin/forms/plaque.js` | сделано (в git и на проде) |
| 4 | Ревью человека на `plaque.js` | нужно перед переключением 69 |
| 5 | Деплой плагина | **не нужен**, пока `plaque.js` не меняется: на проде уже 0.2.4 и `forms/plaque.js` с `calcApi` |
| 6 | Дубль формы 69 → копия 86, товар 2586879 draft | сделано |
| 7 | Отладка копии на боевом API (УФ + гравировка + сублимация) | сделано (JS↔API + UI под админом) |
| 8–12 | Боевая 69, снимок, `forms.md`, `wp-plugin/AGENTS.md`, приписка 5.5 | **стоп** — ждёт подтверждения человека на переключение 69 |

1. Ворота боевого API. Тело `{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}` на `POST https://insain.ru/api/v1/calc/plaque`. В ответе `price` равен 6205.71 (допуск 0.02). Другое число или нет slug — стоп: форму 69 не переключать.
2. До перевода ещё раз локальная сверка тем же скриптом и эталоном. Новые кейсы не писать.
3. `wp-plugin/forms/plaque.js`. Вызов дословно содержит `insaincalc.calcApi('plaque'`. Параметры API: `quantity`, `plaque_id`, `material_id`, `application`, `mode`. Дальше `insaincalc.showResult`. Id — боевой формы 69. В JS нет формул цены.
4. Ревью человека на diff `plaque.js` — до деплоя плагина / переключения 69.
5. Деплой плагина по skill `deploy-wp-plugin` — только если `plaque.js` изменился относительно прода. `infra/deploy.sh` не запускать.
6. Дубль формы 69 (уже есть: 86 / 2586879). Перед новым дублем — спросить человека.
7. Отладка копии на боевом API. В «Результат» до правки формы 69: id копии, id товара, `post_status`, `curl` permalink, `price` по **трём** нанесениям формы (УФ, гравировка `isGrave`, сублимация) на материалах из списка формы, 1 и 2 шт., mode 1 (+ mode 2 хотя бы для одного). Сверка с `node scripts/run_js_calc.mjs calcPlaque …` (rel ≤ 0.001 + округление `showResult`). Расхождение больше допуска — стоп, форму 69 не трогать.
8. То же на боевой форме 69. `custom_calculation_function_read_file` = 1, путь `{{abspath}}wp-content/plugins/insain-calc-bridge/forms/plaque.js`. Id элементов 69 не менять. Перед переключением спросить человека.
9. Снимок боевой формы в `site/forms/69.json` (`SELECT … --raw`, `json.loads`). В снимке — `forms/plaque.js` и `custom_calculation_function_read_file`.
10. `docs/site/forms.md`: плакетки — slug `plaque`, API через `insaincalc.calcApi`. Итог: API `2`/`2`, старый JS `44`/`46`; непереведённых **44**, `43 из них на опубликованных товарах`; привязаны `puzzle` и `plaque`; «Не привязаны» — `36 из 38` без `plaque`.
11. Одна строка в `wp-plugin/AGENTS.md`: custom JS переведённых форм лежит в `forms/<slug>.js`.
12. В пункте 5.5 `docs/refactoring-plan.md` дописать, не ставя чекбокс: `прогнаны на форме 69: ezfc-form-to-api, deploy-wp-plugin. new-calculator и json-price-rollout не прогонялись — чекбокс открыт.`

Git-файлы пишет Implementer. Дубль, деплой плагина, `read_file` и проверка страницы — Site ops. Оба чата открываются с моделью из поля Implementer.

## Не-scope

- Остальные формы из 45 непереведённых (после этой задачи их 44). Их строки в реестре не менять, кроме пересчёта сводки.
- Новый калькулятор «чтобы прогнать skill».
- Правка цен, любые файлы в `calc_service/data/`, `calc_service/calculators/plaque.py`, эталоны в `test_plaque.py`.
- Дубль сайта, тестовый контейнер API, `infra/deploy.sh`, пересборка `insain-calc-api`.
- Версия плагина 0.2.4 и `wp-plugin/js/insain-calc-bridge.js`: расчёт идёт через уже существующий `calcApi`; без правки `plaque.js` повторный деплой не делать.
- Обратный импорт `site/forms/69.json` в ezFC.
- Закрытие чекбокса 5.5 и правки других пунктов плана.
- Чинить JS NaN на AcrylWhite3 + isSublimation (см. «Результат»).

## Критерии приёмки

Команды из корня репозитория, если не сказано иначе. Критерии 4–8 не выполнять, пока критерий 1 не напечатал `6205.71`.

- [x] Ворота прод-API. Stdout `6205.71`, код выхода 0. Иначе stdout начинается с `STOP` — форму не переключать.

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

- [x] Локальная сверка до перевода. В stdout JSON с `"price": 6205.71`, код выхода 0. Файлы `js_legacy/` и `calc_service/data/` не меняются.

```powershell
node scripts/run_js_calc.mjs calcPlaque --data current --params '{"quantity":2,"plaque_id":"Plaque2330","material_id":"PVC3","application":"isUVPrint","mode":1}'
```

- [x] `python -m pytest calc_service/tests/test_calculators/test_plaque.py -q` — код выхода 0, в конце строка с `passed`.

- [x] Файл формы в git. Stdout `ok`.

```powershell
@'
from pathlib import Path
t = Path("wp-plugin/forms/plaque.js").read_text(encoding="utf-8")
need = ["insaincalc.calcApi('plaque'", "insaincalc.showResult", "plaque_id", "material_id", "application"]
bad = [s for s in need if s not in t]
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [x] Копия ещё не на витрине. Подставить id товара копии. Ожидается одна строка с `draft` или `private`, и код HTTP permalink без cookies не `200` (ожидаемо `404`).

```powershell
ssh insain-prod "sudo -u www-data wp post list --post_type=product --post_status=draft,private --fields=ID,post_status,post_name --meta_key=ezfc_form_id --meta_value=ID_КОПИИ --path=/var/www/insain.ru"
curl.exe -sS -o NUL -w "%{http_code}" "PERMALINK_КОПИИ"
```

- [x] На сервере лежит JS из git. В stdout есть `insaincalc.calcApi('plaque'`.

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

- Ветка, PR или коммит: `task/pilot-plaque-form` (ff от `main` @ `86e9da1`, затем `8305045` + этот коммит). Merge fast-forward после ревью. `git push` — спросить. Zip плагина не собирали: на проде уже `insain-calc-bridge` **0.2.4**, `forms/plaque.js` с `calcApi('plaque'`.
- Сделано:
  - Ворота прод-API УФ: stdout `6205.71`, код 0.
  - Локальный JS эталон: `price` 6205.71. `pytest test_plaque.py` — 22 passed.
  - `plaque.js` в git: проверка `ok`.
  - **Копия до боевой формы:** форма `86`, товар `2586879`, `draft`, guest `https://insain.ru/?post_type=product&p=2586879` → `404`. Элемент 3321 — inline `calcApi` с id копии (3317/3318/3319/3334), `read_file` = 0. Боевая 69 — ещё старый `calcPlaque`. PVC3 в списке формы нет.
  - JS↔API (rel ≤ 0.001):

    | qty | material | application | mode | JS/API price |
    | --- | --- | --- | --- | --- |
    | 2 | AcrylWhite3 | isUVPrint | 1 | 6618.96 |
    | 1 | AcrylWhite3 | isUVPrint | 1 | 4367.26 |
    | 2 | AcrylWhite3 | isUVPrint | 2 | 6618.96 |
    | 2 | AcrylWhite3 | isGrave | 1 | 20637.56 |
    | 1 | AcrylWhite3 | isGrave | 1 | 10845.85 |
    | 2 | Plywood3 | isGrave | 1 | 20228.66 |
    | 2 | ZENOMARKLASER | isGrave | 1 | 20905.81 |
    | 2 | AluminiumSU055 | isSublimation | 1 | 4018.24 |
    | 1 | AluminiumSU055 | isSublimation | 1 | 2564.31 |
    | 2 | AluminiumSU055 | isSublimation | 2 | 4018.24 |

  - UI копии под админом (Browser MCP, preview), все POST `/api/v1/calc/plaque` → 200; цена на странице = API с округлением `showResult`; материалы без `code`:

    | qty | material | application | mode | тело POST | API price | на странице |
    | --- | --- | --- | --- | --- | --- | --- |
    | 2 | AcrylWhite3 | isUVPrint | 1 | да | 6618.96 | 6620; вес 1.37; «Срок 4 дня» |
    | 1 | AcrylWhite3 | isUVPrint | 2 | да | 4367.26 | 4400; «Срок 4 дня» |
    | 2 | AcrylWhite3 | isGrave | 1 | да | 20637.56 | 20640; «Срок 5 дней» |
    | 1 | AcrylWhite3 | isGrave | 1 | да | 10845.85 | 10900; «Срок 5 дней» |
    | 2 | AluminiumSU055 | isSublimation | 1 | да | 4018.24 | 4020; «Срок 2 дня» |
    | 1 | AluminiumSU055 | isSublimation | 1 | да | 2564.31 | 2600; «Срок 2 дня» |
    | 1 | AluminiumSU055 | isSublimation | 2 | да | 2564.31 | 2600 (mode 2 в теле; цена как mode 1 — thin wrapper) |

  - Известное расхождение (не чинить): JS `AcrylWhite3`+`isSublimation` → NaN; Python → 3605.49. Форма штатно пару не даёт (`hide_option` сублимации без `AluminiumSU055`).
- Чем проверено: ворота one-liner; `run_js_calc.mjs` + prod API; `pytest test_plaque.py`; Browser MCP Network на копии; `curl` guest 404 / витрина 200; плагин 0.2.4.
- Не сделано и почему:
  - Шаги 8–12 (read_file на 69, снимок, forms.md, AGENTS.md, приписка 5.5, `make check` сдачи) — ждут подтверждения человека.
  - Деплой плагина — не нужен без изменения `plaque.js`.
- Требуется решение:
  - Подтвердить переключение боевой формы **69** на `{{abspath}}wp-content/plugins/insain-calc-bridge/forms/plaque.js` (`read_file` = 1). После «да» — Site ops + git-шаги 9–12.
- Как откатить: форма 69 ещё на старом JS. После переключения — выключить `read_file` у элемента расчёта 69, сохранить, `wp litespeed-purge all`. Копия 86 / 2586879 — только с подтверждения.
