// Форма 40 CalcHeatPress, элемент cjsCalc (1570). Id полей — боевой формы 40.
// numDensity (1562) скрыт, пока сложность не 1.7: calculate_when_hidden=0, на дефолте в расчёт уходит 0.
// {{numDensity}} — factor 0.01 уже внутри, скрытое поле даёт 0.
// ckbMaterialCostomer (2283) передаётся в API как is_customer_material (+25% к цене).
var qty = {{numN}};
var width = {{numW}};
var height = {{numH}};
var itemType = ezfc_functions.get_value_from(1542, true)[0];
var itemIndex = ezfc_functions.get_value_from(1542, true, false, { return_value: 'index' })[0];
var transferType = ezfc_functions.get_value_from(1546, true)[0];
var transferIndex = ezfc_functions.get_value_from(1546, true, false, { return_value: 'index' })[0];

// Параметры ветки film
var filmMaterialId = ezfc_functions.get_value_from(1555, true)[0];
var filmMaterialIndex = ezfc_functions.get_value_from(1555, true, false, { return_value: 'index' })[0];
var filmColors = Number({{numFilm}}) || 1;
var sizeItem = Number({{numSizeItem}}) || 0;
var density = Number({{numDensity}});
if (isNaN(density)) density = 0;
var difficultyRaw = ezfc_functions.get_value_from(1563, true)[0];
var difficultyIndex = ezfc_functions.get_value_from(1563, true, false, { return_value: 'index' })[0];
var difficultyNum = Number(difficultyRaw);
var difficulty = (difficultyRaw === '' || difficultyRaw == null || isNaN(difficultyNum)) ? 1 : difficultyNum;

// Плотность в URL — сырое значение поля (25, не 0.25) и только когда оно видно.
var densityUrl = '';
if (transferType === 'film' && String(difficultyRaw) === '1.7') {
    var densityRaw = ezfc_functions.get_value_from(1562, true, true);
    densityUrl = Number(String(densityRaw == null ? '' : densityRaw).replace('%', '').replace(',', '.'));
    if (isNaN(densityUrl)) densityUrl = '';
}

// Параметры ветки silk
var silkColor = Number({{numSilkColor}}) || 1;
var tShirtColorRaw = ezfc_functions.get_value_from(1591, true)[0];
var tShirtColorIndex = ezfc_functions.get_value_from(1591, true, false, { return_value: 'index' })[0];
var addWhite = Number(tShirtColorRaw) || 0;

// Изделие заказчика (+25% к итоговой цене в cjsCalc формы 40, элемент 2283)
var customerRaw = ezfc_functions.get_value_from(2283, true);
var isCustomerMaterial = (Array.isArray(customerRaw) && customerRaw[0] === 'isMaterialCustomer')
    || customerRaw === 'isMaterialCustomer'
    || customerRaw == 'true';

// 0 — «дешевле» (на форме 40 опций 0 нет). Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(3182, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

insaincalc.syncUrl({
    numN: qty,
    numW: width,
    numH: height,
    dpdMaterial: itemIndex,
    dpdHeatPress: transferIndex,
    dpdApplicationMaterial: transferType === 'film' ? filmMaterialIndex : '',
    numFilm: transferType === 'film' ? filmColors : '',
    dpdFilmDifficulty: transferType === 'film' ? difficultyIndex : '',
    numSizeItem: transferType === 'film' ? sizeItem : '',
    numDensity: densityUrl,
    numSilkColor: transferType === 'silk' ? silkColor : '',
    rdoColorTShirt: transferType === 'silk' ? tShirtColorIndex : '',
    // Чекбокс: GET_check=index; включён → индекс единственной опции 0; выключен → '' (удалить).
    ckbMaterialCostomer: isCustomerMaterial ? 0 : '',
    rdoModeProduction: mode
});

var params = {
    quantity: Number(qty) || 1,
    width: Number(width) || 1,
    height: Number(height) || 1,
    transfer_type: transferType,
    item_type: itemType,
    is_customer_material: isCustomerMaterial,
    mode: mode
};

if (transferType === 'film') {
    params.material_id = filmMaterialId;
    params.film_colors = filmColors;
    params.size_item = sizeItem;
    params.density = density;
    params.difficulty = difficulty;
} else if (transferType === 'silk') {
    params.silk_colors = silkColor + addWhite;
}

insaincalc.calcApi('heat_press', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
