// Форма 82 CalcPrintPromo, элемент cjsCalc (3208). Id полей — боевой формы 82: 3189, 3221.
// Форма 83 CalcCardPromo, элемент cjsCalc (3229). Id полей — боевой формы 83: 3242.
// Развилка по имени dpdFormat: оно есть у формы 82 и нет у формы 83. Id копии не используем.
// Плейсхолдер только numN: поле есть на обеих формах. Чужой плейсхолдер ezFC заменяет на return 0.
var isLeaflets = ezfc_functions.get_element_id_by_name(__form_id__, 'dpdFormat');
if (isLeaflets) {
/* form 82 */
    // Размер и цветность сборного тиража берутся из кода материала, в API не уходят.
    var qty = {{numN}};
    var materialId = ezfc_functions.get_value_from(3189, true)[0];
    var formatIndex = ezfc_functions.get_value_from(3189, true, false, { return_value: 'index' })[0];
    // «стандарт» — data-value 1, «быстрее» — 2. HTML value у «стандарт» равен 0;
    // боевой расчёт читает data-value. Пустое поле → 1; ноль нельзя отбрасывать через ||.
    var modeRaw = ezfc_functions.get_value_from(3221, true)[0];
    var modeNum = Number(modeRaw);
    var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

    insaincalc.syncUrl({
        numN: qty,
        dpdFormat: formatIndex,
        rdoModeProduction: mode
    });

    var params = {
        num_sheet: Number(qty) || 1,
        material_id: materialId,
        mode: mode
    };
/* /form */
} else {
/* form 83 */
    var qty = {{numN}};
    // Сборник визиток зашит в боевом cjsCalc, отдельного поля нет.
    var materialId = 'OffsetPromoViz1000';
    // «стандарт» — data-value 1 (HTML value 0), «быстрее» — data-value 2.
    // Боевой расчёт читает data-value. Пустое поле → 1; ноль нельзя отбрасывать через ||.
    var modeRaw = ezfc_functions.get_value_from(3242, true)[0];
    var modeNum = Number(modeRaw);
    var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

    insaincalc.syncUrl({
        numN: qty,
        rdoModeProduction: mode
    });

    var params = {
        num_sheet: Number(qty) || 1,
        material_id: materialId,
        mode: mode
    };
/* /form */
}

insaincalc.calcApi('print_offset', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
