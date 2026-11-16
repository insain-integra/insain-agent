// Форма 82 CalcPrintPromo, элемент cjsCalc (3208). Id полей — боевой формы 82.
// Размер и цветность сборного тиража берутся из кода материала, в API не уходят.
var qty = {{numN}};
var materialId = ezfc_functions.get_value_from(3189, true)[0];
var formatIndex = ezfc_functions.get_value_from(3189, true, false, { return_value: 'index' })[0];
// «стандарт» — data-value 1, «быстрее» — 2. HTML value у «стандарт» равен 0;
// боевой расчёт читает data-value. Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(3221, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdFormat: formatIndex,
    rdoModeProduction: mode
});

insaincalc.calcApi('print_offset', {
    num_sheet: Number(qty) || 1,
    material_id: materialId,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
