// Форма 55 CalcFlagPaper, элемент cjsCalc (2265). Id полей — боевой формы 55.
var qty = {{numN}};
// Значение dpdSize — «ширина, высота» в мм, например «200,99».
// В значении запятая («200,99»): как в боевом cjsCalc, toString() и разрез по запятой.
var sizeRaw = ezfc_functions.get_value_from(2258, true);
var sizeIndex = ezfc_functions.get_value_from(2258, true, false, { return_value: 'index' })[0];
var sizeParts = String(sizeRaw == null ? '' : sizeRaw).split(',');
var width = parseInt(sizeParts[0], 10);
var height = parseInt(sizeParts.length > 1 ? sizeParts[1] : '', 10);
var color = ezfc_functions.get_value_from(2282, true)[0];
var colorIndex = ezfc_functions.get_value_from(2282, true, false, { return_value: 'index' })[0];
var materialId = ezfc_functions.get_value_from(2263, true)[0];
var materialIndex = ezfc_functions.get_value_from(2263, true, false, { return_value: 'index' })[0];
var laminatId = ezfc_functions.get_value_from(2264, true)[0];
var laminatIndex = ezfc_functions.get_value_from(2264, true, false, { return_value: 'index' })[0];
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2278, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdSize: sizeIndex,
    dpdColor: colorIndex,
    dpdMaterial: materialIndex,
    dpdCoverLaminat: laminatIndex,
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width_mm: width,
    height_mm: height,
    material_id: materialId,
    color: color,
    mode: mode
};
if (laminatId) {
    params.lamination_id = laminatId;
}

insaincalc.calcApi('flag', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
