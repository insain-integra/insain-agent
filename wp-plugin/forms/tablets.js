// Форма 36 CalcTabs, элемент cjsCalc (1348). Id полей — боевой формы 36.
// Ветки без порта в tablets.py (isCutMilling, isShaft, chkAdhesiveLayer)
// пишутся в syncUrl, но в calcApi не передаются.
// Не-API поля (dpdTypeCut, древко, клеевой слой) сохраняются в URL.
// Форма 48 CalcStands — второй набор в этом же файле (1924, 1925, 1926, 1927, 1934,
// 1936, 1937, 1938, 1940, 1941, 1942, 1943, 1946, 1947, 1948, 1949, 1987, 2008,
// 2009, 2318, 2871, 2872, 2873, 2959, 2960, 2961).
// Развилка по имени dpdProfile: его нет у формы 36. Id копии и боевой 48 различаются, по ним не ветвимся.
// Плейсхолдеры полей только формы 48 в файле нельзя: на форме 36 ezFC заменит весь расчёт на return 0.
// Резка формы 48 в боевом cjsCalc зашита: isCutManual / KeencutEvolutionE2, материал — isMaterial.
// Рамка, подвесы, EVA и карманы (calcFrame / calcPockets не портированы) — только URL.
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

var isStands = typeof ezfc_functions.get_element_id_by_name === 'function'
    && ezfc_functions.get_element_id_by_name(__form_id__, 'dpdProfile');
if (isStands) {
/* form 48 */
    var qty = numFrom(ezfc_functions.get_value_from(1924));
    var width = numFrom(ezfc_functions.get_value_from(1925, true));
    var height = numFrom(ezfc_functions.get_value_from(1926, true));
    var materialId = ezfc_functions.get_value_from(1927, true)[0] || '';
    var materialIndex = optionIndex(ezfc_functions.get_value_from(1927, true, false, { return_value: 'index' }));
    var applicationId = ezfc_functions.get_value_from(1934, true)[0] || '';
    var applicationIndex = optionIndex(ezfc_functions.get_value_from(1934, true, false, { return_value: 'index' }));
    var color = ezfc_functions.get_value_from(1936, true)[0] || '4+0';
    var colorIndex = optionIndex(ezfc_functions.get_value_from(1936, true, false, { return_value: 'index' }));
    var customPrintSize = ezfc_functions.get_value_from(2318, true)[0] == '1';
    var printW = numFrom(ezfc_functions.get_value_from(2008, true));
    var printH = numFrom(ezfc_functions.get_value_from(2009, true));
    var printSize = customPrintSize
        ? [printW > 0 ? printW : width, printH > 0 ? printH : height]
        : [width, height];
    var edgeId = ezfc_functions.get_value_from(1938, true)[0] || 'isCutEdge';
    var edgeIndex = optionIndex(ezfc_functions.get_value_from(1938, true, false, { return_value: 'index' }));
    var laminatId = ezfc_functions.get_value_from(1937, true)[0] || 'No';
    var laminatIndex = optionIndex(ezfc_functions.get_value_from(1937, true, false, { return_value: 'index' }));
    var bgMaterialId = ezfc_functions.get_value_from(1949, true)[0] || '';
    var bgMaterialIndex = optionIndex(ezfc_functions.get_value_from(1949, true, false, { return_value: 'index' }));
    var appMaterialId = ezfc_functions.get_value_from(1940, true)[0] || '';
    var appMaterialIndex = optionIndex(ezfc_functions.get_value_from(1940, true, false, { return_value: 'index' }));
    var appW = numFrom(ezfc_functions.get_value_from(1941, true));
    var appH = numFrom(ezfc_functions.get_value_from(1942, true));
    var appColors = numFrom(ezfc_functions.get_value_from(1943)) || 1;
    var appSizeItem = numFrom(ezfc_functions.get_value_from(1946));
    var appDensityRaw = ezfc_functions.get_value_from(1947, true);
    var appDensity = Number(String(appDensityRaw == null ? '' : appDensityRaw).replace('%', '').replace(',', '.'));
    if (isNaN(appDensity)) appDensity = 0;
    var appDensityFactor = numFrom(ezfc_functions.get_value_from(1947));
    var appDifficultyRaw = ezfc_functions.get_value_from(1948, true)[0];
    var appDifficultyNum = Number(appDifficultyRaw);
    var appDifficulty = (appDifficultyRaw === '' || appDifficultyRaw == null || isNaN(appDifficultyNum)) ? 1 : appDifficultyNum;
    var appDifficultyIndex = optionIndex(ezfc_functions.get_value_from(1948, true, false, { return_value: 'index' }));
    // Коды рамки, подвеса и EVA в calcApi не уходят: calcFrame и isEVAFoam не портированы.
    var profileIndex = optionIndex(ezfc_functions.get_value_from(2871, true, false, { return_value: 'index' }));
    var hangerIndex = optionIndex(ezfc_functions.get_value_from(2872, true, false, { return_value: 'index' }));
    var numHangers = numFrom(ezfc_functions.get_value_from(2873, true)) || 0;
    var foamIndex = optionIndex(ezfc_functions.get_value_from(2959, true, false, { return_value: 'index' }));
    var foamW = numFrom(ezfc_functions.get_value_from(2960, true));
    var foamH = numFrom(ezfc_functions.get_value_from(2961, true));
    // 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
    // У формы 48 в радио только 1 и 2; пустое всё равно не превращаем нулём в единицу через ||.
    var modeRaw = ezfc_functions.get_value_from(1987, true)[0];
    var modeNum = Number(modeRaw);
    var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

    // Карманы — повторяемая форма. get_value_from ряды не обходит, читаем DOM как боевой cjsCalc.
    // calcPockets не портирован: ряд с количеством > 0 в calcApi не отправляем.
    var pocketRoot = document.getElementsByClassName('setPockets')[0];
    var pocketList = pocketRoot ? pocketRoot.getElementsByClassName('ezfc-repeatable-form-elements')[0] : null;
    var pocketRows = pocketList ? pocketList.getElementsByClassName('ezfc-element-wrapper-repeatable_form') : [];
    var pocketCount = 0;
    for (var pocketI = 0; pocketI < pocketRows.length; pocketI++) {
        var pocketRow = pocketRows[pocketI];
        var pocketCountEl = pocketRow.getElementsByClassName('countPocket')[0];
        var pocketN = pocketCountEl ? Number(pocketCountEl.value) : 0;
        if (pocketN > 0) pocketCount += pocketN;
    }
    if (pocketCount > 0) {
        // Ряд с количеством есть, в params не пишем.
    }

    insaincalc.syncUrl({
        numN: qty,
        numW: width,
        numH: height,
        dpdMaterial: materialIndex,
        dpdApplication: applicationIndex,
        dpdColor: colorIndex,
        ckbSize: customPrintSize ? 0 : '',
        numPrintW: printW,
        numPrintH: printH,
        dpdEdge: edgeIndex,
        dpdRollWideLaminat: laminatIndex,
        dpdBackgroudMaterial: bgMaterialIndex,
        dpdApplicationMaterial: appMaterialIndex,
        numApplicationW: appW,
        numApplicationH: appH,
        numFilm: appColors,
        numSizeItem: appSizeItem,
        numDensity: appDensity,
        dpdFilmDifficulty: appDifficultyIndex,
        dpdProfile: profileIndex,
        dpdHanger: hangerIndex,
        numHangers: numHangers,
        dpd: foamIndex,
        numFoamW: foamW,
        numFoamH: foamH,
        rdoModeProduction: mode
    });

    var params = {
        quantity: Number(qty) || 1,
        width: width,
        height: height,
        material_id: String(materialId),
        material_mode: 'isMaterial',
        is_cut_manual: 'KeencutEvolutionE2',
        mode: mode
    };

    if (String(applicationId) === 'isUVPrint') {
        params.is_uv_print = {
            printer_id: 'PrintUV',
            resolution: 0,
            surface: 'plain',
            color: String(color || '4+0'),
            double_application: false
        };
    } else if (String(applicationId) === 'isECOPrint') {
        params.is_print = {
            printer_id: 'Technojet160ECO',
            double_application: false,
            is_edge: String(edgeId || 'isCutEdge'),
            is_lamination: Boolean(laminatId && String(laminatId) !== 'No' && String(laminatId) !== '0'),
            size: printSize
        };
    } else if (String(applicationId) === 'isLatexPrint') {
        params.is_print = {
            printer_id: 'HPLatex335',
            double_application: false,
            is_edge: String(edgeId || 'isCutEdge'),
            is_lamination: false,
            size: printSize
        };
    } else if (String(applicationId) === 'isBackgroundFilm' && bgMaterialId && String(bgMaterialId) !== '0') {
        params.is_background_film = {
            material_id: String(bgMaterialId),
            is_edge: String(edgeId || 'isCutEdge'),
            size: printSize
        };
    }

    if (appMaterialId && String(appMaterialId) !== '0') {
        params.is_film = {
            material_id: String(appMaterialId),
            size: [appW > 0 ? appW : width, appH > 0 ? appH : height],
            size_item: appSizeItem > 0 ? appSizeItem : (appW > 0 ? appW : width),
            density: appDensityFactor,
            difficulty: appDifficulty,
            color: appColors,
            double_application: false
        };
    }

    insaincalc.calcApi('tablets', params).then(function (calcCost) {
        insaincalc.showResult(calcCost, qty, __form_id__);
    }).catch(function (err) {
        insaincalc.showError(err, __form_id__);
    });
/* /form */
} else {
/* form 36 */
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
var appMaterialId = ezfc_functions.get_value_from(1484, true)[0] || '';
var appMaterialIndex = optionIndex(ezfc_functions.get_value_from(1484, true, false, { return_value: 'index' }));
var appW = numFrom(ezfc_functions.get_value_from(1419, true));
var appH = numFrom(ezfc_functions.get_value_from(1420, true));
var appColors = numFrom(ezfc_functions.get_value_from(1430, false)) || 1;
var appSizeItem = numFrom(ezfc_functions.get_value_from(1424, false));
var appDensityRaw = ezfc_functions.get_value_from(1425, true, true);
var appDensity = Number(String(appDensityRaw == null ? '' : appDensityRaw).replace('%', '').replace(',', '.'));
if (isNaN(appDensity)) appDensity = 0;
var appDensityFactor = numFrom(ezfc_functions.get_value_from(1425));
var appDifficultyRaw = ezfc_functions.get_value_from(1423, true)[0];
var appDifficultyNum = Number(appDifficultyRaw);
var appDifficulty = (appDifficultyRaw === '' || appDifficultyRaw == null || isNaN(appDifficultyNum)) ? 1 : appDifficultyNum;
var appDifficultyIndex = optionIndex(ezfc_functions.get_value_from(1423, true, false, { return_value: 'index' }));
var bgMaterialId = ezfc_functions.get_value_from(1427, true)[0] || '';
var bgMaterialIndex = optionIndex(ezfc_functions.get_value_from(1427, true, false, { return_value: 'index' }));
var bgEdgeId = ezfc_functions.get_value_from(1483, true)[0] || 'isCutEdge';
var bgEdgeIndex = optionIndex(ezfc_functions.get_value_from(1483, true, false, { return_value: 'index' }));
var hasShaft = ezfc_functions.get_value_from(1533, true) == 'true';
var shaftLen = numFrom(ezfc_functions.get_value_from(1534, true)) || 1;
var hasAdhesiveLayer = ezfc_functions.get_value_from(2718, false) == 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2003, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

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
} else if (String(applicationId) === 'isFilm') {
    params.is_film = {
        material_id: String(appMaterialId || ''),
        size: [appW > 0 ? appW : width, appH > 0 ? appH : height],
        size_item: appSizeItem > 0 ? appSizeItem : (appW > 0 ? appW : width),
        density: appDensityFactor,
        difficulty: appDifficulty,
        color: appColors,
        double_application: isDoubleApplication
    };
} else if (String(applicationId) === 'isSublimation') {
    params.is_sublimation = true;
}

if (bgMaterialId && String(bgMaterialId) !== '0') {
    params.is_background_film = {
        material_id: String(bgMaterialId),
        is_edge: String(bgEdgeId || 'isCutEdge'),
        double_application: isDoubleApplication
    };
}

insaincalc.calcApi('tablets', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
/* /form */
}
