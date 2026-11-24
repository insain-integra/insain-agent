// Форма 54 CalcMagnetLamination, элемент cjsCalc (2234). Id полей — боевой формы 54.
// ckbNumber, ckbBarcode и ckbVariables пишутся в syncUrl и в calcApi не уходят:
// на дефолте галочки сняты, в калькуляторе эти опции не считаются.
// Пустой код ламинации («нет») в запрос не кладём.
// Скругление при прямоугольной форме уходит как shape rectangular_rounded.
// На форме нет режима «дешевле» (value 0); ноль всё равно не подменяем на 1.
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
var width = {{numW}};
var height = {{numH}};
var shape = first(ezfc_functions.get_value_from(2223, true));
var shapeIndex = optionIndex(ezfc_functions.get_value_from(2223, true, false, { return_value: 'index' }));
var difficultyRaw = first(ezfc_functions.get_value_from(2355, true));
var difficultyIndex = optionIndex(ezfc_functions.get_value_from(2355, true, false, { return_value: 'index' }));
var difficultyNum = Number(difficultyRaw);
var difficulty = (difficultyRaw === '' || difficultyRaw == null || isNaN(difficultyNum)) ? 1 : difficultyNum;
var materialId = first(ezfc_functions.get_value_from(2225, true));
var materialIndex = optionIndex(ezfc_functions.get_value_from(2225, true, false, { return_value: 'index' }));
var laminatId = first(ezfc_functions.get_value_from(2226, true));
var laminatIndex = optionIndex(ezfc_functions.get_value_from(2226, true, false, { return_value: 'index' }));
var isNumber = isChecked(ezfc_functions.get_value_from(2228, true));
var isBarcode = isChecked(ezfc_functions.get_value_from(2229, true));
var isVariables = isChecked(ezfc_functions.get_value_from(2230, true));
var isRounding = isChecked(ezfc_functions.get_value_from(2231, true));
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = first(ezfc_functions.get_value_from(2247, true));
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

var apiShape = shape || 'rectangular';
if (isRounding && apiShape === 'rectangular') {
    apiShape = 'rectangular_rounded';
}

var params = {
    quantity: Number(qty) || 1,
    magnet_id: materialId,
    width_mm: Number(width) || 1,
    height_mm: Number(height) || 1,
    shape: apiShape,
    difficulty: difficulty,
    is_packing: false,
    mode: mode
};
if (laminatId) {
    params.lamination_id = laminatId;
}

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdShape: shapeIndex,
    dpdDifficulty: difficultyIndex,
    dpdMaterial: materialIndex,
    dpdLaminat: laminatIndex,
    ckbNumber: isNumber ? 0 : '',
    ckbBarcode: isBarcode ? 0 : '',
    ckbVariables: isVariables ? 0 : '',
    ckbRounding: isRounding ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('magnet_laminated', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
