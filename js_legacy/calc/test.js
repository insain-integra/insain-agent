// считываем размер
let numW = {{numW}};
let numH = {{numH}};
let size = [numW,numH];
let options = new Map();
// считываем материал
let materialID = ezfc_functions.get_value_from(1927, true)[0];
// Считываем параметры резки
let cutID = 'isCutManual';
if (cutID == 'isCutManual') {
    options.set(cutID,true);
}

let backgroundID = ezfc_functions.get_value_from(1934, true)[0];
if (backgroundID == 'isUVPrint') {
    // считываем цветность печати
    let color = ezfc_functions.get_value_from(1936, true)[0];
    options.set(backgroundID ,{
        'printerID':'PrintUV',
        'resolution':1,
        'surface':'isPlain',
        'color':color
    })
}

if (backgroundID == 'isECOPrint') {
    let sizePrint = [...size];
    if (ezfc_functions.get_value_from(2318,true)[0] == '1') {
        sizePrint = [...[{{numPrintW}},{{numPrintH}}]]
    }
    options.set('isPrint',{
        'printerID':'Technojet160ECO',
        'resolution':1,
        'surface':'isPlain',
        'color':'4+0',
        'size':sizePrint
    })
    let edge = ezfc_functions.get_value_from(1938, true)[0];
    options.set('isEdge',edge);
    // считываем параметры ламинации, если заданы
    let laminatID = ezfc_functions.get_value_from(1937, true)[0];
    if (laminatID != 'No') {options.set('isLamination',laminatID)}
}

if (backgroundID == 'isLatexPrint') {
    let sizePrint = [...size];
    if (ezfc_functions.get_value_from(2318,true)[0] == '1') {
        sizePrint = [...[{{numPrintW}},{{numPrintH}}]]
    }
    options.set('isPrint',{
        'printerID':'HPLatex335',
        'resolution':1,
        'surface':'isPlain',
        'color':'4+0',
        'size':sizePrint
    })
    let edge = ezfc_functions.get_value_from(1938, true)[0];
    options.set('isEdge',edge);
};

if (backgroundID == 'isBackgroundFilm') {
    let materialBackgroundFilmID = ezfc_functions.get_value_from(1949,true)[0];
    let sizeBackgroundFilm = [...size];
    if (ezfc_functions.get_value_from(2318,true)[0] == '1') {
        sizeBackgroundFilm = [...[{{numPrintW}},{{numPrintH}}]]
    }
    if (materialBackgroundFilmID != '0') {
        let edge = ezfc_functions.get_value_from(1938, true)[0];
        options.set('isBackgroundFilm',{
            'materialID':materialBackgroundFilmID,
            'isEdge':edge,
            'size':sizeBackgroundFilm
        });
    }
}

let materialApplicationFilmID = ezfc_functions.get_value_from(1940, true)[0];
if (materialApplicationFilmID != '0') {
    let color = ezfc_functions.get_value_from(1943, false);
    let sizeApplication = [{{numApplicationW}},{{numApplicationH}}];
    let sizeApplicationItem = {{numSizeItem}};
    let densityApplication = {{numDensity}};
    let applicationDifficulty = {{dpdFilmDifficulty}};
    options.set('isFilm',{
        'materialID':materialApplicationFilmID,
        'size':sizeApplication,
        'sizeItem':sizeApplicationItem,
        'density':densityApplication,
        'difficulty':applicationDifficulty,
        'color':color
    });
}

let numTypePocket = ezfc_functions.get_value_from(2091);
let pockets = new Array();
if (numTypePocket > 0) {
    let pocketID = ezfc_functions.get_value_from(2014, true)[0];
    let numPocket = ezfc_functions.get_value_from(2093);
    pockets.push({'n':numPocket, 'size':'', 'pocketID':pocketID});
}
if (numTypePocket > 1) {
    let pocketID = ezfc_functions.get_value_from(2096, true)[0];
    let numPocket = ezfc_functions.get_value_from(2095);
    pockets.push({'n':numPocket, 'size':'', 'pocketID':pocketID});
}
if (numTypePocket > 2) {
    let pocketID = ezfc_functions.get_value_from(2319, true)[0];
    let numPocket = ezfc_functions.get_value_from(2322);
    pockets.push({'n':numPocket, 'size':'', 'pocketID':pocketID});
}
if (numTypePocket > 3) {
    let pocketID = ezfc_functions.get_value_from(2320, true)[0];
    let numPocket = ezfc_functions.get_value_from(2323);
    pockets.push({'n':numPocket, 'size':'', 'pocketID':pocketID});
}
if (numTypePocket > 4) {
    let pocketID = ezfc_functions.get_value_from(2321, true)[0];
    let numPocket = ezfc_functions.get_value_from(2324);
    pockets.push({'n':numPocket, 'size':'', 'pocketID':pocketID});
}
options.set('isPocket',pockets);
options.set('Material','isMaterial');

// производим расчет стоимости печати
try {
    marginMin = insaincalc.common.marginMin;
    let calcCost = insaincalc.calcTablets({{numN}},size,materialID,options,{{rdoModeProduction}});
    // извлекли цену и округлили до нужной точности
    PriceTotalManager = insaincalc.round(calcCost.price,{{numN}});
    // извлекли себестоимость
    PriceTotalDiscount = calcCost.cost * (1+marginMin);
    // извлекли вес
    WeightTotal = calcCost.weight;
    // извлекли срок изготовления
    timeReady = insaincalc.timeToWords(calcCost.timeReady);
    dateReady = insaincalc.calcDateReady(calcCost.timeReady);
    dateStart = dateReady[0];
    dateFinish = dateReady[1];

    document.getElementsByClassName('htmTime')[0].getElementsByTagName('div')[0].innerHTML = 'Срок '+timeReady;
    document.getElementsByClassName('htmTime')[0].getElementsByTagName('a')[0].setAttribute('data-bs-original-title',"Готовность заказа: "+dateFinish+" При запуске заказа в работу до: "+dateStart);
    // Выведем расход материалов
    if (document.getElementsByClassName('data-material-table').length > 0) {
        document.getElementsByClassName('data-material-table')[0].innerHTML =  insaincalc.showMaterials(calcCost.material);}
} catch(err) {
    price = 0;
    PriceTotalManager = 0;
    PriceTotalDiscount = 0;
    if (err.name == 'ICalcError') {
        document.getElementsByClassName('htmTime')[0].getElementsByTagName('div')[0].innerHTML = 'Ошибка: '+err.message;
    }
}
