# wt-geotargeting-update

Статус: черновик
Сложность: высокая
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: боевой плагин `wt_geotargeting_pro` 1.7.6 → 1.18.1 впервые, skill нет; смена класса JS и cookie ломает шапку.
Чат: новая сессия Site ops (Opus 5.5), `python scripts/dev.py lock acquire prod wt-geotargeting-update`.

## Цель

На https://insain.ru активен WT Geotargeting Pro 1.18.1. Выбор города в шапке пишет локацию, телефон и город на главной отображаются, цена контрольного товара совпадает со снимком до обновления, главная и страница калькулятора отдают HTTP 200. Лицензия плагина не остаётся DEMO.

## Контекст и ссылки

- Инструкция вендора: https://web-technology.biz/cms-wordpress/plugin-wt-geotargeting-for-cms-wordpress/obnovlenie-plagina/ — бэкап, архив, установка поверх. Последняя Pro на странице: 1.18.1.
- Журнал: https://web-technology.biz/cms-wordpress/plugin-wt-geotargeting-pro/changelog/ — с 1.7.9 класс `WtLocation` → `WtGtLocation`; с 1.10 cookie `wt_geo_data` → `wt_geolocation_data`; с 1.8 меняется логика цен WooCommerce; при активации 1.18 синхронизируются флаги Yoast, WooCommerce и WPBakery.
- `STATUS.md` — строка `wt_geotargeting_pro` 1.7.6 и warning `Wt::__wakeup()` в `includes/WtKit.php`.
- `todo/ai-seo-geo-yoast.md` — ждёт эту задачу. Диагноз T01/T11 снят с 1.7.6: тема `.../themes/insain/modal/region-selection-generate.php` вызывает `WtLocation.setCity`, cookie ошибки DaData — `wt_geo_data`.
- `.cursor/rules/insain-site-autonomous.mdc` — целиком до первого действия на сервере. Установка чужого плагина не входит в «Делай самостоятельно».
- `docs/site/access-tools.md` — wp-cli; warning `Wt::__wakeup()` — шум, пока он есть.
- Архив 1.18.1 передаёт человек. В git архив не класть.
- Остальное не открывать.

## Scope

Прод без git. Всё делает Site ops. `lock acquire prod wt-geotargeting-update` до первого шага, `release` в конце.

1. Инвентарь, только чтение. В «Результат» без секретов и без API-ключа DaData:
   - в архиве головной PHP: `Version: 1.18.1`, slug каталога тот же (`wt_geotargeting_pro`);
   - `wp plugin get wt_geotargeting_pro --fields=name,status,version` — active, 1.7.6;
   - в новом `js/wt-location.js` (распаковка во временный каталог, не в `wp-content`): какое глобальное имя класса (`WtGtLocation` или алиас `WtLocation`) и какое имя cookie пишет плагин;
   - настройки плагина: субдомены (кириллица / punycode), корневые директории города в URL, региональные цены и таблица `wt_gt_product_meta` включены или нет;
   - `rg` по теме и `mu-plugins` на `WtLocation` и `wt_geo_data`;
   - снимок до правки: `curl.exe -sS -D - -o NUL https://insain.ru/` (код, имя `Set-Cookie`), город и телефон на главной, цена одного товара (URL записать), `<title>` главной.
2. Бэкап до установки: `sudo -u www-data wp db export /tmp/insain-db-wt-geo-176-20261121.sql --path=/var/www/insain.ru`; каталог плагина в `/tmp/wt_geotargeting_pro-1.7.6.tgz`; копия `region-selection-generate.php` в `/tmp`. Каталог агент читает без sudo. Не читать — стоп, установку не начинать.
3. Подтверждение человека через `AskQuestion` до любой записи. Показать итог п.1–2. Варианты: «Ставить 1.18.1 сейчас», «Стоп, файлы не менять». Если включены кириллические субдомены или корневая директория города в URL — в карточке это прямо написано, по умолчанию стоп.
4. После «Ставить»: `sudo -u www-data wp plugin install <zip> --force --path=/var/www/insain.ru`. Плагин не деактивировать и не удалять (`wp plugin delete` может снести данные). Zip лежит в `/tmp` и читается `www-data`.
5. В том же окне, только если новый JS больше не отдаёт старые имена: в теме `WtLocation` → `WtGtLocation`, чтение cookie `wt_geo_data` → `wt_geolocation_data`. Чужие вхождения в плагине не патчить — их затирает архив. Гонку клика по городу (нет `return false`) не чинить.
6. Если админка или опция лицензии показывает DEMO — `заблокировано: человек`. Ключ вводит человек в админке. Ключ не писать в чат, отчёт и git.
7. Смоук из критериев. Расхождение цены контрольного товара, HTTP не 200, фатал PHP или `{region_` в `<title>` главной, которого не было в снимке п.1 — откат, затем `заблокировано: человек`.
8. В git только строка версии в `STATUS.md`. Если warning `Wt::__wakeup()` пропал из вывода `wp plugin list` — поправить одну фразу про этот шум в `STATUS.md` и `docs/site/access-tools.md`. Замер DaData (`isBot`, запись `403` в cookie) — абзац в «Результат», настройки DaData не менять.

Откат: каталог плагина и файл темы вернуть из `/tmp` через `sudo -u www-data wp eval` (sudo умеет только `wp` и nginx, `cp` от root недоступен). Если активация мигрировала опции или таблицы — `wp db import` дампа п.2. Пока окно открыто, другие правки WordPress не делать: импорт затрёт их вместе с плагином.

## Файлы

- `/var/www/insain.ru/wp-content/plugins/wt_geotargeting_pro/*`
- `/var/www/insain.ru/wp-content/themes/insain/modal/region-selection-generate.php`
- `STATUS.md`
- `docs/site/access-tools.md`

## Не-scope

- Правки Yoast, плейсхолдеры `{region_*}`, квота и токен DaData, гонка клика в модалке — `todo/ai-seo-geo-yoast.md` после этой задачи.
- Региональные цены, запасы и коэффициенты WooCommerce не включать и не перенастраивать. Совпала цена снимка — достаточно.
- Переименование субдоменов и сохранение «настроек URL (Alpha)» — только если п.1 показал, что они включены, и человек отдельно подтвердил.
- `calc_service`, формы ezFC, `wp-plugin/`, деплой API.
- Skill `site-page-seo` всё ещё говорит cookie `wt_geo_data` — не править здесь.

## Критерии приёмки

Команды с рабочей машины или `ssh insain-prod`. Секреты и ключ лицензии в вывод не печатать.

- [ ] `ssh insain-prod "ls -lh /tmp/insain-db-wt-geo-176-20261121.sql /tmp/wt_geotargeting_pro-1.7.6.tgz"` — оба файла ненулевого размера.
- [ ] `sudo -u www-data wp plugin get wt_geotargeting_pro --field=version --path=/var/www/insain.ru` — `1.18.1`, статус active.
- [ ] `curl.exe -sS -o NUL -w "%{http_code}" https://insain.ru/` — `200`. В `<title>` главной нет нового `{region_`, которого не было в снимке п.1.
- [ ] Цена контрольного товара с URL из «Результата» совпадает со снимком до обновления.
- [ ] В теме нет вызова несуществующего класса: если новый JS отдаёт только `WtGtLocation`, `rg -n "WtLocation" /var/www/insain.ru/wp-content/themes/insain` — пусто.
- [ ] Browser MCP: на главной город и телефон на месте; клик по городу в `#modalLocationSelection` не даёт в консоли `WtLocation is not defined` / `WtGtLocation is not defined`, после перезагрузки в шапке выбранный город. Какое имя cookie записалось — строка в «Результат».
- [ ] `curl.exe -fsS https://insain.ru/api/v1/calculators | head -c 100` и страница калькулятора плакеток — HTTP 200.
- [ ] `STATUS.md`: версия `wt_geotargeting_pro` — `1.18.1`. Фраза про `Wt::__wakeup()` совпадает с фактическим выводом `wp plugin list`.
- [ ] Лицензия не DEMO (статус в админке или опции, без значения ключа в отчёте).

## Проверки

- [ ] `make check` — зелёный, если в git менялись `STATUS.md` или `docs/site/access-tools.md`
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md); ключ лицензии и токен DaData не в diff и не в «Результате»

## Риски

- Прод: замена каталога плагина и правка модалки темы на живом сайте. Откат — каталог и PHP темы из `/tmp`, при миграции БД — импорт `/tmp/insain-db-wt-geo-176-20261121.sql`.
- Цены: логика WooCommerce в плагине с 1.8 другая. Контрольный товар не совпал — откат, региональные цены не трогать.
- Формы: шапка с выбором города стоит рядом с формами ezFC. Формы не менять; смоук — главная открывается и город выбирается.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

- 21.11.2026 — Analyst, Grok 4.7 — задача заведена отдельно от `ai-seo-geo-yoast`; человек подтвердил коммит в main — дальше Site ops (Opus 5.5)

## Найдено вне scope

- `.cursor/skills/site-page-seo/SKILL.md` проверяет геоподмену cookie `wt_geo_data`. После установки имя cookie сменится, skill надо поправить отдельной правкой.

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-21 —
- Часы человека: оценка 2 ч — 1 ч на коммит задачи
- Работа агентов:
- Было / стало: плагин 1.7.6 → 1.18.1
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Откат:
