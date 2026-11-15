// Форма 23 CalcPrintWide, элемент cjsCalc (776). Id полей — боевой формы 23.
var qty = {{numN}};
var formatRaw = ezfc_functions.get_value_from(757, true);
var formatIndex = ezfc_functions.get_value_from(757, true, false, { return_value: 'index' })[0];
// Значение dpdFormat — «ширина, высота» в мм, например «1189,841». Свой размер — «0».
var formatParts = String(formatRaw == null ? '' : formatRaw).split(',');
var width = parseInt(formatParts[0], 10);
var height = parseInt(formatParts.length > 1 ? formatParts[1] : '', 10);
var customWRaw = ezfc_functions.get_value_from(759, true);
var customHRaw = ezfc_functions.get_value_from(760, true);
var customW = Number(String(customWRaw == null ? '' : customWRaw).replace(',', '.'));
var customH = Number(String(customHRaw == null ? '' : customHRaw).replace(',', '.'));
// Поля своего размера в сантиметрах. В API уходят миллиметры.
if (!width) {
    width = customW * 10;
    height = customH * 10;
}
var materialId = ezfc_functions.get_value_from(762, true)[0];
var materialIndex = ezfc_functions.get_value_from(762, true, false, { return_value: 'index' })[0];
var printerId = ezfc_functions.get_value_from(761, true)[0];
var printerIndex = ezfc_functions.get_value_from(761, true, false, { return_value: 'index' })[0];
// 0 — «нет». Глянец и мат старый JS не различает: оба только включают ламинацию.
var laminatRaw = ezfc_functions.get_value_from(764, true)[0];
var laminatIndex = ezfc_functions.get_value_from(764, true, false, { return_value: 'index' })[0];
var laminatNum = Number(laminatRaw);
var laminat = (laminatRaw === '' || laminatRaw == null || isNaN(laminatNum)) ? 0 : laminatNum;
// Чекбокс: get_value_from → 'true' у включённой опции.
var isJoining = ezfc_functions.get_value_from(810, true) == 'true';
// data-value 1 — одинаковая обработка, 2 — разная. В URL value 0/1, не data-value.
// ezFC не отмечает радио со value 0: rdoProcessEdge=0 оставляет пункт пустым,
// условие прячет край и шаг. Отмечаем индекс 0 и даём форме пересчитать.
var processUrl = '';
try {
    processUrl = new URL(window.location.href).searchParams.get('rdoProcessEdge');
} catch (eProcessUrl) {
    processUrl = '';
}
var processListed = ezfc_functions.get_value_from(800, true);
var deferEdgeZero = false;
if (!(processListed && typeof processListed === 'object') && processUrl === '0' && !insaincalc._printRollEdgeZero) {
    insaincalc._printRollEdgeZero = true;
    var processElId = ezfc_functions.get_element_id_by_name(__form_id__, 'rdoProcessEdge');
    var processInput = document.getElementById('ezfc_element-' + processElId + '-0');
    if (processInput && window.jQuery) {
        processInput.checked = true;
        window.jQuery(processInput).trigger('change');
        deferEdgeZero = true;
    } else if (processInput) {
        processInput.checked = true;
        processListed = ezfc_functions.get_value_from(800, true);
    }
}
if (!(processListed && typeof processListed === 'object') && processUrl === '0') {
    processListed = [1];
}
var processRaw = (processListed && typeof processListed === 'object') ? processListed[0] : processListed;
var processIndexListed = ezfc_functions.get_value_from(800, true, false, { return_value: 'index' });
var processIndex = (processIndexListed && typeof processIndexListed === 'object') ? processIndexListed[0] : processIndexListed;
if (processUrl === '0' && (processIndex === '' || processIndex == null)) {
    processIndex = 0;
}
var processNum = Number(processRaw);
var sameEdges = processNum === 1;
var edgeCode = ezfc_functions.get_value_from(799, true)[0];
var edgeIndex = ezfc_functions.get_value_from(799, true, false, { return_value: 'index' })[0];
var stepAllNum = Number(ezfc_functions.get_value_from(772, false));
var stepAll = isNaN(stepAllNum) ? 0 : stepAllNum;
var edgeTop = ezfc_functions.get_value_from(807, true)[0];
var edgeTopIndex = ezfc_functions.get_value_from(807, true, false, { return_value: 'index' })[0];
var stepTopNum = Number(ezfc_functions.get_value_from(808, false));
var stepTop = isNaN(stepTopNum) ? 0 : stepTopNum;
var edgeRight = ezfc_functions.get_value_from(801, true)[0];
var edgeRightIndex = ezfc_functions.get_value_from(801, true, false, { return_value: 'index' })[0];
var stepRightNum = Number(ezfc_functions.get_value_from(802, false));
var stepRight = isNaN(stepRightNum) ? 0 : stepRightNum;
var edgeBottom = ezfc_functions.get_value_from(804, true)[0];
var edgeBottomIndex = ezfc_functions.get_value_from(804, true, false, { return_value: 'index' })[0];
var stepBottomNum = Number(ezfc_functions.get_value_from(805, false));
var stepBottom = isNaN(stepBottomNum) ? 0 : stepBottomNum;
var edgeLeft = ezfc_functions.get_value_from(803, true)[0];
var edgeLeftIndex = ezfc_functions.get_value_from(803, true, false, { return_value: 'index' })[0];
var stepLeftNum = Number(ezfc_functions.get_value_from(806, false));
var stepLeft = isNaN(stepLeftNum) ? 0 : stepLeftNum;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(790, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

// Первый проход с value 0 только отмечает радио. URL и POST — после change,
// когда край и шаг уже видны. Иначе скрытый шаг пишется как 0.
if (!deferEdgeZero) {
insaincalc.syncUrl({
    numN: qty,
    dpdFormat: formatIndex,
    numW: customW,
    numH: customH,
    dpdMaterial: materialIndex,
    dpdPrinter: printerIndex,
    dpdRollLaminat: laminatIndex,
    // Чекбокс: GET_check=index; включён → 0; выключен → '' (удалить).
    ckbJoing: isJoining ? 0 : '',
    rdoProcessEdge: processIndex,
    dpdProcessEdge: edgeIndex,
    // Поле в сантиметрах, factor 10: step* уже миллиметры. В URL — см, max поля 50.
    numStepEyelets: stepAll / 10,
    dpdProcessEdgeTop: edgeTopIndex,
    numStepEyeletsTop: stepTop / 10,
    dpdProcessEdgeRight: edgeRightIndex,
    numStepEyeletsRight: stepRight / 10,
    dpdProcessEdgeBottom: edgeBottomIndex,
    numStepEyeletsBottom: stepBottom / 10,
    dpdProcessEdgeLeft: edgeLeftIndex,
    numStepEyeletsLeft: stepLeft / 10,
    rdoModeProduction: mode
});
}

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    material_id: materialId,
    printer_code: printerId,
    mode: mode
};
if (laminat > 0) {
    params.is_lamination = true;
}
if (isJoining) {
    params.is_joining = true;
}
// «Поля 5 см» и «поля 10 см» старый calcPrintRoll не считает. В API их нет.
if (sameEdges) {
    if (edgeCode === 'isEyelet') {
        params.is_eyelet = [stepAll, stepAll, stepAll, stepAll];
    } else if (edgeCode === 'isCutting') {
        params.is_cutting = [1, 1, 1, 1];
    } else if (edgeCode === 'isGluing') {
        params.is_gluing = [1, 1, 1, 1];
    } else if (edgeCode === 'isPocket') {
        params.is_pocket = [1, 1, 1, 1];
    }
} else {
    var codes = [edgeTop, edgeRight, edgeBottom, edgeLeft];
    var steps = [stepTop, stepRight, stepBottom, stepLeft];
    var cutting = [0, 0, 0, 0];
    var gluing = [0, 0, 0, 0];
    var pocket = [0, 0, 0, 0];
    var eyelet = [0, 0, 0, 0];
    var hasCutting = false;
    var hasGluing = false;
    var hasPocket = false;
    var hasEyelet = false;
    for (var i = 0; i < 4; i++) {
        if (codes[i] === 'isEyelet') {
            eyelet[i] = steps[i];
            hasEyelet = true;
        } else if (codes[i] === 'isCutting') {
            cutting[i] = 1;
            hasCutting = true;
        } else if (codes[i] === 'isGluing') {
            gluing[i] = 1;
            hasGluing = true;
        } else if (codes[i] === 'isPocket') {
            pocket[i] = 1;
            hasPocket = true;
        }
    }
    if (hasCutting) {
        params.is_cutting = cutting;
    }
    if (hasGluing) {
        params.is_gluing = gluing;
    }
    if (hasPocket) {
        params.is_pocket = pocket;
    }
    if (hasEyelet) {
        params.is_eyelet = eyelet;
    }
}

if (!deferEdgeZero) {
insaincalc.calcApi('print_roll', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
}
