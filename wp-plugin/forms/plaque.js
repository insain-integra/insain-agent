// Форма 69 CalcPlaque, элемент cjsCalc (2783). Id полей — боевой формы 69.
var qty = {{numN}};
var plaqueId = ezfc_functions.get_value_from(2778, true)[0];
var plaqueIndex = ezfc_functions.get_value_from(2778, true, false, { return_value: 'index' })[0];
var materialId = ezfc_functions.get_value_from(2776, true)[0];
var materialIndex = ezfc_functions.get_value_from(2776, true, false, { return_value: 'index' })[0];
var applicationId = ezfc_functions.get_value_from(2779, true)[0];
var applicationIndex = ezfc_functions.get_value_from(2779, true, false, { return_value: 'index' })[0];
var modeRaw = ezfc_functions.get_value_from(2796, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdFormat: plaqueIndex,
    dpdMaterial: materialIndex,
    dpdApplication: applicationIndex,
    rdoModeProduction: mode
});

insaincalc.calcApi('plaque', {
    quantity: Number(qty) || 1,
    plaque_id: plaqueId,
    material_id: materialId,
    application: applicationId,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
