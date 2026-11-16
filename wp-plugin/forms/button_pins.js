// Форма 12 CalcButtonPins, элемент cjsCalc (1639). Id полей — боевой формы 12.
var qty = {{numN}};
var pinId = ezfc_functions.get_value_from(214, true)[0];
var pinIndex = ezfc_functions.get_value_from(214, true, false, { return_value: 'index' })[0];
// Чекбокс: значение опции isPacking, как в старом cjsCalc. Включён — автоподбор пакета.
var isPacking = ezfc_functions.get_value_from(1659, true) == 'isPacking';
// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(1753, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    dpdSize: pinIndex,
    // Чекбокс: GET_check=index; включён → индекс единственной опции 0; выключен → '' (удалить).
    chkPacking: isPacking ? 0 : '',
    rdoModeProduction: mode
});

insaincalc.calcApi('button_pins', {
    quantity: Number(qty) || 1,
    pin_id: pinId,
    is_packing: isPacking,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
