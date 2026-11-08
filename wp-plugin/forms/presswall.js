// Форма 46 CalcPresswall, элемент cjsCalc (1862). Id полей — боевой формы 46.
var qty = {{numN}};
var presswallId = ezfc_functions.get_value_from(1844, true)[0];
var presswallIndex = ezfc_functions.get_value_from(1844, true, false, { return_value: 'index' })[0];
var attachmentId = ezfc_functions.get_value_from(1845, true)[0];
var attachmentIndex = ezfc_functions.get_value_from(1845, true, false, { return_value: 'index' })[0];
var materialId = ezfc_functions.get_value_from(1879, true)[0];
var materialIndex = ezfc_functions.get_value_from(1879, true, false, { return_value: 'index' })[0];
var bagId = ezfc_functions.get_value_from(1880, true)[0];
var bagIndex = ezfc_functions.get_value_from(1880, true, false, { return_value: 'index' })[0];
var presswallMode = ezfc_functions.get_value_from(1883, true)[0];
var presswallModeIndex = ezfc_functions.get_value_from(1883, true, false, { return_value: 'index' })[0];
var numDays = {{numDays}};
var modeRaw = ezfc_functions.get_value_from(1875, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdPresswall: presswallIndex,
    dpdAttachment: attachmentIndex,
    dpdBanner: materialIndex,
    dpdBag: bagIndex,
    rdoPresswal: presswallModeIndex,
    numDays: numDays,
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    presswall_id: presswallId,
    material_id: materialId || '',
    is_presswall: presswallMode === 'isPresswall',
    is_rent: presswallMode === 'isRent' ? (Number(numDays) || 0) : 0,
    mode: mode
};
if (attachmentId === 'isEyelet') {
    params.is_eyelet = [300, 300, 300, 300];
}
if (attachmentId === 'isPocket') {
    params.is_pocket = [1, 0, 1, 0];
    params.is_cutting = [0, 1, 0, 1];
}
if (bagId) {
    params.is_bag = bagId;
}

insaincalc.calcApi('presswall', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
