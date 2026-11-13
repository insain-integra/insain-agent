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
var modeRaw = ezfc_functions.get_value_from(MMMM, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

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
| Режим `rdoModeProduction` (`0` / `1` / `2`) | `get_value_from(id, true)[0]` и `GET_check=value`. Ноль не заменять на 1 |

`{{dpdFormat}}` для текстового dropdown нельзя: плагин делает `parseFloat("Puzzle300420")` → `0`.

`true` у `get_value_from` обязателен для кодов: без него тоже `parseFloat` → `0`.

## GET и share-URL

У каждого шарингового поля: `ADVANCED → GET` (имя в URL). Соглашение: GET = имя элемента формы
(`numN`, `dpdFormat`, `dpdMaterial`, `dpdApplication`, `rdoModeProduction`). Тот же набор имён и
`GET_check` прописывается и на копии, и на боевой форме перед её переключением. `insaincalc.syncUrl`
в `forms/<slug>.js` обязателен — это проверяет `calc_service/tests/test_wp_plugin_forms.py`.

- Dropdown с кодом в `data-value`: `GET_check=index`, в URL пишем индекс, в API — `get_value_from(..., true)[0]`.
- Режим `rdoModeProduction` при каждом переводе формы на API: `GET_check=value`, в том числе если среди значений есть `0`. В URL и в API одно и то же число. Пустое поле заменяется на `1`, ноль остаётся нулём.

Иначе режим «дешевле / стандарт / быстрее» начнёт меняться местами при перезагрузке (как было у пазлов).

Файлы в URL не кладём.

## Блок результата

Эталон раскладки — форма 79 (CalcPuzzle), не старый блок боевой формы. `showResult` пишет числа по **имени** элемента и в разметку ниже. Свой вывод в `forms/<slug>.js` не добавлять. Id полей ввода не менять. Группы и HTML правят в админке ezFC и на копии, и на боевой форме перед её переключением.

Сверху вниз внутри группы расчёта:

1. **Цена** — одна группа `grpPrice`, колонки 6, стиль обёртки `border: 1px solid #3dcc5c; border-radius: 5px; padding: 0.0em;`. Ненулевой padding сдвигает две колонки на две строки.
   - Слева `grpPriceManager`, колонки 3. Заголовок с текстом «цена» (не «Цена» и не «через менеджера»). Под ним видимые `sbtPriceTotalManager` (`  руб.`) и `sbtPriceManager` (` руб./шт`).
   - Справа `grpPriceDiscount`, колонки 3, стиль `padding-bottom: 0em;width: auto;`. Внутри скрытые `sbtPriceTotalDiscount` и `sbtPriceDiscount` и видимый `htmCost`.
2. **Срок** — группа `grpTime`. Внутри сначала `htmTime`, сразу под ним `rdoModeProduction`. Режим — ребёнок группы срока, не сосед группы расчёта.
3. **Вес** — `sbtWeightTotal`, подпись «Вес тиража», после ` кг.`
4. **Материалы** — группа `grpMaterial` и в ней `htmMaterial`.

`htmTime`, класс `htmTime` только на внутреннем `div`, не в `wrapper_class`. Иначе `showResult` затирает внутренний `<a>` и подсказка дат пропадает:

```html
<div class="porto-tooltip inline htmTime">
<div class="inline">Срок</div>
<a class="inline ezfc-element-description" style="white-space: pre-line;" title="" data-html="true" data-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Готовность">&nbsp;</a>
</div>
```

`htmCost`, доступ через шорткод, не сырая себестоимость. Стиль обёртки `margin: 0em;padding:0em;`, `do_shortcode` = 1:

```html
[access capability="read_maxdiscount"]
<p style="font-size: 0.7em; margin: 0em; padding-bottom: 0.7em;">со скидкой&nbsp;</p>
<p style="font-size: 1.12em; margin: 0em;">{{sbtPriceTotalDiscount}}</p>
<p style="font-size: 0.84em; margin: 0em; color: gray; padding: 0.5em;">{{sbtPriceDiscount}}</p>
[/access]
```

`htmMaterial`, `do_shortcode` = 1:

```html
[access capability="read_material"]
<div class="data-material">
<h3>Расход материалов</h3>
<div class="data-material-table">&nbsp;</div>
</div>
[/access]
```

Скидка в `showResult`: `cost * (1 + marginMin)`, не себестоимость. Старый видимый блок себестоимости (`htmCost` с `{{sbtCostTotal}}`, подпись «Себестоимость», доступ `edit_posts`) и клиентские `sbtPrice` / `sbtPriceTotal` на результате не оставлять: `showResult` не заполняет их как скидку. Бывшие `sbtCostTotal` / `sbtCost` переименовать в `sbtPriceTotalDiscount` / `sbtPriceDiscount` и скрыть. Отдельный заголовок «Цена» над колонками убрать: он занимает всю строку.

У скрытых `sbtPriceTotalDiscount` и `sbtPriceDiscount` включить `calculate_when_hidden`. Плейсхолдер в `htmCost` спрашивает значение у ezFC. Скрытый subtotal с выключенным флагом отдаёт 0, хотя `showResult` уже записал число. Видимые менеджерские поля флаг не включают. Поле штучной скидки не копировать с `sbtPriceManager`: у него флаг выключен, и после скрытия `{{sbtPriceDiscount}}` показывает 0. Дубль старой формы этот блок не приносит — его собирают по этому разделу, не заново.

Проверка на странице: менеджерская цена и «со скидкой» в одной строке; под «Срок …» сразу режим; у `<a>` есть `data-bs-original-title` с датами; в таблице материалов название, размер и количество, внутренних `code` нет.

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
   - блок результата как у формы 79: цена и «со скидкой» в одной строке, режим внутри группы срока, таблица материалов (раздел «Блок результата»);
   - у срока есть подсказка с датами;
   - URL обновляется GET-именами формы.

## Чего не копировать из старого JS

- Карты `0 → Puzzle300420` — код уже в `data-value`.
- `document.querySelector('#ezfc_element-… select')`.
- Свой `setAmount` / запись в `.htmTime` — это `insaincalc.showResult`.
- `await` внутри `function(price)` ezFC: custom JS синхронный, продолжение — в `.then`.
