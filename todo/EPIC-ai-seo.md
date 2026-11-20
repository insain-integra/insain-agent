# EPIC-ai-seo

Статус: черновик
Цель: G4

## Цель

Сайт https://insain.ru корректно индексируется и цитируется ИИ-поисковиками (Алиса/Нейро, ChatGPT, Copilot, Claude, Perplexity, Gemini, DeepSeek, GigaChat) и поисковыми системами: чистый HTML без технических шаблонов геоподмены и страниц-заглушек, валидная разметка schema.org, актуальные факты и FAQ, заполненные карточки своей продукции `INS…`, быстрая отдача HTML и согласованная навигация. Источник аудита — `insain-ru-ai-audit.md` (задачи `T01`–`T15`).

## Связь с другими целями

- **G1 (`todo/EPIC-forms-to-api.md`, срок 30.11.2026):** переключение 45 боевых форм ezFC на API в приоритете; правки общих скриптов/CSS и кэша (`T13`) вынесены после G1, правки шаблонов/меню (`T07`) включают smoke форм на API.
- **G2 (`todo/EPIC-site-content.md`):** базовые правила безопасности и skills контура сайта обкатываются на первых задачах этого эпика (`site-content-guardrails` → `ai-seo-h1-structure`, далее карточки `INS` и меню).
- **G7 (`todo/EPIC-supplier-catalog.md`):** 694 карточки `prg…` удаляются в `todo/supplier-old-cleanup.md`, поэтому `T06` выполняется только для ~63 карточек `INS…`, а требования `T06` встроены в `todo/supplier-parser.md` и `todo/supplier-catalog-load.md`. Правки меню (`T07`) и общие 301-редиректы (`T09`) идут после `todo/supplier-old-cleanup.md`.

## Задачи Волны 0 (в работе сейчас)

- `site-content-guardrails` (закрыто 2026-11-16, `docs/history/log.md`) — правила безопасности правок WP/WPBakery/Yoast, дополнение `docs/site/access-tools.md`, каркас skill контура сайта (G2, предпосылка `T03`).
- `todo/wt-geotargeting-update.md` — предпосылка `T01`/`T11`: WT Geotargeting Pro 1.7.6 → 1.18.1 на проде, шапка и лицензия живы. Пока она не закрыта, `ai-seo-geo-yoast` не стартует.
- `todo/ai-seo-geo-yoast.md` — `T01` + `T11`: убрать `{region_name_prepositional}` из title/description/JSON-LD в Yoast; решить проблему токена DaData / cookie геоплагина. Ждёт `todo/wt-geotargeting-update.md`.
- `ai-seo-cleanup-noindex` (закрыто 2026-11-17, `docs/history/log.md`) — `T02`: выставить `noindex` и убрать из sitemap служебные Woo, технические CPT (`porto_builder`, `faq`) и страницы-заглушки; перевод заглушек в 410/301 перенесён в Волну 2 (`ai-seo-redirects-indexation`).
- `ai-seo-h1-structure` (закрыто 2026-11-16, `docs/history/log.md`) — `T03`: один `<h1>` на главной, категориях и карточках. Предпосылка `site-content-guardrails` закрыта (2026-11-16, `docs/history/log.md`).

## Планируемые волны (файлы `todo/` заводятся перед стартом волны)

### Волна 1 — контент и разметка (после Волны 0 и подтверждения факт-листа владельцем)

- **ai-seo-faq-and-facts** (`T04` + `T05`, после `ai-seo-cleanup-noindex`): обновить устаревшие даты/факты («11 лет», 2019, календари-2027, `sameAs`) + новый раздел `/faq/` (15–25 реальных вопросов с подтверждёнными цифрами и валидной разметкой `FAQPage`).
- **ai-seo-org-schema** (`T08`, после `ai-seo-geo-yoast`): JSON-LD `Organization` (главная) и `LocalBusiness` (5 страниц `/contacts/<city>/`) с подтверждёнными реквизитами.
- **ai-seo-ins-products** (`T06` только для ~63 товаров `INS…`, после `ai-seo-geo-yoast` и `ai-seo-h1-structure`): описание, таблица характеристик, ориентир цены «от» (для 36 калькуляторных — согласованно с `calc_service`), meta/title, `Product`/`Offer`; без касания форм ezFC. Обкатка skill карточки Woo + SEO.

### Волна 2 — меню, HTML-структура, редиректы и индексация (после `todo/supplier-old-cleanup.md`)

- **ai-seo-html-nav-popup** (`T07`, после `supplier-old-cleanup` и `ai-seo-h1-structure`): программно скрывать в HTML-меню пустые категории `product_cat` (сохраняя в админке всю структуру из 287 пунктов для будущей загрузки поставщиков), `noindex` пустым рубрикам, перенос поп-апа выбора города после `<main>`, обёртка `<nav>` / `<main>` / `<article>`, smoke форм ezFC.
- **ai-seo-redirects-indexation** (`T09` + `T10` + `T12`, после `supplier-old-cleanup` и `ai-seo-faq-and-facts`): 301 со старых URL (`/catalog_hg?rid=…`) и 410/301 со страниц-заглушек из `ai-seo-cleanup-noindex` (`/services/`, `/careers/`, `/our-office/`, `/contact-us-advanced/`, `/site-map/`, `/header-types/`, `/sample-page/`, `/test-mode/`, демо-`faq`) тем же механизмом, что выбран в `supplier-old-cleanup`; регистрация в Яндекс Вебмастере, Google Search Console, Bing Webmaster Tools + IndexNow; выкладка `/llms.txt`.

### Волна 3 — производительность, внешние карточки и регламент (после G1 — 30.11.2026)

- **ai-seo-perf-assets** (`T13`, после G1): настройка страничного кэша для гостей (убрать безусловный `Set-Cookie: wt_geo_data`), сокращение числа JS/CSS и неиспользуемых модулей Porto/WPBakery без риска для форм ezFC.
- **ai-seo-external-and-reglament** (`T14` старт + `T15` регламент): выравнивание Яндекс Бизнеса и 2ГИС для 5 городов + оформление постоянного регламента в `docs/site/` для ежемесячного мониторинга ботов (`GPTBot` и др.), переходов из ИИ и публикаций ответов раз в 2 недели.

## Порядок

1. `site-content-guardrails` закрыта (2026-11-16, `docs/history/log.md`). Дальше `todo/wt-geotargeting-update.md` (прод, `lock prod`), затем `todo/ai-seo-geo-yoast.md` (прод, `lock prod`). `ai-seo-cleanup-noindex` закрыта 2026-11-17 (`docs/history/log.md`).
2. `ai-seo-h1-structure` (закрыто 2026-11-16, `docs/history/log.md`) можно стартовать: предпосылка закрыта.
3. Перед стартом Волны 1 владелец передаёт подтверждённый факт-лист (адреса, телефоны, ИНН, ссылки `sameAs`, цифры заказов/сроков и ответы для FAQ).
4. После `todo/supplier-old-cleanup.md` заводятся задачи Волны 2; после G1 — задачи Волны 3.
