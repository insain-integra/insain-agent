# ezfc-form-builder

Статус: черновик
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

- [ ] `python -m pytest calc_service/tests/test_ezfc_form_builder.py -q` — все тесты `passed`, `failed` нет; покрыта генерация блока результата эталона 79, загрузка опций из `calc_service/data/materials/*.json` и проверка обязательных полей.
- [ ] Проверка лимита `AGENTS.md`: `(Get-Content AGENTS.md).Count -le 150` — `True`.
- [ ] На проде `ssh insain-prod "php -l /tmp/ezfc_build_apply.php"` — `No syntax errors detected`.
- [ ] На проде `dry-run` генератора на тестовой спеке (например, 2 поля ввода + dropdown из `hardsheet.json`) выполняется без ошибок и без записи в БД.
- [ ] После подтверждения человека (или на черновике без влияния на опубликованные товары): `apply` создаёт форму в `wp_insain_ezfc_*`, форма открывается в редакторе админки ezFC без ошибок JSON/интерфейса и привязана к `draft`-товару (для гостя `curl.exe -s -o NUL -w "%{http_code}"` возвращает `404`), все 4 элемента скидки/менеджера имеют корректные `hidden`/`calculate_when_hidden` как в `docs/ezfc-api-migration.md`.
- [ ] Откат проверен: `restore` удаляет созданную тестовую форму без следов в `wp_insain_ezfc_forms` и `wp_insain_ezfc_forms_elements`.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: прямая вставка строк в `wp_insain_ezfc_*`. Минимизация: `dry-run` до записи, манифест отката в `/tmp`, запрет модифицировать формы на `publish`-товарах/страницах, обязательная проверка открытия созданной формы в админке ezFC.
- Цены: нет (скрипт только читает `calc_service/data/*.json` как источник названий и кодов для UI).
- Формы: несовпадение JSON-кодирования `data` с ожиданиями ezFC (слеши `\/`, unicode, структура `calculate`/`conditional`). Минимизация: брать за основу реальный дамп формы 79 и кодировать как в `scripts/ezfc_copy_apply.php`.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
