// Форма 49 CalcRollup, элемент cjsCalc (2026). Id полей — боевой формы 49.
var qty = {{numN}};
var rollupType = ezfc_functions.get_value_from(2024, true)[0];
var rollupTypeIndex = ezfc_functions.get_value_from(2024, true, false, { return_value: 'index' })[0];
var size = ezfc_functions.get_value_from(2020, true)[0];
var sizeIndex = ezfc_functions.get_value_from(2020, true, false, { return_value: 'index' })[0];
var materialId = ezfc_functions.get_value_from(2043, true)[0];
var materialIndex = ezfc_functions.get_value_from(2043, true, false, { return_value: 'index' })[0];
var modeRaw = ezfc_functions.get_value_from(2039, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

var rollupId = 'Rollup_' + rollupType + '_' + size;

insaincalc.syncUrl({
    numN: qty,
    dpdRollup: rollupTypeIndex,
    dpdSize: sizeIndex,
    dpdPoster: materialIndex,
    rdoModeProduction: mode
});

insaincalc.calcApi('rollup', {
    quantity: Number(qty) || 1,
    rollup_id: rollupId,
    material_id: materialId || '',
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
