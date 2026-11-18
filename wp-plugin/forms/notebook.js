// Форма 45 CalcNotebook, элемент cjsCalc (1808). Id полей — боевой формы 45.
var qty = {{numN}};
var sheets = {{numSheet}};
// dpdFormat — «ширина,высота» в мм, например «148,210».
var sizeRaw = ezfc_functions.get_value_from(1797, true);
var formatIndex = ezfc_functions.get_value_from(1797, true, false, { return_value: 'index' })[0];
var sizeParts = String(sizeRaw == null ? '' : sizeRaw).split(',');
var width = parseInt(sizeParts[0], 10);
var height = parseInt(sizeParts.length > 1 ? sizeParts[1] : '', 10);

var coverMaterialId = ezfc_functions.get_value_from(1799, true)[0];
var coverMaterialIndex = ezfc_functions.get_value_from(1799, true, false, { return_value: 'index' })[0];
var coverColor = ezfc_functions.get_value_from(1798, true)[0];
var coverColorIndex = ezfc_functions.get_value_from(1798, true, false, { return_value: 'index' })[0];
var coverLaminatId = ezfc_functions.get_value_from(1800, true)[0];
var coverLaminatIndex = ezfc_functions.get_value_from(1800, true, false, { return_value: 'index' })[0];

var backingMaterialId = ezfc_functions.get_value_from(1832, true)[0];
var backingMaterialIndex = ezfc_functions.get_value_from(1832, true, false, { return_value: 'index' })[0];
var backingColor = ezfc_functions.get_value_from(1833, true)[0];
var backingColorIndex = ezfc_functions.get_value_from(1833, true, false, { return_value: 'index' })[0];
var backingLaminatId = ezfc_functions.get_value_from(1834, true)[0];
var backingLaminatIndex = ezfc_functions.get_value_from(1834, true, false, { return_value: 'index' })[0];

var innerMaterialId = ezfc_functions.get_value_from(1837, true)[0];
var innerMaterialIndex = ezfc_functions.get_value_from(1837, true, false, { return_value: 'index' })[0];
var innerColor = ezfc_functions.get_value_from(1838, true)[0];
var innerColorIndex = ezfc_functions.get_value_from(1838, true, false, { return_value: 'index' })[0];

var bindingIndex = ezfc_functions.get_value_from(1825, true, false, { return_value: 'index' })[0];
var edge = ezfc_functions.get_value_from(1826, true)[0];
var edgeIndex = ezfc_functions.get_value_from(1826, true, false, { return_value: 'index' })[0];

// 0 — «дешевле». Пустое поле → 1; ноль нельзя отбрасывать через ||.
var modeRaw = ezfc_functions.get_value_from(1821, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

// Выключенный чекбокс → 0, включённый → ['isPrintLaser'].
var laserRaw = ezfc_functions.get_value_from(2007, true);
var isPrintLaser = !!(laserRaw && laserRaw[0] === 'isPrintLaser');

insaincalc.syncUrl({
    numN: qty,
    dpdFormat: formatIndex,
    // dpdBinding в API не уходит: единственное значение metallwire, переплёт всегда пружина.
    dpdBinding: bindingIndex,
    dpdEdge: edgeIndex,
    dpdCoverMaterial: coverMaterialIndex,
    dpdCoverColor: coverColorIndex,
    dpdCoverLaminat: coverLaminatIndex,
    numSheet: sheets,
    dpdInnerMaterial: innerMaterialIndex,
    dpdInnerColor: innerColorIndex,
    ckbPrintLaser: isPrintLaser ? 0 : '',
    dpdBackingMaterial: backingMaterialIndex,
    dpdBackingColor: backingColorIndex,
    dpdBackingLaminat: backingLaminatIndex,
    rdoModeProduction: mode
});

insaincalc.calcApi('notebook', {
    quantity: Number(qty) || 1,
    width_mm: width,
    height_mm: height,
    cover_material_id: coverMaterialId,
    cover_color: coverColor,
    cover_lamination_id: coverLaminatId || '',
    backing_material_id: backingMaterialId,
    backing_color: backingColor,
    backing_lamination_id: backingLaminatId || '',
    inner_material_id: innerMaterialId,
    inner_num_sheet: Number(sheets) || 1,
    inner_color: innerColor,
    binding_type: 'spring',
    binding_edge: edge,
    is_print_laser: isPrintLaser,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
