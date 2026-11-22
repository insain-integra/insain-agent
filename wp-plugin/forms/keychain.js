// Форма 74, элемент cjsCalc (2968). Id полей — боевой формы 74.
// Упаковки на форме нет: старый calcAcrylicKeychain всегда считает зиплок.
// Файл fluAtrwork в URL и в API не уходит.
var qty = {{numN}};
var keychainId = ezfc_functions.get_value_from(2965, true)[0];
var blankIndex = ezfc_functions.get_value_from(2965, true, false, { return_value: 'index' })[0];
var colorRaw = ezfc_functions.get_value_from(2985, true)[0];
var colorIndex = ezfc_functions.get_value_from(2985, true, false, { return_value: 'index' })[0];
// В форме data-value «4+0» / «4+4», в API color — 1 или 2.
var color = String(colorRaw) === '4+4' ? 2 : 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2981, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdBlank: blankIndex,
    dpdColor: colorIndex,
    rdoModeProduction: mode
});

insaincalc.calcApi('keychain', {
    quantity: Number(qty) || 1,
    keychain_id: keychainId,
    color: color,
    is_packing: true,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
