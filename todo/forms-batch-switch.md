# forms-batch-switch

Статус: черновик
Сложность: высокая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Opus 5.5
Почему: боевые формы переключаются впервые (шаги 17–24 skill `ezfc-form-to-api` ещё не прогнаны), пакетом; в git — снимок и реестр без конфликта данных.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Боевые формы ezFC, уже переведённые на `insaincalc.calcApi` на копиях, переключены на API одним пакетом по одному подтверждению человека. Первая в пакете — форма 69 CalcPlaque (страница https://insain.ru/catalog/kalkulyator-nagradnyh-plaketok/). Остальные формы добавляются в «Состав пакета» по мере закрытия их задач на перевод.

## Состав пакета

Заполняется по мере закрытия задач на перевод. Форма попадает в пакет, если её копия принята человеком, а `forms/<slug>.js` с `calcApi` и `syncUrl` в `main`.

| Форма | Slug API | Страница | Копия (форма / товар) | Задача на перевод |
| --- | --- | --- | --- | --- |
| 69 CalcPlaque | `plaque` | `/catalog/kalkulyator-nagradnyh-plaketok/` | 86 / 2586879 (draft) | пилот закрыт |
| 26 CalcUVPrint | `uv_print` | `/catalog/uf-pechat-na-suveniry/` | 87 / 2586881 (draft) | копия принята 05.11.2026 |
| 41 CalcMug | `mug` | `/catalog/kalkulyator-sublimaczionnoj-pechati-na-kruzhki/` | 88 / 2586882 (draft) | `form-mug` (закрыто 2026-11-07, `docs/history/log.md`) |
| 85 CalcEmbossing | `embossing` | `/catalog/kalkulyator-tisneniya/` | 89 / 2586883 (draft) | копия принята 07.11.2026, `form-embossing` (закрыто 2026-11-07, `docs/history/log.md`) |
| 78 CalcAcrilycPrizes | `acrylic_prizes` | `/catalog/kalkulyator-akrilovyh-prizov/` | 91 / 2586884 (draft) | копия принята 08.11.2026, `form-acrylic-prizes` (закрыто 2026-11-08, `docs/history/log.md`) |
| 46 CalcPresswall | `presswall` | `/catalog/kalkulyator-pressvolov/` | 92 / 2586885 (draft) | копия принята 09.11.2026, `form-presswall` |
| 49 CalcRollup | `rollup` | `/catalog/kalkulyator-rollapov/` | 93 / 2586886 (draft) | копия принята 09.11.2026, `form-rollup` (закрыто 2026-11-09, `docs/history/log.md`) |
| 73 CalcPennantPaper | `pennant` | `/catalog/kalkulyator-vympelov-bumazhnyh/` | 94 / 2586887 (draft) | копия принята 11.11.2026, `form-pennant` (закрыто 2026-11-11, `docs/history/log.md`) |
| 55 CalcFlagPaper | `flag` | `/catalog/kalkulyator-flazhkov-bumazhnyh/` | 95 / 2586888 (draft) | копия принята 12.11.2026, `form-flag` (закрыто 2026-11-12, `docs/history/log.md`) |

## Контекст и ссылки

- Skills `.cursor/skills/ezfc-form-to-api/SKILL.md` и `.cursor/skills/deploy-wp-plugin/SKILL.md` — как делать. Правила прода — `.cursor/rules/insain-site-autonomous.mdc`, целиком, до первого действия на сервере.
- `docs/ezfc-api-migration.md` — GET и share-URL, чеклист перевода; `docs/site/access-tools.md`, «Принятый режим»: `read_file`, снимок `SELECT … --raw`, обратный импорт запрещён.
- `docs/site/forms.md` — реестр форм и сводка.
- `wp-plugin/forms/<slug>.js` — custom JS переведённых форм (в 0.2.6 есть `plaque.js`).
- Что дала форма 69 (пилот): на копии 86 UV, гравировка и сублимация сошлись с JS (rel ≤ 0.001), UI и share-URL проверены под админом, плагин 0.2.6 и API (`main` @ `52676c2` и новее) на проде. На боевой 69 пока старый `calcPlaque`, GET пустые, у режима `GET_check` = index.
- GET и `GET_check`, которые надо прописать на боевой 69 (id элементов боевой формы снять `SELECT --raw`, не переносить с копии 86):

  | поле | имя элемента → GET | GET_check |
  | --- | --- | --- |
  | количество | numN | — |
  | плакетка | dpdFormat | index |
  | материал | dpdMaterial | index |
  | нанесение | dpdApplication | index |
  | режим | rdoModeProduction | **value** |

- GET и `GET_check` формы 26 (копия 87 принята 05.11.2026; id боевой формы снять `SELECT --raw`, не переносить с копии 87):

  | поле | имя элемента → GET | GET_check |
  | --- | --- | --- |
  | количество и размеры | numN, numW, numH, numItemW, numItemH | — |
  | цвет, разрешение, поверхность, материал, пресет | dpdColor, dpdResolution, dpdSurfacePrint, dpdSurfaceMaterial, dpdPreset | index |
  | режим | rdoModeProduction | **value** |
  | нумерация, штрихкод, переменные, материал заказчика | ckbNumber, ckbBarcode, ckbVariables, ckbMaterialCustomer | — |

  На форме нет значения разрешения 0: индекс 0 у `dpdResolution` даёт value 1. Эталон с разрешением 0 проверен раннером и API, не страницей.

- Остальное не открывать.

## Scope

Порядок жёсткий. Каждое действие на проде — только с подтверждения человека, если оно вне списка «Делай самостоятельно» в `.cursor/rules/insain-site-autonomous.mdc`.

1. Предполётная регрессия по каждой форме пакета: на копии под админом прогнать эталонный набор (для 69 — три нанесения, 1 и 2 шт., режимы), открыть URL с GET в новой вкладке, перезагрузить. Плагин и API менялись после первых проверок (`showResult`, `size_mm`, `syncUrl`), поэтому прогон повторяется. Расхождение с API (`price`) или с JS (rel > 0.001) — стоп.
2. Дрейф: снять боевую форму и копию (`SELECT … --raw`), сверить id элементов, GET, список материалов и нанесений. Список расхождений — в «Результат»; решение по ним — человека.
3. GET на боевых формах пакета: прописать те же имена и `GET_check`, что на копиях. Перед записью — бэкап `wp db export` в `/tmp`; запись через `wp eval-file` или админку ezFC; подтверждение человека.
4. Одно «да» человека на пакет. Затем по форме по очереди: у элемента расчёта `custom_calculation_function_read_file` = 1 и путь `{{abspath}}wp-content/plugins/insain-calc-bridge/forms/<slug>.js`; id элементов не менять; сброс кэша (`wp litespeed-purge all`, при ошибке 400 — `purge url <страница>`); проверка страницы и расчёта (в Network `POST /api/v1/calc/<slug>` → 200, цена на странице = API с округлением `showResult`); только потом следующая форма. Расхождение — стоп, откат формы, остальные не трогать.
5. Снимок каждой боевой формы в `site/forms/<id>.json` (`SELECT … --raw`, файл проходит `json.loads`, в нём есть `forms/<slug>.js` и `custom_calculation_function_read_file`). Снимок обратно не импортировать.
6. `docs/site/forms.md`: у каждой формы пакета слот «API через `insaincalc.calcApi`», сводка (непереведённых форм, число на опубликованных товарах, привязанные slug) пересчитана по факту. Другие строки не переписывать.
7. Одна строка в `wp-plugin/AGENTS.md`: custom JS переведённых форм лежит в `forms/<slug>.js`.
8. Если к этому пакету прогнали skill `new-calculator` или `json-price-rollout` — убрать его из «Skills без прогона» в `BACKLOG.md`.
9. Копии (86 и остальные) оставить на черновике. Удаление — отдельным решением человека.

Git-файлы пишет Implementer. Дубль, `read_file`, GET на проде, сброс кэша и проверка страниц — Site ops.

## Файлы

- `site/forms/<id>.json` — снимки боевых форм пакета
- `docs/site/forms.md`, `wp-plugin/AGENTS.md`
- `todo/forms-batch-switch.md` — «Состав пакета» дописывают задачи на перевод; пока идёт эта задача, параллельно не дописывать
- WordPress: боевые формы «Состава пакета» и их копии

## Не-scope

- Перевод новых форм и новые калькуляторы: каждая форма сначала проходит свою задачу на перевод (сверка, `calcApi`, копия, GET), потом попадает в «Состав пакета».
- Правка цен, `calc_service/data/`, калькуляторов, эталонов, плагина и `insain-calc-bridge.js`. Баг bridge или API — стоп, отдельная задача.
- Обратный импорт снимков в ezFC; `infra/deploy.sh`; пересборка `insain-calc-api`.
- JS NaN на AcrylWhite3 + isSublimation (строка в `BACKLOG.md`).
- Закрытие чекбокса 5.5.

## Критерии приёмки

Команды из корня репозитория. `ID` — id боевой формы, `SLUG` — slug её JS. Для каждой формы пакета выполняется отдельно. Скрипт через `@'…'@ | python -` в PowerShell 5.1 — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`.

- [ ] Копия не на витрине. Одна строка `draft` или `private`, HTTP без cookies не `200` (ожидаемо `404`).

```powershell
ssh insain-prod "sudo -u www-data wp post list --post_type=product --post_status=draft,private --fields=ID,post_status,post_name --meta_key=ezfc_form_id --meta_value=ID_КОПИИ --path=/var/www/insain.ru"
curl.exe -sS -o NUL -w "%{http_code}" "PERMALINK_КОПИИ"
```

- [ ] На сервере лежит JS из git. В stdout есть `insaincalc.calcApi('SLUG'` и `insaincalc.syncUrl`.

```powershell
ssh insain-prod "grep -E 'calcApi|syncUrl' /var/www/insain.ru/wp-content/plugins/insain-calc-bridge/forms/SLUG.js"
```

- [ ] Боевая форма читает файл плагина. В выводе шапка `id` и ровно одна строка с числом.

```powershell
ssh insain-prod 'sudo -u www-data wp db query --raw --path=/var/www/insain.ru "SELECT id FROM wp_insain_ezfc_forms_elements WHERE f_id=ID AND data LIKE ''%forms/SLUG.js%'' AND data LIKE ''%custom_calculation_function_read_file%''"'
```

- [ ] GET боевой формы совпадают с копией. Снимок GET-полей боевой и копии (`SELECT … --raw`) — имена и `GET_check` одинаковы, расхождений нет. Результат сравнения — в «Результат».
- [ ] Снимок в git. Stdout `ok`.

```powershell
@'
import json
from pathlib import Path
snap = Path("site/forms/ID.json").read_text(encoding="utf-8")
json.loads(snap)
assert "forms/SLUG.js" in snap
assert "custom_calculation_function_read_file" in snap
print("ok")
'@ | python -
```

- [ ] Расчёт на боевой странице: набор эталона даёт `POST /api/v1/calc/SLUG` → 200 и `price` равный API (с округлением `showResult`); URL с GET открывает форму с теми же значениями. В «Результат» — код и `price` каждого прогона для каждой формы. Для 69: 2 шт., Plaque2330, AcrylWhite3, УФ-печать, режим 1 — API `6618.96`, на странице `6620`.
- [ ] Витрина открывается. Stdout `200`.

```powershell
curl.exe -sS -o NUL -w "%{http_code}" "СТРАНИЦА_ФОРМЫ"
```

- [ ] Реестр и правило плагина. Stdout `ok`. Перед запуском в `SLUGS` подставить slug форм пакета; число непереведённых форм Implementer пересчитывает по реестру и сверяет с текстом «Непереведённых форм: **N**» в `docs/site/forms.md`.

```powershell
@'
from pathlib import Path
SLUGS = ["plaque"]
forms = Path("docs/site/forms.md").read_text(encoding="utf-8")
for slug in SLUGS:
    row = next(ln for ln in forms.splitlines() if f"| {slug} |" in ln)
    assert "calcApi" in row and "старый JS" not in row, slug
plugin = Path("wp-plugin/AGENTS.md").read_text(encoding="utf-8")
assert "forms/<slug>.js" in plugin
print("ok")
'@ | python -
```

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: страницы каталога живые, переключение меняет расчёт для клиентов. Подтверждение — одно на пакет, после зелёной предполётной регрессии и дрейфа. Откат формы — `read_file` = 0, сброс кэша; плагин — zip предыдущего коммита плагина; GET — из бэкапа `wp db export`.
- Дрейф: пока копии ждали, в админке ezFC могли править боевые формы (цены в опциях, список материалов). Шаг 2 обязателен.
- Цены: JSON не менять. Чужой `price` на проде не выравнивать правкой прайса.
- Формы: только формы «Состава пакета». Id элементов боевых форм сохраняются. Снимок — история, не источник заливки.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Сделано:
  - Блок результата копий по разделу «Блок результата» `docs/ezfc-api-migration.md` (07.11.2026, снимок `wp_insain_ezfc_forms_elements` только чтение): 86 и 87 — как у 79 элемент в элемент, правка не нужна. 88 — на предполётной проверке убрать скрытые `grpPriceCustomer` / `sbtPrice` / `sbtPriceTotal` и `hdgPrice` «Цена», обернуть `htmMaterial` в `grpMaterial`; группа скидки названа `grpCost`, не `grpPriceDiscount`.
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Как откатить:
