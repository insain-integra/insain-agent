// Форма 36 CalcTabs, элемент cjsCalc (1348). Id полей — боевой формы 36.
// Ветки без порта в tablets.py (isCutMilling, isFilm, isShaft, chkAdhesiveLayer)
// пишутся в syncUrl, но в calcApi не передаются.
// Не-API поля (dpdTypeCut, параметры плёнки для аппликации/фона/древка) сохраняются в URL.
var qty = {{numN}};
var width = Number(String({{numW}}).replace(',', '.')) || 0;
var height = Number(String({{numH}}).replace(',', '.')) || 0;
var materialId = ezfc_functions.get_value_from(1339, true)[0] || '';
var materialIndex = optionIndex(ezfc_functions.get_value_from(1339, true, false, { return_value: 'index' }));
var materialMode = ezfc_functions.get_value_from(1340, true)[0] || 'isMaterial';
var materialModeIndex = optionIndex(ezfc_functions.get_value_from(1340, true, false, { return_value: 'index' }));
var typeCutIndex = optionIndex(ezfc_functions.get_value_from(1375, true, false, { return_value: 'index' }));
var cutId = ezfc_functions.get_value_from(1371, true)[0] || '';
var cutIndex = optionIndex(ezfc_functions.get_value_from(1371, true, false, { return_value: 'index' }));
var difficultyRaw = ezfc_functions.get_value_from(1342, true)[0];
var difficultyIndex = optionIndex(ezfc_functions.get_value_from(1342, true, false, { return_value: 'index' }));
var lenCut = numFrom(ezfc_functions.get_value_from(1468, false));
var applicationId = ezfc_functions.get_value_from(1368, true)[0] || '';
var applicationIndex = optionIndex(ezfc_functions.get_value_from(1368, true, false, { return_value: 'index' }));
var isDoubleApplication = ezfc_functions.get_value_from(3313, false) == 1;
var color = ezfc_functions.get_value_from(1378, true)[0] || '4+0';
var colorIndex = optionIndex(ezfc_functions.get_value_from(1378, true, false, { return_value: 'index' }));
var resolutionRaw = ezfc_functions.get_value_from(2770, true)[0];
var resolutionIndex = optionIndex(ezfc_functions.get_value_from(2770, true, false, { return_value: 'index' }));
var laminatId = ezfc_functions.get_value_from(1429, true)[0] || 'No';
var laminatIndex = optionIndex(ezfc_functions.get_value_from(1429, true, false, { return_value: 'index' }));
var edgeId = ezfc_functions.get_value_from(1477, true)[0] || 'isCutEdge';
var edgeIndex = optionIndex(ezfc_functions.get_value_from(1477, true, false, { return_value: 'index' }));
var appMaterialIndex = optionIndex(ezfc_functions.get_value_from(1484, true, false, { return_value: 'index' }));
var appW = numFrom(ezfc_functions.get_value_from(1419, true));
var appH = numFrom(ezfc_functions.get_value_from(1420, true));
var appColors = numFrom(ezfc_functions.get_value_from(1430, false)) || 1;
var appSizeItem = numFrom(ezfc_functions.get_value_from(1424, false));
var appDensityRaw = ezfc_functions.get_value_from(1425, true, true);
var appDensity = Number(String(appDensityRaw == null ? '' : appDensityRaw).replace('%', '').replace(',', '.'));
if (isNaN(appDensity)) appDensity = 0;
var appDifficultyIndex = optionIndex(ezfc_functions.get_value_from(1423, true, false, { return_value: 'index' }));
var bgMaterialIndex = optionIndex(ezfc_functions.get_value_from(1427, true, false, { return_value: 'index' }));
var bgEdgeIndex = optionIndex(ezfc_functions.get_value_from(1483, true, false, { return_value: 'index' }));
var hasShaft = ezfc_functions.get_value_from(1533, true) == 'true';
var shaftLen = numFrom(ezfc_functions.get_value_from(1534, true)) || 1;
var hasAdhesiveLayer = ezfc_functions.get_value_from(2718, false) == 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2003, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

function optionIndex(raw) {
    if (raw == null || typeof raw !== 'object' || raw[0] == null || raw[0] === '') {
        return '';
    }
    return raw[0];
}

function numFrom(raw) {
    var val = Array.isArray(raw) ? raw[0] : raw;
    var n = Number(String(val == null ? '' : val).replace(',', '.'));
    return isNaN(n) ? 0 : n;
}

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    rdoMaterial: materialModeIndex,
    dpdTypeCut: typeCutIndex,
    dpdCut: cutIndex,
    dpdDifficulty: difficultyIndex,
    numLenCut: lenCut,
    dpdApplication: applicationIndex,
    ckbDoubleApplication: isDoubleApplication ? 0 : '',
    dpdColor: colorIndex,
    dpdResolution: resolutionIndex,
    dpdRollWideLaminat: laminatIndex,
    dpdEdge: edgeIndex,
    dpdApplicationMaterial: appMaterialIndex,
    numApplicationW: appW,
    numApplicationH: appH,
    numFilm: appColors,
    numSizeItem: appSizeItem,
    numDensity: appDensity,
    dpdFilmDifficulty: appDifficultyIndex,
    dpdBackgroudMaterial: bgMaterialIndex,
    dpdBackroundEdge: bgEdgeIndex,
    ckbShaft: hasShaft ? 0 : '',
    numLengthShaft: shaftLen,
    chkAdhesiveLayer: hasAdhesiveLayer ? 0 : '',
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

if (String(cutId) === 'isCutManual') {
    params.is_cut_manual = 'KeencutEvolutionE2';
} else if (String(cutId) === 'isCutManualMetal') {
    params.is_cut_manual_metal = 'AccusheadPro12';
} else if (String(cutId) === 'isCutLaser') {
    var sizeItem = Math.min(width, height);
    var difficultyNum = Number(difficultyRaw);
    if (String(difficultyRaw) === 'isLenCut') {
        params.is_cut_laser = {
            size_item: sizeItem,
            density: 0,
            difficulty: 1,
            len_cut: lenCut
        };
    } else {
        params.is_cut_laser = {
            size_item: sizeItem,
            density: 0,
            difficulty: isNaN(difficultyNum) ? 1 : difficultyNum,
            len_cut: 0
        };
    }
}

if (String(applicationId) === 'isUVPrint') {
    var resNum = Number(resolutionRaw);
    params.is_uv_print = {
        printer_id: 'PrintUV',
        resolution: isNaN(resNum) ? 1 : resNum,
        surface: 'plain',
        color: String(color || '4+0'),
        double_application: isDoubleApplication
    };
} else if (String(applicationId) === 'isECOPrint') {
    params.is_print = {
        printer_id: 'Technojet160ECO',
        double_application: isDoubleApplication,
        is_edge: String(edgeId || 'isCutEdge'),
        is_lamination: Boolean(laminatId && String(laminatId) !== 'No')
    };
} else if (String(applicationId) === 'isLatexPrint') {
    params.is_print = {
        printer_id: 'HPLatex335',
        double_application: isDoubleApplication,
        is_edge: String(edgeId || 'isCutEdge'),
        is_lamination: false
    };
} else if (String(applicationId) === 'isSublimation') {
    params.is_sublimation = true;
}

insaincalc.calcApi('tablets', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
