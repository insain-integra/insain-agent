// Форма 56 CalcPlasticCards, элемент cjsCalc (2298). Id полей — боевой формы 56.
// dpdColor и ckbVariables пишутся в syncUrl и в calcApi не уходят:
// цветность и «переменные данные» calcPlasticCards не считает.
// is_embossing в API есть, поля на форме нет — не отправляем.
// Пустой radio при включённом GET не получает checked. Если режим подставлен
// из этого пустого значения, отмечаем пункт «стандарт» через getElementById.
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
// У формы 56 в радио только data-value 1 и 2. Невыбранный пункт отдаёт число 0
// (или строку "0"), не массив и не ''. first(0) не пустой, поэтому скаляр 0 —
// «ничего не выбрано», не режим «дешевле»: mode 1, как дефолт calcPlasticCards.
// Выбранное значение приходит массивом и сохраняется, в том числе [0]. Через || не схлопываем.
var modeListed = ezfc_functions.get_value_from(2311, true);
var modeRaw = first(modeListed);
var modeNum = Number(modeRaw);
var modeUnset = typeof modeListed !== 'object' && modeNum === 0;
var mode = (modeUnset || modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;
// «стандарт» — первый пункт радио, индекс 0, data-value 1.
// Id по имени: запись копии меняет только get_value_from, литерал 2311 на копии пустой.
// Выбранный массив ([1], [2], [0]) сюда не попадает. change не шлём: расчёт уже mode 1.
if (modeUnset && typeof document !== 'undefined' && typeof ezfc_functions.get_element_id_by_name === 'function') {
    var modeElId = ezfc_functions.get_element_id_by_name(__form_id__, 'rdoModeProduction');
    var modeInput = modeElId ? document.getElementById('ezfc_element-' + modeElId + '-0') : null;
    if (modeInput) {
        modeInput.checked = true;
    }
}

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
