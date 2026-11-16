# ai-seo-geo-yoast

Статус: черновик
Сложность: высокая
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: правка глобальных SEO-шаблонов Yoast и геоплагина `wt_geotargeting_pro` на проде впервые (задачи `T01` и `T11` аудита).
Чат: новая сессия Site ops (Opus 5.5) с захватом `lock acquire prod ai-seo-geo-yoast`.

## Цель

В исходном HTML главной, категорий, карточек товаров и страниц контактов филиалов (при запросе с `User-Agent: GPTBot/1.0` и без cookie) отсутствует шаблон `{region_name_prepositional}` в `<title>`, `<meta name="description">` и JSON-LD schema.org (`T01`). Ошибка DaData «Feature 'SUGGESTIONS' disabled for token…» не попадает в cookie `wt_geo_data` (`T11`).

## Контекст и ссылки

- `insain-ru-ai-audit.md` — задачи `T01` и `T11`, «План правок → п. 1».
- `todo/EPIC-ai-seo.md`.
- `.cursor/rules/insain-site-autonomous.mdc` — целиком до первого действия на сервере.
- `docs/site/access-tools.md` — Yoast (`wpseo_titles`, `wpseo_taxonomy_meta`, `wp post meta`, `wp yoast index`) и шум `Wt::__wakeup()` от `wt_geotargeting_pro`.
- `docs/site/content-inventory.md` — страницы контактов 5 городов (`ekaterinburg` 4692, `snezhinsk` 4726, `chelyabinsk` 4785, `perm` 4787, `tyumen` 4794) и CPT `region` (5 записей).
- Остальное не открывать.

## Scope

На проде (Site ops):

1. Диагностика (только чтение, уточнение фактов от 2026-11-17):
   - предварительно проверено (2026-11-17): в `<title>` и `<meta name="description">` плейсхолдера нет, утечка идёт только в `og:description` и Yoast JSON-LD (`WebPage.name`/`description`) на 2 страницах (`/`, `/contacts/all/`), 6 категориях и ~7% выборки товаров (~50 из 758); причина — `wt_geotargeting_pro` (`1.7.6`, `modules/WtGtPost/WtGtPost.php`) подписывается на `wpseo_title`, `wpseo_opengraph_title`, `wpseo_metadesc`, но не покрывает `wpseo_opengraph_desc` и `wpseo_schema_graph` / `wpseo_schema_webpage`;
   - зафиксировать перед правкой текущий вывод `curl` с `User-Agent: GPTBot/1.0` на `/`, `/contacts/all/`, `/catalog/magnity-pvh/`, `/category/awards/znachki/`, `/contacts/perm/` (`<title>`, `description`, `og:description`, JSON-LD, заголовок `Set-Cookie: wt_geo_data`);
   - прочитать в WP опции `wpseo_titles`, настройки `wt_geotargeting_pro`, в каких постметах/опциях стоит `{region_*}`, и как работает текущая геоподмена телефона/города в шапке.
2. Подтверждение человека (`заблокировано: человек` через `AskQuestion`):
   - по `T11` (DaData / `wt_geotargeting_pro`): выбрать — передать новый рабочий токен DaData (вне git), переключить определение города на локальную базу без DaData или отключить автозапись DaData-запросов (оставив ручной выбор города в шапке);
   - по `T01` (выбор архитектуры — альтернативы):
     - обновить `wt_geotargeting_pro` до новой версии (проверить закрытие `wpseo_opengraph_desc` и `wpseo_schema_graph` в Yoast 27.x);
     - заменить плагин на `BelingoGeo`;
     - реализовать собственный геоплагин (геоподстановка в контенте/SEO/OG/JSON-LD, обработка ИИ-ботов, cookie без DaData-ошибок);
     - добавить обёртку фильтров `wpseo_opengraph_desc` и `wpseo_schema_graph` (`mu-plugin` / `wp-plugin`) поверх текущего `wt_geotargeting_pro`;
     - заменить `{region_*}` в SEO-полях Yoast на статичный текст («в Екатеринбурге» + отдельные статичные title/description для 4 филиалов `/contacts/perm/`, `/contacts/chelyabinsk/`, `/contacts/tyumen/`, `/contacts/snezhinsk/`).
3. Бэкап БД: `sudo -u www-data wp db export /tmp/insain-db-before-ai-seo-geo.sql --path=/var/www/insain.ru`.
4. Применить согласованные правки в Yoast и `wt_geotargeting_pro`, выполнить `wp yoast index --path=/var/www/insain.ru`, сбросить кэш (`wp cache flush` и при необходимости `wp litespeed-purge all` / `purge url`).
5. Проверка `curl` с `GPTBot/1.0` и проверка отображения телефона/выбора города в браузере (и отсутствии сбоя на страницах калькуляторов на API).
6. Строки для обновления `STATUS.md` / `docs/site/content-inventory.md` записать в раздел «Результат» (при закрытии перенести в `main`).

## Файлы

- WordPress: опции и мета Yoast (`wpseo_titles`, `_yoast_wpseo_title`, `_yoast_wpseo_metadesc`, при необходимости `wpseo_taxonomy_meta`), настройки плагина `wt_geotargeting_pro`

## Не-scope

- Перенос поп-апа выбора города из начала HTML и кэширование главной — `T07` / `T13`.
- Наполнение разметки `Organization` / `LocalBusiness` реквизитами — `T08`.
- Формы ezFC, цены, `calc_service`, `wp-plugin/`, удаление товаров `prg`.

## Критерии приёмки

Команды из корня репозитория / по SSH на `insain-prod`.

- [ ] Бэкап БД создан: `ssh insain-prod "ls -lh /tmp/insain-db-before-ai-seo-geo.sql"` — файл ненулевого размера.
- [ ] В исходном HTML для ботов нет плейсхолдеров региона: `curl.exe -sS -A "GPTBot/1.0" https://insain.ru/` (и категории/карточки/филиалы) — поиск `{region_` возвращает 0 совпадений в `<title>`, `<meta name="description">`, JSON-LD и HTML в целом.
- [ ] Cookie `wt_geo_data` не содержит текста ошибки DaData: `curl.exe -sS -I -A "GPTBot/1.0" https://insain.ru/` — в заголовках ответа нет `SUGGESTIONS` / `disabled for token`.
- [ ] На страницах филиалов (`/contacts/perm/`, `/contacts/chelyabinsk/`, `/contacts/tyumen/`, `/contacts/snezhinsk/`) — свои уникальные `<title>` с нужным городом, HTTP `200`.
- [ ] Калькулятор на API жив: `curl.exe -fsS https://insain.ru/api/v1/calculators | head -c 100` и страница калькулятора плакеток отдаёт `200`.

## Проверки

- [ ] `make check` — N/A, если в git только доки (или зелёный при наличии правок в git)
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md); ключи/токены DaData не попали в git и логи

## Риски

- Прод: глобальные шаблоны Yoast меняют `<title>` и `description` всех страниц и товаров; откат — из бэкапа `/tmp/insain-db-before-ai-seo-geo.sql` или восстановление значений `wpseo_titles` / настроек `wt_geotargeting_pro`, зафиксированных в шаге 1.
- Цены: нет.
- Формы: не сломать выбор города и шапку с формами ezFC.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

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
- Откат:
