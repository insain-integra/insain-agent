# ai-seo-org-schema

Статус: черновик
Сложность: высокая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Opus 5.5
Почему: JSON-LD `Organization` на всех страницах и `LocalBusiness` на 5 городских — впервые, без skill; mu-plugin из git на прод выкладывается впервые.

## Цель

Yoast-граф JSON-LD на https://insain.ru описывает бренд «Инсайн» как `Organization`, а 5 страниц `/contacts/<город>/` — как `LocalBusiness` со своим юрлицом, адресом, телефоном, почтой и графиком. Все значения — только подтверждённые из `docs/site/facts.md`. В `sameAs` нет Instagram и WhatsApp. Аудит `T08`.

## Контекст и ссылки

- `docs/site/facts.md` — разделы «Города», «Реквизиты», «Профили (sameAs)», «Решения для schema и страниц». Единственный источник значений.
- `todo/EPIC-ai-seo.md` — Волна 1.
- `docs/site/access-tools.md` — Yoast (`wpseo_titles`, `wp yoast index`, сброс кэша), правила правки контента.
- `docs/site/content-inventory.md` — строка 14 (Yoast 27.5, Local SEO нет) и строка 109 (`insain-geo-yoast-fix.php` — уже фильтрует `wpseo_schema_graph`; не ломать).
- `calc_service/tests/test_wp_plugin_forms.py` — образец pytest по файлам для WordPress.
- Остальное не открывать.

## Scope

Смешанная задача.

- В git (Implementer, ветка `task/ai-seo-org-schema`):
  - `wp-mu-plugins/insain-org-schema.php` — новый mu-plugin. Фильтр `wpseo_schema_organization` дописывает в `Organization` `foundingDate` 2008, `contactPoint` (телефон и почта Екатеринбурга), `areaServed` (5 городов). Фильтр `wpseo_schema_graph` на страницах `/contacts/ekaterinburg/`, `/contacts/snezhinsk/`, `/contacts/chelyabinsk/`, `/contacts/perm/`, `/contacts/tyumen/` добавляет узел `LocalBusiness`: `@id` `<url>#localbusiness`, `name`, `legalName`, `taxID`, `address` (`PostalAddress`), `telephone`, `email`, `openingHoursSpecification` пн–пт 09:00–18:00, `url`, `parentOrganization` → `@id` Organization Yoast. Юрлицо: Екатеринбург — ООО «ИНСАЙН-ПРИНТ», остальные 4 — ООО «ИНСАЙН». Адрес Екатеринбурга — фактический (офис 1), у Челябинска, Перми и Тюмени — без `streetAddress`. Страницы определять по slug, не по id. Значения — массив в начале файла с комментарием-ссылкой на `docs/site/facts.md`.
  - `scripts/check_org_schema.py` — читает JSON-LD с `/` и 5 городских страниц и печатает по строке `ok <url>` или причину; код возврата 0, только если все 6 ok. Проверяет: имя `Organization` — «Инсайн», в `sameAs` есть `vk.com/insain_ru` и `t.me/insainbot`, нет `instagram` и `wa.me`; у каждого `LocalBusiness` `taxID`, телефон, почта и город совпадают с `docs/site/facts.md`; нигде нет `{region_`.
  - `calc_service/tests/test_mu_org_schema.py` — по тексту PHP: оба ИНН, телефоны и почты 5 городов есть; `ПОМЕЩ 8`, `instagram`, `wa.me` нет. Падает, если значение пропало из PHP.
- На проде (Site ops, после слияния в `main`, `lock acquire prod ai-seo-org-schema`):
  1. Снимок до: `wpseo_titles` и `wpseo_social` в JSON (`wp option get … --format=json`) в `/tmp/ai-seo-org-schema-<дата>/`; JSON-LD 6 страниц там же; вывод `python scripts/check_org_schema.py` (ожидаемо красный).
  2. Yoast, «Представление сайта» (админка через Browser MCP): организация, название «Инсайн», логотип — текущий; «Другие профили» — только https://vk.com/insain_ru и https://t.me/insainbot, Instagram удалить.
  3. `php -l` файла, выкладка `wp-mu-plugins/insain-org-schema.php` с `main` в `wp-content/mu-plugins/` тем же каналом, что `insain-geo-yoast-fix.php` (канал записать в `docs/site/access-tools.md`).
  4. `wp yoast index`, `wp cache flush`, `wp litespeed-purge all`.
  5. `python scripts/check_org_schema.py` — 6 ok; https://validator.schema.org/ для `/` и `/contacts/ekaterinburg/` — 0 ошибок; 200 и форма на одной странице калькулятора (smoke, что mu-plugin ничего не уронил).

## Файлы

- `wp-mu-plugins/insain-org-schema.php`, `scripts/check_org_schema.py`, `calc_service/tests/test_mu_org_schema.py`, `todo/ai-seo-org-schema.md`.
- Общие, только в `main` при закрытии (Site ops): `docs/site/access-tools.md` (канал выкладки mu-plugin), `docs/site/content-inventory.md` (строка про `insain-org-schema.php`), `STATUS.md` (строка mu-plugins). Пересечений с активными `todo/` по файлам ветки нет.

## Не-scope

- Снятие WhatsApp и Instagram из подвала и блоков «Мы в сети», рубрика календарей 2020–2021 — отдельная задача.
- Правка `/contacts/all/` (телефон, почта, фраза про онлайн-офис) — `ai-seo-faq-and-facts`; в schema эту страницу не размечать.
- `FAQPage`, `/faq/`, тексты страниц, счётчики — `ai-seo-faq-and-facts`.
- Перенос `insain-geo-yoast-fix.php` в git — строка в «Найдено вне scope».
- Координаты `geo`, отзывы, `aggregateRating`, Яндекс Бизнес и 2ГИС — их нет в `docs/site/facts.md`.
- Плагин `wp-plugin/` (insain-calc-bridge) не трогать.

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_mu_org_schema.py -q` — `passed`; с удалённым ИНН в PHP — `failed`.
- [ ] `python scripts/check_org_schema.py` — 6 строк `ok`, код возврата 0.
- [ ] validator.schema.org для `/` и `/contacts/ekaterinburg/` — 0 ошибок (скриншот или текст результата в отчёте Site ops).
- [ ] `curl -s -o NUL -w "%{http_code}" https://insain.ru/` и 5 городских страниц — `200`; одна страница калькулятора — `200`, форма ezFC на месте.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md); в PHP только значения из `docs/site/facts.md` с пометкой «подтверждено».

## Риски

- Прод: `Organization` выводится в графе на каждой странице — ошибка в mu-plugin ломает JSON-LD или PHP всего сайта. Откат: удалить `wp-content/mu-plugins/insain-org-schema.php` (удаление на сервере — после «да» через `AskQuestion`), вернуть `wpseo_titles` и `wpseo_social` из снимка шага 1, `wp yoast index`, сброс кэша.
- Прод: `insain-geo-yoast-fix.php` тоже фильтрует `wpseo_schema_graph` — проверить, что маски `{region_*}` не вернулись (скрипт проверки).
- Прод: `LocalBusiness` без улицы (Челябинск, Пермь, Тюмень) — решение владельца; валидатор может дать предупреждение, не ошибку.
- Цены: нет
- Формы: нет; smoke одной страницы калькулятора.

## Режим

прод

## Журнал передач

2026-11-29 — Analyst, Opus 5.5 — задача по `docs/site/facts.md` и решениям владельца от 29.11.2026 — дальше Implementer.

## Найдено вне scope

- `wp-content/mu-plugins/insain-geo-yoast-fix.php` (задача `ai-seo-geo-yoast`) есть только на сервере, исходника в git нет.

## Результат

- Ветка, PR или коммит:
- Период: 2026-11-29 —
- Часы человека: <оценка 1 ч — 1 ч на коммит задачи | N ч факт>
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
