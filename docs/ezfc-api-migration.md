# Перевод калькулятора ezFC на Python API

Один и тот же вывод во всех формах: цена менеджера, цена со скидкой, вес, срок с подсказкой, таблица материалов. Его делает `insaincalc.showResult` в `wp-plugin/js/insain-calc-bridge.js`. В `cjsCalc` остаётся сбор параметров, вызов `calcApi` и отдельно вызов `showResult`.

Эталон: форма пазлов, элемент `cjsCalc`. Документация ezFC: [ez-form-calculator.ezplugins.de/documentation](https://ez-form-calculator.ezplugins.de/documentation/).

## Что делает форма, что — bridge

| Задача | Кто |
|---|---|
| Прочитать поля формы | custom JS: `{{numN}}`, `ezfc_functions.get_value_from` |
| Собрать тело `POST /api/v1/calc/{slug}` | custom JS |
| Вызвать API и привести ответ к `calcCost` | `insaincalc.calcApi` |
| Обновить `?numN=&dpdformat=` | `insaincalc.syncUrl` (имена = GET полей формы) |
| Записать цену, вес, срок, материалы | `insaincalc.showResult` |
| Показать ошибку API | `insaincalc.showError` |

Не читать поля через DOM (`querySelector`, `select.options`). Не дублировать `timeToWords` / `calcDateReady` / запись цены в форме.

## Шаблон `cjsCalc` → Custom_calculation

```js
var qty = {{numN}};
var materialId = ezfc_functions.get_value_from(NNNN, true)[0];
var fmtIndex = ezfc_functions.get_value_from(NNNN, true, false, { return_value: 'index' })[0];
var mode = Number(ezfc_functions.get_value_from(MMMM, true)[0]) || 1;

insaincalc.syncUrl({ numN: qty, dpdformat: fmtIndex, rdoModeProduction: mode });

insaincalc.calcApi('SLUG', {
    quantity: Number(qty) || 1,
    material_id: materialId,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
```

Подставить: `SLUG`, id элементов, ключи API, ключи `syncUrl` (GET-имена формы).

`calcApi` и `showResult` не смешивать в одну обёртку: форме может понадобиться свой разбор `calcCost` до вывода.

## Как читать поля

| Что нужно | Как |
|---|---|
| Число (`numN`, размеры) | плейсхолдер `{{numN}}` по **имени** элемента |
| Текстовый код dropdown (`Puzzle300420`, `PVC3`) | `ezfc_functions.get_value_from(id, true)[0]` |
| Индекс option для URL | `get_value_from(id, true, false, { return_value: 'index' })[0]` |
| Значение radio (`1` / `2`) | `get_value_from(id, true)[0]` и `GET_check_option_value=value` |

`{{dpdFormat}}` для текстового dropdown нельзя: плагин делает `parseFloat("Puzzle300420")` → `0`.

`true` у `get_value_from` обязателен для кодов: без него тоже `parseFloat` → `0`.

## GET и share-URL

У каждого шарингового поля: `ADVANCED → GET` (имя в URL).

- Dropdown с кодом в `data-value`: `GET_check=index`, в URL пишем индекс, в API — `get_value_from(..., true)[0]`.
- Radio со значениями `1`/`2`: `GET_check=value`, в URL и в API одно и то же число.

Иначе режим «стандарт / быстрее» начнёт меняться местами при перезагрузке (как было у пазлов).

Файлы в URL не кладём.

## Имена полей вывода (не трогать в форме)

Почти на всех калькуляторах уже так:

- `sbtPriceTotalManager` / `sbtPriceManager`
- `sbtPriceTotalDiscount` / `sbtPriceDiscount` (если есть)
- `sbtWeightTotal`
- блок `.htmTime` (текст «Срок …» + `data-bs-original-title` на `<a>`)
- `.data-material-table`

`showResult` ищет их по имени через `get_element_id_by_name`. Новые id выдумывать не нужно.

Цена со скидкой: `cost * (1 + marginMin)`, как в calcUVPrint, не сырая себестоимость.

## Чеклист перевода

1. `GET /api/v1/tool_schema/{slug}` — список параметров API.
2. В админке ezFC выписать id и имена полей ввода; проставить GET.
3. Заменить `insaincalc.calcXxx(...)` на `insaincalc.calcApi` и `insaincalc.showResult`.
4. Удалить из `cjsCalc` свой вывод цены/срока/материалов и чтение через DOM.
5. Лоадер `/icalc/` оставить, пока форме нужны `insaincalc.round`, `timeToWords`, `showMaterials`.
6. Проверка на странице:
   - в Network есть `POST /api/v1/calc/{slug}` и в теле верные коды, не `0`;
   - смена dropdown меняет цену и материалы;
   - перезагрузка не меняет режим и срок;
   - у срока есть подсказка с датами;
   - URL обновляется GET-именами формы.

## Чего не копировать из старого JS

- Карты `0 → Puzzle300420` — код уже в `data-value`.
- `document.querySelector('#ezfc_element-… select')`.
- Свой `setAmount` / запись в `.htmTime` — это `insaincalc.showResult`.
- `await` внутри `function(price)` ezFC: custom JS синхронный, продолжение — в `.then`.
