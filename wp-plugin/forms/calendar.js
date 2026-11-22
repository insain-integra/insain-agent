// Форма 50 CalcCalendarQuarterly, элемент cjsCalc (2069). Id полей — боевой формы 50.
// Материал и цветность в форме не выбираются: PaperCoated300M и 4+0, как в боевом cjsCalc.
var qty = {{numN}};
var sizeId = ezfc_functions.get_value_from(2050, true)[0];
var sizeIndex = ezfc_functions.get_value_from(2050, true, false, { return_value: 'index' })[0];
var fieldId = ezfc_functions.get_value_from(2055, true)[0];
var fieldIndex = ezfc_functions.get_value_from(2055, true, false, { return_value: 'index' })[0];
var blockSuffix = ezfc_functions.get_value_from(2056, true)[0];
var blockIndex = ezfc_functions.get_value_from(2056, true, false, { return_value: 'index' })[0];
var laminatId = ezfc_functions.get_value_from(2057, true)[0];
var laminatIndex = ezfc_functions.get_value_from(2057, true, false, { return_value: 'index' })[0];
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
// На форме 50 в радио только 1 и 2.
var modeRaw = ezfc_functions.get_value_from(2082, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

var calendarId = 'Quarterly' + String(sizeId == null ? '' : sizeId) + String(fieldId == null ? '' : fieldId);
var blockId = String(sizeId == null ? '' : sizeId) + String(blockSuffix == null ? '' : blockSuffix);

insaincalc.syncUrl({
    numN: qty,
    dpdSize: sizeIndex,
    dpdField: fieldIndex,
    dpdBlock: blockIndex,
    dpdCoverLaminat: laminatIndex,
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    calendar_type: 'quarterly',
    calendar_id: calendarId,
    block_id: blockId,
    top_material_id: 'PaperCoated300M',
    top_color: '4+0',
    bottom_material_id: 'PaperCoated300M',
    bottom_color: '4+0',
    mode: mode
};
if (laminatId) {
    params.top_lamination_id = laminatId;
    params.bottom_lamination_id = laminatId;
}

insaincalc.calcApi('calendar', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
