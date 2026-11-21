// Форма 30 CalcPolySticker, элемент cjsCalc (1081). Id полей — боевой формы 30.
// Боевой cjsCalc кладёт в isPrint строку принтера, а calcSticker читает .printerID.
// Печать в цену не входит: color и printer_code в calcApi не отправляем.
// Принтер не No включает метки резки. Ламинация зашита в форме, поля нет:
// KMBizhubC220 → Laminat32G, Technojet160ECO → LaminatDLCLAM, латекс без плёнки.
// fluAtrwork — файл макета: в URL и в calcApi не уходит.
var qty = {{numN}};
var width = Number({{numW}});
var height = Number({{numH}});
var materialId = ezfc_functions.get_value_from(1076, true)[0];
var materialIndex = ezfc_functions.get_value_from(1076, true, false, { return_value: 'index' })[0];
var difficultyRaw = ezfc_functions.get_value_from(1072, true)[0];
var difficultyIndex = ezfc_functions.get_value_from(1072, true, false, { return_value: 'index' })[0];
var difficultyNum = Number(difficultyRaw);
var difficulty = (difficultyRaw === '' || difficultyRaw == null || isNaN(difficultyNum)) ? 1 : difficultyNum;
var printerId = ezfc_functions.get_value_from(1077, true)[0];
var printerIndex = ezfc_functions.get_value_from(1077, true, false, { return_value: 'index' })[0];
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2415, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    dpdDifficulty: difficultyIndex,
    dpdPrint: printerIndex,
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    difficulty: difficulty,
    material_id: materialId,
    mode: mode
};
if (printerId && String(printerId) !== 'No') {
    params.is_find_mark = true;
    if (printerId === 'KMBizhubC220') {
        params.lamination_id = 'Laminat32G';
    } else if (printerId === 'Technojet160ECO') {
        params.lamination_id = 'LaminatDLCLAM';
    }
}

insaincalc.calcApi('poly_sticker', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
