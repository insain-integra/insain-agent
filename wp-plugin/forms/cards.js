// Форма 56 CalcPlasticCards, элемент cjsCalc (2298). Id полей — боевой формы 56.
// dpdColor и ckbVariables пишутся в syncUrl и в calcApi не уходят:
// цветность и «переменные данные» calcPlasticCards не считает.
// is_embossing в API есть, поля на форме нет — не отправляем.
function first(raw) {
    if (raw == null || raw === '') {
        return '';
    }
    if (typeof raw === 'object') {
        return raw[0] == null ? '' : raw[0];
    }
    return raw;
}

function optionIndex(raw) {
    if (raw == null || typeof raw !== 'object' || raw[0] == null || raw[0] === '') {
        return '';
    }
    return raw[0];
}

function isChecked(raw) {
    return String(first(raw)) === 'true';
}

var qty = {{numN}};
var materialId = first(ezfc_functions.get_value_from(2289, true));
var materialIndex = optionIndex(ezfc_functions.get_value_from(2289, true, false, { return_value: 'index' }));
var colorIndex = optionIndex(ezfc_functions.get_value_from(2288, true, false, { return_value: 'index' }));
var laminatId = first(ezfc_functions.get_value_from(2290, true));
var laminatIndex = optionIndex(ezfc_functions.get_value_from(2290, true, false, { return_value: 'index' }));
var isNumber = isChecked(ezfc_functions.get_value_from(2292, true));
var isBarcode = isChecked(ezfc_functions.get_value_from(2293, true));
var isVariables = isChecked(ezfc_functions.get_value_from(2294, true));
var isEmbossingFoil = isChecked(ezfc_functions.get_value_from(2295, true));
var isMagneticStripe = isChecked(ezfc_functions.get_value_from(2296, true));
var isSignatureStrip = isChecked(ezfc_functions.get_value_from(2315, true));
var isScratchPanel = isChecked(ezfc_functions.get_value_from(2316, true));
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = first(ezfc_functions.get_value_from(2311, true));
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdMaterial: materialIndex,
    dpdColor: colorIndex,
    dpdLaminat: laminatIndex,
    ckbNumber: isNumber ? 0 : '',
    ckbBarcode: isBarcode ? 0 : '',
    ckbVariables: isVariables ? 0 : '',
    ckbEmbossingFoil: isEmbossingFoil ? 0 : '',
    ckbMagneticStripeHiCo: isMagneticStripe ? 0 : '',
    ckbSignatureStrip: isSignatureStrip ? 0 : '',
    ckbScratchPanel: isScratchPanel ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('cards', {
    quantity: Number(qty) || 1,
    material_id: materialId,
    lamination: laminatId || '',
    is_number: isNumber,
    is_barcode: isBarcode,
    is_embossing_foil: isEmbossingFoil,
    is_magnetic_stripe: isMagneticStripe,
    is_signature_strip: isSignatureStrip,
    is_scratch_panel: isScratchPanel,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
