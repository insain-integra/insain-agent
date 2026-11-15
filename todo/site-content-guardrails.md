# site-content-guardrails

Статус: закрытие
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: не нужен
Почему: правила работы агентов с контентом прода и базовый skill контура сайта (`G2`).
Чат: новая сессия Implementer (Opus 5.5) в worktree задачи.

## Цель

У агентов есть единые правила безопасной правки страниц, WPBakery, Yoast SEO, меню и товаров WooCommerce на https://insain.ru, а также стартовый skill для правки страниц и SEO-меты. Это снимает риск поломки разметки `[vc_…]`, потери SEO-индекса Yoast и необратимых изменений на проде при выполнении `todo/EPIC-ai-seo.md`.

## Контекст и ссылки

- Эпик `todo/EPIC-site-content.md` (цель `G2`) и `todo/EPIC-ai-seo.md`.
- `.cursor/rules/insain-site-autonomous.mdc` — правила автономной работы с продом и обязательные подтверждения человека.
- `docs/site/access-tools.md` — каналы доступа (wp-cli, Browser MCP), ограничения WPBakery `[vc_…]`, `wp yoast index`, `wpseo_taxonomy_meta`.
- `docs/site/content-inventory.md` — карта объектов сайта (WPBakery на 6 страницах и 12 `porto_builder`, Yoast 27.5, child-тема `insain`, 63 товара `INS`).
- Образец оформления skill: `.cursor/skills/ezfc-form-to-api/SKILL.md` (только структура/формат, не содержание).
- Остальное не открывать.

## Scope

В git (Implementer):

1. Дополнить `docs/site/access-tools.md` (раздел правил безопасности редакционного контента):
   - обязательный бэкап БД (`sudo -u www-data wp db export … --path=/var/www/insain.ru`) перед массовыми или структурными правками контента/SEO/меню;
   - правило одного типа объектов за задачу (не мешать страницы, товары, меню и код темы без явного scope);
   - запрет править страницы с `_wpb_vc_js_status=true` (шорткоды `[vc_…]`) и сериализованную опцию `wpseo_taxonomy_meta` «вслепую» через `wp post update` / SQL — только Browser MCP (WPBakery / админка Yoast) или точечный проверенный PHP-скрипт с бэкапом и diff;
   - обязательный `wp yoast index` и сброс кэша (`wp cache flush` / `wp litespeed-purge`) после правок SEO-полей через wp-cli;
   - правило «не выдумывать факты»: цены, сроки, реквизиты, цифры заказов только из подтверждённого источника владельца или `calc_service`.
2. Уточнить в `.cursor/rules/insain-site-autonomous.mdc` (если строка не дублирует `AGENTS.md`, уложиться в компактный объём) ссылку на редакционные правила в `docs/site/access-tools.md` и обязательность `wp yoast index` при CLI-правке Yoast.
3. Создать стартовый skill `.cursor/skills/site-page-seo/SKILL.md` для правки страниц (в т. ч. WPBakery/Porto) и SEO-меты Yoast (чек-лист: бэкап, замер `curl` до/после, правка, переиндексация Yoast, сброс кэша, проверка `<h1>`, `<title>`, `description`, JSON-LD и отсутствие ошибок консоли).

## Файлы

- `docs/site/access-tools.md`
- `.cursor/rules/insain-site-autonomous.mdc`
- `.cursor/skills/site-page-seo/SKILL.md`

## Не-scope

- Правки на проде (WordPress, БД, Nginx, плагины).
- Написание остальных skills (товар Woo, меню/тема, медиа) — делаются по мере прогона задач `todo/EPIC-ai-seo.md`.
- Правка `AGENTS.md`, `STATUS.md`, `docs/site/content-inventory.md` и `docs/site/forms.md`.

## Критерии приёмки

- [x] В `docs/site/access-tools.md` есть явные правила: бэкап перед правками контента, запрет прямой правки `[vc_…]` и `wpseo_taxonomy_meta` без админки/проверенного скрипта, `wp yoast index` после CLI-правок Yoast, запрет выдумывать факты.
- [x] Создан `.cursor/skills/site-page-seo/SKILL.md` с пошаговым чеклистом до/после и отката.
- [x] `python scripts/dev.py check` — зелёный вывод (код возврата 0).

## Проверки

- [x] `python scripts/dev.py check` — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет (меняется только документация и skill в git).
- Цены: нет.
- Формы: нет.

## Режим

обычный

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

16.11.2026 — Implementer, Opus 5.5 — правила контента в access-tools.md, ссылка и wp yoast index в insain-site-autonomous.mdc, skill site-page-seo; make check зелёный (код 0) — дальше Reviewer
16.11.2026 — Reviewer, Grok 4.7 — есть блокер: откат в skill не восстанавливает post_content — дальше Implementer
16.11.2026 — Implementer, Opus 5.5 — блокер Ревью 1 закрыт: откат в skill шаг 5 через `--post_content="$(cat …)"` в stdin `ssh insain-prod "tr -d '\r' | bash -s"` с проверкой diff, только для страниц без WPBakery/porto_builder; в промпте Ревью 1 «Статус:» → «Статус задачи —» (тест одной строки статуса); make check зелёный (код 0) — дальше Reviewer
16.11.2026 — Reviewer, Grok 4.7 — есть блокер: откат меты в шаге 5 теряет кириллицу в конвейере PowerShell 5.1 — дальше Implementer
16.11.2026 — Implementer, Opus 5.5 — блокер Ревью 2 закрыт: мета откатывается из файлов на сервере (`$(cat /tmp/meta-…)`, сохраняются в шаге 0.3) с diff-проверкой, перед конвейером `$OutputEncoding` и `[Console]::InputEncoding` — UTF-8 без BOM; в PowerShell 5.1 stdin — UTF-8 байты кириллицы, `3f` 0, без BOM; make check зелёный (код 0) — дальше Reviewer
16.11.2026 — Reviewer, Grok 4.7 — принято: блокер Ревью 2 закрыт, кириллица меты в шаге 5 доходит без замены — дальше человек
16.11.2026 — человек — принято — закрытие

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит: `task/site-content-guardrails`, слияние в `main` при закрытии.
- Период: 16.11.2026.
- Часы человека: 0.
- Работа агентов: Implementer (Opus 5.5), три сессии; Reviewer (Grok 4.7), три.
- Доработка по Ревью 2: в skill шаг 0.3 каждый меняемый ключ меты сохраняется на сервере `wp post meta get <id> <ключ> > /tmp/meta-<id>-<ключ>-<задача>-before.txt`; шаг 5 восстанавливает мету `wp post meta update <id> <ключ> "$(cat /tmp/meta-…)"` и сверяет `wp post meta get … | diff -` с файлом (ожидается `meta restored`), ключ, которого не было, — `wp post meta delete`. Кириллица в here-string больше не нужна. Первая строка блока — `$OutputEncoding = [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false`: без `$OutputEncoding` кириллица уходит как `3f`, без `[Console]::InputEncoding` при кодовой странице 65001 (терминал Cursor) PowerShell 5.1 добавляет в stdin BOM `efbbbf`, и первая команда `bash -s` сломается. Чем проверено (локально, прод не трогался): блок шага 5 из SKILL.md (отступ fence снят, `ssh insain-prod` заменён на `python`, добавлена строка `echo 'Печать визиток'`) в `powershell.exe -File` (5.1.26100.9711 Desktop) — код 0, в stdin `3f` 0 шт., первые байты `656368` (без BOM), «Печать» — `d09fd0b5d187d0b0d182d18c`, `<задача>` — `3cd0b7d0b0d0b4d0b0d187d0b03e`, `$(cat` буквально, аргумент — `tr -d '\r' | bash -s`. Для сравнения тот же here-string без настройки: `273f3f3f3f3f3f27` (6 × `3f`); только с `$OutputEncoding`: UTF-8, но префикс `efbbbf`. `python scripts/dev.py check` — код 0, calc_service `621 passed in 55.76s`, bot_service `81 passed in 1.80s`. Замечание «желательно» не правилось.
- Доработка по Ревью 1: в skill шаг 5 первый пункт — только страницы без `_wpb_vc_js_status=true` и не `porto_builder`; контент возвращается `wp post update <id> --post_content="$(cat /tmp/page-<id>-<задача>-before.txt)"`, мета — `wp post meta update`, затем `wp post get … | diff -` с файлом (ожидается `restored`). Команды передаются here-string `@'…'@` в stdin `ssh insain-prod "tr -d '\r' | bash -s"`: `$(…)` раскрывается на сервере, кавычки не теряются в аргументе `ssh` (PowerShell 5.1), CRLF срезается. WPBakery и `porto_builder` — ревизией, со ссылкой на правило 3. Замечание «желательно» не правилось. Чем проверено: `python scripts/dev.py check` — код 0, calc_service `621 passed in 56.39s`, bot_service `81 passed in 1.19s`; команда на проде не прогонялась (прод вне scope).
- Было / стало: были разрозненные оговорки в таблице `access-tools.md` и одна строка про бэкап в правиле; стали пять явных правил правки контента, ссылка на них из правила прода и skill `site-page-seo` с чеклистом до/после и откатом.
- Сделано:
  - `docs/site/access-tools.md` — новый раздел «Правила правки редакционного контента»: бэкап БД перед массовой/структурной правкой (имя дампа с задачей и датой), один тип объектов за задачу, запрет слепой правки `[vc_…]` и `wpseo_taxonomy_meta` (только Browser MCP или проверенный PHP-скрипт с бэкапом и diff), `wp yoast index` + `wp cache flush` + `wp litespeed-purge all` после CLI-правки Yoast, запрет выдумывать факты; строка «Страницы» в таблице ссылается на раздел.
  - `.cursor/rules/insain-site-autonomous.mdc` — раздел «Перед массовыми правками» заменён на «Правки контента WordPress»: ссылка на раздел правил и skill, бэкап, обязательный `wp yoast index` (3 строки, без дублей `AGENTS.md`).
  - `.cursor/skills/site-page-seo/SKILL.md` — шаги 0–5: выбор канала по `_wpb_vc_js_status`, сохранение старых значений, бэкап, замер `curl.exe` и `yoast/v1/get_head` до/после (`<title>`, `<h1>`, `description`, JSON-LD), правка, переиндексация и кэш, консоль Browser MCP, откат (файл/мета, ревизии WPBakery, импорт дампа только через человека).
  - `docs/dashboard.md` — пересобран `make check` из-за смены статуса.
- Чем проверено: `python scripts/dev.py check` — код возврата 0, calc_service `621 passed in 130.95s`, bot_service `81 passed in 1.63s`. Self-review по чеклисту AGENTS.md: в diff только файлы задачи и дашборд, цен и кода нет, тексты по-русски.
- Не сделано и почему: команды skill на проде не прогонялись — прод вне scope (Site ops не нужен); проверятся первой задачей `todo/EPIC-ai-seo.md`.
- Требуется решение: нет.

## Ревью 1

Вердикт: есть блокер.

Diff `task/site-content-guardrails` против `main` (незакоммиченный): `docs/site/access-tools.md`, `.cursor/rules/insain-site-autonomous.mdc`, новый `.cursor/skills/site-page-seo/SKILL.md`, файл задачи. `docs/dashboard.md` — пересборка статуса, не замечание. `python scripts/dev.py check` повторно не запускался: в «Результате» код 0, calc_service 621 passed, bot_service 81 passed; в diff нет кода калькуляторов.

Закрыто: пять правил в `access-tools.md` (бэкап, один тип объектов, запрет слепой правки `[vc_…]` и `wpseo_taxonomy_meta`, `wp yoast index` и сброс кэша, запрет выдумывать факты); в `insain-site-autonomous.mdc` ссылка на этот раздел и обязательный `wp yoast index` после CLI-меты, без дубля `AGENTS.md`. В skill есть замер до/после (`curl.exe`, `<title>`, `<h1>`, `description`, JSON-LD), канал правки, переиндексация, кэш и проверка консоли.

- `блокер` — `.cursor/skills/site-page-seo/SKILL.md`, шаг 5: `wp post update <id> /tmp/page-<id>-<задача>-before.txt` не восстанавливает контент. У `wp post update` позиционные аргументы — только id, путь к файлу в контент не читается, команда завершится ошибкой id. Критерий «чеклист отката» этой командой не выполнен. Нужна команда, которая записывает содержимое сохранённого файла в `--post_content` и запускается из PowerShell через `ssh insain-prod`: подстановка `$(...)` внутри двойных кавычек выполняется локально, а не на сервере. Первый пункт шага 5 ограничить страницами без `_wpb_vc_js_status=true`. Для WPBakery и `porto_builder` оставить откат ревизией: `wp post update --post_content` на таких страницах запрещён правилом 3 в `access-tools.md`.
- `желательно` — `docs/site/access-tools.md`, п. 3: фраза «`wp post update --post_content=…`, REST и SQL их не трогают» читается как «эти команды шорткоды не меняют». `--post_content` перезаписывает `[vc_…]`. Заголовок пункта и «Только через Browser MCP…» запрет уже содержат; формулировку сменить на явный запрет («ими `post_content` не править»). Сдачу не держит, Implementer не правит, пока не отметит человек.

```text
Implementer. todo/site-content-guardrails.md, ветка task/site-content-guardrails

Статус задачи — доработка. Закрой блокер из «Ревью 1». Замечание «желательно» не правь, пока его не отметит человек.

Блокер: `.cursor/skills/site-page-seo/SKILL.md`, шаг 5. Команда `wp post update <id> /tmp/page-<id>-<задача>-before.txt` не восстанавливает контент: позиционные аргументы `wp post update` — только id. Нужна рабочая команда, которая пишет содержимое сохранённого файла в `--post_content` и выполняется из PowerShell через `ssh insain-prod` (подстановка `$(...)` в двойных кавычках не должна читаться локально вместо сервера). Первый пункт шага 5 — только страницы без `_wpb_vc_js_status=true`. Страницы WPBakery и `porto_builder` откатываются ревизией, как во втором пункте.

Файлы scope не расширять. Коммит не делать, push не делать. После правки — `python scripts/dev.py check` (код 0), статус `ревью`, строка в «Журнал передач».
```

## Ревью 2

Вердикт: есть блокер.

Повторный круг — только шаг 5 `.cursor/skills/site-page-seo/SKILL.md` после «Ревью 1». `python scripts/dev.py check` повторно не запускался: в «Результате» код 0 после этой правки, в diff нет кода калькуляторов.

Блокер Ревью 1 по контенту закрыт. Первый пункт шага 5 — только страница без `_wpb_vc_js_status=true` и не `porto_builder`; WPBakery и `porto_builder` откатываются ревизией. Here-string `@'…'@` из кода шага 5 (отступ code fence снят) передан нативному процессу вместо `ssh`: в stdin есть буквальная подстрока `$(cat`, аргумент команды — `tr -d '\r' | bash -s` одной строкой. Локальный PowerShell `$(cat)` не раскрывает.

- `блокер` — тот же шаг 5, строка `wp post meta update … '<старое значение>'` внутри here-string. Windows PowerShell 5.1.26100.9711, `$OutputEncoding` = `us-ascii`: конвейер в нативную программу заменяет кириллицу на байт `0x3F` до `bash -s`. На коде шага 5 hex имени файла содержит `3c3f3f3f3f3f3f3e` (`<задача>`, шесть букв → шесть `?`), hex значения меты — `?` на месте «старое значение». Старые `_yoast_wpseo_title` и `_yoast_wpseo_metadesc` на insain.ru на кириллице: откат запишет вопросительные знаки. Контент из `$(cat)` на сервере этой подстановкой не портится. Нужно, чтобы значение меты доходило до `wp` на сервере без замены: выставить `$OutputEncoding` в UTF-8 без BOM перед конвейером или восстановить мету из файла на сервере, как контент. Проверка локально, без прода: прогнать here-string с кириллическим значением меты в PowerShell 5.1 и показать UTF-8 байты, а не `3f`. В промпте не писать вторую строку, которая начинается с `Статус:`.
- `желательно` — из «Ревью 1», `docs/site/access-tools.md`, п. 3: формулировка «REST и SQL их не трогают». Сдачу не держит, в этом круге не менять.

```text
Implementer. todo/site-content-guardrails.md, ветка task/site-content-guardrails

Статус задачи — доработка. Закрой блокер из «Ревью 2». Замечание «желательно» не правь.

Блокер: `.cursor/skills/site-page-seo/SKILL.md`, шаг 5. Откат контента через `--post_content="$(cat …)"` и here-string в `ssh insain-prod "tr -d '\r' | bash -s"` оставлен: `$(cat)` в PowerShell не раскрывается. В том же скрипте `wp post meta update … '<старое значение>'` теряет кириллицу: Windows PowerShell 5.1 кодирует конвейер в нативную программу как `$OutputEncoding` = `us-ascii` и подставляет `?` (байт 0x3F). Так откат запишет вопросительные знаки в русские `_yoast_wpseo_title` и `_yoast_wpseo_metadesc`. Значение меты должно дойти до сервера без замены (UTF-8 без BOM у `$OutputEncoding` перед конвейером или восстановление меты из файла на сервере). На проде не запускать. Проверка: here-string с кириллицей в PowerShell 5.1, в stdin нативной программы UTF-8 байты, не `3f`.

Файлы scope не расширять. Коммит не делать, push не делать. В промпте и в тексте задачи не добавлять вторую строку, которая начинается с `Статус:`. После правки — `python scripts/dev.py check` (код 0), статус `ревью`, строка в «Журнал передач».
```

## Ревью 3

Вердикт: принято.

Повторный круг — только шаг 5 `.cursor/skills/site-page-seo/SKILL.md` после «Ревью 2». `python scripts/dev.py check` повторно не запускался: в «Результате» код 0 после этой правки, в diff нет кода калькуляторов. Строка `Статус:` в шапке одна, значение `ревью`.

Блокер Ревью 2 закрыт. Шаг 0.3 пишет каждый меняемый ключ на сервер: `wp post meta get <id> <ключ> > /tmp/meta-<id>-<ключ>-<задача>-before.txt`. Шаг 5 больше не кладёт значение меты в here-string: `wp post meta update <id> <ключ> "$(cat /tmp/meta-…-before.txt)"`, затем `wp post meta get … | diff -` с тем же файлом (`meta restored`). Перед конвейером обе переменные — UTF-8 без BOM: `$OutputEncoding = [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false`.

Проверка локально, `ssh` и прод не вызывались. Windows PowerShell 5.1.26100.9711, кодовая страница 65001. Блок шага 5 (отступ code fence снят, `ssh insain-prod` заменён на `python`, первой строкой here-string добавлен `echo 'Печать визиток'`) через `powershell.exe -NoProfile -File`: код 0; в stdin байт `3f` — 0, BOM нет; «Печать» — `d09fd0b5d187d0b0d182d18c`; `<задача>` и `<ключ>` на месте; подстрока `$(cat` буквальная; аргумент программы — `tr -d '\r' | bash -s`. Тот же блок только с `$OutputEncoding`: кириллица цела, но stdin начинается с `efbbbf`. Без обеих настроек: кириллицы нет, `3f` — 53. `tr -d '\r'` BOM не снимает, поэтому в skill нужны обе строки.

- `желательно` — из «Ревью 1», без изменений: `docs/site/access-tools.md`, п. 3, фраза «REST и SQL их не трогают». Сдачу не держит, правки не требуется.
