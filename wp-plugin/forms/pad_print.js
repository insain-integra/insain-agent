// Форма 38 CalcPadPrint, элемент cjsCalc (1448). Id полей — боевой формы 38.
var qty = {{numN}};
var sizeItem = ezfc_functions.get_value_from(1434, true)[0] || 'isSmallItems';
var presetIndex = ezfc_functions.get_value_from(1434, true, false, { return_value: 'index' })[0];
var colorRaw = ezfc_functions.get_value_from(1435, true)[0];
var color = Number(colorRaw) || 1;
var colorIndex = ezfc_functions.get_value_from(1435, true, false, { return_value: 'index' })[0];
// Материал поверхности не используется в calcPadPrint.js и API, сохраняется только в URL.
var surfaceIndex = ezfc_functions.get_value_from(1442, true, false, { return_value: 'index' })[0];

// Чекбокс: get_value_from → [true]/0/'true'; без [0], как в старом CalcPadPrint cjsCalc.
var isPantone = ezfc_functions.get_value_from(1444, true) == 'true';
var isMaterialCustomer = ezfc_functions.get_value_from(1445, true) == 'true';
var isPacking = ezfc_functions.get_value_from(1446, true) == 'true';

// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(1462, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdPreset: presetIndex,
    dpdColor: colorIndex,
    dpdSurfaceMaterial: surfaceIndex,
    // Чекбокс: GET_check=index; включён → индекс единственной опции 0; выключен → '' (удалить).
    ckbPantone: isPantone ? 0 : '',
    ckbMaterialCustomer: isMaterialCustomer ? 0 : '',
    ckbPacking: isPacking ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('pad_print', {
    quantity: Number(qty) || 1,
    size_item: sizeItem,
    color: color,
    is_pantone: isPantone,
    is_packing: isPacking,
    material_mode: isMaterialCustomer ? 'isMaterialCustomer' : 'isMaterial',
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
