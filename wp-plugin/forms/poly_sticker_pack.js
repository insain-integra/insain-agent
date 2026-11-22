// Форма 70 CalcPolyStickerPack, элемент cjsCalc (2826). Id полей — боевой формы 70.
// Наклейки — repeatable form 71 (setStickers) внутри grpSetStickers.
// Сбор рядов — тот же DOM по классам, что в боевом cjsCalc: get_value_from не обходит
// экземпляры repeatable (id 2848, 2849, 2851 — шаблон формы 71, не набор значений по рядам).
// Боевой cjsCalc кладёт в isPrint строку принтера, а calcSticker читает .printerID.
// Печать в цену не входит: print_method всегда No. Принтер не No включает метки.
// Ламинация зашита в форме, поля нет:
// KMBizhubC220 → Laminat32G, Technojet160ECO → LaminatDLCLAM, латекс без плёнки.
// fluAtrwork — файл макета: в URL и в calcApi не уходит.
// Ряды наклеек в GET не пишутся: numW и numH формы 71 совпадают с размером пака.
var qty = {{numN}};
var width = Number({{numW}});
var height = Number({{numH}});
var materialId = ezfc_functions.get_value_from(2823, true)[0];
var materialIndex = ezfc_functions.get_value_from(2823, true, false, { return_value: 'index' })[0];
var printerId = ezfc_functions.get_value_from(2824, true)[0];
var printerIndex = ezfc_functions.get_value_from(2824, true, false, { return_value: 'index' })[0];
var isBackground = ezfc_functions.get_value_from(2870, false) == 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(2839, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

var numStickers = 0;
var sumSide = 0;
var sumDifficulty = 0;
var container = document.getElementsByClassName('setStickers')[0];
var repeatRoot = container ? container.getElementsByClassName('ezfc-repeatable-form-elements')[0] : null;
var stickerRows = repeatRoot ? repeatRoot.getElementsByClassName('ezfc-element-wrapper-repeatable_form') : [];
for (var i = 0; i < stickerRows.length; i++) {
    var element = stickerRows[i];
    var widthInput = element.getElementsByClassName('widthSticker')[0];
    var heightInput = element.getElementsByClassName('heightSticker')[0];
    if (!widthInput || !heightInput) {
        continue;
    }
    var stickerW = Number(widthInput.value);
    var stickerH = Number(heightInput.value);
    if (!(stickerW > 0) || !(stickerH > 0)) {
        continue;
    }
    var diffSelect = element.getElementsByClassName('difficultySticker')[0];
    var difficultySticker = 1;
    if (diffSelect && diffSelect.selectedIndex >= 0) {
        var diffData = diffSelect.options[diffSelect.selectedIndex].getAttribute('data-value');
        var diffNum = Number(diffData);
        // Как в боевом cjsCalc: индекс 0 → 1, иначе 1.3. data-value тех же опций совпадает.
        if (diffData === '' || diffData == null || isNaN(diffNum)) {
            difficultySticker = String(diffSelect.value) === '0' ? 1 : 1.3;
        } else {
            difficultySticker = diffNum;
        }
    }
    numStickers += 1;
    sumSide += (stickerW + stickerH) / 2;
    sumDifficulty += difficultySticker;
}
if (!numStickers) {
    numStickers = 1;
    sumSide = 20;
    sumDifficulty = 1;
}

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    dpdPrint: printerIndex,
    chkBackground: isBackground ? 0 : '',
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    material_id: materialId,
    num_stickers: numStickers,
    sticker_size: sumSide / numStickers,
    sticker_difficulty: sumDifficulty / numStickers,
    is_background: isBackground,
    print_method: 'No',
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

insaincalc.calcApi('poly_sticker_pack', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
