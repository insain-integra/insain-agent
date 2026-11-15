# ai-seo-h1-structure

Статус: черновик
Сложность: средняя
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: правка WPBakery главной страницы и шаблона заголовков категорий Porto на проде с обкаткой skill `.cursor/skills/site-page-seo/SKILL.md` (`T03`, `G2`).
Чат: новая сессия Site ops (Opus 5.5) с захватом `lock acquire prod ai-seo-h1-structure`.

## Цель

На главной странице (`ID 143`), в категориях товаров (`product_cat`) и в карточках товаров (`product`) в исходном HTML присутствует ровно один тег `<h1>` с реальным заголовком документа (`T03`). Рецепт правки WPBakery/Porto закреплён в `.cursor/skills/site-page-seo/SKILL.md`.

## Контекст и ссылки

- `insain-ru-ai-audit.md` — задача `T03`, «План правок → п. 3».
- `todo/EPIC-ai-seo.md` и `todo/EPIC-site-content.md` (`G2`).
- `.cursor/skills/site-page-seo/SKILL.md` и `docs/site/access-tools.md` (из `site-content-guardrails`, закрыто 2026-11-16, `docs/history/log.md`).
- `.cursor/rules/insain-site-autonomous.mdc`.
- `docs/site/content-inventory.md` — главная (`ID 143`, `_wpb_vc_js_status=true`), тема `insain` 1.1 / `porto` 7.8.5, шаблоны `porto_builder`.
- Остальное не открывать.

## Scope

1. Диагностика (только чтение):
   - снять все `<h1>` и `<h2>` на главной (`/`), 3–5 категориях (`/category/awards/znachki/` и др.), 3 карточках `INS…`, страницах `/about/` и `/shipment/`;
   - установить источник второго `<h1>` в категориях (настройка «Page Title» / шаблон Porto vs заголовок в описании категории `description`) и убедиться, что на главной заголовок «Главная» выведен как `<h2>` или скрыт.
2. Подтверждение человека (`заблокировано: человек` через `AskQuestion`):
   - утвердить текст `<h1>` на главной (ориентир аудита: «Изготовление сувенирной, наградной и рекламной продукции в Екатеринбурге»);
   - утвердить способ исправления дубля `<h1>` на страницах категорий (оставить `<h1>` в шапке Porto Page Title и перевести заголовки в описаниях категорий в `<h2>`, либо наоборот).
3. Бэкап БД: `sudo -u www-data wp db export /tmp/insain-db-before-ai-seo-h1.sql --path=/var/www/insain.ru`.
4. Применить правки через Browser MCP (WPBakery на странице 143 / настройки Porto / описания категорий), сбросить кэш.
5. Дополнить `.cursor/skills/site-page-seo/SKILL.md` проверенными на практике шагами (в т.ч. для WPBakery и Porto Page Title).
6. Проверка через `curl` и Browser MCP (отсутствие визуальных поломок и работа калькуляторов на API).

## Файлы

- WordPress: главная страница `ID 143` (WPBakery), настройки заголовков категорий Porto / описания категорий `product_cat`
- `.cursor/skills/site-page-seo/SKILL.md` (уточнение по итогам реального прогона)

## Не-scope

- Перенос поп-апа выбора города и оборачивание `<nav>` / `<main>` — Волна 2 (`T07`).
- Массовое наполнение описаний 63 карточек `INS…` — Волна 1 (`T06`).
- Формы ezFC, `calc_service`, `wp-plugin/`.

## Критерии приёмки

- [ ] Бэкап БД создан: `ssh insain-prod "ls -lh /tmp/insain-db-before-ai-seo-h1.sql"` — ненулевой размер.
- [ ] Главная: `curl.exe -sS -A "GPTBot/1.0" https://insain.ru/` — ровно 1 тег `<h1` (проверено Python-разбором в отчёте), текст соответствует утверждённому человеком.
- [ ] Категории и карточки: проверка минимум 3 категорий (включая `/category/awards/znachki/`) и 3 карточек `INS…` через `curl` — на каждой ровно 1 `<h1`.
- [ ] Главная и страница калькулятора плакеток отдают `200`, ошибок верстки и консоли при проверке Browser MCP нет.
- [ ] При правке `.cursor/skills/site-page-seo/SKILL.md` `python scripts/dev.py check` зелёный.

## Проверки

- [ ] `python scripts/dev.py check` — зелёный вывод (если правился skill в git)
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: правка главной страницы WPBakery и настроек темы Porto может задеть шапку/отступы; откат — ревизия страницы 143 в WP, откат настройки Porto или дамп `/tmp/insain-db-before-ai-seo-h1.sql`.
- Цены: нет.
- Формы: не затрагивать шорткоды/блоки ezFC.

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
