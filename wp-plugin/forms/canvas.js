// Форма 80 CalcCanvas, элемент cjsCalc (3134). Id полей — боевой формы 80.
var qty = {{numN}};
// Значение dpdSize — «ширина, высота» в мм, например «400,500». Свой размер — «0».
var sizeRaw = ezfc_functions.get_value_from(3130, true);
var sizeIndex = ezfc_functions.get_value_from(3130, true, false, { return_value: 'index' })[0];
var sizeParts = String(sizeRaw == null ? '' : sizeRaw).split(',');
var width = parseInt(sizeParts[0], 10);
var height = parseInt(sizeParts.length > 1 ? sizeParts[1] : '', 10);
var isCustomSize = !width;
var customWRaw = ezfc_functions.get_value_from(3152, true);
var customHRaw = ezfc_functions.get_value_from(3153, true);
var customW = Number(String(customWRaw == null ? '' : customWRaw).replace(',', '.'));
var customH = Number(String(customHRaw == null ? '' : customHRaw).replace(',', '.'));
if (isCustomSize) {
    width = customW;
    height = customH;
}
// Чекбокс: get_value_from → 1 / 0, как в боевом cjsCalc.
var isFrame = ezfc_functions.get_value_from(3151, false) == 1;
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(3147, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdSize: sizeIndex,
    numW: isCustomSize ? customW : '',
    numH: isCustomSize ? customH : '',
    chkFrame: isFrame ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('canvas', {
    quantity: Number(qty) || 1,
    width: width,
    height: height,
    is_frame: isFrame,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
