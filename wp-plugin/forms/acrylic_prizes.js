// Форма 78 CalcAcrilycPrizes, элемент cjsCalc (3081). Id полей — боевой формы 78.
// Слои — repeatable form 77 (setLayers) внутри frmStellaLayers (3076) и frmBazisLayers (3100).
// Сбор слоёв — тот же DOM по классам, что в боевом cjsCalc: get_value_from не обходит
// экземпляры repeatable (id 3063–3068 — шаблон формы 77, не набор значений по рядам).
var qty = {{numN}};
var modeRaw = ezfc_functions.get_value_from(3094, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

var layers = [];
var layerConfigs = [
    { containerClass: 'setStellaLayers', isTop: true },
    { containerClass: 'setBazisLayers', isTop: false }
];

layerConfigs.forEach(function (config) {
    var container = document.getElementsByClassName(config.containerClass)[0];
    if (!container) {
        return;
    }
    var repeatRoot = container.getElementsByClassName('ezfc-repeatable-form-elements')[0];
    if (!repeatRoot) {
        return;
    }
    var elements = repeatRoot.getElementsByClassName('ezfc-element-wrapper-repeatable_form');
    for (var i = 0; i < elements.length; i++) {
        var element = elements[i];
        var materialSelect = element.getElementsByClassName('materialID')[0];
        if (!materialSelect || materialSelect.selectedIndex < 0) {
            continue;
        }
        var materialID = materialSelect.options[materialSelect.selectedIndex].attributes[1].nodeValue;

        var widthLayer = Number(element.getElementsByClassName('widthLayer')[0].value);
        var heightLayer = Number(element.getElementsByClassName('heightLayer')[0].value);
        var sizeLayers = [widthLayer, heightLayer];

        var applicationSelect = element.getElementsByClassName('applicationID')[0];
        var applicationID = applicationSelect.options[applicationSelect.selectedIndex].attributes[1].nodeValue;

        var widthApplication = Number(element.getElementsByClassName('widthApplication')[0].value);
        var heightApplication = Number(element.getElementsByClassName('heightApplication')[0].value);
        var sizeApplication = [widthApplication, heightApplication];

        // Как в боевом cjsCalc: резка на каждом слое, difficulty 1.3.
        var optionsLayer = {
            isCutLaser: { sizeItem: 0, density: 0, difficulty: 1.3, lenCut: 0 }
        };
        if (applicationID === 'isUVPrint') {
            optionsLayer.isUVPrint = { size: sizeApplication };
        }
        if (applicationID === 'isGrave') {
            optionsLayer.isGrave = 1;
            optionsLayer.isGraveFill = sizeApplication;
        }

        layers.push({
            materialID: materialID,
            size: sizeLayers,
            isTop: config.isTop,
            options: optionsLayer
        });
    }
});

insaincalc.syncUrl({
    numN: qty,
    rdoModeProduction: mode
});

insaincalc.calcApi('acrylic_prizes', {
    quantity: Number(qty) || 1,
    layers: layers,
    mode: mode
}).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
