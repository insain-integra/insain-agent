# Интеграция с WordPress

Настройка Cursor, SSH и автономных проверок на prod: [agent-autonomous-environment.md](agent-autonomous-environment.md).

## Текущее состояние

На сайте используется **ez Form Calculator for WordPress**. Формы уже собраны в админке плагина, а для каждого калькулятора внутри формы есть custom JS-обработчик: он собирает значения через API плагина (`ezfc_functions.get_value_from`, плейсхолдеры `{{numN}}` и т.п.), вызывает старую JS-функцию `insaincalc.calc...`, затем записывает результат обратно в переменные формы.

Типовой фрагмент старого обработчика:

```js
let calcCost = insaincalc.calcAcrilycPrizes({{numN}}, layers, options, {{rdoModeProduction}});

PriceTotalManager = insaincalc.round(calcCost.price, {{numN}});
PriceTotalDiscount = calcCost.cost * (1 + marginMin);
WeightTotal = calcCost.weight;
timeReady = insaincalc.timeToWords(calcCost.timeReady);
dateReady = insaincalc.calcDateReady(calcCost.timeReady);
document.getElementsByClassName('data-material-table')[0].innerHTML =
    insaincalc.showMaterials(calcCost.material);
```

Документация плагина: [ez Form Calculator documentation](https://ez-form-calculator.ezplugins.de/documentation/). Важное ограничение для миграции: старый обработчик написан как синхронный JS, а `fetch` к `calc_service` всегда асинхронный.

## Целевое состояние

Пользователь заполняет ту же форму ez Form Calculator, но расчёт выполняется в Python:

1. custom JS-обработчик формы собирает параметры и маппит значения в коды API;
2. вместо старого `insaincalc.calc...` вызывает тонкую bridge-функцию из `wp-plugin`;
3. bridge делает `POST /api/v1/calc/{slug}`;
4. bridge адаптирует новый ответ API к старому объекту `calcCost`;
5. тот же обработчик вызывает `insaincalc.syncUrl(...)` для обновления шаринговой ссылки;
6. `insaincalc.showResult(...)` выводит цену, срок, вес и материалы.

> Bridge (v0.2.3) не знает коды материалов конкретной формы и не ходит в `/product/{slug}`.
> Сбор параметров — в custom JS формы. Расчёт (`calcApi`) и вывод (`showResult`) — отдельные методы `insaincalc`.
> Пошаговый перевод: [ezfc-api-migration.md](ezfc-api-migration.md).

На боевом сайте использовать относительный API URL:

```text
/api/v1
```

На боевом сайте `https://insain.ru` используется тот же относительный путь `/api/v1` (nginx проксирует на calc-api). См. [agent-autonomous-environment.md](agent-autonomous-environment.md).

## Главная Схема Замены

Нельзя просто написать `let calcCost = fetch(...)`: в таком виде ez Form получит `Promise`, а не объект расчёта. Обработчик, в котором вызывается новый сервис, должен быть `async` или должен продолжать работу в `.then(...)`.

Рекомендуемый вариант для форм ez Form Calculator:

```js
insaincalc.calcApi('puzzle', {
    quantity: {{numN}},
    puzzle_id: puzzleId,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, {{numN}}, __form_id__);
});
```

## JS Bridge

Файлы:

```text
wp-plugin/
├── insain-calc-bridge.php
└── js/insain-calc-bridge.js
```

Методы на объекте `insaincalc` (v0.2.3):

- `calcApi(slug, params)` — `POST /api/v1/calc/{slug}` и адаптер в старый `calcCost`. Устаревший ответ (если форму пересчитали раньше) возвращает `null`.
- `showResult(calcCost, qty, formId)` — цена, вес, срок с подсказкой, материалы.
- `showError(err, formId)` — текст ошибки в блоке срока.
- `syncUrl(params)` — query-строка (`history.replaceState`), имена = GET полей формы.

Поля формы читает сам ezFC: `{{numN}}` и `ezfc_functions.get_value_from`. Маппинг в параметры API — только в custom JS формы.

Адаптация ответа:

```js
{
    cost: result.cost,
    price: result.price,
    unit_price: result.unit_price,
    time: result.time_hours,
    timeReady: result.time_ready,
    weight: result.weight_kg,
    material: Map,        // собрано из result.materials
    materials: Array,     // исходный массив Python API
    share_url: result.share_url,
    raw: result
}
```

Это сохраняет совместимость с текущими вызовами:

- `insaincalc.round(calcCost.price, n)`;
- `calcCost.cost`;
- `calcCost.weight`;
- `insaincalc.timeToWords(calcCost.timeReady)`;
- `insaincalc.calcDateReady(calcCost.timeReady)`;
- `insaincalc.showMaterials(calcCost.material)`.

## GET-поля и шаринговые ссылки

Задача: делиться ссылкой на готовый расчёт (`?numN=111&dpdformat=0`), чтобы при открытии
форма заполнилась и пересчиталась автоматически.

Разделение ответственности:

| Направление | Кто делает |
|---|---|
| URL → поля (при загрузке) | **ez Form Calculator**, встроенное свойство `GET` у поля (`ADVANCED → GET`) |
| поля → API | custom JS формы (маппинг в коды API) |
| API → расчёт | `insaincalc.calcApi()` |
| поля → URL (для шеринга) | `insaincalc.syncUrl()`, вызывается из того же custom JS |

Важно:

- В URL храним «язык формы» (GET-имена ez Form Calculator: `numN`, `dpdformat`), а не
  API-имена (`quantity`, `puzzle_id`). Тогда встроенное чтение ez Form Calculator работает
  без нашего кода, а маппинг в API-имена живёт в custom JS.
- У каждого шарингового поля в ez Form Calculator должно быть задано `ADVANCED → GET`
  (у `numN` уже есть; для остальных полей — проставить в админке).
- Файл-поля (например «Файлы для печати») в URL не кладём.

Автообновление ссылки: custom JS секции CALCULATE выполняется при каждом пересчёте,
поэтому отдельная кнопка не нужна — достаточно вызвать `insaincalc.syncUrl(...)` в обработчике:

```js
var qty = {{numN}};
var puzzleId = ezfc_functions.get_value_from(3104, true)[0];
var fmtIndex = ezfc_functions.get_value_from(3104, true, false, { return_value: 'index' })[0];
var mode = Number(ezfc_functions.get_value_from(3121, true)[0]) || 1;

insaincalc.syncUrl({ numN: qty, dpdformat: fmtIndex, rdoModeProduction: mode });

insaincalc.calcApi('puzzle', {
    quantity: qty,
    puzzle_id: puzzleId,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
```

## Пилот: Puzzle

Страница: `https://insain.ru/catalog/kalkulyator-pazlov/`.

API:

```http
POST /api/v1/calc/puzzle
GET  /api/v1/product/puzzle   # опционально: defaults/base_calc_slug, тонкий bridge не вызывает
```

`/api/v1/product/puzzle` возвращает:

```json
{
  "base_calc_slug": "puzzle",
  "defaults": {
    "quantity": 1,
    "puzzle_id": "Puzzle300420"
  }
}
```

Поля ez Form Calculator:

| Параметр API | Старое поле формы | ezfc_id | Примечание |
| --- | --- | --- | --- |
| `quantity` | `numn` | `3103` | Тираж |
| `puzzle_id` | `dpdformat` | `3104` | Select формата |
| `mode` | режим производства | зависит от формы | Если нет поля, использовать `1` |

Читать поля формы **через API ez Form Calculator**, не через DOM:

- числа и индексы — плейсхолдеры по **имени** элемента: `{{numN}}`, `{{dpdFormat}}`, `{{rdoModeProduction}}`;
- текстовые коды dropdown (`Puzzle300420`) — `ezfc_functions.get_value_from(id, true)[0]` (`true`, иначе `parseFloat` даст `0`);
- id элемента по имени: `ezfc_functions.get_element_id_by_name(__form_id__, 'dpdFormat')`.

Документация: [ez Form Calculator](https://ez-form-calculator.ezplugins.de/documentation/).

Пример обработчика (как CalcMug):

```js
let puzzleId = ezfc_functions.get_value_from(3104, true)[0];
insaincalc.calcApi('puzzle', {
    quantity: {{numN}},
    puzzle_id: puzzleId,
    mode: Number(ezfc_functions.get_value_from(3121, true)[0]) || 1
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, {{numN}}, __form_id__);
});
```

`{{dpdFormat}}` для текстового dropdown нельзя использовать: плагин делает `parseFloat` от `data-value` (`Puzzle300420` → `0`). Индекс для share-URL: `get_value_from(3104, true, false, { return_value: 'index' })[0]`. В API уходит `get_value_from(3104, true)[0]`.

Дальше текущий код вывода цены, веса, срока и материалов можно оставить прежним.

## Узкие Места

- Асинхронность: любой обработчик, в котором вызывается `calc_service`, должен уметь дождаться `Promise`. Это главный риск для ez Form Calculator.
- Область видимости переменных: если ez Form ожидает, что `PriceTotalManager`, `WeightTotal` и другие значения будут установлены синхронно в одном проходе расчёта, нужно проверить, срабатывает ли обновление после `await`/`.then(...)`.
- Формат select-полей: HTML `value` — индекс, код API лежит в `data-value`. Читать через `get_value_from(id, true)[0]`, не через DOM и не через `{{dpdFormat}}` (это индекс, `parseFloat` кода даст `0`).
- Материалы: старый `material` был `Map`, новый API возвращает `materials[]`. Bridge конвертирует массив обратно в `Map`, но надо проверить, что `insaincalc.showMaterials()` корректно отображает новый набор полей.
- Сроки: старый код ждёт `timeReady`, API отдаёт `time_ready`. Bridge маппит поле, но `timeToWords()` и `calcDateReady()` остаются на стороне сайта.
- Ошибки API: при недоступности сервиса нельзя затирать форму нулями без сообщения пользователю. В `catch` нужно показывать понятную ошибку или оставлять предыдущий успешный результат.
- CORS/прокси: на `insain.ru` используется относительный `/api/v1`, поэтому браузер идёт на тот же origin и CORS не нужен. При выносе API на отдельный домен нужно явно разрешить origin WordPress.
- Defaults: тонкий bridge `/product/{slug}` не загружает. Если форме нужны server-side defaults/`base_calc_slug`, custom JS формы запрашивает их сам (`GET /api/v1/product/{slug}`) и при необходимости кэширует на время страницы. Обычно проще передать все параметры явно из полей формы.

## Что Нужно Для Каждого Следующего Калькулятора

Пошаговый рецепт и шаблон `cjsCalc`: [ezfc-api-migration.md](ezfc-api-migration.md).

Кратко собрать перед правкой формы:

1. URL страницы и slug API (`GET /api/v1/tool_schema/{slug}`).
2. Id/имена полей ввода и GET-имена для share-URL.
3. Эталон: те же входы, старая и новая цена / срок / вес.

## Проверка Перехода

Минимальный чек-лист для пилота:

1. Открыть страницу на `https://insain.ru` (URL калькулятора из задачи).
2. Проверить в DevTools, что загружен `insain-calc-bridge.js`.
3. Проверить `GET /api/v1/product/puzzle`.
4. Проверить `POST /api/v1/calc/puzzle` для всех трёх вариантов пазла.
5. Проверить, что цена, себестоимость, вес, срок и таблица материалов обновляются в форме.
6. Проверить ошибку API: временно передать несуществующий `puzzle_id` и убедиться, что форма не ломается.
7. Проверить share-параметры в URL: `quantity`, `puzzle_id`, `mode`.
