// Форма 85 CalcEmbossing, элемент cjsCalc (3294). Id полей — боевой формы 85.
var qty = {{numN}};
var clicheW = {{numW}};
var clicheH = {{numH}};
var itemW = {{numItemW}};
var itemH = {{numItemH}};
var embossingId = ezfc_functions.get_value_from(3280, true)[0];
var embossingIndex = ezfc_functions.get_value_from(3280, true, false, { return_value: 'index' })[0];
var itemRaw = ezfc_functions.get_value_from(3279, true)[0];
var itemIndex = ezfc_functions.get_value_from(3279, true, false, { return_value: 'index' })[0];
// data-value «0» у «Другое» → API item_type other
var itemType = (!itemRaw || itemRaw === '0') ? 'other' : itemRaw;
var surfaceIndex = ezfc_functions.get_value_from(3287, true, false, { return_value: 'index' })[0];
// 0 — «дешевле» (на форме 85 опций 0 нет). Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(3307, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;
// Чекбокс: get_value_from → [true]/0/'true'; без [0], как в старом CalcEmbossing cjsCalc
var isCliche = ezfc_functions.get_value_from(3291, true) == 'true';
var isPacking = ezfc_functions.get_value_from(3292, true) == 'true';
var isCustomerMaterial = ezfc_functions.get_value_from(3311, true) == 'true';

insaincalc.syncUrl({
    numN: qty,
    numW: clicheW,
    numH: clicheH,
    numItemW: itemW,
    numItemH: itemH,
    dpdEmbossing: embossingIndex,
    dpdPreset: itemIndex,
    dpdSurfaceMaterial: surfaceIndex,
    // Чекбокс: GET_check=index; включён → индекс единственной опции 0; выключен → '' (удалить).
    ckbCliche: isCliche ? 0 : '',
    ckbPacking: isPacking ? 0 : '',
    ckbMaterialCustomer: isCustomerMaterial ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('embossing', {
    quantity: Number(qty) || 1,
    cliche_width_mm: Number(clicheW) || 1,
    cliche_height_mm: Number(clicheH) || 1,
    embossing_type: embossingId,
    item_type: itemType,
    is_cliche: isCliche,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
