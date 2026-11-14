// Форма 22 CalcSticker, элемент cjsCalc (629). Id полей — боевой формы 22.
// numDensity скрыт, пока сложность не 1.7: calculate_when_hidden=0, на дефолте в расчёт уходит 0.
// {{numDensity}} — это get_value_from(649): factor 0.01 уже внутри, скрытое поле даёт 0.
// chkMark (резка по меткам) в API стикера нет: в URL пишется, в calcApi не уходит.
// Широкая печать: Technojet160ECO, HPLatex335, TechnojetXR720, цветность всегда 4+0.
// Широкая ламинация (элемент 1064) уходит только с Technojet160ECO и только если value не No.
var qty = {{numN}};
var widthRaw = ezfc_functions.get_value_from(620, true);
var heightRaw = ezfc_functions.get_value_from(621, true);
var width = Number(String(widthRaw == null ? '' : widthRaw).replace(',', '.'));
var height = Number(String(heightRaw == null ? '' : heightRaw).replace(',', '.'));
var sizeItem = Number({{numSizeItem}});
var density = Number({{numDensity}});
if (isNaN(density)) density = 0;
var difficultyRaw = ezfc_functions.get_value_from(650, true)[0];
var difficultyIndex = ezfc_functions.get_value_from(650, true, false, { return_value: 'index' })[0];
var difficultyNum = Number(difficultyRaw);
var difficulty = (difficultyRaw === '' || difficultyRaw == null || isNaN(difficultyNum)) ? 1 : difficultyNum;
var materialId = ezfc_functions.get_value_from(623, true)[0];
var materialIndex = ezfc_functions.get_value_from(623, true, false, { return_value: 'index' })[0];
var printerId = ezfc_functions.get_value_from(811, true)[0];
var printerIndex = ezfc_functions.get_value_from(811, true, false, { return_value: 'index' })[0];
var sheetLaminat = ezfc_functions.get_value_from(1063, true)[0];
var sheetLaminatIndex = ezfc_functions.get_value_from(1063, true, false, { return_value: 'index' })[0];
var wideLaminat = ezfc_functions.get_value_from(1064, true)[0];
var wideLaminatIndex = ezfc_functions.get_value_from(1064, true, false, { return_value: 'index' })[0];
// Чекбокс: get_value_from → 1 / 0, как в боевом cjsCalc. В API стикера метки нет.
var isFindMark = ezfc_functions.get_value_from(653, false) == 1;
var isMountingFilm = ezfc_functions.get_value_from(1485, false) == 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(643, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

// Плотность в URL — сырое значение поля (25, не 0.25) и только когда оно видно.
var densityUrl = '';
if (String(difficultyRaw) === '1.7') {
    var densityRaw = ezfc_functions.get_value_from(649, true, true);
    // В поле суффикс «%»: сырое значение 25, в API уже 0.25.
    densityUrl = Number(String(densityRaw == null ? '' : densityRaw).replace('%', '').replace(',', '.'));
    if (isNaN(densityUrl)) densityUrl = '';
}

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: materialIndex,
    dpdDifficulty: difficultyIndex,
    numSizeItem: sizeItem,
    numDensity: densityUrl,
    chkMark: isFindMark ? 0 : '',
    dpdPrint: printerIndex,
    dpdRollLaminat: sheetLaminatIndex,
    dpdRollWideLaminat: wideLaminatIndex,
    chkMountingFilm: isMountingFilm ? 0 : '',
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    size_item: sizeItem,
    density: density,
    difficulty: difficulty,
    material_id: materialId,
    is_mounting_film: isMountingFilm,
    mode: mode
};
// Цветность на форме не выбирается: у печати в старом JS всегда 4+0.
// Лазер читает листовую ламинацию 1063. Экосольвент — широкую 1064.
// Латекс, сольвент и УФ ламинацию не передают.
if (printerId === 'KMBizhubC220') {
    params.color = '4+0';
    params.printer_code = printerId;
    if (sheetLaminat && String(sheetLaminat) !== 'No') {
        params.lamination_id = sheetLaminat;
    }
} else if (printerId === 'Technojet160ECO' || printerId === 'HPLatex335' || printerId === 'TechnojetXR720') {
    params.color = '4+0';
    params.printer_code = printerId;
    if (printerId === 'Technojet160ECO' && wideLaminat && String(wideLaminat) !== 'No') {
        params.lamination_id = wideLaminat;
    }
}

insaincalc.calcApi('sticker', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
