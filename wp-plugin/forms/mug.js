// Форма 41 CalcMug, элемент cjsCalc (1603). Id полей — боевой формы 41.
var qty = {{numN}};
var mugId = ezfc_functions.get_value_from(1597, true)[0];
var mugIndex = ezfc_functions.get_value_from(1597, true, false, { return_value: 'index' })[0];
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(1617, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;
// Чекбокс: get_value_from → [true]/0/'true'; без [0], как в старом CalcMug cjsCalc
var isPacking = ezfc_functions.get_value_from(1601, true) == 'true';
var isDifferent = ezfc_functions.get_value_from(1599, true) == 'true';

insaincalc.syncUrl({
    numN: qty,
    dpdTypeMug: mugIndex,
    // Чекбокс: GET_check=index; включён → индекс единственной опции 0; выключен → '' (удалить).
    ckbPacking: isPacking ? 0 : '',
    ckbDifferent: isDifferent ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('mug', {
    quantity: Number(qty) || 1,
    mug_id: mugId,
    is_packing: isPacking,
    is_different: isDifferent,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
