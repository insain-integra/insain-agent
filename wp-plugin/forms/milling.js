// Форма 35 CalcMilling, элемент cjsCalc (1314). Id полей — боевой формы 35.
var qty = {{numN}};
var width = Number(String({{numW}}).replace(',', '.'));
var height = Number(String({{numH}}).replace(',', '.'));
var materialRaw = ezfc_functions.get_value_from(1298, true);
var materialId = Array.isArray(materialRaw) ? materialRaw[0] : materialRaw;
if (materialId == null) {
    materialId = '';
}
var materialIndex = ezfc_functions.get_value_from(1298, true, false, { return_value: 'index' })[0];
var materialModeRaw = ezfc_functions.get_value_from(1299, true);
var materialMode = Array.isArray(materialModeRaw) ? materialModeRaw[0] : materialModeRaw;
if (materialMode == null || materialMode === '') {
    materialMode = 'isMaterial';
}
var materialModeIndex = ezfc_functions.get_value_from(1299, true, false, { return_value: 'index' })[0];
var cutRaw = ezfc_functions.get_value_from(1301, true);
var cut = Array.isArray(cutRaw) ? cutRaw[0] : cutRaw;
var cutIndex = ezfc_functions.get_value_from(1301, true, false, { return_value: 'index' })[0];
var sizeItem = Number(String({{numSizeItem}}).replace(',', '.')) || 0;
var density = Number(String({{numDensity}}).replace(',', '.')) || 0;
var lenRaw = ezfc_functions.get_value_from(1305, false);
var lenCut = Number(Array.isArray(lenRaw) ? lenRaw[0] : lenRaw);
if (isNaN(lenCut)) {
    lenCut = 0;
}
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(1328, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    rdoMaterial: materialModeIndex,
    dpdDifficulty: cutIndex,
    numSizeItem: String(cut) === '1.7' ? sizeItem : '',
    numDensity: String(cut) === '1.7' ? Math.round(density * 10000) / 100 : '',
    numLenCut: String(cut) === 'isLenCut' ? lenCut : '',
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    material_id: String(materialId),
    material_mode: String(materialMode),
    mode: mode
};
// «без резки» — ключ is_cut_milling не отправляем.
if (String(cut) !== 'noCut') {
    var difficultyNum = Number(cut);
    if (String(cut) === 'isLenCut') {
        params.is_cut_milling = {
            size_item: sizeItem,
            density: density,
            difficulty: 1,
            len_cut: lenCut
        };
    } else {
        params.is_cut_milling = {
            size_item: sizeItem,
            density: density,
            difficulty: isNaN(difficultyNum) ? 1 : difficultyNum,
            len_cut: 0
        };
    }
}

insaincalc.calcApi('milling', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
