// Форма 26 CalcUVPrint, элемент cjsCalc (910). Id полей — боевой формы 26.
var qty = {{numN}};
var width = {{numW}};
var height = {{numH}};
var itemWidth = {{numItemW}};
var itemHeight = {{numItemH}};
var color = ezfc_functions.get_value_from(895, true)[0];
var colorIndex = ezfc_functions.get_value_from(895, true, false, { return_value: 'index' })[0];
var resolution = Number(ezfc_functions.get_value_from(934, true)[0]) || 0;
var resolutionIndex = ezfc_functions.get_value_from(934, true, false, { return_value: 'index' })[0];
var surfaceRaw = ezfc_functions.get_value_from(891, true)[0];
var surfaceIndex = ezfc_functions.get_value_from(891, true, false, { return_value: 'index' })[0];
var materialIndex = ezfc_functions.get_value_from(896, true, false, { return_value: 'index' })[0];
var presetRaw = ezfc_functions.get_value_from(933, true)[0];
var presetIndex = ezfc_functions.get_value_from(933, true, false, { return_value: 'index' })[0];
var mode = Number(ezfc_functions.get_value_from(2866, true)[0]) || 1;
// Чекбокс: get_value_from → [true]/0/'true'; без [0], как в старом calcUVPrint cjsCalc
var isNumber = ezfc_functions.get_value_from(901, true) == 'true';
var isBarcode = ezfc_functions.get_value_from(902, true) == 'true';
var isVariables = ezfc_functions.get_value_from(903, true) == 'true';
var isCustomerMaterial = ezfc_functions.get_value_from(3009, true) == 'true';

var presetParts = String(presetRaw == null ? '0' : presetRaw).split(',');
if (presetRaw && String(presetRaw) !== '0' && presetParts.length >= 5) {
    width = parseInt(presetParts[0], 10);
    height = parseInt(presetParts[1], 10);
    itemWidth = parseInt(presetParts[2], 10);
    itemHeight = parseInt(presetParts[3], 10);
    resolution = Number(presetParts[4]) || 0;
    surfaceRaw = 'isPlain';
}

var surface = (surfaceRaw === 'isAround' || surfaceRaw === 'round') ? 'round' : 'plain';

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    numItemW: itemWidth,
    numItemH: itemHeight,
    dpdColor: colorIndex,
    dpdResolution: resolutionIndex,
    dpdSurfacePrint: surfaceIndex,
    dpdSurfaceMaterial: materialIndex,
    dpdPreset: presetIndex,
    rdoModeProduction: mode,
    ckbNumber: isNumber ? 1 : 0,
    ckbBarcode: isBarcode ? 1 : 0,
    ckbVariables: isVariables ? 1 : 0,
    ckbMaterialCustomer: isCustomerMaterial ? 1 : 0
});

insaincalc.calcApi('uv_print', {
    quantity: Number(qty) || 1,
    width: Number(width) || 1,
    height: Number(height) || 1,
    item_width: Number(itemWidth) || Number(width) || 1,
    item_height: Number(itemHeight) || Number(height) || 1,
    resolution: resolution,
    color: color,
    surface: surface,
    mode: mode,
    is_number: isNumber,
    is_barcode: isBarcode,
    is_variables: isVariables,
    is_customer_material: isCustomerMaterial
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
