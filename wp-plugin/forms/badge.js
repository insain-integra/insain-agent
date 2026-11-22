// Форма 64 CalcBadge, элемент cjsCalc (2613). Id полей — боевой формы 64.
// Поля chkPocket, chkGrave, numGraveW, numGraveH, chkEpoxy и опция AdhesiveLayer50
// пишутся в syncUrl, но в calcApi не уходят (в API badge эти ветки не портированы).
var qty = {{numN}};
var width = Number(String({{numW}}).replace(',', '.')) || 0;
var height = Number(String({{numH}}).replace(',', '.')) || 0;
var materialId = ezfc_functions.get_value_from(2598, true)[0];
var materialIndex = optionIndex(ezfc_functions.get_value_from(2598, true, false, { return_value: 'index' }));
var difficultyRaw = ezfc_functions.get_value_from(2599, true)[0];
var difficultyIndex = optionIndex(ezfc_functions.get_value_from(2599, true, false, { return_value: 'index' }));
var difficulty = Number(difficultyRaw) || 1;
var hasPocket = ezfc_functions.get_value_from(2600, true) == 'Pocket';
var isGrave = ezfc_functions.get_value_from(2603, true) == 'isGrave';
var graveW = {{numGraveW}};
var graveH = {{numGraveH}};
var isUvPrint = ezfc_functions.get_value_from(2607, true) == 'isUVPrint';
var color = ezfc_functions.get_value_from(2608, true)[0] || '4+0';
var colorIndex = optionIndex(ezfc_functions.get_value_from(2608, true, false, { return_value: 'index' }));
var isEpoxy = ezfc_functions.get_value_from(2609, true) == 'isEpoxy';
var attachmentId = ezfc_functions.get_value_from(2610, true)[0];
var attachmentIndex = optionIndex(ezfc_functions.get_value_from(2610, true, false, { return_value: 'index' }));
var isPacking = ezfc_functions.get_value_from(2611, true) == 'isPacking';
// 0 — «cтандарт». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2626, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

function optionIndex(raw) {
    if (raw == null || typeof raw !== 'object' || raw[0] == null || raw[0] === '') {
        return '';
    }
    return raw[0];
}

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    dpdDifficulty: difficultyIndex,
    chkPocket: hasPocket ? 0 : '',
    chkGrave: isGrave ? 0 : '',
    numGraveW: graveW,
    numGraveH: graveH,
    chkUVPrint: isUvPrint ? 0 : '',
    dpdColor: colorIndex,
    chkEpoxy: isEpoxy ? 0 : '',
    dpdAttachment: attachmentIndex,
    chkPacking: isPacking ? 0 : '',
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    difficulty: difficulty,
    material_id: materialId,
    is_print: false,
    is_uv_print: isUvPrint,
    color: color,
    is_packing: isPacking,
    mode: mode
};
if (attachmentId && attachmentId !== 'No' && attachmentId !== 'AdhesiveLayer50') {
    params.attachment_id = attachmentId;
}

insaincalc.calcApi('badge', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
