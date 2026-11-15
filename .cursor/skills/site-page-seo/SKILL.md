---
name: site-page-seo
description: Правка страницы на insain.ru (в том числе WPBakery/Porto и шаблонов porto_builder) и SEO-меты Yoast — заголовок, description, focus keyword, текст страницы. Порядок — бэкап, замер curl до, правка нужным каналом, wp yoast index, сброс кэша, замер после (h1, title, description, JSON-LD), консоль, откат. Применять, когда задача из todo/ меняет одну или несколько опубликованных страниц или их SEO-мету. Не для товаров WooCommerce, меню, медиа, темы и форм ezFC (skill ezfc-form-to-api).
---

# Правка страницы и SEO-меты Yoast

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.

Прод-шаги — Site ops, под `python scripts/dev.py lock acquire prod <задача>` / `release prod <задача>`. Правила, которые здесь не повторяются, — `docs/site/access-tools.md`, раздел «Правила правки редакционного контента»; карта страниц и признак WPBakery — `docs/site/content-inventory.md`. Правка опубликованной страницы, не названной в scope задачи, — через подтверждение человека (`.cursor/rules/insain-site-autonomous.mdc`).

Обозначения: `<id>` — id страницы, `<url>` — её адрес на https://insain.ru, `<задача>` — имя задачи. Команды wp-cli ниже выполняются как `ssh insain-prod "sudo -u www-data wp … --path=/var/www/insain.ru 2>/dev/null"` (stderr — шум `Wt::__wakeup()`); в примерах сокращено до `wp …`.

## 0. До правки

1. В задаче есть: список `<id>`, что меняется (текст, `title`, `description`, focus keyword) и источник новых фактов. Цифры, цены, сроки, реквизиты без источника владельца или `calc_service` не писать — вопрос в отчёт.
2. Канал правки по странице:
   - `wp post meta get <id> _wpb_vc_js_status` = `true` или запись — `porto_builder`: текст только конструктором WPBakery через Browser MCP;
   - иначе текст — `wp post update <id> --post_content=…` или редактор в админке;
   - мета Yoast (`_yoast_wpseo_title`, `_yoast_wpseo_metadesc`, `_yoast_wpseo_focuskw`) — `wp post meta update` или метабокс Yoast;
   - SEO рубрик (`wpseo_taxonomy_meta`) — только админка Yoast, не wp-cli и не SQL.
3. Старые значения — в отчёт и в файлы на сервере: `wp post get <id> --field=post_content > /tmp/page-<id>-<задача>-before.txt`, `wp post meta list <id> --keys=_yoast_wpseo_title,_yoast_wpseo_metadesc,_yoast_wpseo_focuskw --format=json`, для каждого меняемого ключа — `wp post meta get <id> <ключ> > /tmp/meta-<id>-<ключ>-<задача>-before.txt` (ключа нет — в отчёт «не было»).
4. Больше одной страницы или структурная правка — бэкап БД: `wp db export /tmp/insain-db-<задача>-<ГГГГММДД-ЧЧММ>.sql`. Путь — в отчёт.

## 1. Замер до

С локальной машины (в PowerShell именно `curl.exe`, не алиас):

```powershell
curl.exe -fsS "<url>" -o $env:TEMP\page-<id>-before.html
Select-String -Path $env:TEMP\page-<id>-before.html -Pattern '<title>','<h1','name="description"','application/ld\+json' | Select-Object -First 10
curl.exe -fsS "https://insain.ru/wp-json/yoast/v1/get_head?url=<url>" -o $env:TEMP\head-<id>-before.json
```

Записать в отчёт: `<title>`, число и текст `<h1>` (на странице ровно один), `description`, наличие JSON-LD (`application/ld+json`). Переменная `{region_name_prepositional}` в заголовках — от геоплагина, не раскрывать и не удалять.

## 2. Правка

Одна страница за раз, каналом из шага 0.2. В WPBakery — менять только текст нужных блоков, не структуру строк и колонок; после «Обновить» проверить, что страница не перешла в классический редактор.

## 3. Переиндексация и кэш

- Мета Yoast менялась через wp-cli — `wp yoast index`, иначе `<head>` отдаёт старые значения.
- Всегда: `wp cache flush`, `wp litespeed-purge all`.

## 4. Замер после

1. Повторить команды шага 1 в файлы `…-after`. Сравнить: `<title>` и `description` — новые, `<h1>` один и ожидаемый, JSON-LD на месте и `get_head` отвечает 200.
2. Browser MCP: открыть `<url>`, вёрстка не сломана (нет сырых `[vc_…]` в тексте), в консоли нет новых ошибок по сравнению с другой страницей того же шаблона.
3. В отчёт: до/после по каждому полю, путь бэкапа, ошибки консоли (или «нет»).

## 5. Откат

- Одна страница без `_wpb_vc_js_status=true` и не `porto_builder`: контент и мета — из файлов шага 0.3 на сервере (ключ, которого не было, — `wp post meta delete <id> <ключ>`); затем шаг 3. Команды уходят на сервер через stdin `bash -s`: так `$(cat …)` раскрывается на сервере, а не в PowerShell, и кавычки не теряются при передаче аргумента в `ssh`; `tr -d '\r'` убирает CRLF из конвейера PowerShell. Windows PowerShell 5.1 кодирует конвейер в нативную программу по `$OutputEncoding` (по умолчанию `us-ascii`, кириллица → `?`), а при кодовой странице 65001 добавляет BOM из `[Console]::InputEncoding` (`EF BB BF` ломает первую команду `bash -s`), поэтому первой строкой обе — UTF-8 без BOM; кириллицу в here-string всё равно не писать, значения — только из файлов на сервере.

  ```powershell
  $OutputEncoding = [Console]::InputEncoding = New-Object System.Text.UTF8Encoding $false
  @'
  sudo -u www-data wp post update <id> --post_content="$(cat /tmp/page-<id>-<задача>-before.txt)" --path=/var/www/insain.ru 2>/dev/null
  sudo -u www-data wp post meta update <id> <ключ> "$(cat /tmp/meta-<id>-<ключ>-<задача>-before.txt)" --path=/var/www/insain.ru 2>/dev/null
  sudo -u www-data wp post get <id> --field=post_content --path=/var/www/insain.ru 2>/dev/null | diff - /tmp/page-<id>-<задача>-before.txt && echo restored
  sudo -u www-data wp post meta get <id> <ключ> --path=/var/www/insain.ru 2>/dev/null | diff - /tmp/meta-<id>-<ключ>-<задача>-before.txt && echo meta restored
  '@ | ssh insain-prod "tr -d '\r' | bash -s"
  ```

  Строки `meta update` и `meta get … | diff` — по одной на каждый ключ из шага 0.3. Ожидаются `restored` и `meta restored`; вывод `diff` — откат не совпал, блокер в отчёт.
- Страница с `_wpb_vc_js_status=true` или `porto_builder`: `--post_content` запрещён (`docs/site/access-tools.md`, правило 3) — «Редакции» записи в админке (Browser MCP), вернуть ревизию до правки; затем шаг 3.
- Массовая правка или сломана разметка нескольких страниц — импорт дампа только с подтверждением человека (`wp db import` перетирает всю БД, включая заказы после дампа): блокер `заблокировано: человек` с вариантами «точечно вернуть ревизии» / «импорт дампа».

## Роли и цепочка

- Analyst — задача со списком страниц, новыми текстами/метой и источником фактов.
- Site ops — шаги 0–5 на проде, отчёт с до/после в «Результат» задачи.
- Человек — приёмка вида (скриншот) через `AskQuestion`, затем `finish-task`.
