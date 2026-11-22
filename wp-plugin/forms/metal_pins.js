// Форма 34 CalcMetalPins, элемент cjsCalc (1232). Id полей — боевой формы 34.
// Вид значка: 1 простой, 2 двухсторонний (вторая толщина 0), 3 двухсоставной.
var qty = {{numN}};
var kind = Number(ezfc_functions.get_value_from(1225, true)[0]);
var w1 = {{numW1}};
var h1 = {{numH1}};
var w2 = {{numW2}};
var h2 = {{numH2}};
var t1 = {{sbtStandartT1}};
var t2 = {{sbtStandartT2}};
var enamels1 = {{numEnamels1}};
var enamels2 = {{numEnamels2}};
var customT1 = {{numT1}};
var customT2 = {{numT2}};

if (ezfc_functions.get_value_from(1256, false) == 1) {
    t1 = customT1;
}
if (ezfc_functions.get_value_from(1276, false) == 1) {
    t2 = customT2;
}
if (kind === 2) {
    t2 = 0;
}

var metal1 = ezfc_functions.get_value_from(1254, true)[0];
var process1 = ezfc_functions.get_value_from(1252, true)[0];
var plating1 = ezfc_functions.get_value_from(1229, true)[0];
var metal2 = ezfc_functions.get_value_from(1279, true)[0];
var process2 = ezfc_functions.get_value_from(1280, true)[0];
var plating2 = ezfc_functions.get_value_from(1281, true)[0];
var epoxy1 = ezfc_functions.get_value_from(3125, false) == 1;
var epoxy2 = ezfc_functions.get_value_from(3126, false) == 1;
var mould = ezfc_functions.get_value_from(3312, false) == 1;
var attachmentId = ezfc_functions.get_value_from(1230, true)[0];
var packId = ezfc_functions.get_value_from(1227, true)[0];

var modeRaw = ezfc_functions.get_value_from(2812, true)[0];
var modeNum = Number(modeRaw);
var mode = (modeRaw === '' || modeRaw == null || isNaN(modeNum)) ? 1 : modeNum;

function optionIndex(raw) {
    if (raw == null || typeof raw !== 'object' || raw[0] == null || raw[0] === '') {
        return '';
    }
    return raw[0];
}

function checkedIndex(raw) {
    return raw == 1 ? 0 : '';
}

// В списке формы «алюминий» записан aluminium, в прайсе ключ aluminum.
function metalCode(code) {
    if (code === 'aluminium') {
        return 'aluminum';
    }
    return code;
}

// В списке формы «безопасная булавка» — SafetyPinMetall, в прайсе SafetyPin.
function attachmentCode(code) {
    if (code === 'SafetyPinMetall') {
        return 'SafetyPin';
    }
    return code;
}

function makeStamp(width, height, thickness, metal, processId, plating, enamels, epoxy) {
    return {
        size: [Number(width) || 0, Number(height) || 0, Number(thickness) || 0],
        materialID: metalCode(metal),
        processID: Number(processId) || 1,
        platingID: plating,
        numEnamels: Number(enamels) || 0,
        isEpoxy: epoxy ? 'isEpoxy' : '',
        isMould: mould ? 'isMould' : ''
    };
}

var stamps = [makeStamp(w1, h1, t1, metal1, process1, plating1, enamels1, epoxy1)];
if (kind >= 2) {
    stamps.push(makeStamp(w2, h2, t2, metal2, process2, plating2, enamels2, epoxy2));
}

var params = {
    quantity: Number(qty) || 1,
    width_mm: Number(w1) || 0,
    height_mm: Number(h1) || 0,
    stamps: stamps,
    mode: mode
};
if (attachmentId && attachmentId !== 'No') {
    params.attachment_id = attachmentCode(attachmentId);
}
if (packId && packId !== 'No') {
    params.pack_id = packId;
}

insaincalc.syncUrl({
    numN: qty,
    dpdForm: optionIndex(ezfc_functions.get_value_from(1225, true, false, { return_value: 'index' })),
    numW1: w1,
    numH1: h1,
    dpdMetall1: optionIndex(ezfc_functions.get_value_from(1254, true, false, { return_value: 'index' })),
    dpdProcess1: optionIndex(ezfc_functions.get_value_from(1252, true, false, { return_value: 'index' })),
    dpdPlating1: optionIndex(ezfc_functions.get_value_from(1229, true, false, { return_value: 'index' })),
    numEnamels1: enamels1,
    ckbThinkness1: checkedIndex(ezfc_functions.get_value_from(1256, false)),
    numT1: customT1,
    ckbEpoxy1: checkedIndex(ezfc_functions.get_value_from(3125, false)),
    ckbMould: checkedIndex(ezfc_functions.get_value_from(3312, false)),
    numW2: w2,
    numH2: h2,
    dpdMetall2: optionIndex(ezfc_functions.get_value_from(1279, true, false, { return_value: 'index' })),
    dpdProcess2: optionIndex(ezfc_functions.get_value_from(1280, true, false, { return_value: 'index' })),
    dpdPlating2: optionIndex(ezfc_functions.get_value_from(1281, true, false, { return_value: 'index' })),
    numEnamels2: enamels2,
    ckbThinkness2: checkedIndex(ezfc_functions.get_value_from(1276, false)),
    numT2: customT2,
    ckbEpoxy2: checkedIndex(ezfc_functions.get_value_from(3126, false)),
    dpdAttachment: optionIndex(ezfc_functions.get_value_from(1230, true, false, { return_value: 'index' })),
    dpdPacking: optionIndex(ezfc_functions.get_value_from(1227, true, false, { return_value: 'index' })),
    rdoModeProduction: mode
});

insaincalc.calcApi('metal_pins', params).then(function (calcCost) {
    insaincalc.showResult(calcCost, qty, __form_id__);
}).catch(function (err) {
    insaincalc.showError(err, __form_id__);
});
