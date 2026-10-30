// Форма 69 CalcPlaque, элемент cjsCalc (2783). Id полей — боевой формы 69.
var qty = {{numN}};
var plaqueId = ezfc_functions.get_value_from(2778, true)[0];
var materialId = ezfc_functions.get_value_from(2776, true)[0];
var applicationId = ezfc_functions.get_value_from(2779, true)[0];
var mode = Number(ezfc_functions.get_value_from(2796, true)[0]) || 1;

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
