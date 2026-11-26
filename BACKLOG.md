# BACKLOG

Неоформленные идеи: что сделать и зачем. Спецификация задачи живёт в `todo/`
и после закрытия удаляется. Третьего трекера нет.
Прежний `ROADMAP.md` удалён; полный текст — в истории git.

Адрес API: `https://insain.ru/api/v1` (тот же хост, что и сайт). Субдомен `calc.insain.ru` не используется.

## Уже работает

- **W1, W2.** JS-обёртка и плагин `insain-calc-bridge` на проде. Формы ходят на `https://insain.ru/api/v1` относительным путём `/api/v1`.
- **D1–D3.** Образ calc API, compose и nginx на VDS уже развёрнуты. Публичный адрес — `https://insain.ru/api/v1`.
- **I4.** Пять падающих тестов `bot_service` починены (задача 4.2).
- **I5.** Тесты `plaque` и `poly_sticker_pack` добавлены (задача tests-plaque-poly-sticker-pack).

## Калькуляторы

- **C1–C11.** Этих калькуляторов в `calc_service` нет, и отдельных форм ezFC под них в реестре нет. В G1 (перевод 45 боевых форм) не входят. Брать в `todo/` после G1, если появится страница.
  - C1 — медали, на базе `metal_pins`.
  - C2 — акриловые медали и ленты, база `laser`, ориентир inari.pro.
  - C3 — металлические брелоки, на базе `metal_pins`.
  - C4 — полимерные брелоки.
  - C5 — брошюры, на базе `notebook`.
  - C6 — спортивные медали, ориентир sportpriz.ru.
  - C7 — гравировка на металле, ориентир Эльмуна.
  - C8 — шелкография на бумаге, ориентир Студия 11.
  - C9 — пакеты ПВД, ориентир РА Логотип.
  - C10 — дизайн и вёрстка, расширение калькулятора `design`.
  - C11 — штампы и печати с автооснасткой.

## Сайт

- **Формы ezFC.** Оформлено в `todo/EPIC-forms-to-api.md` (цель G1): пачки по 5–10, копии выборочно.

## Контент сайта (G2)

Оформлено в `todo/EPIC-site-content.md`. Бывшие пункты 6.1–6.5 архивного плана.

## Skills без прогона

- **new-calculator**, **json-price-rollout** и **port-fix-prerequisite** ещё не прогнаны на реальной задаче. `ezfc-form-to-api` и `deploy-wp-plugin` прогнаны на форме 69, `finish-task` — на `uv-print-prepare` 08.11.2026. Чекбокс бывшего 5.5 не закрыт.

## Каталог поставщиков

Оформлено в `todo/EPIC-supplier-catalog.md` (цель G7 в `docs/vision.md`): снятие карточек Проекта 111, новый парсер, загрузка Проекта 111, Happygifts и Oasis.

## Решение владельца

- **26.10.2026.** Товары Проекта 111 убрать с сайта полностью: 694 товара с SKU `prg`, 12 670 вариаций и карточка `dbprg4594/18` (тот же артикул 4594). Свои товары `INS` остаются. Плагин `insainParse` не выключать: деактивация удаляет его таблицы.

## Отложено

- **Бот на VDS.** Цель G5, эпик `todo/EPIC-bot.md`. Пауза снята 07.11.2026; выкатки ещё нет. Рефакторинг `agent.py` (I3) — вместе с этапом 1.
- **Max (M1–M3).** Изучить Max Bot API, отделить транспорт от ядра, поднять бота в Max. После этапа 1 G5.
- **PostgreSQL и pgvector (I1, I2).** Логи, история диалогов и база знаний бота. Зачем: память не в файлах. Пока бот не на VDS — не подключать.
- **Тестовый контейнер calc API.** Второй контейнер из ветки задачи на VDS, только localhost, и режим `?api=test` в бридже для админа. Зачем: менять логику калькулятора, на котором уже работает боевая форма, не задевая клиентов. Вернуться, когда на API будет несколько форм.
- **Дубль сайта на втором VDS.** Решено 28.10.2026 не делать: письма и оплата из копии, персональные данные, лицензии ezFC/WPBakery/Porto, расхождение с продом, риск перепутать сервер. Вернуться, если тестовых копий форм не хватит.
- **Оркестратор задач и метрики агентского кода.** Зачем: только если обычный режим идёт несколько недель и узкое место — переключение ролей.
- **JS и Python расходятся на AcrylWhite3 + isSublimation.** JS даёт NaN, Python считает цену (3605.49). Форма 69 такую пару не отдаёт: `hide_option` сублимации без `AluminiumSU055`. Чинить, только если другая форма пошлёт такую пару.
- **`print_roll` / `isJoing`.** Сейчас порт как JS: при включённой стыковке всегда режет на полосы, даже если изделие влезает на рулон без стыка (роллап и др.). Правильнее: стыковать только если не влезает; включать стыковку автоматически и предупреждать «печать со стыковкой будет». Пока не менять — иначе разъедется с legacy JS и формами.

## Найдено вне scope

- Из `form-embossing`: Старый cjsCalc формы 85 читает `ckbMaterialCustomer` с id 3291 (`ckbCliche`), а не 3311 — баг боевого JS; в `embossing.js` исправлено на 3311.
- Из `form-embossing`: `dpdSurfaceMaterial`, `ckbPacking`, `ckbMaterialCustomer` есть на форме, в API `embossing` не входят (как `materialID` в старом `calcEmbossing` не используется); в `syncUrl` пишутся, в `calcApi` не уходят.
- Из `form-embossing`: У `rdoModeProduction` формы 85 только значения `1`/`2` (опции «дешевле»/0 нет).
- Из `acrylic-prizes-port-fix`: На ветке `task/form-acrylic-prizes` эталон `REF_FORM_DEFAULT` был только в рабочем дереве (не в коммите); сняли заново раннером `calcAcrilycPrizes` 08.11.2026 — числа совпали с задачей.
- Из `form-acrylic-prizes`: `calc_service/calculators/uv_print.py`: `time_prepare *= max(1, mode.value)` (plain и non-plain) — при `mode=0` готовит как mode=1; JS `calcUVPrint` умножает на `modeProduction` (0 → 0). Ломает второй УФ в `acrylic_prizes` после сброса `mode_uv`. Вынесено в `uv-print-prepare` (закрыто 2026-11-08, `docs/history/log.md`).
- Из `form-acrylic-prizes`: В `acrylic_prizes.py` при гравировке читается `is_grave_fill`, а боевой cjsCalc/JS кладут `isGraveFill` — вынесено в `acrylic-prizes-port-fix` (закрыто 2026-11-08, `docs/history/log.md`).
- Из `form-acrylic-prizes`: В dropdown формы 77 `dpdMaterial` нет кода `PVC3` (эталон git/API); на странице для проверки брать материал из списка формы и сверять цену с `POST` на тех же слоях.
- Из `form-acrylic-prizes`: При дубле формы 78 создались две копии **90** и **91**; рабочая — **91**. Форма **90** лишняя, удаление — только с подтверждения человека.
- Из `presswall-banner-options`: `STATUS.md`, раздел Git: снимок всё ещё `e52e947` (25–28.10.2026). На VDS до этой выкатки был `511c660`. Файл не правил.
- Из `form-presswall`: `weight_kg` presswall на эталоне: раннер 9.79, Python и боевой API 9.78 (rel 0.00102) — presswall.py суммирует вес баннера, уже округлённый print_roll до 0.01. Учтено: допуск `abs=0.02` в assert веса.
- Из `form-presswall`: skill `ezfc-form-to-api` (verify.md, шаг 1а) требует строку раннера дефолта в `docs/js-runner-cases.md`; файла нет в «Файлы» задачи — команда только в комментарии `REF_FORM_DEFAULT`.
- Из `form-presswall`: Раннер `calcPresswall` с баннером `BannerFronlitLamin440` (ламинированный 440) падает «Поле weight_kg не число (NaN)» — старый JS не считает вес этого баннера; API отдаёт цену (каркас 2,5×2,5 + карман: 12790.624). Сверку JS и API на ламинированном баннере сделать нечем.
- Из `print-sheet-weight-port-fix`: Раннер не грузит `laminat.json` / `calcLamination.js` — дефолт формы 73 с ламинацией раннером не считается.
- Из `print-sheet-weight-port-fix`: Струйный вес `print_sheet` по-прежнему берётся из `calcPrintInkJet` (тоже по листу). Решение 11.11.2026 записано для лазерной ветки.
- Из `form-pennant`: Раннер не грузит `laminat.json` / `calcLamination.js` — дефолт формы 73 с ламинацией раннером не считается; правка `scripts/run_js_calc.mjs` не в этой задаче.
- Из `form-pennant`: Порядок строк на копии (бумага, плёнка, шнур) отличается от боевой 73 (плёнка, бумага, шнур). Размеры и количества те же: `showResult` выводит `materials` в порядке ответа API. Боевую форму и JS не менял.
- Из `form-flag`: Подпись опции `dpdSize` «200х90мм», `data-value` «200,99»: страница считает 200×99. Править форму в этой задаче нельзя.
- Из `form-flag`: Имя `PaperCoated115M`: JS `js_legacy/material/sheet.json` «113г/м», Python `calc_service/data/materials/sheet.json` «115г/м». Код, тираж 18 и цена совпали.
- Из `form-flag`: Эталон задачи 100×150 нет в `dpdSize` (148×105, 200×99, 210×148). На странице его не ввести.
- Из `form-flag`: Вес на копии 0.24 кг (API `weight_kg` 0.2377), на боевой форме 55 при тех же полях «Вес тиража 0.29 кг». Цена 4 100 и срок «Срок 1 день» с той же подсказкой дат совпали. Калькулятор в этой задаче не менялся.
- Из `print-sheet-port-fix`: `print_laser.py:239` / `:260` — тот же `max(1, mode)` и `round` вместо `ceil`; вызывается из `sticker` и `/calc/print_laser`, не из листа. Вынести отдельной задачей после сверки со `calcPrintLaser`.
- Из `print-sheet-port-fix`: Раннер `calcCutGuillotine` на входе гильотины листа даёт `time_ready` NaN (из блокера `form-print-sheet`); сверку листа не держит.
- Из `form-print-sheet`: Раннер `calcCutGuillotine` на входе 50 листов, 210×297 на листе 320×450, поля [3,3,3,3], interval 0, mode 1 падает: `time_ready` не число (NaN). На странице time 0.05, Python time_hours 0.05, cost 67, price 108. Сверку листа не держит. `scripts/run_js_calc.mjs` не правил.
- Из `form-print-sheet`: Раннер `calcPrintSheet` с `isLamination` падает: `Cannot read properties of undefined (reading 'Laminat')`. На странице https://insain.ru/catalog/listovki-pod-zakaz/ тот же вход считается. `scripts/run_js_calc.mjs` не правил.
- Из `cut-plotter-sheet-layout`: `print_laser.py`: время `round` вместо JS `Math.ceil` — `poly_sticker` time_hours 0.88 против раннера 0.89, стикерпак 1.79 против 1.8. `price` там ещё `int(...)`, из-за этого стикер VHI80 1307.28 против 1307.5632666666668 (внутри rel 0.001).
- Из `cut-plotter-sheet-layout`: Вес эпоксидки в `common/process_tools.py` округляется `round`: стикерпак 0.19 кг против раннера 0.2. На цену не влияет.
- Из `cut-plotter-sheet-layout`: `calcCutPlotter` в JS не заполняет `weight` (раннер 0); Python на RAFLACOAT считает 0.0475 кг. В эталон резки вес не входил.
- Из `sticker-print-wide`: `sticker.py`, рулон с `length_min > 0`: стоимость плёнки умножается на ширину в метрах, в JS — в мм (Python в 1000 раз ниже). ORAJET3640 не задет (`length_min` 0).
- Из `sticker-print-wide`: `print_wide.py`: время подготовки `time_prepare * max(1, mode)`, в JS `timePrepare * modeProduction` — расхождение в режиме 0.
- Из `sticker-print-wide`: JS `calcLaminationWide` не задаёт `timeReady` (0); в `lamination_wide` — `time_hours` + базовый срок, отмечено в docstring.
- Из `form-sticker`: Ползунок `numDensity` (649): на странице скрыт (`ezfc-hidden`), в инпуте «25%», `factor` 0.01, `calculate_when_hidden` = 0. Плейсхолдер `{{numDensity}}` на дефолте равен 0. В API уходит 0. Поле видно только при сложности 1.7.
- Из `form-sticker`: `chkMark` / `isFindMark`: параметра в API `sticker` нет (на `cut_plotter` есть, `sticker.py` его не прокидывает). На дефолте флажок выключен. В `syncUrl` пишется, в `calcApi` не уходит.
- Из `form-sticker`: `chkMark` по-прежнему только в URL. Широкие принтеры и `dpdRollWideLaminat` с 15.11.2026 уходят в `calcApi` из git и с той же даты — из custom JS копии 97.
- Из `form-sticker`: На живой странице старый JS даёт price 653.134 при тех же материалах (3 листа 320×450 RAFLACOAT). Раннер `--data current` и боевой API — 662.134. `insaincalc.round` обоих — 700. Цены JSON не менялись.
- Из `form-sticker`: Боевая страница под админом: старый блок «через менеджера» 800 ₽ и «при заказе с сайта» 700 ₽, срок «2 дня». Копия по `showResult`: «цена» 700 ₽, «со скидкой» 536 ₽, срок «2 дня». Срок совпал. 800 — старое поле, в этой задаче не выравнивается.
- Из `form-sticker`: `wp litespeed-purge all` вернул `Error: Something went wrong! Got 400`. `wp cache flush` — `Success`. Превью копии после этого отдало свежий расчёт.
- Из `form-sticker`: 1000×1000, рулон и широкая печать: `calcPrintWide` делит площадь на `material.size[0]`. У ORAJET3640 это `[1260, 0]`, частное `NaN`, `mergeMaps` затирает метры резки. Раннер на 1 шт + `Technojet160ECO` отдаёт quantity `null`. Дельта цены печати (+402) при этом совпадает с API. В порт `null` не переносить: после правки длины в таблице остаётся расход резки.
- Из `form-sticker`: Рулон + лазер `KMBizhubC220`: раннер `calcSticker` падает (`reading 'density'`), API считает как без печати. К замечанию про 1000×1000 не относится: там есть цена и метры, не обнуление.
- Из `form-sticker`: `showError` не обнуляет уже показанную цену: после успешного расчёта слишком большой размер меняет срок на текст ошибки, сумма в колонке цены остаётся прежней. Общее для форм на API. На копии это изменится только с правкой моста и выкладкой плагина.
- Из `form-sticker`: JS бросает ошибку на первом листе с раскладкой 0, даже если следующий размер вмещает. Python пропускает неподходящий размер и берёт следующий подходящий; ошибка — когда не подошёл ни один. В `sheet.json` у листовых материалов один размер, для RAFLACOAT это одно и то же.
- Из `form-sticker`: Рулон ORAJET3640, 100 шт 50×50, без печати: на 14.11.2026 раннер `price` 577.368832, боевой `POST /api/v1/calc/sticker` 558.59224. Оба `insaincalc.round(..., 100)` дают 600. Перепроверено 15.11.2026: тот же боевой POST — `price` 577.368832, на копии страница 600 ₽. Расхождение 558 на проде больше не воспроизводится.
- Из `form-laser`: Копия 98 шлёт в `POST` `size_item: 0` и `density: 0`, хотя поле «Размер элементов» показывает 50, а «Плотность элементов» — `25%` (defaultValue `25`). Цена на странице поэтому 2 600 / 1 500 / 1 700 ₽, не округление эталона 23638 / 22465 / 27961. С включённым клеевым слоем на том же теле экран 4 600 ₽ (акрил и лист скотча), не 25 626. `material_mode` и `is_adhesive_layer` при этом уходят верные. Не чинилось: вне списка правок этой сессии (только `GET_check` 3675, и только если ссылка не восстанавливает радио).
- Из `form-laser`: `badge.py`: `time_ready` 16.55 против JS 17.9 и вес 1.18 против 0.87. Цена после `noMaterial` сошлась. Срок и вес не чинить в этой задаче.
- Из `form-print-roll`: Ламинация. На дефолте А0 с `isLamination: 1` раннер даёт price 2335, time_ready 16.55; до правки `POST` с `is_lamination: true` оставался 1544 / 16.52. Пропуск `calcPrintRoll call calcLaminationWide` был в `scripts/js_port_gaps_allowed.txt`. 16.11.2026 человек вернул починку в эту задачу: правка в `print_roll.py`, строка пропуска снята, см. «Результат». `size_mm` по-прежнему вне scope.
- Из `form-print-roll`: `size_mm`. Боевая форма не вызывает `showMaterials`, таблицы материалов на странице нет. В ответе API на дефолте и эталоне ключа нет (плёнка 1.2 м; на эталоне ещё люверсы 80 шт). В `print_roll.js` размер не подставляется. Для колонки «Размер» на копии нужен `size_mm` в калькуляторе, образец `pennant-materials-size-mm` / `flag-materials-size-mm`.
- Из `form-print-roll`: «Поля 5 см» и «поля 10 см» (`isField50`, `idField100`) старый `calcPrintRoll` не считает. В API не уходят — так же, как боевой JS.
- Из `print-offset-promo`: Радио «стандарт» на форме 82: value 0 и data-value 1. Боевой JS читает value. В калькулятор и в форму не переносить.
- Из `print-offset-promo`: Штатный раннер до этой задачи не загружает `calcPrintOffset.js`.
- Из `print-offset-promo`: Живой price обычного офсета `PaperCoated115M`, 1000 шт, 210×297, `4+0`, mode 1 — 14450.546 и до этой правки, и после. Константа теста 14108.116 не менялась; тест держится на `rel=0.03`. В этой задаче не чинить.
- Из `ai-seo-h1-structure`: Единственный `<h1>` в карточках, на `/about/`, `/shipment/` и в рубриках без `<h1>` в описании скрыт (`.pt-right.d-none`, `porto_settings.show-pagetitle=""`); видимый заголовок — `<h2>`. Счёт «ровно один `<h1>`» выполнен, но заголовок невидим пользователю.
- Из `ai-seo-h1-structure`: Страница 2975 `agreement` — `<h1>` в `post_content`, не проверялась на дубль.
- Из `ai-seo-h1-structure`: WTGeotargeting: `GPTBot` и другие ИИ-боты не в списке `isBot()` — для них выполняется запрос DaData по IP на каждый визит без cookie (лишний внешний вызов); итог всё равно Екатеринбург по умолчанию.
- Из `ai-seo-h1-structure`: В `post_content` 143 остались демо-заголовки Porto («BIG SALE … UP TO 70% OFF», «Online Purchases Only»); в HTML главной их нет (скрытая строка).
- Из `ai-seo-h1-structure`: На всех проверенных страницах (главная, плакетки, пазлы) в консоли 3 uncaught `TypeError` из `wp-content/plugins/insainParse/includes/script/scrtp.js` (строки 31, 49, 59) — не связаны с правкой (есть и на незатронутых страницах).
- Из `ai-seo-h1-structure`: Форма калькулятора плакеток (69 CalcPlaque) — на старом JS (`/icalc/*.json`), запросов к `/api/v1/` нет; API проверен на форме пазлов.
- Из `form-print-offset`: `GET /api/v1/tool_schema/print_offset` по-прежнему помечает `width`, `height`, `color` как required. На форме 82 таких полей нет. Боевой `POST` без них на промо-коде уже отдаёт цену (закрытый `print-offset-promo` и эта сверка). Схему не менял: `print_offset.py` в «Не-scope».
- Из `form-print-offset`: Радио «стандарт»: HTML `value` 0, `data-value` 1. Боевой `get_value_from(3221)` без `true` суммирует `parseFloat(data-value)` и даёт 1, не 0. Срок на странице «6 дней» (48 ч). В калькулятор это не переносил: цена от режима не зависит.
- Из `form-print-offset`: Имя `GET` у `numN`, `dpdFormat`, `rdoModeProduction` в базе боевой формы пустое. `GET_check` у формата и режима на боевой уже `index` (не пусто). На копии Site ops прописал имена GET; у формата оставил `index`, у режима сменил на `value`. Боевую не менял.
- Из `form-print-offset`: В `docs/js-runner-cases.md` строка дефолта формы 82 всё ещё с mode 0 (`time_ready` 56). Файл общий, не правил. Актуальная команда — в «Результат».
- Из `ai-seo-cleanup-noindex`: Страницы `/wishlist/` (ID 3) и `/my-orders/` (ID 2154) отдают сырые шорткоды `[yith_wcwl_wishlist]` и `[dokan-my-orders]` — плагины YITH Wishlist и Dokan не установлены; на `/wishlist/` ведёт сквозная иконка в шапке.
- Из `ai-seo-cleanup-noindex`: `porto_builder` отдаёт два `<meta name="robots">`: Porto `noindex,nofollow` и Yoast `index, follow` (конфликт снимется настройкой `noindex-porto_builder`).
- Из `ai-seo-cleanup-noindex`: Porto `enable-faq=1` занимает слаг `/faq/` (архив CPT) — будущий раздел `/faq/` (`ai-seo-faq-and-facts`) с ним конфликтует.
- Из `ai-seo-cleanup-noindex`: `category-sitemap.xml` содержит `/category/banner/`, который отдаёт 404 (записей `post` — 0).
- Из `form-button-pins`: Старый JS кладёт в `isPrint` вставки строку `KMBizhubC220`, а не `{printerID, color}`: печать вставки не считается. API повторяет это, иначе цена разойдётся с боевой формой.
- Из `form-button-pins`: В `pins.json` у D78 поле `title` говорит «56мм» при размере 78.
- Из `form-button-pins`: Боевой `LaminationCalculator` делает `math.ceil` цены, `cut_plotter` и ламинация отдают `time_hours` через `round`, раннер — `ceil`. На эталоне 2×D38: price API 760.59 против раннера 759.88388712 (rel 0.00093), time 0.25 против 0.27. Боевые калькуляторы не менялись.
- Из `print-sheet-mode2-defects`: В `D:\Projects\insain-agent-print-sheet-mode2-defects` при `wt-check` обнаружены незакоммиченные правки в основной папке `D:\Projects\insain-agent`: `M todo/ai-seo-geo-yoast.md` (чужая работа на `main`, не трогалась).
- Из `print-sheet-mode2-defects`: 19.11.2026, Site ops: на `main` файл `todo/ai-seo-geo-yoast.md` по-прежнему `M`, не трогался.
- Из `form-notebook`: `ssh insain-prod` (порт 22) — timeout. Id и имена полей формы 45 сняты с HTML боевой страницы (`data-id`, `ezfc_vars`), не из SQL.
- Из `form-notebook`: `calcNotebook` не подключён в `scripts/run_js_calc.mjs`. Эталон дефолта — консоль страницы. В `docs/js-runner-cases.md` не писал.
- Из `form-notebook`: Вес дефолта: JS 15.2892 (лист с обрезью), Python 15.00. В критерий цены и срока не входит. Тот же зазор на кейсе блока `4+0` + цифровая печать: JS 15.2892, Python 15.00.
- Из `form-notebook`: В блоке `calcPrintSheet` пропуски `call calcCutRoller`, `call calcPrintLaser` уже есть в `scripts/js_port_gaps_allowed.txt`. Блок `calcNotebook` пустой.
- Из `form-notebook`: Код проволоки в API `MetallBindindWire3_8`, в JS `MetallBindindWire`. Имя и `size_mm` 9.5×42000 совпали.
- Из `form-notebook`: Ламинация листа `0+0`: `cost` совпал с JS (1388.1508256410257), `price` 2262.59 против 2262.41 (разница 0.18 ₽, rel < 0.001).
- Из `form-notebook`: Копия без GET в URL: радио режима не отмечено ни одно (на боевой отмечен «стандарт»). `preselect` 0 у 1821 и 3834 одинаковый; у копии `GET_check=value`, значения вариантов 1 и 2, варианта со значением 0 нет. Цена верная: JS подставляет `mode = 1`, после `syncUrl` ссылка с `rdoModeProduction=1` отмечает «стандарт». Перед боевой формой нужен `preselect` под `value` или решение в `docs/ezfc-api-migration.md`. (Не блокер приёмки копии после фикса mode 2; на боевой 45 решать отдельно.)
- Из `form-notebook`: `wp litespeed-purge all` снова `Error: Something went wrong! Got 400` (уже в `BACKLOG.md` из `form-sticker`). `wp cache flush` — `Success`.
- Из `form-notebook`: `ssh insain-prod`: 2 таймаута `banner exchange` за сессию, повтор через 10–15 с проходил.
- Из `mode-logic-and-checks`: `calc_service/tests/test_calculators/test_print_offset.py`: `EXPECTED_REF.price` = `14108.116` при фактической цене `14450.546` на том же `REF_PARAMS` и `mode=1`. Старый assert проходит только из-за `rel=0.03`. Цена от этой правки не менялась (`timePrepare=0`). Точное значение уже зафиксировано в `test_print_offset_modes_match_js`.
- Из `form-canvas`: `calc_service/calculators/print_roll.py`: при `quantity=2, width=400, height=300` (размер вне пресетов формы 80) расход `CanvasDLCNM320` (`length_min=500` мм) в `materials` даёт `0.48` м вместо `0.5` м в JS (разница ~10 ₽ в `calcCanvas` для `400×300`). `print_roll.py` не правился (вне scope).
- Из `form-canvas`: На дефолте формы `400×500` без подрамника `materials` холста `0.6` м против `0.605` м в JS (то же округление `print_roll` до 2 знаков). Цена совпала: `2543`.
- Из `form-canvas`: Форма 80 (`dpdSize` id=3130): у опции `id=8` подпись `"1000х1100 мм"` при `value="1000,1200"`.
- Из `form-canvas`: `scripts/run_js_calc.mjs`: `calcCanvas` не подключён (эталоны сняты в консоли боевой страницы, 20.11.2026; Reviewer сверил тем же загрузчиком локально, скрипт не менялся).
- Из `ezfc-form-builder`: В `materials/calendar.json` (секция Flip) и `materials/presswall.json` (Joker, Tritix) подпись в JSON совпадает с ключом, поэтому в списке опций виден код. Генератор подставляет в `text` только `title` / `name` / `description` и сам ключ туда не пишет.
- Из `wt-geotargeting-update`: `.cursor/skills/site-page-seo/SKILL.md` проверяет геоподмену cookie `wt_geo_data`. После установки имя cookie сменится, skill надо поправить отдельной правкой.
- Из `wt-geotargeting-update`: `AGENTS.md` (строка про wp-cli) всё ещё называет PHP warning `Wt::__wakeup()` шумом. После 1.18.1 в `wp plugin list` его нет; в этой задаче правились только `STATUS.md` и `docs/site/access-tools.md`.
- Из `wt-geotargeting-update`: Из-за обновления поверх 1.7.6 через `wp plugin install --force` хук `WtGeoTargetingPro::upgrader()` не запускался. Таблица `wp_insain_wt_gt_geolocation_cache` и cron `wt_geotargeting_pro_geolocation_delete_old_cache` созданы в закрытой `ai-seo-geo-yoast` (2026-11-21). `WtGtProThirdPartyIntegrationSync::run()` по-прежнему не вызывался, чтобы не включить флаги WooCommerce/Yoast.
- Из `ai-seo-geo-yoast`: Текущий API-ключ DaData в `wt_geotargeting_geobase` возвращает `403 Feature 'SUGGESTIONS' disabled` (был публично засвечен ещё на 1.7.6); после закрытия задачи владельцу нужно перевыпустить/включить токен в ЛК DaData и обновить его в админке WP (`WT GeoTargeting → Геолокация`, вне git).
- Из `ai-seo-geo-yoast`: На `/catalog/kalkulyator-pazlov/` есть сторонняя ошибка консоли `Failed to load resource: net::ERR_NAME_NOT_RESOLVED` (не связана с правкой).
- Из `ai-seo-geo-yoast`: Мелкие опечатки в существующих мета-описаниях Yoast: «Россси» в `product_cat/642` (`magnity-akrilovye`) и «Контактная информации» на `/contacts/all/`, `/contacts/chelyabinsk/`, `/contacts/tyumen/`.
- Из `form-heat-press`: До выкатки боевой `POST /api/v1/calc/heat_press` на `REF_FORM_DEFAULT` (`transfer_type="film"`) возвращал `400`. После `deploy-api` `17b84f8` тот же POST → 200, `price` совпадает с раннером. Пункт закрыт.
- Из `form-heat-press`: В `cut_plotter.py` используется `round` вместо `ceil`, из-за чего `time_hours` на дефолте `film` (mode 0/1) меньше JS на 0.01 ч (0.16%); `time_ready` укладывается в `rel ≤ 0.001`. На боевом API после выкатки то же: `time_hours` 6.071 против раннера 6.081, `time_ready` rel 0.00066. На доработке то же у `filmSublimation` и `filmEcosolvent`: оба времени меньше раннера на 0.01 ч; на 100×50×50 mode 1 `time_ready` rel 0.00029 и 0.00033. `paperLaser` резку не вызывает, `time_hours` и `time_ready` совпали точно.
- Из `form-heat-press`: В форме 40 поле `1562` (`numDensity`, value 25, factor 0.01) скрыто по умолчанию (`calculate_when_hidden=0`), поэтому дефолт передаёт `density=0`; у `dpdMaterial` значение `ambrella` (добавлено в схему `heat_press.py`).
- Из `form-heat-press`: На тех же дефолтах строка «со скидкой»: копия `12 939` (`showResult` от `cost` API), боевая старая форма `12 926`. Менеджерская цена `16 000` и срок «4 дня» совпали. Формула скидки старого JS не чинилась.
- Из `form-heat-press`: В `filmEcosolvent` возвращаемый `PrintRollCalculator` элемент `materials` (`POLIFLEX4030`) не содержит `size_mm` (в отличие от `film` и `paperLaser`); `print_roll.py` вне scope задачи.
- Из `form-heat-press`: В `paperLaser` `weight_kg` считается по изделию в `print_sheet.py` (`0.0341`), тогда как JS считает по целому листу с обрезью (`0.0505`) — принятое правило для цепочек `calcPrintSheet` (11.11.2026).
- Из `form-poly-sticker`: Боевой `cjsCalc` формы 30 кладёт в `isPrint` строку принтера, `calcSticker` читает `.printerID` и `.color`. Печать в цену не входит. JS копии это повторяет: `color` и `printer_code` не отправляются. Починка меняет цену (100 шт 50×50 RaflatacMW, KM + метки + Laminat32G: раннер со строкой 10812.3, с объектом `{printerID, color:4+0}` 11447.1). Широкая печать на листовой Raflatac в Python бросает «только на рулонном материале».
- Из `form-poly-sticker`: Рулонная ламинация в `lamination.py` ниже раннера. `calcLamination` 4 листа 320×450, mode 1: Laminat32G JS price 401.00 / Python 376; LaminatDLCLAM JS 831.35 / Python 720. На форме это KM 10812.3 против API 10783.55 и экосольвент 11306.8 против 11179.15. Срок в допуске rel ≤ 0.001. Ламинация не на боевой форме API, эталон `test_lamination.py` не двигался. На дефолте ламинации нет.
- Из `form-poly-sticker`: mode=2 дефолта: weight раннер 0.65, Python и боевой API 0.64 — round веса эпоксидки. `price` и `time_ready` совпали.
- Из `form-poly-sticker`: Кейс 80×80 PaperCoated115M из `docs/js-runner-cases.md` (price 4107.8) — не дефолт формы 30.
- Из `form-poly-sticker`: В HTML боевой и копии у «Способ печати» выбран index 1 «Цифровая лазерная печать» (`data-initvalue=1`), не «Без печати». Эталон без печати — выбор «Без печати» или GET `dpdPrint=0`. Открытие копии без GET даёт тот же лазер, что боевая: 10 800 руб. и 108 руб./шт, API price 10783.55.
- Из `form-poly-sticker`: Скидка на копии (showResult, cost 5486) — 7 132 руб. и 71.32 руб./шт. Боевой старый JS на тех же полях без печати — 7 121 руб. и 71.21 руб./шт. Менеджерская цена и срок совпали. Формулу скидки до шагов 17–24 не менять.
- Из `form-sticker-pack`: Срок дефолта формы 29 на 0.01 ч меньше JS при той же цене: mode 1 JS `time_hours` 0.47 / `time_ready` 16.47, Python и боевой API 0.46 / 16.46; mode 2 — 8.52 против 8.51 (rel 0.00117). `cost` и `price` совпали на mode 0/1/2. `sticker.py` вне scope, не чинился.
- Из `form-vizitki`: Пропуски порта `calcPrintSheet call calcCutRoller` и `call calcPrintLaser` уже в `scripts/js_port_gaps_allowed.txt`. Лазер вшит в `print_sheet.py`, роликовый рез — TODO. Дефолт визиток (90×50, PaperCoated300M) в эту ветку не попадает: 6 листов 320×450.
- Из `form-vizitki`: На копии смена материала на «350гр, матовая» вместе с форматом «Евро» и цветом 4+4 дала `material_id` ColotechPlus350M, ширина 85, высота 55 и `price` 0 при HTTP 200. Дефолт 90×50 при этом снова считается в 1 100. Подпись «Евро (86х54 мм)» в запрос уходит как 85×55.
- Из `print-sheet-big-sheet`: Гильотинное плечо буквального JS: `calcCutGuillotine(num, maxSize принтера, material.size, id, mode)` кладёт mode в аргумент margins, и предварительный рез выходит с нулевой ценой. Python вызывает тот же калькулятор с margins 0 и mode отдельно. Для EPSONWF7610 и PaperCoated300M, 100 шт 90×50, это +27 к cost, +44 к price и +0.02 ч. На дефолтном KMBizhubC220 ни один размер из `sheet.json` в эту ветку не попадает: 320×450 входит в принтер, 1000×700 и 1020×720 идут на роликовый. Эталон задачи — роликовый MAJESTIC, он с раннером совпал.
- Из `form-vizitki-promo`: Подпись радио «стандарт» на боевой форме 83 в HTML начинается с латинской «c» (`cтандарт`). На расчёт не влияет. На копии 109 подпись та же, не менялась.
- Из `form-vizitki-promo`: Боевая страница в браузере показывает 2 500 руб.: `calcPrintOffsetPromo(1000,"OffsetPromoViz1000",1)` на загруженных `/icalc/` даёт price 2470.8, `round` → 2500. API и раннер — 2284.8 → на копии 2 300. Срок обоих «6 дней», вес 1.35 кг. Боевая форма не переключалась.
- Из `form-pad-print`: `scripts/run_js_calc.mjs`: `calcPadPrint.js` не подключён в раннере (эталон снят прямым прогоном `js_legacy/calc/calcPadPrint.js` в Node vm с `calc_service/data/common.json` и `equipment/tools.json`).
- Из `form-pad-print`: `js_legacy/calc/calcPadPrint.js` при `n > 100` (`REF_PARAMS`, `n=500`): `nameMaterials` содержит одновременно `costSmallTampon` и `costLargeTampon`, после чего `if (diffPrint == 0)` добавляет выбранный тампон второй раз (`7943 ₽` в JS против `7393 ₽` в `pad_print.py` / `EXPECTED_REF`); на `n <= 100` (`REF_FORM_DEFAULT`, `n=100`) `ceil(n/100) - 1 == 0`, расхождение ~0.04 ₽ и цены сходятся точно (`3001 / 3436 / 3972 ₽`).
- Из `form-milling`: В форме 35 (`dpdMaterial`, элемент 1298) есть коды `Polycarbonate4` и `AcrylColor5`, которых нет в `calc_service/data/materials/hardsheet.json`.
- Из `form-milling`: `calcMilling` не подключён в `scripts/run_js_calc.mjs` (эталон снят в консоли боевой страницы).
- Из `form-milling`: Для материалов `PET03`–`PET20` из `dpdMaterial` в `calc_service/data/equipment/milling.json` отсутствует группа в `costCut` (ставка резки 0 руб/м, как и в JS).
- Из `form-milling`: 100 шт 50×50 мм PVC3: и JS, и API отдают в материалах 0 листов (доля листа только в себестоимости). На дефолте без материала список пуст. В JS имя материала пустое (в JSON нет `name`), API пишет `description`.
- Из `form-poly-sticker-pack`: У эпоксидки в JS размер 0, в API у EpoxyPoly нет size_mm. Плёнка 320×450 и ламинация 330×0 в ответе есть.
- Из `form-poly-sticker-pack`: Ряды наклеек формы 71 в share-URL не пишутся: numW и numH совпадают с размером пака.
- Из `form-poly-sticker-pack`: Боевая страница на старом прайсе: cost 3721, раннер current 3734. Оба округляются до 7000.
- Из `milling-cut-floor`: Длинный рез ПВХ без листа (100 шт, 50×50, `noMaterial`) остаётся `1641.75`: ставка 30 ₽/м выше порога, её эта задача не меняет.
- Из `form-metal-pins`: В dropdown формы код алюминия `aluminium`, в прайсе ключ `aluminum`. Код булавки `SafetyPinMetall`, в прайсе `SafetyPin`. Старый JS на этих пунктах падает. Подмена только в `forms/metal_pins.js`; прямой POST с этими кодами калькулятор не алиасит.
- Из `form-metal-pins`: Колонки CostStamp 4 и 5 в JSON обе равны 80: подписи «офсет» и «шелкография» на форме относительно комментария JSON не меняют цену.
- Из `form-metal-pins`: `calcMetalPins` не пишет `result.material`. Боевая таблица материалов пустая. API на дефолте отдаёт «Крепление игла-цанга» и «Полиэтиленовый пакетик», количество 100, `size_mm` нет. Состав страницы и API разный, потому что старый JS карту не заполняет; `size_mm` в JS формы не подставлялся. Строки материалов в калькуляторе не снимались: эталон `PolyBag` уже в тесте.
- Из `form-metal-pins`: Подпись режима на форме начинается с латинской `c` («cтандарт»), поэтому поиск по слову «стандарт» её не находит. Так же на боевой странице.
- Из `form-metal-pins`: Разобрать учёт веса в доставке значков. `calcMetalPins.js` в стандартном и ускоренном режиме всегда ставит `calcWeight = 1`, API берёт фактический вес, но не ниже 1 кг. На 100 шт (0,5 кг) цены сходятся; с ~300 шт для 20×20×1,2 мм API дороже. Тираж 1000, mode 1: API price 90445, JS 82903.8. Mode 0 на 1000 шт совпадает (79967). 23.11.2026 решено код не менять и реальный вес в API оставить, пока учёт веса не разобран.
- Из `form-calendar`: В цепочке `js_port_gaps` у `calcPrintSheet` строка `call calcPrintLaser` уже лежит в `scripts/js_port_gaps_allowed.txt`; к квартальному калькулятору не относится, строку не добавлял.
- Из `form-badge`: `calc_service/calculators/badge.py`: при `is_uv_print=True` в `uv_params` захардкожено `"color": "4+0"` вместо `color` (в JS передаётся `dpdColor`, но `modeProduction = 1`).
- Из `form-badge`: `calc_service/common/process_tools.py`: `calc_attachment` и `calc_packing` не заполняют `size_mm` у материалов (`Magnet4513`, `ZipLock0812`); в `badge.py` закрыто локально через `_ensure_size_mm`.
- Из `form-badge`: Дефолт формы 64: `weight_kg` API `1.65`, раннер `1.22`. `badge.py` включает вес второй лазерной резки, JS его не складывает (тот же разрыв, что у `EXPECTED_REF` в `test_badge.py`). На цену и срок лида не влияет.
- Из `form-keychain`: Подпись `PaperCoated115M`: legacy «113г/м», текущий каталог «115г/м». Код, лист 320×450 и количество совпадают.
- Из `form-keychain`: Тираж 50, цветность «4+0»: срок Python 16.95 ч против JS 16.97 ч — `cut_plotter` округляет время через `round`, JS через `ceil`. Дефолт формы (100 шт, «4+4») по сроку совпал.
- Из `form-keychain`: Вес JS на дефолте 0.12 кг без заготовки; API 1.27 кг с заготовкой.
- Из `form-keychain`: `print_laser` по-прежнему отдаёт `price` как `int()`: на дефолте формы 5742.6 против JS 5743.30, rel 0.00012.
- Из `form-plastic-cards`: Боевой cjsCalc (элемент 2298) пишет ключи `isSignatureStrip ` и `isScratchPanel ` с хвостовым пробелом. На живой форме включённые галки не входят в цену. В `forms/cards.js` ключи без пробела: на 100 шт полоса подписи даёт JS cost 2140 / price 3552.4, скретч — cost 2100 / price 3486. Дефолт обе галки выключены.
- Из `form-plastic-cards`: `isEmbossing` в боевом JS закомментирован, поля формы нет. В API параметр необязательный, в запрос не уходит.
- Из `form-plastic-cards`: `calcCards.js` не подключён в `scripts/run_js_calc.mjs`. Эталон снят прямым прогоном файла в Node vm. Раннер не менялся.
- Из `form-badge`: `calc_service/common/process_tools.py`: `calc_attachment` и `calc_packing` не заполняют `size_mm` у материалов (`Magnet4513`, `ZipLock0812`); в `badge.py` закрыто локально через `_ensure_size_mm`.
- Из `form-badge`: Дефолт формы 64: `weight_kg` API `1.65`, раннер `1.22`. `badge.py` включает вес второй лазерной резки, JS его не складывает (тот же разрыв, что у `EXPECTED_REF` в `test_badge.py`). На цену и срок лида не влияет.
- Из `form-magnet-acrylic`: Имя бумаги `PaperCoated115M`: JS «Титан DIGITAL мелованная (матовая) SRA3 113г/м», API «…115г/м» (`description` в `sheet.json`). Состав, размер листа 320×450 и количество 4 совпадают. JSON не менялся.
- Из `form-magnet-acrylic`: В цепочке `js_port_gaps` у `calcPrintSheet` строка `call calcPrintLaser`: лазерная печать вшита в `print_sheet.py`, строка уже в `scripts/js_port_gaps_allowed.txt`. Новых строк в allowed нет.
- Из `form-magnet-acrylic`: У формы 75 нет радио «дешевле» (value 0), только «стандарт» 1 и «быстрее» 2. `mode=0` проверен на калькуляторе, на странице его не выбрать.
- Из `form-magnet-acrylic`: Форма 75 и копия 118 сами открываются на «двухсторонние» (4+4). Эталон задачи — «односторонние» (4+0). На 4+4 менеджерская цена 5 300 руб. и срок совпали; строка «со скидкой» 4 157 руб. / 41.57 руб./шт на копии и 4 156 руб. / 41.56 руб./шт на боевой.
- Из `form-magnet-acrylic`: Обе заготовки на тираже 100, color 1, mode 1 дают одну цену API 5120.5. Смена формы меняет название и размер (65×65 → 52×77), не цену.
- Из `form-magnet-acrylic`: `wp litespeed-purge all` дважды вернул `Got 400`. `wp cache flush` прошёл. Превью под админом отдало новый расчёт.
- Из `form-magnet-laminated`: Нумерация (`option isNumber`) детектором пропусков считается перенесённой из-за слова `number` в схеме; в расчёте её нет. На дефолте галочка снята, цену не двигает. Строку в allowed не добавлял.
- Из `form-magnet-laminated`: Сложность на форме 54 и 57: 1 / 1.5 / 2, в enum схемы 1 / 1.3 / 1.7. `calculate()` число формы принимает. Прямоугольный дефолт сложность не использует.
- Из `form-magnet-laminated`: Скругление при форме не `rectangular` JS добавляет к вырубке, API умеет его только как `rectangular_rounded` (сабельный рез). В JS копии так только для прямоугольника.
- Из `form-magnet-laminated`: Сложность на форме 54 и 57: 1 / 1.5 / 2, в enum схемы 1 / 1.3 / 1.7. `calculate()` число формы принимает. Прямоугольный дефолт сложность не использует.
- Из `form-magnet-laminated`: Консоль превью копии: `insainParse/scrtp.js` — `TypeError` на `options` и `querySelector`; `admin-ajax.php?action=woocommerce_load_status_widget` — 504. Ошибок `insaincalc` и `ezfc` нет. Форму не трогал.
- Из `form-magnet-laminated`: Скругление при форме не `rectangular` JS добавляет к вырубке, API умеет его только как `rectangular_rounded` (сабельный рез). В JS копии так только для прямоугольника.
- Из `form-tablets`: `scripts/run_js_calc.mjs`: для формы 51 (`CalcHashtags`) падает с `insaincalc.calcMilling is not a function` (не подключён `calcMilling.js`); для формы 68 (`CalcShild`) на дефолте с `materialID=""` падает с `Поле weight_kg не число (NaN)` (в `calcLaser.js` при пустом материале `weight` становится `NaN`).
- Из `form-tablets`: `ssh insain-prod` (5.181.252.133:22): в текущей сессии connection timed out — исходники форм 36/48/51/68/76 получены с опубликованных страниц (`curl.exe` + read-only Browser MCP). Для шагов Site ops понадобится рабочий SSH-доступ к VDS.
- Из `form-tablets`: `scripts/run_js_calc.mjs`: для формы 51 (`CalcHashtags`) падает с `insaincalc.calcMilling is not a function` (не подключён `calcMilling.js`); для формы 68 (`CalcShild`) на дефолте с `materialID=""` падает с `Поле weight_kg не число (NaN)` (в `calcLaser.js` при пустом материале `weight` становится `NaN`).
- Из `form-tablets`: `ssh insain-prod` (5.181.252.133:22): в текущей сессии connection timed out — исходники форм 36/48/51/68/76 получены с опубликованных страниц (`curl.exe` + read-only Browser MCP). Для шагов Site ops понадобится рабочий SSH-доступ к VDS.
- Из `form-tablets`: `scripts/run_js_calc.mjs`: для формы 51 (`CalcHashtags`) падает с `insaincalc.calcMilling is not a function` (не подключён `calcMilling.js`); для формы 68 (`CalcShild`) на дефолте с `materialID=""` падает с `Поле weight_kg не число (NaN)` (в `calcLaser.js` при пустом материале `weight` становится `NaN`).
- Из `form-tablets`: `ssh insain-prod` (5.181.252.133:22): в текущей сессии connection timed out — исходники форм 36/48/51/68/76 получены с опубликованных страниц (`curl.exe` + read-only Browser MCP). Для шагов Site ops понадобится рабочий SSH-доступ к VDS.
- Из `form-tablets`: `calc_service/calculators/sticker.py:308`: для рулонов с `length_min > 0` (`Avery500c`, `Oracal352`, `LGLT4000`, `FES24`, `DMP2000`, `TM3100`) формула `cost_per_m2 * num_min * length_min / 1_000_000 * (width_mm / 1000)` делит на 1000 дважды (против `calcSticker.js:44`, где `* materialCut[1][0]`), занижая стоимость плёнки в 1000 раз (починено в этой задаче по решению человека 26.11.2026). `calc_service/calculators/cut_plotter.py:499`: `round` вместо `Math.ceil` даёт -0.02 ч на `Avery500w 50×50 mode=1` (-0.04 ч в `time_ready`: 21.22 против 21.26, rel=0.00188). Тот же остаток 0.02 ч на `mode=2`: `LGLT4000`/`DMP2000`/`TM3100` 13.79 против 13.81, `FES24` 14.25 против 14.27. После чтения `length_min` себестоимость эталона `cut_plotter` `Avery500c` сдвинулась `400.64` → `401` и `2954.06` → `2955`, цена осталась `642` и `4727`. Формулу `cut_plotter.py` не меняли. На API из калькуляторов сейчас только `puzzle`, он `length_min` не читает.
- Из `form-tablets`: `calc_service/materials/loader.py:171`: `length_min=merged.get("lengthMin")` не читал ключ `"length_min"` из `roll.json` и `sheet.json`, из-за чего `material.length_min` всегда был `None` в runtime (починено в этой задаче по решению человека 27.11.2026).
- Из `form-tablets`: Поле `numDensity` (боевое 1425, копия 4377) при «Простая форма» скрыто, `calculate_when_hidden=0`, `factor=0.01`. Старый `cjsCalc` формы 36 и `tablets.js` читают его через `get_value_from` и получают `0`. На копии Avery500w поэтому `13 700` (`POST` `13685.42`), а не `13 800` от эталона с `density` `0.25`. Чтобы в цену входила плотность 25% скрытого поля, нужно отдельное решение: боевая форма 36 так не считает.
- Из `form-tablets`: `scripts/run_js_calc.mjs`: для формы 51 (`CalcHashtags`) падает с `insaincalc.calcMilling is not a function` (не подключён `calcMilling.js`); для формы 68 (`CalcShild`) на дефолте с `materialID=""` падает с `Поле weight_kg не число (NaN)` (в `calcLaser.js` при пустом материале `weight` становится `NaN`).
- Из `form-tablets`: `ssh insain-prod` (5.181.252.133:22): в текущей сессии connection timed out — исходники форм 36/48/51/68/76 получены с опубликованных страниц (`curl.exe` + read-only Browser MCP). Для шагов Site ops понадобится рабочий SSH-доступ к VDS.
- Из `form-tablets`: `calc_service/calculators/sticker.py:308`: для рулонов с `length_min > 0` (`Avery500c`, `Oracal352`, `LGLT4000`, `FES24`, `DMP2000`, `TM3100`) формула `cost_per_m2 * num_min * length_min / 1_000_000 * (width_mm / 1000)` делит на 1000 дважды (против `calcSticker.js:44`, где `* materialCut[1][0]`), занижая стоимость плёнки в 1000 раз (починено в этой задаче по решению человека 26.11.2026). `calc_service/calculators/cut_plotter.py:499`: `round` вместо `Math.ceil` даёт -0.02 ч на `Avery500w 50×50 mode=1` (-0.04 ч в `time_ready`: 21.22 против 21.26, rel=0.00188). Тот же остаток 0.02 ч на `mode=2`: `LGLT4000`/`DMP2000`/`TM3100` 13.79 против 13.81, `FES24` 14.25 против 14.27. После чтения `length_min` себестоимость эталона `cut_plotter` `Avery500c` сдвинулась `400.64` → `401` и `2954.06` → `2955`, цена осталась `642` и `4727`. Формулу `cut_plotter.py` не меняли. На API из калькуляторов сейчас только `puzzle`, он `length_min` не читает.
- Из `form-tablets`: `calc_service/materials/loader.py:171`: `length_min=merged.get("lengthMin")` не читал ключ `"length_min"` из `roll.json` и `sheet.json`, из-за чего `material.length_min` всегда был `None` в runtime (починено в этой задаче по решению человека 27.11.2026).
