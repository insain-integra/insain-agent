# ai-seo-geo-yoast

Статус: черновик
Сложность: высокая
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: правка глобальных SEO-шаблонов Yoast и геоплагина `wt_geotargeting_pro` на проде впервые (задачи `T01` и `T11` аудита).
Чат: новая сессия Site ops (Opus 5.5) с захватом `lock acquire prod ai-seo-geo-yoast`.

## Цель

В исходном HTML главной, категорий, карточек товаров и страниц контактов филиалов (при запросе с `User-Agent: GPTBot/1.0` и без cookie) отсутствует шаблон `{region_name_prepositional}` в `<title>`, `<meta name="description">` и JSON-LD schema.org (`T01`). Ошибка DaData «Feature 'SUGGESTIONS' disabled for token…» не попадает в cookie `wt_geo_data` (`T11`). Переключение города в модальном окне шапки (`#modalLocationSelection`) срабатывает с первого клика без гонки перезагрузки и повторного нажатия.

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
   - предварительно проверено (2026-11-18) по переключению города со 2-го раза:
     - `/var/www/insain.ru/wp-content/themes/insain/modal/region-selection-generate.php` (строки 31, 38): в `<a href="<?php echo $url; ?>" onclick="WtLocation.setCity(..., 'reload')">` нет `return false;` / `event.preventDefault()` — клик одновременно запускает `window.location.reload(true)` и переход по `href=""` (на `/contacts/*` — на `/contacts` с 301-редиректом на `/contacts/`); у ссылок городов нет закрытия модалки и блокировки повторного клика на время ответа сервера (1–5+ с);
     - `/var/www/insain.ru/wp-content/plugins/wt_geotargeting_pro/js/wt-location.js` (строки 81–84): `WtLocation` создаётся только в `jQuery(document).ready(...)`, поэтому ранний клик до готовности DOM падает без записи `wt_geo_data` и просто перезагружает страницу со старым городом;
   - предварительно проверено (2026-11-18) по `T11` / DaData:
     - в `wt_geotargeting_geobase` включён `base_name = dadata_service` с 40-символьным API-ключом; ошибка `403 Feature 'SUGGESTIONS' disabled for token…` означает не «неактуальный» токен, а исчерпание дневного лимита бесплатного тарифа (10 000 запросов/сут) или отключение пакета в ЛК DaData;
     - >10 000 запросов/сут набираются даже при малом числе живых посетителей: сайт работает на `nginx + PHP-FPM` без page-кэша (`advanced-cache.php` отсутствует, `fastcgi_cache` не настроен), `WtInitialization` вызывает `reloadData()` на `plugins_loaded` при каждом PHP-хите без cookie `wt_geo_data`, а список `WtGeolocation::isBot()` (2017 г.) не отсекает ИИ-ботов (`GPTBot`, `ClaudeBot`, `PerplexityBot` и др.) и современных краулеров; дополнительно нет серверного кэша по IP, а при IPv6 (`getIp()` ждёт только IPv4) уходит пустой `?ip=`;
     - в `includes/DaData.php` и `includes/WtGeolocation.php` (`1.7.6`) не проверяются HTTP-код ответа и `family === 'CLIENT_ERROR'`, из-за чего JSON ошибки вместе с API-ключом в `message` записывается в публичный заголовок `Set-Cookie: wt_geo_data`;
     - при планируемом обновлении `wt_geotargeting_pro` обязательно проверить в коде новой версии (`DaData.php`, `WtGeolocation.php`): отсекаются ли `403` / `CLIENT_ERROR` (без записи в cookie), обновлён ли `isBot()` под ИИ-ботов/краулеров и есть ли кэширование по IP / защита от пустого IPv6;
   - прочитать в WP опции `wpseo_titles`, настройки `wt_geotargeting_pro`, в каких постметах/опциях стоит `{region_*}`, и как работает текущая геоподмена телефона/города в шапке.
2. Подтверждение человека (`заблокировано: человек` через `AskQuestion`):
   - по `T11` (DaData / `wt_geotargeting_pro`): сначала проверить, решает ли обновление `wt_geotargeting_pro` фильтрацию ботов, обработку ошибок DaData без записи токена в cookie и укладывается ли расход в лимит; если нет — выбрать:
     - оставить DaData с доп. защитой (`mu-plugin` / правка фильтрации ботов, кэш IP и блокировка записи `CLIENT_ERROR` в `wt_geo_data`) и при необходимости перевыпустить скомпрометированный в cookie токен DaData (вне git);
     - переключить определение города на локальную базу без DaData;
     - отключить автозапрос по IP (`base_name = none`, город по умолчанию Екатеринбург + ручной выбор города в шапке);
   - по `T01` (выбор архитектуры — альтернативы):
     - обновить `wt_geotargeting_pro` до новой версии (проверить закрытие `wpseo_opengraph_desc` и `wpseo_schema_graph` в Yoast 27.x);
     - заменить плагин на `BelingoGeo`;
     - реализовать собственный геоплагин (геоподстановка в контенте/SEO/OG/JSON-LD, обработка ИИ-ботов, cookie без DaData-ошибок);
     - добавить обёртку фильтров `wpseo_opengraph_desc` и `wpseo_schema_graph` (`mu-plugin` / `wp-plugin`) поверх текущего `wt_geotargeting_pro`;
     - заменить `{region_*}` в SEO-полях Yoast на статичный текст («в Екатеринбурге» + отдельные статичные title/description для 4 филиалов `/contacts/perm/`, `/contacts/chelyabinsk/`, `/contacts/tyumen/`, `/contacts/snezhinsk/`).
3. Бэкап БД: `sudo -u www-data wp db export /tmp/insain-db-before-ai-seo-geo.sql --path=/var/www/insain.ru`; также сохранить копии правимых файлов темы/плагина в `/tmp/` (`region-selection-generate.php`, `wt-location.js`) до правки.
4. Применить согласованные правки в Yoast и `wt_geotargeting_pro`, починить переключение города в `region-selection-generate.php` и `wt-location.js` (убрать гонку `onclick` + `href`, обеспечить раннюю инициализацию `WtLocation` до `ready` и закрытие/блокировку модалки на время reload), выполнить `wp yoast index --path=/var/www/insain.ru`, сбросить кэш (`wp cache flush` и при необходимости `wp litespeed-purge all` / `purge url`).
5. Проверка `curl` с `GPTBot/1.0` и проверка в браузере (Browser MCP): отображение телефона/города, переключение города в `#modalLocationSelection` с первого клика (на `/` и `/contacts/ekaterinburg/`, с пустой cookie и при смене города) и отсутствие сбоя на страницах калькуляторов на API.
6. Строки для обновления `STATUS.md` / `docs/site/content-inventory.md` записать в раздел «Результат» (при закрытии перенести в `main`).

## Файлы

- WordPress: опции и мета Yoast (`wpseo_titles`, `_yoast_wpseo_title`, `_yoast_wpseo_metadesc`, при необходимости `wpseo_taxonomy_meta`), настройки и JS плагина `wt_geotargeting_pro` (`/var/www/insain.ru/wp-content/plugins/wt_geotargeting_pro/js/wt-location.js`), шаблон модалки темы (`/var/www/insain.ru/wp-content/themes/insain/modal/region-selection-generate.php`)

## Не-scope

- Перенос поп-апа выбора города из начала HTML и кэширование главной — `T07` / `T13`.
- Наполнение разметки `Organization` / `LocalBusiness` реквизитами — `T08`.
- Формы ezFC, цены, `calc_service`, `wp-plugin/`, удаление товаров `prg`.

## Критерии приёмки

Команды из корня репозитория / по SSH на `insain-prod`.

- [ ] Бэкап БД создан: `ssh insain-prod "ls -lh /tmp/insain-db-before-ai-seo-geo.sql"` — файл ненулевого размера.
- [ ] В исходном HTML для ботов нет плейсхолдеров региона: `curl.exe -sS -A "GPTBot/1.0" https://insain.ru/` (и категории/карточки/филиалы) — поиск `{region_` возвращает 0 совпадений в `<title>`, `<meta name="description">`, JSON-LD и HTML в целом.
- [ ] Cookie `wt_geo_data` не содержит текста ошибки DaData и API-токена: `curl.exe -sS -D - -o NUL -A "GPTBot/1.0" https://insain.ru/` — в заголовках ответа нет `SUGGESTIONS` / `disabled for token` / `CLIENT_ERROR`, а при включённой DaData запросы ИИ-ботов (`GPTBot`, `ClaudeBot`, `PerplexityBot`) и краулеров не вызывают обращения к DaData.
- [ ] На страницах филиалов (`/contacts/perm/`, `/contacts/chelyabinsk/`, `/contacts/tyumen/`, `/contacts/snezhinsk/`) — свои уникальные `<title>` с нужным городом, HTTP `200`.
- [ ] Переключение города в модалке `#modalLocationSelection` срабатывает с первого клика в Browser MCP (на `/` и `/contacts/ekaterinburg/`): cookie `wt_geo_data` сразу получает выбранный город, переход не конфликтует с `href=""` / `/contacts`, город в шапке меняется после первой перезагрузки, новых ошибок JS в консоли нет.
- [ ] Калькулятор на API жив: `curl.exe -fsS https://insain.ru/api/v1/calculators | head -c 100` и страница калькулятора плакеток отдаёт `200`.

## Проверки

- [ ] `make check` — N/A, если в git только доки (или зелёный при наличии правок в git)
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md); ключи/токены DaData не попали в git и логи

## Риски

- Прод: глобальные шаблоны Yoast меняют `<title>` и `description` всех страниц и товаров; откат — из бэкапа `/tmp/insain-db-before-ai-seo-geo.sql` или восстановление значений `wpseo_titles` / настроек `wt_geotargeting_pro`, зафиксированных в шаге 1; файлы темы/плагина (`region-selection-generate.php`, `wt-location.js`) восстанавливаются из копий в `/tmp/`.
- Безопасность/квота DaData: пока `wt_geotargeting_pro` 1.7.6 отдаёт `403` в `Set-Cookie: wt_geo_data`, текущий API-ключ DaData виден в публичных заголовках ответа; если DaData остаётся включённой после фикса/обновления плагина — ключ стоит перевыпустить в ЛК DaData (вне git).
- Цены: нет.
- Формы: не сломать выбор города и шапку с формами ezFC.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

- 18.11.2026 — Analyst — диагностирован баг переключения города со 2-го раза (`region-selection-generate.php`, `wt-location.js`), добавлен в scope задачи — дальше Site ops
- 18.11.2026 — Analyst — диагностирована причина >10 000 запросов/сут к DaData (отсутствие page-кэша под nginx, устаревший `isBot()` 2017 г. без ИИ-ботов/краулеров, нет кэша IP и проверка только IPv4) и утечка токена в `Set-Cookie: wt_geo_data` при 403; уточнён scope `T11` с учётом планируемого обновления `wt_geotargeting_pro` — дальше Site ops

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
