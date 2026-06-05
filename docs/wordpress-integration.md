# Интеграция с WordPress

Настройка Cursor, SSH и автономных проверок на prod: [agent-autonomous-environment.md](agent-autonomous-environment.md).

## Текущее состояние

На сайте используется **ez Form Calculator for WordPress**. Формы уже собраны в админке плагина, а для каждого калькулятора внутри формы есть custom JS-обработчик: он собирает значения через плейсхолдеры ez Form Calculator (`{{numN}}`, `{{dpdformat}}` и т.п.), вызывает старую JS-функцию `insaincalc.calc...`, затем записывает результат обратно в переменные формы и DOM.

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

1. custom JS-обработчик формы собирает параметры;
2. вместо старого `insaincalc.calc...` вызывает bridge-функцию из `wp-plugin`;
3. bridge делает `GET /api/v1/product/{product_slug}` для defaults и `base_calc_slug`;
4. bridge делает `POST /api/v1/calc/{slug}`;
5. bridge адаптирует новый ответ API к старому объекту `calcCost`;
6. существующий код формы выводит цену, срок, вес и материалы почти без изменений.

На боевом сайте использовать относительный API URL:

```text
/api/v1
```

На боевом сайте `https://insain.ru` используется тот же относительный путь `/api/v1` (nginx проксирует на calc-api). См. [agent-autonomous-environment.md](agent-autonomous-environment.md).

## Главная Схема Замены

Нельзя просто написать `let calcCost = fetch(...)`: в таком виде ez Form получит `Promise`, а не объект расчёта. Обработчик, в котором вызывается новый сервис, должен быть `async` или должен продолжать работу в `.then(...)`.

Рекомендуемый вариант для форм ez Form Calculator:

```js
let calcCost = await insainCalcLegacy('puzzle', {
    quantity: {{numN}},
    puzzle_id: puzzleId,
    mode: {{rdoModeProduction}} || 1
});
```

Если конкретное поле/обработчик ez Form не допускает `await`, использовать Promise-цепочку:

```js
insainCalcLegacy('puzzle', {
    quantity: {{numN}},
    puzzle_id: puzzleId,
    mode: {{rdoModeProduction}} || 1
}).then(function(calcCost) {
    PriceTotalManager = insaincalc.round(calcCost.price, {{numN}});
    WeightTotal = calcCost.weight;
});
```

## JS Bridge

Файлы:

```text
wp-plugin/
├── insain-calc-bridge.php
└── js/insain-calc-bridge.js
```

Публичные функции bridge:

- `insainCalc(slug, params)` — прямой `POST /api/v1/calc/{slug}`, возвращает новый Python-контракт.
- `insainCalcLegacy(productSlug, params)` — загружает `/product/{productSlug}`, применяет `defaults`, вызывает калькулятор и возвращает объект в старом формате `calcCost`.
- `InsainCalcBridge.recalculate(productSlug)` — вариант для автономной привязки к DOM-полям, если у формы нет удобного custom JS-сборщика.

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

## Пилот: Puzzle

Страница: `https://insain.ru/catalog/kalkulyator-pazlov/`.

API:

```http
GET /api/v1/product/puzzle
POST /api/v1/calc/puzzle
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

Коды `dpdformat`:

| value формы | `puzzle_id` |
| --- | --- |
| `0` | `Puzzle300420` |
| `1` | `Puzzle208298` |
| `2` | `Puzzle159215` |

Пример замены в обработчике формы:

```js
const puzzleMap = {
    0: 'Puzzle300420',
    1: 'Puzzle208298',
    2: 'Puzzle159215'
};

let puzzleId = puzzleMap[{{dpdformat}}] || {{dpdformat}};
let calcCost = await insainCalcLegacy('puzzle', {
    quantity: {{numN}},
    puzzle_id: puzzleId,
    mode: 1
});
```

Дальше текущий код вывода цены, веса, срока и материалов можно оставить прежним.

## Узкие Места

- Асинхронность: любой обработчик, в котором вызывается `calc_service`, должен уметь дождаться `Promise`. Это главный риск для ez Form Calculator.
- Область видимости переменных: если ez Form ожидает, что `PriceTotalManager`, `WeightTotal` и другие значения будут установлены синхронно в одном проходе расчёта, нужно проверить, срабатывает ли обновление после `await`/`.then(...)`.
- Формат select-полей: в DOM может быть `value=0`, а API ждёт `Puzzle300420`. Для каждого калькулятора нужен явный маппинг `value -> code`.
- Материалы: старый `material` был `Map`, новый API возвращает `materials[]`. Bridge конвертирует массив обратно в `Map`, но надо проверить, что `insaincalc.showMaterials()` корректно отображает новый набор полей.
- Сроки: старый код ждёт `timeReady`, API отдаёт `time_ready`. Bridge маппит поле, но `timeToWords()` и `calcDateReady()` остаются на стороне сайта.
- Ошибки API: при недоступности сервиса нельзя затирать форму нулями без сообщения пользователю. В `catch` нужно показывать понятную ошибку или оставлять предыдущий успешный результат.
- CORS/прокси: на `insain.ru` используется относительный `/api/v1`, поэтому браузер идёт на тот же origin и CORS не нужен. При выносе API на отдельный домен нужно явно разрешить origin WordPress.
- Кэширование defaults: `/product/{slug}` можно кэшировать в JS на время страницы, но при изменении product defaults в API нужно учитывать браузерный/CDN-кэш.

## Что Нужно Для Каждого Следующего Калькулятора

Для перехода очередной формы на `calc_service` нужно собрать:

1. URL страницы калькулятора на сайте.
2. Название старой JS-функции и полный custom JS-сборщик из ez Form Calculator.
3. Список плейсхолдеров ez Form (`{{numN}}`, `{{dpdmaterial}}`, `{{rdoModeProduction}}` и т.п.).
4. Маппинг значений select/radio/checkbox в коды нового API.
5. `product_slug` и `base_calc_slug` из `GET /api/v1/product/{slug}`.
6. Пример эталонного расчёта: входные параметры, старая цена/срок/вес, новая цена/срок/вес.
7. Особые DOM-выводы: `.htmTime`, `.data-material-table`, поля цены, поля веса, подсказки tooltip.

## Проверка Перехода

Минимальный чек-лист для пилота:

1. Открыть страницу на `https://insain.ru` (URL калькулятора из задачи).
2. Проверить в DevTools, что загружен `insain-calc-bridge.js`.
3. Проверить `GET /api/v1/product/puzzle`.
4. Проверить `POST /api/v1/calc/puzzle` для всех трёх вариантов пазла.
5. Проверить, что цена, себестоимость, вес, срок и таблица материалов обновляются в форме.
6. Проверить ошибку API: временно передать несуществующий `puzzle_id` и убедиться, что форма не ломается.
7. Проверить share-параметры в URL: `quantity`, `puzzle_id`, `mode`.
