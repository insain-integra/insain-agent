# site-content-guardrails

Статус: черновик
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

- [ ] В `docs/site/access-tools.md` есть явные правила: бэкап перед правками контента, запрет прямой правки `[vc_…]` и `wpseo_taxonomy_meta` без админки/проверенного скрипта, `wp yoast index` после CLI-правок Yoast, запрет выдумывать факты.
- [ ] Создан `.cursor/skills/site-page-seo/SKILL.md` с пошаговым чеклистом до/после и отката.
- [ ] `python scripts/dev.py check` — зелёный вывод (код возврата 0).

## Проверки

- [ ] `python scripts/dev.py check` — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет (меняется только документация и skill в git).
- Цены: нет.
- Формы: нет.

## Режим

обычный

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
