# insainparse-admin-scripts

Статус: черновик
Сложность: высокая
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: правка файла стороннего плагина на проде без git и без skill, впервые; плагин нельзя выключать — деактивация удаляет его таблицы.

## Цель

Скрипты и стиль плагина insainParse подключаются только на его странице админки «InsainParser». На остальных страницах wp-admin (в т.ч. редактор ezFC, товары) нет `scrtp.js` и `TypeError` из него; глобальные `window.onload` и `window.onclick` плагин там не перехватывает. Страница InsainParser работает как раньше.

## Контекст и ссылки

Факты на 10.11.2026 (чтение кода на VDS):

- `/var/www/insain.ru/wp-content/plugins/insainParse/includes/mfp-function.php`: `add_action('admin_enqueue_scripts', 'true_include_in_admin')` без проверки страницы — на каждой странице админки подключаются `xhr.js`, `dropdoun.js`, `scrtp.js` и стиль с хэндлом `style` (`includes/css/style.css`). Меню — `add_menu_page('InsainParser', …, 'manage_options', 'insainParse/includes/view/mfp-first-acp-page.php')`.
- `includes/script/scrtp.js` присваивает `window.onclick` и `window.onload`; в `onload` запрашивает статус cron-задач и обращается к `#stock-dropdown`, `#start_cron_task`, `#edit-dropdown` — они есть только на странице парсера, на других страницах `null` → `TypeError`.
- Посетители сайта ошибку не видят: на публичных страницах `scrtp.js` нет (HTML https://insain.ru/catalog/kalkulyator-rollapov/).
- `docs/site/content-inventory.md`, «Плагин insainParse» — что делает плагин, `deleteTabel` при деактивации. `todo/supplier-parser.md` — замена плагина новым парсером; эта задача — минимальная правка до замены.
- Остальное не открывать.

## Scope

- На проде (Site ops):
  1. Бэкап `mfp-function.php` рядом: `mfp-function.php.bak-<ДДММГГГГ>` (владелец и права как у оригинала).
  2. В `true_include_in_admin($hook)` — выход, если `$hook` не хук страницы плагина. Хук определить на сервере: значение, которое возвращает `add_menu_page` в `mfp_Add_My_Admin_Link`, или `get_current_screen()->id` на странице InsainParser. Условие одно на все четыре `wp_enqueue_*`.
  3. `php -l`, проверки ниже, сброс OPcache/кэша, если нужен.
- В git — только этот файл задачи. Строку для `docs/site/content-inventory.md`, «Плагин insainParse» (правка, дата, путь бэкапа) — в «Результат»: файл правят задачи `supplier-*`, вносится при закрытии.

## Файлы

- VDS: `/var/www/insain.ru/wp-content/plugins/insainParse/includes/mfp-function.php` и его бэкап

## Не-scope

- Выключение, удаление, обновление плагина insainParse и его таблиц.
- Правка `scrtp.js`, `xhr.js`, `dropdoun.js`, логики парсера, cron.
- Новый парсер — `todo/supplier-parser.md`. Элементы ezFC — `todo/ezfc-options-source-reset.md`.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `HOOK` — хук страницы плагина из шага 2.

- [ ] Синтаксис. Stdout: `No syntax errors detected`.

```powershell
ssh insain-prod "php -l /var/www/insain.ru/wp-content/plugins/insainParse/includes/mfp-function.php"
```

- [ ] Бэкап есть, diff с ним — только условие в `true_include_in_admin`.

```powershell
ssh insain-prod "cd /var/www/insain.ru/wp-content/plugins/insainParse/includes; ls -l mfp-function.php*; diff mfp-function.php.bak-* mfp-function.php"
```

- [ ] На чужой странице админки скрипт не подключается, на странице плагина — подключается. Скрипт `wp eval-file` вызывает `do_action('admin_enqueue_scripts', 'index.php')`, затем то же с `HOOK`, и печатает `wp_script_is('scrtp', 'enqueued')` после каждого. Stdout: `index.php: no`, `HOOK: yes`.
- [ ] Плагин активен. Stdout: `active`.

```powershell
ssh insain-prod "sudo -u www-data wp plugin get insainParse --field=status --path=/var/www/insain.ru"
```

- [ ] Под админом в браузере: консоль на `wp-admin/index.php` и в редакторе формы ezFC — без `TypeError` из `scrtp.js`; страница InsainParser открывается, выпадающие списки поставщиков раскрываются и закрываются кликом мимо.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: правка PHP стороннего плагина; ошибка в файле уронит админку и сайт (файл подключается на каждом запросе). `php -l` до сохранения; откат — вернуть бэкап поверх файла.
- Плагин не деактивировать даже для проверки: `deleteTabel` удаляет его таблицы.
- Цены: нет. Формы: нет.

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
- Часы человека: не учтено
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
