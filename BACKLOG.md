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
