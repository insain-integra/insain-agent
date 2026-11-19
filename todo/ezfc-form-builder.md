# ezfc-form-builder

Статус: выкатка
Сложность: высокая
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: новый инструмент с записью в таблицы WordPress (ezFC) по эталону формы 79, требует правки `AGENTS.md` и первого прогона на проде.

## Цель

Есть детерминированный и безопасный конструктор, который по декларативной JSON-спеке формы и справочникам `calc_service/data/*.json` создаёт новую форму ezFC на сайте строго в едином стиле эталонной формы 79 (`CalcPuzzle`: `grpPrice`, `grpPriceManager`, `grpPriceDiscount`, `grpTime`, `rdoModeProduction`, `sbtWeightTotal`, `grpMaterial`, `htmCost`, `htmTime`, `htmMaterial`, `read_file` на `wp-plugin/forms/<slug>.js`, `GET`/`GET_check`) и умеет обновлять списки опций элементов при расширении JSON-каталогов.

## Контекст и ссылки

- `docs/ezfc-api-migration.md` — эталон блока результата (форма 79 `CalcPuzzle`), правила чтения полей и `GET`/`GET_check`.
- `docs/site/access-tools.md` — структура таблиц `wp_insain_ezfc_forms`, `_forms_elements`, `_forms_options`, запрет обратного импорта `form_import` из-за смены `id`.
- `scripts/ezfc_copy_apply.php` и `scripts/ezfc_copy.py` — образец безопасного `wp eval-file`: `dry-run` по умолчанию, защита боевых опубликованных форм, бэкап в `/tmp`, формат кодирования `data`.
- `wp-plugin/forms/puzzle.js` (если нет — эталон формы 79 в БД) и `wp-plugin/forms/laser.js` — образец `cjsCalc` с `syncUrl`, `calcApi`, `showResult`, `showError`.
- `AGENTS.md` — разделы «Запреты» (исключение для скрипта записи в ezFC) и «Сессии» (лимит 150 строк файла).
- Остальное не открывать.

## Scope

- В git (Implementer):
  - Шаблон структуры формы 79 (`scripts/ezfc_form_template_79.json` — опции формы, элементы результата `grpPrice`/`grpTime`/`sbtWeightTotal`/`grpMaterial`/`htmCost`/`htmTime`/`htmMaterial`, типовые заготовки полей `num`/`dropdown`/`radio`/`checkbox`/`hidden`/`cjsCalc`).
  - `scripts/ezfc_build_form.py`:
    - валидирует JSON-спеку новой формы (`name`, `slug`, список полей ввода, условия `conditional` по именам полей, `options_from` из `calc_service/data/materials/*.json` / `equipment/*.json` / `common.json` или явный список опций);
    - формирует пакет сборки формы (или пакет обновления опций существующей формы `--update-options`) в формате для `ezfc_build_apply.php`.
  - `scripts/ezfc_build_apply.php` для `sudo -u www-data wp eval-file … --path=/var/www/insain.ru`:
    - режим без флага `apply` — только `dry-run` (показывает создаваемую форму/элементы/опции или diff опций при обновлении, ничего не пишет);
    - режим `apply` — создаёт новую форму в `wp_insain_ezfc_forms`, `_forms_options`, `_forms_elements` (проставляя `parent_id`, `position`, `GET`, `GET_check_option_value`, `custom_calculation_function_read_file = 1`, путь `{{abspath}}wp-content/plugins/insain-calc-bridge/forms/<slug>.js`), печатает таблицу `name → id` созданных элементов и путь бэкапа/манифеста отката в `/tmp/ezfc-build-*.json`;
    - режим `update-options` — обновляет только массив `options` указанных элементов `dropdown`/`radio` и при необходимости перепривязывает id; защищает опубликованные боевые формы без явного подтверждённого флага и сохраняет бэкап строк до записи;
    - режим `restore <файл>` — откатывает созданную форму (удаляет созданные строки этой формы) или возвращает `data` элементов из бэкапа.
  - Рекомендованный паттерн для новых форм: либо `ezfc_functions.get_element_id_by_name(__form_id__, '<name>')` в `wp-plugin/forms/<slug>.js`, либо подстановка созданных `id` через `scripts/ezfc_build_form.py` (зафиксировать один вариант и покрыть тестом в `test_wp_plugin_forms.py` / `test_ezfc_form_builder.py`, не ломая существующие формы).
  - Тесты `calc_service/tests/test_ezfc_form_builder.py` (валидация спеки, резолв опций из JSON-справочников, сохранение структуры блока результата по эталону 79, `php -l` если доступен php).
  - Точечное обновление `AGENTS.md` (раздел «Запреты» — добавить `scripts/ezfc_build_apply.php` рядом с `ezfc_copy_apply.php`, сохранив файл ≤ 150 строк) и `docs/site/access-tools.md` (описание нового инструмента).
- На проде (Site ops):
  - Снять эталонный JSON формы 79 (`SELECT … --raw`) для формирования/проверки `scripts/ezfc_form_template_79.json` (если нужно уточнить поля/опции эталона на этапе Implementer — запрос в журнал).
  - После слияния/подготовки скрипта — проверить `dry-run` и `apply` на тестовой форме + черновике товара (`draft`, 404 для гостя), проверить открытие формы в админке ezFC (Browser MCP) и откат через `restore` на тестовой копии, затем финально оставить тестовый черновик удалённым или в чистом виде по отчёту.

## Файлы

- `scripts/ezfc_build_form.py`
- `scripts/ezfc_build_apply.php`
- `scripts/ezfc_form_template_79.json`
- `calc_service/tests/test_ezfc_form_builder.py`
- `AGENTS.md`
- `docs/site/access-tools.md`

## Не-scope

- Перевод 45 существующих форм из `todo/EPIC-forms-to-api.md` и правка `scripts/ezfc_copy_apply.php` / `scripts/ezfc_copy.py`.
- Написание сквозного skill для интервью и создания калькуляторов (это `todo/ai-calc-authoring-skill.md`).
- Создание пилотного калькулятора C2 (это `todo/pilot-acrylic-medals-calc.md`).
- Правка `docs/site/forms.md` и `wp-plugin/js/insain-calc-bridge.js`.

## Критерии приёмки

- [x] `python -m pytest calc_service/tests/test_ezfc_form_builder.py -q` — все тесты `passed`, `failed` нет; покрыта генерация блока результата эталона 79, загрузка опций из `calc_service/data/materials/*.json` и проверка обязательных полей.
- [x] Проверка лимита `AGENTS.md`: `(Get-Content AGENTS.md).Count -le 150` — `True`.
- [ ] На проде `ssh insain-prod "php -l /tmp/ezfc_build_apply.php"` — `No syntax errors detected`.
- [ ] На проде `dry-run` генератора на тестовой спеке (например, 2 поля ввода + dropdown из `hardsheet.json`) выполняется без ошибок и без записи в БД.
- [ ] После подтверждения человека (или на черновике без влияния на опубликованные товары): `apply` создаёт форму в `wp_insain_ezfc_*`, форма открывается в редакторе админки ezFC без ошибок JSON/интерфейса и привязана к `draft`-товару (для гостя `curl.exe -s -o NUL -w "%{http_code}"` возвращает `404`), все 4 элемента скидки/менеджера имеют корректные `hidden`/`calculate_when_hidden` как в `docs/ezfc-api-migration.md`.
- [ ] Откат проверен: `restore` удаляет созданную тестовую форму без следов в `wp_insain_ezfc_forms` и `wp_insain_ezfc_forms_elements`.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: прямая вставка строк в `wp_insain_ezfc_*`. Минимизация: `dry-run` до записи, манифест отката в `/tmp`, запрет модифицировать формы на `publish`-товарах/страницах, обязательная проверка открытия созданной формы в админке ezFC.
- Цены: нет (скрипт только читает `calc_service/data/*.json` как источник названий и кодов для UI).
- Формы: несовпадение JSON-кодирования `data` с ожиданиями ezFC (слеши `\/`, unicode, структура `calculate`/`conditional`). Минимизация: брать за основу реальный дамп формы 79 и кодировать как в `scripts/ezfc_copy_apply.php`.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

20.11.2026 — Implementer, Gemini 4 Hydrogen High — заблокировано: нужен реальный дамп формы 79 (CalcPuzzle), схема таблиц ezFC и эталоны типов элементов с прода — дальше Site ops

```text
Блокер: в репозитории нет дампа формы 79 (CalcPuzzle) и схемы таблиц/элементов ezFC 2.14.0.2 с прода (в docs/site/access-tools.md указан только /tmp/ezfc-form-79.json на VDS), без них невозможно точно собрать scripts/ezfc_form_template_79.json (192 опции, точные e_id, ключи data, parent_id/group_id, calculate_when_hidden), scripts/ezfc_build_form.py и scripts/ezfc_build_apply.php.
Пробовал: поиск по worktree (Glob/Grep по *79*, site/**, wp-plugin/forms/**, sbtPriceTotalDiscount) — файла wp-plugin/forms/puzzle.js и снимка формы 79 в git нет; правка WordPress/SSH — зона Site ops.
Гипотеза: на проде в БД ezFC есть форма 79 (CalcPuzzle), таблица типов wp_insain_ezfc_elements и примеры элементов checkbox/hidden/conditional (напр. в форме 28 CalcLaser), которые нужно снять только чтением в $env:TEMP (не в git-папку, чтобы не нарушить изоляцию worktree).
Вопрос: Site ops (только чтение на проде):
1) Снять полный JSON-дамп формы 79 (CalcPuzzle: wp_insain_ezfc_forms id=79, wp_insain_ezfc_forms_elements f_id=79, wp_insain_ezfc_forms_options f_id=79) через wp db query --raw --skip-column-names, раскрыть вложенные JSON-строки data и сохранить в $env:TEMP\ezfc-form-79.json.
2) Снять SHOW COLUMNS для wp_insain_ezfc_forms, wp_insain_ezfc_forms_elements, wp_insain_ezfc_forms_options, wp_insain_ezfc_elements; полный список типов из wp_insain_ezfc_elements; а также по 1-2 примера реальных элементов checkbox, hidden, dropdown, radio, num с conditional и calculate (например, из формы 28 и любой формы с hidden) и сохранить всё в $env:TEMP\ezfc-elements-ref.json.
3) Проверить в коде плагина ez-form-calculator-premium (только чтение) сигнатуру/поведение ezfc_functions.get_element_id_by_name(form_id, name) и точное имя поля связи с группой (parent_id vs group_id, колонка SQL или ключ в data).
4) Вернуть статус «черновик» и записать пути к сохранённым файлам в «Результат» / журнал; лишних файлов в worktree не оставлять.
Следующая сессия: Site ops, модель Opus 5.5
```

20.11.2026 — Site ops, Opus 5.5 — запрос Implementer закрыт только чтением на проде: дампы формы 79 и справочник элементов в `$env:TEMP`, ответы по `get_element_id_by_name` и `group_id` в «Результате» — дальше Implementer

20.11.2026 — Implementer, Gemini 4 Hydrogen High — реализованы шаблон 79 (`scripts/ezfc_form_template_79.json`), генератор `scripts/ezfc_build_form.py`, PHP-скрипт `scripts/ezfc_build_apply.php`, тесты `calc_service/tests/test_ezfc_form_builder.py`, точечно `AGENTS.md` и `docs/site/access-tools.md`; `make check` зелёный — дальше Reviewer

20.11.2026 — Reviewer, Grok 4.7 — принято по diff, блокеров нет — дальше человек: слияние перед прод-проверкой Site ops

20.11.2026 — человек — принято: слить в main и запушить, затем прод-проверка — дальше Site ops

## Ревью 1

Вердикт: **принято**. Блокеров нет. Статус остаётся `ревью`.

Сверено с дампом `ezfc-form-79.json`, справочником `ezfc-elements-ref.json` и `scripts/ezfc_copy_apply.php`:

- 192 опции формы совпадают с дампом по `(o_id, value)`, `form_data` совпадает. Раскодированный HTML блока результата совпадает с дампом.
- Минимальная сборка повторяет порядок формы 79: загрузчик с максимальным `position`, `htmMaterial` с `position` 1. `e_id` 10 в шаблоне и в пакете нет.
- `group_id` в шаблоне обнулён. `ezfc_build_apply.php` после вставки группы пишет в `data.group_id` строковый id родителя. Колонки вставки совпадают со схемой (`forms`, `forms_elements`, `forms_options`).
- `sbtPriceTotalDiscount` и `sbtPriceDiscount`: `hidden="1"`, `calculate_when_hidden="1"`, `e_id` 15. У `sbtPriceManager` и `sbtPriceDiscount` ряды `calculate` как в дампе, цели вынесены в `refs` и подставляются новыми id.
- Запись `data` — `wp_json_encode(..., JSON_UNESCAPED_UNICODE)`, тот же вызов, что в `scripts/ezfc_copy_apply.php`.
- `options_from`: `value` — ключ каталога, `text` — `title` / `name` / `description`, `Default` пропускается. В тесте PVC3 получает подпись «ПВХ 3 мм».
- Без флага `apply` скрипт ничего не пишет. `update-options` и `restore` останавливаются на `publish`-постах без `allow-published`. Ошибка вставки вызывает очистку строк этой формы. `restore` бэкапа опций возвращает `data` только строк из манифеста.
- `get_element_id_by_name(__form_id__, '<name>')` и лишние `{{…}}` покрыты тестом; обход `wp-plugin/forms/*.js` на лишние скобки входит в те же 15 тестов.
- `AGENTS.md` — 130 строк. Исключение в «Запретах» добавляет `scripts/ezfc_build_apply.php` рядом с `ezfc_copy_apply.php`.

Прод-критерии (`php -l`, dry-run, apply на draft, админка ezFC, restore) остаются открытыми: их закрывает Site ops после слияния.

Замечания:

- желательно: битый `path` в `ezfc_build_set_nested` завершает скрипт без `ezfc_build_cleanup_partial`, уже вставленная форма остаётся в БД. Ошибка самой вставки и отсутствующее имя цели очищаются. Генератор такой `path` не строит.
- желательно: `restore` сборки удаляет все строки по `form_id` из манифеста и не сверяет `name_to_id` и имя формы. Формы на `publish`-постах защищены. Подмена `form_id` в файле отката сотрёт другой неопубликованный черновик целиком.
- желательно: пресет `set` остаётся `hidden="1"` при `hidden: false` в спеке. Подпись режима в шаблоне — «стандарт»; в дампе 79 первая буква латинская `c`, значения опций те же (`1`, `2`). У видимого `sbtPriceTotalManager` `calculate_when_hidden="1"`, как в дампе 79; в `docs/ezfc-api-migration.md` для видимых менеджерских полей этот флаг не требуется.
- желательно: `common.json` назван в scope рядом с каталогами, но записей с `title` / `name` / `description` в нём нет, `options_from` по этому файлу завершается ошибкой.

## Найдено вне scope

- В `materials/calendar.json` (секция Flip) и `materials/presswall.json` (Joker, Tritix) подпись в JSON совпадает с ключом, поэтому в списке опций виден код. Генератор подставляет в `text` только `title` / `name` / `description` и сам ключ туда не пишет.

## Результат

- Ветка, PR или коммит: ветка `task/ezfc-form-builder` (worktree `..\insain-agent-ezfc-form-builder`, незакоммиченные правки готовы к ревью)
- Период: 20.11.2026
- Часы человека: —
- Работа агентов: Site ops (Opus 5.5), Implementer (Gemini 4 Hydrogen High)
- Было / стало: не было инструмента программного создания форм ezFC по эталону формы 79; добавлены шаблон `scripts/ezfc_form_template_79.json`, генератор `scripts/ezfc_build_form.py`, wp-cli скрипт `scripts/ezfc_build_apply.php`, тесты `calc_service/tests/test_ezfc_form_builder.py`, обновлены `AGENTS.md` (130 строк) и `docs/site/access-tools.md`.
- Сделано:
  - Implementer 20.11.2026:
    - `scripts/ezfc_form_template_79.json`: снят с дампа формы 79 (192 опции формы, `form_data`, `Загрузчик калькулятора`, `grpParam`, `fluAtrwork`, `cjsCalc` в режиме `read_file`, 16 элементов блока результата `grpCalc`/`grpPrice`/`grpTime`/`rdoModeProduction`/`sbtWeightTotal`/`grpMaterial`/`htmCost`/`htmTime`/`htmMaterial`, 12 пресетов типов элементов; скрытые элементы через `data.hidden="1"` + `calculate_when_hidden="1"`, без `e_id=10`).
    - `scripts/ezfc_build_form.py`: валидация JSON-спеки (`name`, `slug`, `fields`, `qty_element`, `conditional`/`calculate`/`set` по именам, проверка отсутствия циклов групп), резолв `options_from` из `calc_service/data/materials/*.json` и `equipment/*.json` (с фильтрами `section`/`sections`/`include`/`exclude`/`prepend`/`append`, пропуск `Default`, подписи из `title`/`name`/`description`), проверка `read_file`-JS (`validate_read_file_js`: отклонение лишних `{{…}}`, хардкода id, несуществующих имён в `get_element_id_by_name(__form_id__, '<name>')`), генерация пакетов `build` (с топологическим порядком вставки и убывающими `position`) и `--update-options`.
    - `scripts/ezfc_build_apply.php`: режимы `dry-run` (по умолчанию), `apply` (создание формы, вставка групп до детей с проставлением `data.group_id`, перепривязка `refs`, кодирование `wp_json_encode(..., JSON_UNESCAPED_UNICODE)`, манифест `/tmp/ezfc-build-<id>-*.json`), `update-options` (защита `publish`-постов, сохранение старых `id` опций по `value`, бэкап в `/tmp/ezfc-build-options-<id>-*.json`), `restore <файл>`.
    - `calc_service/tests/test_ezfc_form_builder.py`: 15 тестов (шаблон 79, `options_from`, сборка пакета/позиций/ссылок, валидация ошибок и циклов, проверка лишних `{{…}}` в `read_file`-JS и во всех `wp-plugin/forms/*.js`, CLI `--update-options`, синтаксис/безопасность `ezfc_build_apply.php`).
    - Точечно обновлены `AGENTS.md` (исключение в «Запретах» для `scripts/ezfc_build_apply.php`, ровно 130 строк ≤ 150) и `docs/site/access-tools.md`.
  - Site ops 20.11.2026, только чтение на проде (`SELECT`/`SHOW COLUMNS` через `wp eval-file`, временный скрипт удалён из `/tmp` VDS). Дампы вне git, на машине агента:
    - `$env:TEMP\ezfc-form-79.json` (`C:\Users\79222\AppData\Local\Temp\ezfc-form-79.json`, ~110 КБ): `form` (строка `wp_insain_ezfc_forms`), `elements` — 22 строки `_forms_elements` с `data` раскрытым в объект и исходной строкой в `data_raw` (образец кодирования), `options` — 192 строки `_forms_options` с `value` и `value_decoded`.
    - `$env:TEMP\ezfc-elements-ref.json` (`C:\Users\79222\AppData\Local\Temp\ezfc-elements-ref.json`): `columns` (SHOW COLUMNS), `element_types` (38 типов), `element_type_defaults` (дефолтный `data` каждого типа из кода плагина), `type_usage` (какие `e_id` реально стоят в формах), `examples` по 2 элемента на тип (`f_id` 79/28 в приоритете, с `conditional`/`calculate`), `examples_hidden_flag` — элементы с `hidden=1`.
  - Схема: `wp_insain_ezfc_forms(id, name, data)`, `_forms_elements(id, f_id, e_id, data, position)`, `_forms_options(f_id, o_id, value)`. **Таблицы `wp_insain_ezfc_elements` нет** — типы `e_id` заданы в коде `Ezfc_settings::get_elements()` (`class.ezfc_settings.php`), версия плагина 2.14.0.2.
  - Типы `e_id`, которые реально используются на сайте: 4 `dropdown`, 5 `radio`, 6 `checkbox`, 7 `numbers`, 12 `html`, 14 `fileupload`, 15 `subtotal`, 22 `set`, 24 `custom_calculation`, 25 `group`, 31 `heading` (реже 1, 9, 34, 38). Дубли типов в коде (`checkbox` 30/33, `radio` 37, `numbers` 29, `subtotal` 28) на сайте не встречаются — брать первые id. Тип `hidden` (`e_id` 10) не используется ни в одной форме: «скрытые» элементы — это обычные элементы с `data.hidden = "1"` (у `subtotal`/`set` ещё `calculate_when_hidden = "1"`), примеры — `sbtPriceTotalDiscount`, `sbtPriceDiscount` (79), `setMaxSize`, `sbtCostTotal` (28).
  - Ответы на п. 3 (код плагина, только чтение):
    - Связь с группой — **ключ `group_id` внутри JSON `data`**, SQL-колонки нет (`ALTER … ADD COLUMN group_id` в `class.ezfc_backend.php` закомментирован), `parent_id` в формах не используется (это только `__parent_id` повторяемых форм на фронте). Корень — `group_id` `"0"`. В дампе 79 значения смешанные: число (`3109`) и строка (`"3102"`) — плагин принимает оба. Порядок — колонка `position` (в 79: 1 = `htmMaterial`, 22 = загрузчик, то есть обратно `id`); у элементов внутри группы `group_id` = `id` группы, поэтому при создании формы id групп нужно знать до записи детей (вставка группы, затем дети с подстановкой её нового `id`, как в `form_element_duplicate_group`).
    - `ezfc_functions.get_element_id_by_name(form_id, name)` (`frontend.js`, стр. ~65): ищет в `ezfc_vars.element_vars[form_id]` элемент, чьё `name` совпадает **без учёта регистра**, возвращает его `id` из `_forms_elements` или `false`. Если `form_id` пустой — берёт форму по DOM `[data-elementname=name]` (первая на странице); вызов с одним аргументом `get_element_id_by_name(name)` тоже работает.
    - Подстановки в коде `custom_calculation` работают и для `read_file` (`inc/php/elements/custom_calculation.php`, `replace_magic_values`): после `file_get_contents` файла заменяются `__form_id__` → id формы и `{{имя}}` → `ezfc_functions.get_value_from(<id>)` (без учёта регистра). **Любой оставшийся `{{…}}` в файле (например, в строке или шаблоне JS) превращает весь расчёт в `return 0` с `console.warn`.** Путь файла поддерживает `{{abspath}}`, `{{ezfc_path}}`, `{{upload_path}}`. Значит, `wp-plugin/forms/<slug>.js` может быть общим для формы и её копий: `get_element_id_by_name(__form_id__, '<name>')` резолвится в рантайме без подстановки id генератором.
- Чем проверено:
  - Implementer 20.11.2026:
    - `python -m pytest calc_service/tests/test_ezfc_form_builder.py -q` → `15 passed in 1.57s`.
    - `(Get-Content AGENTS.md).Count` → `130`, `(Get-Content AGENTS.md).Count -le 150` → `True`.
    - `python scripts/dev.py check` → `744 passed` (`calc_service/tests`) и `81 passed` (`bot_service/tests`), exit code `0`.
  - Site ops 20.11.2026:
    - `python -c "json.load(...)"` по обоим файлам — валидны; 79: `CalcPuzzle`, 22 элемента, 192 опции (совпадает с `docs/site/access-tools.md`).
    - `grep`/`sed` по `/var/www/insain.ru/wp-content/plugins/ez-form-calculator-premium` (`frontend.js`, `class.ezfc_backend.php`, `class.ezfc_settings.php`, `inc/php/elements/custom_calculation.php`, `class.ezfc_frontend.php`).
    - В worktree файлов дампа нет (`Get-ChildItem -Recurse -Filter ezfc-*.json` — пусто); блокировка `prod` снята.
- Не сделано и почему:
  - Локально не выполнен `php -l` (бинарника `php` на Windows нет; проверяется на VDS в рамках этапа Site ops).
  - Прод-проверка (`php -l`, `dry-run`, `apply` на `draft`-товаре, открытие в админке ezFC, `restore`) не выполнялась — зона Site ops после ревью.
- Требуется решение: человек — слияние `task/ezfc-form-builder` в `main` (статус `выкатка`), затем прод-проверки Site ops (Opus 5.5): `php -l`, dry-run, apply на `draft`, открытие в админке ezFC, `restore`. Желательные замечания «Ревью 1» не править, пока человек их не отметит.
