// Форма 28 CalcLaser, элемент cjsCalc (992). Id полей — боевой формы 28.
var qty = {{numN}};
var width = Number(String({{numW}}).replace(',', '.'));
var height = Number(String({{numH}}).replace(',', '.'));
var materialRaw = ezfc_functions.get_value_from(989, true);
var materialId = Array.isArray(materialRaw) ? materialRaw[0] : materialRaw;
if (materialId == null) {
    materialId = '';
}
var materialIndex = ezfc_functions.get_value_from(989, true, false, { return_value: 'index' })[0];
var materialModeRaw = ezfc_functions.get_value_from(1027, true);
var materialMode = Array.isArray(materialModeRaw) ? materialModeRaw[0] : materialModeRaw;
if (materialMode == null || materialMode === '') {
    materialMode = 'isMaterial';
}
var materialModeIndex = ezfc_functions.get_value_from(1027, true, false, { return_value: 'index' })[0];
var cutRaw = ezfc_functions.get_value_from(985, true);
var cut = Array.isArray(cutRaw) ? cutRaw[0] : cutRaw;
var cutIndex = ezfc_functions.get_value_from(985, true, false, { return_value: 'index' })[0];
var sizeItem = Number(String({{numSizeItem}}).replace(',', '.')) || 0;
var density = Number(String({{numDensity}}).replace(',', '.')) || 0;
var lenRaw = ezfc_functions.get_value_from(1013, false);
var lenCut = Number(Array.isArray(lenRaw) ? lenRaw[0] : lenRaw);
if (isNaN(lenCut)) {
    lenCut = 0;
}
var isFindMark = ezfc_functions.get_value_from(988, false) == 1;
var isAdhesive = ezfc_functions.get_value_from(2630, false) == 1;
var graveRaw = ezfc_functions.get_value_from(1015, true);
var grave = Array.isArray(graveRaw) ? graveRaw[0] : graveRaw;
var graveIndex = ezfc_functions.get_value_from(1015, true, false, { return_value: 'index' })[0];
var graveResRaw = ezfc_functions.get_value_from(1025, true);
var graveRes = Array.isArray(graveResRaw) ? graveResRaw[0] : graveResRaw;
var graveResIndex = ezfc_functions.get_value_from(1025, true, false, { return_value: 'index' })[0];
var graveW = Number(String({{numGraveW}}).replace(',', '.')) || 0;
var graveH = Number(String({{numGraveH}}).replace(',', '.')) || 0;
var graveThick = Number(String({{numThinknessContur}}).replace(',', '.')) || 0;
var graveLen = Number(String({{numLenContur}}).replace(',', '.')) || 0;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(1006, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    rdoMaterial: materialModeIndex,
    dpdDifficulty: cutIndex,
    numSizeItem: sizeItem,
    numDensity: density,
    numLenCut: lenCut,
    chkMark: isFindMark ? 0 : '',
    chkAdhesiveLayer: isAdhesive ? 0 : '',
    dpdGrave: graveIndex,
    dpdGraveResolution: graveResIndex,
    numGraveW: graveW,
    numGraveH: graveH,
    numThinknessContur: graveThick,
    numLenContur: graveLen,
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    material_id: materialId,
    material_mode: String(materialMode),
    mode: mode
};
// «без резки» — ключ is_cut_laser не отправляем. Пустой {} в API включил бы резку.
if (String(cut) !== 'noCut') {
    var difficultyNum = Number(cut);
    if (String(cut) === 'isLenCut') {
        params.is_cut_laser = {
            size_item: sizeItem,
            density: density,
            difficulty: 1,
            len_cut: lenCut
        };
    } else {
        params.is_cut_laser = {
            size_item: sizeItem,
            density: density,
            difficulty: isNaN(difficultyNum) ? 1 : difficultyNum,
            len_cut: 0
        };
    }
    params.is_find_mark = isFindMark;
}
if (String(grave) !== 'noGrave' && grave != null && grave !== '') {
    var graveResNum = Number(graveRes);
    params.is_grave = isNaN(graveResNum) ? 1 : graveResNum;
    if (String(grave) === 'isGraveFill') {
        params.is_grave_fill = [graveW, graveH];
    }
    if (String(grave) === 'isGraveContur') {
        params.is_grave_contur = [graveThick, graveLen];
    }
}
if (isAdhesive) {
    params.is_adhesive_layer = 'AdhesiveLayer50';
}

insaincalc.calcApi('laser', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
