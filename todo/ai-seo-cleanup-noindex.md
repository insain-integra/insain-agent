# ai-seo-cleanup-noindex

Статус: черновик
Сложность: высокая
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: удаление/410/301 страниц и настройка `noindex` / `sitemap` Yoast на боевом сайте впервые (задача `T02` аудита).
Чат: новая сессия Site ops (Opus 5.5) с захватом `lock acquire prod ai-seo-cleanup-noindex` (последовательно с другими прод-задачами).

## Цель

Страницы-заглушки (демо Porto `/services/`, 2 демо-записи CPT `faq` с Lorem ipsum, `sample-page`, `test-mode`, `header-types` и подтверждённые человеком шаблонные английские страницы) сняты с публикации (410 или 301). Служебные страницы WooCommerce (`cart`, `checkout`, `my-account`, `my-orders`, `wishlist`, `order-tracking`) и технические CPT (`porto_builder`, неиспользуемый `faq`, при необходимости `region`) закрыты `noindex` и исключены из `sitemap_index.xml`.

## Контекст и ссылки

- `insain-ru-ai-audit.md` — задача `T02`, «Результаты проверки → Sitemap / Контент-заглушки», «План правок → п. 2».
- `todo/EPIC-ai-seo.md`.
- `.cursor/rules/insain-site-autonomous.mdc` — целиком до первого действия на сервере.
- `docs/site/content-inventory.md` — «Страницы» (список 38 страниц: `sample-page`, `header-types`, `site-map`, `contact-us`, `our-office`, `careers`, `services`, `test-mode`, служебные Woo, CPT `faq` 2 шт., `porto_builder` 23 шт.).
- `docs/site/access-tools.md` — Yoast (`wpseo_titles`, `_yoast_wpseo_meta-robots-noindex`, `wp yoast index`).
- Остальное не открывать.

## Scope

На проде (Site ops):

1. Инвентарь (только чтение):
   - проверить содержимое, статус и наличие ссылок из меню/страниц на кандидатов-заглушек (`/services/`, 2 записи CPT `faq`, `sample-page`, `test-mode`, `header-types`, а также `careers`, `our-office`, `contact-us`, `site-map`, `blog`);
   - проверить текущий `https://insain.ru/sitemap_index.xml` и дочерние карты: какие служебные страницы и CPT туда попадают сейчас;
   - проверить, как настроены `cart`, `checkout`, `my-account`, `my-orders`, `wishlist`, `order-tracking` (мета `_yoast_wpseo_meta-robots-noindex`, присутствие в sitemap).
2. Подтверждение человека (`заблокировано: человек` через `AskQuestion`):
   - утвердить точный список URL для снятия (draft/trash → 410 или 301 и куда именно, с учётом выбранного/будущего способа редиректов);
   - утвердить список служебных страниц и CPT (`porto_builder`, `faq`, `region` и др.) для `noindex` и исключения из sitemap Yoast.
3. Бэкап БД: `sudo -u www-data wp db export /tmp/insain-db-before-ai-seo-cleanup.sql --path=/var/www/insain.ru`.
4. Применить изменения в WP и Yoast, выполнить `wp yoast index --path=/var/www/insain.ru`, сбросить кэш.
5. Проверить через `curl` HTTP-коды удалённых страниц, `noindex` в `<head>` служебных страниц и состав `sitemap_index.xml`, а также работу корзины/чекаута и `/my-account/`.
6. Сводку чисел до/после для `docs/site/content-inventory.md` записать в «Результат».

## Файлы

- WordPress: страницы-заглушки и CPT `faq`, служебные страницы WooCommerce, настройки Yoast `wpseo_titles` (отображение типов контента в поиске) и мета `_yoast_wpseo_meta-robots-noindex`

## Не-scope

- Создание нового раздела `/faq/` с 15–25 вопросами и разметкой `FAQPage` — Волна 1 (`ai-seo-faq-and-facts`, `T04`).
- Удаление 694 товаров `prg…` и редиректы карточек — `todo/supplier-old-cleanup.md`.
- Массовые 301-редиректы `/catalog_hg?rid=…` — Волна 2 (`ai-seo-redirects-indexation`, `T09`).
- Правка меню (`Main Menu`), шаблонов темы и форм ezFC.

## Критерии приёмки

- [ ] Бэкап БД создан: `ssh insain-prod "ls -lh /tmp/insain-db-before-ai-seo-cleanup.sql"` — файл ненулевого размера.
- [ ] Заглушки не отдают `200`: `curl.exe -sS -o NUL -w "%{http_code}\n"` по каждому утверждённому URL заглушки (`/services/`, `sample-page`, `test-mode`, `header-types`, демо-FAQ) — код `410` или `301` (на живую страницу, не на другую заглушку).
- [ ] Служебные страницы WooCommerce (`cart`, `checkout`, `my-account`, `my-orders`, `wishlist`, `order-tracking`) отсутствуют в `page-sitemap.xml` и содержат `<meta name="robots" content="noindex` в HTML (проверено скриптом через `curl`).
- [ ] В `sitemap_index.xml` нет дочерних карт `porto_builder` и демо-`faq`.
- [ ] Корзина/оформление заказа (`/cart/`, `/checkout/`) и главная (`https://insain.ru/`) отдают `200`.

## Проверки

- [ ] `make check` — N/A, если в git только доки
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: случайное снятие/noindex нужной страницы или поломка `cart`/`checkout`/`my-account`; откат — возврат статуса `publish` по ID, сброс опций Yoast или восстановление из `/tmp/insain-db-before-ai-seo-cleanup.sql`.
- Цены: нет.
- Формы: не трогать страницы с формами ezFC и калькуляторами.

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
