// Форма 6 CalcPrint, элемент cjsCalc (104). Id полей — боевой формы 6.
var qty = {{numN}};
var formatRaw = ezfc_functions.get_value_from(99, true);
var formatIndex = ezfc_functions.get_value_from(99, true, false, { return_value: 'index' })[0];
// Значение dpdFormat — «ширина, высота» в мм, например «297,210». Свой размер — «0».
var formatParts = String(formatRaw == null ? '' : formatRaw).split(',');
var width = parseInt(formatParts[0], 10);
var height = parseInt(formatParts.length > 1 ? formatParts[1] : '', 10);
var customWRaw = ezfc_functions.get_value_from(100, true);
var customHRaw = ezfc_functions.get_value_from(101, true);
var customW = Number(String(customWRaw == null ? '' : customWRaw).replace(',', '.'));
var customH = Number(String(customHRaw == null ? '' : customHRaw).replace(',', '.'));
if (!width) {
    width = customW;
    height = customH;
}
var color = ezfc_functions.get_value_from(102, true)[0];
var colorIndex = ezfc_functions.get_value_from(102, true, false, { return_value: 'index' })[0];
var materialId = ezfc_functions.get_value_from(103, true)[0];
var materialIndex = ezfc_functions.get_value_from(103, true, false, { return_value: 'index' })[0];
// Снятая галка — вылеты 2 мм и интервал 4 мм, как в боевом cjsCalc. Включённая — без полей принтера.
var isMargins = ezfc_functions.get_value_from(419, false) == 1;
var margins = isMargins ? -1 : [2, 2, 2, 2];
var interval = isMargins ? 0 : 4;
var laminatRaw = ezfc_functions.get_value_from(401, false);
var laminatNum = Number(laminatRaw);
var laminat = (laminatRaw === '' || laminatRaw == null || isNaN(laminatNum)) ? 0 : laminatNum;
var rollId = ezfc_functions.get_value_from(400, true)[0];
var rollIndex = ezfc_functions.get_value_from(400, true, false, { return_value: 'index' })[0];
var packId = ezfc_functions.get_value_from(402, true)[0];
var packIndex = ezfc_functions.get_value_from(402, true, false, { return_value: 'index' })[0];
var laminatId = '';
if (laminat == 1) {
    laminatId = rollId;
} else if (laminat == 2) {
    laminatId = packId;
}
// Чекбокс: get_value_from → [true]/0/'true'; без [0], как в боевом cjsCalc.
var isNumber = ezfc_functions.get_value_from(661, true) == 'true';
var isBarcode = ezfc_functions.get_value_from(663, true) == 'true';
var isVariables = ezfc_functions.get_value_from(666, true) == 'true';
var isRounding = ezfc_functions.get_value_from(667, true) == 'true';
var isCrease = ezfc_functions.get_value_from(664, true) == 'true';
var isHole = ezfc_functions.get_value_from(668, true) == 'true';
var numCrease = {{numCrease}};
var numHole = {{numHole}};
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(519, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdFormat: formatIndex,
    numW: customW,
    numH: customH,
    // Чекбокс: GET_check=index; включён → индекс единственной опции 0; выключен → '' (удалить).
    ckbMargin: isMargins ? 0 : '',
    dpdColor: colorIndex,
    dpdMaterial: materialIndex,
    rdoLaminat: laminat,
    dpdRollLaminat: rollIndex,
    dpdPackLaminat: packIndex,
    ckbNumber: isNumber ? 0 : '',
    ckbBarcode: isBarcode ? 0 : '',
    ckbVariables: isVariables ? 0 : '',
    ckbRounding: isRounding ? 0 : '',
    ckbCrease: isCrease ? 0 : '',
    numCrease: numCrease,
    ckbHole: isHole ? 0 : '',
    numHole: numHole,
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    color: color,
    margins: margins,
    interval: interval,
    material_id: materialId,
    mode: mode,
    option_numbering: isNumber,
    option_barcode: isBarcode,
    option_variable_data: isVariables,
    option_rounding: isRounding,
    holes_per_item: isHole ? (Number(numHole) || 0) : 0,
    crease_lines_per_item: isCrease ? (Number(numCrease) || 0) : 0
};
if (laminatId && String(laminatId) !== '0') {
    params.lamination_id = laminatId;
}

insaincalc.calcApi('print_sheet', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
