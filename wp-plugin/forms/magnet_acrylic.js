// Форма 75, элемент cjsCalc (2992). Id полей — боевой формы 75.
// Упаковки на форме нет: старый calcAcrylicMagnets всегда считает зиплок.
// Файл fluAtrwork в URL и в API не уходит.
// На форме нет режима «дешевле» (value 0); ноль всё равно не подменяем на 1.
var qty = {{numN}};
var magnetId = ezfc_functions.get_value_from(2989, true)[0];
var blankIndex = ezfc_functions.get_value_from(2989, true, false, { return_value: 'index' })[0];
var colorRaw = ezfc_functions.get_value_from(2990, true)[0];
var colorIndex = ezfc_functions.get_value_from(2990, true, false, { return_value: 'index' })[0];
// В форме data-value «4+0» / «4+4», в API color — 1 или 2.
var color = String(colorRaw) === '4+4' ? 2 : 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(3005, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdBlank: blankIndex,
    dpdColor: colorIndex,
    rdoModeProduction: mode
});

insaincalc.calcApi('magnet_acrylic', {
    quantity: Number(qty) || 1,
    magnet_id: magnetId,
    color: color,
    is_packing: true,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
