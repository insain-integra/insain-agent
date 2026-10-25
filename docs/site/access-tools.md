# Инструменты доступа к WordPress из Cursor

Снято 25.10.2026, только чтение. Учётки, Application Password и ключи WooCommerce не создавались, в БД ничего не записывалось.

Три канала:

- **wp-cli** — `ssh insain-prod`, затем `sudo -u www-data wp … --path=/var/www/insain.ru`. WP-CLI 2.12.0. Есть команды `post`, `menu`, `media`, `option`, `term`, `db`, `wc`, `yoast`, `export`/`import`, `search-replace`. Пакеты не ставятся: `/var/www/.wp-cli/packages` не создаётся (`Permission denied`). Каждая команда печатает PHP Warning от `wt_geotargeting_pro` (`Wt::__wakeup()`), это шум, его отфильтровывать.
- **REST API** — `https://insain.ru/wp-json/`. Пространства имён `wp/v2`, `wc/v3`, `wc/store/v1`, `yoast/v1`, `contact-form-7/v1`, `jetpack/v4`, `litespeed/v3` и другие. Аутентификация: в корне объявлены только Application Passwords. У пользователя 1 (`admin`) паролей приложений 0, ключей в `wp_insain_woocommerce_api_keys` 0. Анонимно доступно только публичное чтение. Своих маршрутов у ezFC в REST нет.
- **Browser MCP** — реальный Chrome с админ-сессией WP. В этой сессии не подключён: `No connection to browser extension`. Перед работой нужно нажать Connect в расширении.

## Объект → чтение → запись → ограничения

| Объект | Чтение | Запись | Ограничения |
|---|---|---|---|
| Страницы | `wp post list --post_type=page`, `wp post get <id>`; REST `GET /wp/v2/pages` анонимно (200) | `wp post update <id> --post_content=…` / `--post_title=…`; админка (Browser MCP). REST — только с Application Password | У 6 страниц контент WPBakery: в `post_content` шорткоды `[vc_…]`, править как текст рискованно, такие страницы — через конструктор. REST `context=edit` анонимно — 401 |
| Товары WooCommerce | `wp wc product list --user=1` (758), `wp wc product_cat list --user=1` (305), `wp post meta`; REST `GET /wp/v2/product`, Store API `GET /wc/store/v1/products` анонимно (200) | `wp wc product update <id> --user=1 …` (внутренний REST Woo, ключи не нужны); админка. REST `wc/v3` — только с ключами Woo или Application Password | Без `--user` wp-cli отвечает 401. `wc/v3` анонимно — 401. Каталог `prg` (694 + 12 670 вариаций) ведёт парсер InsainParser: ручная правка перетрётся при следующей загрузке. У `INS` активен Easy Auto SKU Generator |
| Меню | `wp menu list`, `wp menu item list <menu>`, `wp menu location list` | `wp menu item add-post/add-term/update/delete`; админка «Внешний вид → Меню» | REST `/wp/v2/menus`, `/wp/v2/menu-items` анонимно — 401. Главное меню — 287 пунктов, почти все термы `product_cat`; переименование рубрики меняет пункт меню |
| SEO-мета (Yoast 27.5) | `wp post meta list <id> --keys=_yoast_wpseo_title,_yoast_wpseo_metadesc`; `wp option get wpseo_titles`; REST `GET /yoast/v1/get_head?url=…` анонимно (200, готовый `<head>`) | `wp post meta update <id> _yoast_wpseo_title …`; `wp option update` для шаблонов; админка Yoast | Мета Yoast в REST записей не зарегистрированы (у страницы 143 в `meta` только `_acf_changed`, `footnotes`), записать через REST нельзя даже с паролем. После правки меты через wp-cli индекс `wp_insain_yoast_indexable` сам не обновляется — нужен `wp yoast index`. SEO рубрик — сериализованная опция `wpseo_taxonomy_meta` (40 КБ): точечно только через админку. В заголовках переменная `{region_name_prepositional}` геоплагина, её не раскрывать |
| Медиа | `wp post list --post_type=attachment`; REST `GET /wp/v2/media` анонимно (200) | `wp media import <файл/URL>`, `wp post update` (alt, заголовок); админка + WP Media Folder | Файл нужно сначала положить на сервер (scp в `/tmp`). Папки WP Media Folder — его таксономия, wp-cli о них не знает. `uploads` 1,3 ГБ, из них `ezfc-uploads` 274 МБ |
| Формы ezFC 2.14.0.2 | `wp db query` по `wp_insain_ezfc_*` (см. ниже); экран админки «Import / Export» | Админка ezFC (Browser MCP); `wp db query "UPDATE wp_insain_ezfc_forms_elements …"` | REST нет. Плагин в wp-cli команд не регистрирует. Прямой SQL — без валидации плагина, JSON внутри JSON; ошибка экранирования ломает форму. После записи — `wp litespeed-purge all` |

## Формы ezFC

### Как хранится

Плагин `ez-form-calculator-premium` 2.14.0.2. Таблицы `wp_insain_ezfc_forms`, `_forms_elements`, `_forms_options`, `_templates` (3 шаблона), `_submissions`, `_files`, `_preview`, `_forms_views`, `_options`, `_debug`.

Форма — строки трёх таблиц:

| Таблица | Колонки | Что лежит |
|---|---|---|
| `wp_insain_ezfc_forms` | `id`, `name` varchar(300), `data` mediumtext | имя и JSON с `global_conditions` |
| `wp_insain_ezfc_forms_elements` | `id`, `f_id`, `e_id`, `data` text, `position` | элемент формы. `e_id` — тип элемента, `data` — JSON всех настроек элемента |
| `wp_insain_ezfc_forms_options` | `f_id`, `o_id`, `value` mediumtext | настройки формы, у формы 79 их 192 |

Всего 49 форм и 1 420 элементов.

Custom JS — строка в поле `custom_calculation` внутри JSON `forms_elements.data` у элемента типа custom calculation (у формы 79 это элемент 3108, `e_id` 24). Хранится одной JSON-строкой: переводы строк `\r\n`, слэши `\/`, кириллица как есть или `\uXXXX`. В HTML-элементах разметка хранится HTML-сущностями (`&lt;div`). Таких JS-элементов 49.

В JS два вида ссылок на другие поля:

- по имени: `{{numN}}`, плагин подставляет при выводе (`replace_magic_values`);
- по id строки в `forms_elements`: `ezfc_functions.get_value_from(3104, true)`. Так ссылаются 43 элемента из 49.

Плагин умеет брать JS из файла на сервере: настройки элемента `custom_calculation_function_read_file` = 1 и `custom_calculation_function_filename` (с подстановками `{{abspath}}`, `{{ezfc_path}}`, `{{upload_path}}`). К содержимому файла применяются те же `{{…}}` и фильтр `ezfc_custom_calculation_js`. Сейчас ни одна форма этот режим не использует (0 из 49). Плагин `insain-calc-bridge` хуков ezFC не использует.

### Экспорт и импорт одной формы

**Экспорт одной формы — да.** В админке («Export» у формы, `form_get_export_data`) — JSON `{form, elements, options, version}`. Без админки — один `SELECT` с `JSON_OBJECT` по трём таблицам. Тестовый снимок формы 79 (CalcPuzzle): `/tmp/ezfc-form-79.json` на VDS, 22 элемента, 192 опции, около 40 КБ, `json.load` проходит, JS элемента 3108 (666 символов) читается как текст. В `wp db query` обязателен `--raw`, иначе mysql-клиент удваивает обратные слэши и JSON становится невалидным.

**Импорт одной формы — частично.** Импорт есть (`form_import`), но:

- элементы всегда вставляются с новыми `id`. Ссылки `calculate` и `conditional` плагин пересчитывает, а числа внутри текста `custom_calculation` не трогает. У 43 JS-элементов после импорта `get_value_from(<старый id>)` указывает в пустоту;
- режим «сохранить id» сохраняет только id формы (`meta ezfc_form_id` у товаров остаётся верным): форма и её элементы удаляются и вставляются заново, id элементов всё равно новые;
- режим «в существующую форму» дописывает элементы, старые не удаляет — получаются дубли.

**Правка только custom JS — да.** Это одна строка `forms_elements.data` с известным `id`: через админку или `UPDATE` с пересборкой JSON. Id элементов при этом не меняются.

### Принятый режим (решение владельца 25.10.2026)

**Структура формы — снимки после правки в админке.** Структуру форм (поля, условия, опции) правят в админке ezFC. После правки агент снимает форму одним `SELECT … --raw` в `site/forms/<id>.json`. Репозиторий — история и diff, не источник для заливки: обратный импорт ломает ссылки на id элементов.

**Custom JS переведённых форм — источник правды в репозитории.** Файл `<slug>.js` поставляется в составе плагина `insain-calc-bridge` (деплой через `wp plugin install`, разрешён). При переводе формы на `calcApi` у её JS-элемента один раз в админке включается `read_file` с путём `{{abspath}}wp-content/plugins/insain-calc-bridge/forms/<slug>.js`. Id элементов не меняются, `get_value_from(N)` продолжает работать. Формы переключаются по одной, каждая — в момент перевода на API. Дальше JS правится только в git, правка в админке у такой формы не действует. Формы старого JS остаются в базе, по ним только снимки.

## Решения

1. **Запись через REST — не используется.** Контур сайта идёт через wp-cli и Browser MCP. Учётки не созданы. Если понадобится внешний скрипт без SSH: Application Password отдельному пользователю с ролью `shop_manager` или `editor` (не `admin`), создаётся в профиле пользователя или `wp user application-password create <user> <имя>`. Для `wc/v3` отдельно — ключ WooCommerce (Woo → Настройки → Дополнительно → REST API), права read или read/write. Хранить в `.env`, в git не класть.
2. **Custom JS из файла — принято 25.10.2026** (см. «Принятый режим»).
3. **Browser MCP** — расширение подключено владельцем 25.10.2026. Нужен для админки: экспорт или импорт ezFC через интерфейс, включение `read_file`, WPBakery, папки медиатеки.
