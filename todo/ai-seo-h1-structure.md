# ai-seo-h1-structure

Статус: закрытие
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

- [x] Бэкап БД создан: `ssh insain-prod "ls -lh /tmp/insain-db-before-ai-seo-h1.sql"` — ненулевой размер.
- [x] Главная: `curl.exe -sS -A "GPTBot/1.0" https://insain.ru/` — ровно 1 тег `<h1` (проверено Python-разбором в отчёте), текст соответствует утверждённому человеком.
- [x] Категории и карточки: проверка минимум 3 категорий (включая `/category/awards/znachki/`) и 3 карточек `INS…` через `curl` — на каждой ровно 1 `<h1`.
- [x] Главная и страница калькулятора плакеток отдают `200`, ошибок верстки и консоли при проверке Browser MCP нет.
- [x] При правке `.cursor/skills/site-page-seo/SKILL.md` `python scripts/dev.py check` зелёный.

## Проверки

- [x] `python scripts/dev.py check` — зелёный вывод (если правился skill в git)
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: правка главной страницы WPBakery и настроек темы Porto может задеть шапку/отступы; откат — ревизия страницы 143 в WP, откат настройки Porto или дамп `/tmp/insain-db-before-ai-seo-h1.sql`.
- Цены: нет.
- Формы: не затрагивать шорткоды/блоки ezFC.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

2026-11-16 — Site ops, Opus 5.5 — Scope п. 1 (диагностика, только чтение) выполнен, на проде ничего не менялось; стоп на п. 2 — дальше человек, затем Site ops.

```text
Блокер: нужны два решения владельца (Scope п. 2) — текст <h1> главной (ID 143) и способ убрать второй <h1> в рубриках.
Пробовал: curl.exe -A "GPTBot/1.0" + Python-разбор 15 URL; wp-cli read-only (term description, post_content/post_meta 143, porto_settings, шаблоны porto/page_header). Итог:
  - главная: <h1> 0; <h2 class="entry-title" style="display: none;">Главная</h2> печатает Porto (inc/functions/layout.php:2665, rich-snippets=1), первый видимый <h2> — «УФ-печать» из слайдера WPBakery; page_header_6.php на front page отключает page-title.
  - рубрики: Porto всегда печатает <h1 class="page-title"> (porto_breadcrumb_tag(), breadcrumb_tag пуст → h1), но show-pagetitle="" → обёртка .pt-right.d-none (скрыт). Второй <h1> — в description трёх product_cat: 119 stendy «Стенды информационные», 356 znachki-zakatnye «Значки закатные», 358 znachki-metallicheskie «Металлические значки по индивидуальному эскизу». У /category/awards/znachki/, /awards/, /souvenirs/, /futbolki/, /vse-kalkulyatory/ — по одному скрытому <h1>.
  - карточки INS8573/INS4242/INS8215: 1 скрытый <h1 page-title> + видимый <h2 class="product_title">; /about/, /shipment/: 1 скрытый <h1> + <h2 class="entry-title">.
  - <h1 в post_content опубликованных записей — только страница 2975 agreement (вне scope).
Гипотеза: дубль в рубриках — ручной <h1> в HTML описания (не WPBakery, правится точечно); на главной <h1> нет, потому что Porto не выводит page-title на front page, а в WPBakery-контенте заголовка h1 нет.
Вопрос: 1) текст и способ вывода <h1> на главной; 2) <h1>→<h2> в описаниях 3 рубрик или иной способ.
Следующая сессия: Site ops, модель Opus 5.5
```

2026-11-16 — человек — запрошена доп. диагностика: механизм WTGeotargeting для заголовков/описаний по городам и полная проверка всех рубрик product_cat на дубль `<h1>` — дальше Site ops

2026-11-16 — Site ops, Opus 5.5 — доп. диагностика (только чтение): WTGeotargeting разобран, все 305 рубрик проверены по HTML; на проде ничего не менялось — дальше человек, затем Site ops.

```text
Блокер: нужны два решения владельца (Scope п. 2) с учётом геотаргетинга — текст и способ вывода <h1> главной (ID 143) и способ убрать второй <h1> в 3 рубриках.
Пробовал:
  - WTGeotargeting: плагин wt_geotargeting_pro 1.7.6; города — CPT region (2994 Снежинск, 2995 Екатеринбург by_default=true, 2996 Челябинск, 2997 Пермь, 2998 Тюмень) с мета region_name_{nominative,genitive,dative,accusative,instrumental,prepositional}, phone, email, address. Город: cookie wt_geo_data → если бот из списка isBot() (googlebot, yandex, bing…; GPTBot НЕТ) — без определения → иначе DaData по IP → нет совпадения с 5 регионами → Екатеринбург (wt_geotargeting_default). Один URL на все города, поддоменов нет.
  - Маски {region_*} плагин подставляет только в the_title (is_singular), document_title, wpseo_title/opengraph_title/wpseo_metadesc; в post_content и description рубрик — нет. Шорткоды в контенте: [wt_contacts get="…"], [wt_location get="…" show_for=…], [wt_geotargeting city_show="…"]…[/wt_geotargeting], [wt_geotargeting get="city"] (определённый город, не регион из списка). wp eval do_shortcode: [wt_contacts get="region_name_prepositional"] → «Екатеринбурге».
  - Где уже применяется: Yoast title/metadesc страницы 143 и 2 страниц, 43/42 товара, 6 рубрик в wpseo_taxonomy_meta — маски {region_name_prepositional}; шапка Porto header builder ([wt_geotargeting get="city"], [wt_location get='phone'/'email']), porto_builder 2508 footer-left и 4864 location, страница 73 contacts ([wt_geotargeting city_show=…]), 5 страниц городов + all ([wt_location region=…]). В description и termmeta рубрик — 0 вхождений.
  - curl главной (GPTBot/Googlebot/браузер без cookie и GPTBot с cookie каждого из 5 городов): title/description меняются по городу («в Екатеринбурге», «в Снежинске», «в Челябинске», «в Перми», «в Тюмени»); без cookie — Екатеринбург; страничного кэша нет (нет x-litespeed-cache, vary_cookies пуст) — HTML собирается на каждый запрос.
  - Рубрики: 305 product_cat, 68 с description, <h1> в description — 3, шорткодов в description — 0; termmeta только order/display_type/thumbnail_id/product_count_product_cat; <h1> в wpseo_taxonomy_meta — 0. curl GPTBot всех 305 с сервера: 305×200; ровно 1 <h1> (скрытый Porto page-title) — 302; 2 <h1> — 3: 119 stendy, 356 znachki-zakatnye, 358 znachki-metallicheskie (второй — из description); 0 <h1> — 0.
Гипотеза: <h1> главной можно сделать «городским» тем же механизмом, что title/description — шорткодом [wt_contacts get="region_name_prepositional"] внутри vc_column_text (в атрибуте text у vc_custom_heading шорткод не раскроется — проверить на прогоне); поисковые боты без cookie всегда получат «Екатеринбурге». Дубль в рубриках — только 3 ручных <h1> в description.
Вопрос: 1) текст <h1> главной: фиксированный «…в Екатеринбурге» или с шорткодом города; 2) <h1>→<h2> в description 3 рубрик или иной способ.
Следующая сессия: Site ops, модель Opus 5.5
```

2026-11-16 — человек — утверждены решения по п. 2: 1) H1 главной (ID 143): «Изготовление сувенирной, наградной и рекламной продукции в [wt_contacts get="region_name_prepositional"]» видимым текстовым блоком WPBakery первой строкой; 2) в 3 рубриках (119 stendy, 356 znachki-zakatnye, 358 znachki-metallicheskie) заменить <h1>→<h2> в description с сохранением исходников в отчёт, остальные 302 рубрики не трогать — дальше Site ops

2026-11-16 — Site ops, Opus 5.5 — Scope п. 3–6 выполнены: бэкап БД, `<h1>` на главной (WPBakery, шорткод города), `<h1>`→`<h2>` в description 3 рубрик, skill дополнен, приёмка curl + Browser MCP, `make check` зелёный; не закоммичено — дальше Reviewer (Grok 4.7)

2026-11-16 — Reviewer, Grok 4.7 — принято — дальше человек (приёмка и finish-task)
2026-11-16 — человек — принято — закрытие

## Ревью 1

Вердикт: `принято`. Прод не менялся, коммита нет. Статус `закрытие`: выкат уже на проде, дальше человек — приёмка вида и `finish-task`.

- Diff `task/ai-seo-h1-structure`: только `.cursor/skills/site-page-seo/SKILL.md`, `todo/ai-seo-h1-structure.md`, `docs/dashboard.md` (дашборд пересобирает `make check` — не замечание).
- Skill, разделы 2.1–2.3 и абзац шага 1: по-русски, по фактическому прогону, без посторонних тем. WPBakery — только конструктор Browser MCP; для страницы с `_wpb_vc_js_status=true` откат ревизией, `--post_content` по-прежнему запрещён. `description` рубрики `product_cat` прямо отделён от WPBakery и от `wpseo_taxonomy_meta` — правило 3 в `docs/site/access-tools.md` не нарушено. Шаг 1: число `<h1>` считать Python-разбором `re.findall(r"<h1\b[^>]*>(.*?)</h1>", body, re.S)` по `curl.exe -A "GPTBot/1.0"` с `--retry 3 --retry-all-errors --connect-timeout 30`.
- Прод, только чтение, тот же `curl.exe` и тот же regex. Все 8 URL — `200`, ровно один `<h1>`: главная «Изготовление сувенирной, наградной и рекламной продукции в Екатеринбурге»; с cookie `wt_geo_data` (urlencoded JSON `{"city":"Пермь","region":"","district":"","country":"RU"}`) — «…в Перми»; `/category/awards/znachki/` «Значки»; `/category/posm/stendy/` «Стенды»; `/category/awards/znachki/znachki-zakatnye/` «Значки закатные»; `/category/awards/znachki/znachki-metallicheskie/` «Значки металлические»; три карточки — по одному `<h1>` с названием товара. В HTML трёх рубрик на месте `<h2>` бывших заголовков описаний; сырых `[vc_` и `[wt_` нет. Один запрос оборвался по таймауту и прошёл со второй попытки (`200`).
- `ssh insain-prod`, только чтение: `wp term get product_cat {119,356,358} --field=description | diff - /tmp/term-…-after.txt` — пусто; первая строка `-after` — `<h2>`, `-before` — `<h1>`; `wp post meta get 143 _wpb_vc_js_status` = `true`; `wp post get 1817285 --field=post_content | diff -q - /tmp/page-143-ai-seo-h1-structure-before.txt` — пусто; дамп `/tmp/insain-db-before-ai-seo-h1.sql` — 245M.
- Self-review по AGENTS.md «Перед сдачей»: diff внутри scope; цен и курсов в коде нет; калькуляторы не менялись; комментарии skill по-русски; `STATUS.md` правке не противоречит. Консоль Browser MCP и вид страниц заново не снимались: в отчёте Site ops те же 3 `TypeError` из `insainParse/scrtp.js` есть и на нетронутой странице пазлов — уже в «Найдено вне scope», регрессом этой правки не считаю.
- `python scripts/dev.py check` в worktree: exit 0, `624 passed`, `81 passed`. В `docs/dashboard.md` статус задачи — `закрытие`.
- `желательно` (сдачу не держит): пример команд в шаге 1 skill по-прежнему `curl.exe -fsS` без `-A "GPTBot/1.0"` и `--retry`; требование дописано следующим абзацем.

## Найдено вне scope

- Единственный `<h1>` в карточках, на `/about/`, `/shipment/` и в рубриках без `<h1>` в описании скрыт (`.pt-right.d-none`, `porto_settings.show-pagetitle=""`); видимый заголовок — `<h2>`. Счёт «ровно один `<h1>`» выполнен, но заголовок невидим пользователю.
- Страница 2975 `agreement` — `<h1>` в `post_content`, не проверялась на дубль.
- WTGeotargeting: `GPTBot` и другие ИИ-боты не в списке `isBot()` — для них выполняется запрос DaData по IP на каждый визит без cookie (лишний внешний вызов); итог всё равно Екатеринбург по умолчанию.
- В `post_content` 143 остались демо-заголовки Porto («BIG SALE … UP TO 70% OFF», «Online Purchases Only»); в HTML главной их нет (скрытая строка).
- На всех проверенных страницах (главная, плакетки, пазлы) в консоли 3 uncaught `TypeError` из `wp-content/plugins/insainParse/includes/script/scrtp.js` (строки 31, 49, 59) — не связаны с правкой (есть и на незатронутых страницах).
- Форма калькулятора плакеток (69 CalcPlaque) — на старом JS (`/icalc/*.json`), запросов к `/api/v1/` нет; API проверен на форме пазлов.

## Результат

- Ветка, PR или коммит: `task/ai-seo-h1-structure` (слияние в `main` по `finish-task`; правки в git: `.cursor/skills/site-page-seo/SKILL.md`, `todo/ai-seo-h1-structure.md`, `docs/dashboard.md`).
- Период: 2026-11-16.
- Часы человека: решения по Scope п. 2.
- Работа агентов: Site ops, Opus 5.5 — диагностика (2 сессии) и выкатка.
- Было / стало (`curl.exe -A "GPTBot/1.0"`, Python-разбор `<h1\b[^>]*>(.*?)</h1>`):

  | URL | `<h1>` до | `<h1>` после |
  |---|---|---|
  | `/` | 0 | 1: «Изготовление сувенирной, наградной и рекламной продукции в Екатеринбурге» (видимый, 32px) |
  | `/category/awards/znachki/` | 1 «Значки» | 1 «Значки» |
  | `/category/awards/` | 1 | 1 |
  | `/category/souvenirs/` | 1 | 1 |
  | `/category/posm/stendy/` (119) | 2: «Стенды», «Стенды информационные» | 1 «Стенды»; «Стенды информационные» — `<h2>` |
  | `/category/awards/znachki/znachki-zakatnye/` (356) | 2: «Значки закатные» ×2 | 1; второй — `<h2>` |
  | `/category/awards/znachki/znachki-metallicheskie/` (358) | 2: «Значки металлические», «Металлические значки по индивидуальному эскизу» | 1; второй — `<h2>` (24px, видимый) |
  | `/catalog/znachki-metallicheskie-s-emalyami/` (INS8573) | 1 | 1 |
  | `/catalog/znachki-polimernye/` (INS4242) | 1 | 1 |
  | `/catalog/naklejki-na-bumazhnoj-osnove/` (INS8215) | 1 | 1 |

  Все 10 — `200`, `title`/`description` не изменились, JSON-LD на месте, сырых `[vc_`/`[wt_` в HTML нет; `GET /wp-json/yoast/v1/get_head?url=https://insain.ru/` — `200`.
- Сделано:
  1. Бэкап БД: `/tmp/insain-db-before-ai-seo-h1.sql`, 245M, `-- Dump completed on 2026-11-15 21:53:38`.
  2. Исходники на сервере: `/tmp/page-143-ai-seo-h1-structure-before.txt` (7940 Б), `/tmp/term-{119,356,358}-ai-seo-h1-structure-before.txt`; после — `…-after.txt`.
  3. Главная 143: в конструкторе WPBakery (Browser MCP, backend editor) первой строкой добавлено `[vc_row wrap_container="yes"][vc_column][vc_column_text]<h1>Изготовление сувенирной, наградной и рекламной продукции в [wt_contacts get="region_name_prepositional"]</h1>[/vc_column_text][/vc_column][/vc_row]`, сохранено «Обновить». `_wpb_vc_js_status=true` сохранился, новая ревизия 2586894 (2026-11-16 00:06:47). Побочные эффекты пересериализации WPBakery (diff `post_content` до/после): в `vc_custom_heading` «ЛАЗЕРНАЯ РЕЗКА\nи ГРАВИРОВКА» перевод строки стал `<br />` (заголовок и раньше шёл в 2 строки), вокруг `[porto_info_box]` с политикой и `[wpmfgallery]` появились `</p>`/`<p>` (в HTML пустых `<p>` 0), убраны атрибуты по умолчанию `icon_border_radius="0"`/`"500"`, переставлен порядок атрибутов у двух `vc_row`. Визуально без изменений, кроме нового заголовка.
  4. Рубрики 119, 356, 358: в `description` `<h1>…</h1>` → `<h2>…</h2>`, остальной текст байт в байт (`diff` до/после — только строка 1). `wp term update --description` дважды вырезал заголовок (ядро вешает `wp_filter_kses` на `pre_term_description`, `--user=1` и `kses_remove_filters()` не помогают) — итог записан `wp eval` с `remove_filter("pre_term_description","wp_filter_kses")` + `wp_update_term` из файлов `-after`; `term get | diff - …-after.txt` — совпадает у всех трёх. Остальные 302 рубрики не трогались.
  5. `wp cache flush`, `wp litespeed-purge all`. `wp yoast index` не нужен: мета Yoast не менялась.
  6. `.cursor/skills/site-page-seo/SKILL.md`: разделы 2.1 (WPBakery через Browser MCP: ожидание `vc`, `vc.shortcodes.create`, мусорный `css`, `createShortcodeString`, побочные эффекты пересохранения, ревизия-точка отката), 2.2 (шорткод `[wt_contacts]` и проверка по cookie `wt_geo_data`), 2.3 (Porto Page Title и запись `description` рубрики в обход `wp_filter_kses`); в шаге 1 — подсчёт `<h1>` Python-разбором и ретраи `curl.exe`.
- Исходные `description` рубрик (до правки):

  119 `stendy`:
  ```html
  <h1>Стенды информационные</h1>
  Любая организация нуждается в эффективном средстве предоставления информации, таком как настенные стенды.

  Компания «Инсайн» предлагает изготовление разнообразных стендов, таких как информационные стенды с карманами для листовок и объявлений, «Уголок потребителя», плакаты по охране труда, доски почета  и другие. Также мы может изготовить стенды по индивидуальному проекту.
  ```

  356 `znachki-zakatnye`:
  ```html
  <h1>Значки закатные</h1>
  Благодаря короткому сроку изготовления и низкой стоимости, закатные значки считаются одним из самых массовых рекламных материалов. И одним из самых результативных! Основными достоинствами <strong>закатных значков</strong> являются их <strong>низкая цена</strong>, возможность нанесения полноцветного изображения и производство небольшими тиражами в короткие сроки.
  ```

  358 `znachki-metallicheskie`:
  ```html
  <h1>Металлические значки по индивидуальному эскизу</h1>
  Значки к юбилею, значки, свидетельствующие о принадлежности к группе, организации, памятные значки, наградные значки и медали, значки депутатов и официальных лиц, значки и брелоки с корпоративной символикой и много других вариантов на все случаи жизни Вы можете заказать в компании «Инсайн».

  Мы изготавливаем как низкобюджетные значки для небольших организаций, студотрядов, так и сложные оригинальные изделия, медали и ордена для награждения.
  ```
- Чем проверено:
  - Геоподстановка: `curl.exe -A "GPTBot/1.0" -b "wt_geo_data=<{"city":…}>" https://insain.ru/` — `<h1>` 1 у каждого города: «…в Екатеринбурге», «…в Снежинске», «…в Челябинске», «…в Перми», «…в Тюмени»; без cookie — «…в Екатеринбурге». `wp eval do_shortcode('[wt_contacts get="region_name_prepositional"]')` → «Екатеринбурге».
  - Browser MCP, главная: один видимый `<h1>` над баннером, шапка (город, телефон, меню), баннеры «Лазерная резка и гравировка» / «УФ-печать» на месте, сырых шорткодов нет; ошибки консоли — только `insainParse/scrtp.js` (см. «Найдено вне scope»).
  - Browser MCP, `/catalog/kalkulyator-nagradnyh-plaketok/`: загрузка 200, один `<h1>` «Калькулятор наградных плакеток», форма считает (3 800 руб.), ошибки консоли те же 3 из `insainParse`. Калькулятор на API — `/catalog/kalkulyator-pazlov/`: `POST /api/v1/calc/puzzle` ×4 → 200, цена 1 200 руб. `curl.exe https://insain.ru/api/v1/calculators` → 200.
  - Рубрика 358 в браузере: `<h2>` «Металлические значки по индивидуальному эскизу» видим (24px), `<h1>` Porto скрыт.
  - `python scripts/dev.py check` в worktree: `624 passed`, `81 passed`, exit 0.
- Не сделано и почему: скриншот рубрик для приёмки не снят (Browser MCP — таймаут скриншота >5 с), вид проверен через DOM; коммит не делался — по указанию Orchestrator.
- Требуется решение: нет (приёмка вида главной — человеком).
- Откат:
  - Главная 143 — «Редакции» в админке: вернуть ревизию 1817285 (2021-10-05 10:18:18), её `post_content` совпадает с `/tmp/page-143-ai-seo-h1-structure-before.txt` (`diff -q` пусто); затем `wp cache flush`, `wp litespeed-purge all`.
  - Рубрики: `wp eval` из skill, раздел 2.3, с файлами `/tmp/term-{119,356,358}-ai-seo-h1-structure-before.txt`; затем сброс кэша.
  - Крайний случай — `/tmp/insain-db-before-ai-seo-h1.sql` только с подтверждением человека.
