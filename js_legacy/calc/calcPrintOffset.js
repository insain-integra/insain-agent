// Функция расчета стоимости офсетной печати
insaincalc.calcPrintOffset = function calcPrintOffset(numSheet,sizeSheet,color,materialID,modeProduction = 1) {
    //Входные данные
    //	numSheet - кол-во листов печати
    //	sizeSheet - размер листов, [ширина, высота]
    //	color - цветность печати, вида '4+0'
    //	materialID - материал изделия в виде ID из данных материалов
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    let printerID = 'OffsetPrint';
    let printer = insaincalc.printer[printerID];
    let material = insaincalc.sheet.Paper[materialID];
    let baseTimeReady = printer.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    // проверяем помещается ли материал в принтер
    try {
        margins = [0,0,0,0];
        interval = 0;
        if (color != '0+0') {
            margins=[2,2,2,2];
            interval=4;
        }
        let layoutOnSRA2 = insaincalc.calcLayoutOnSheet(sizeSheet, printer.maxSize,margins, interval);
        let numSheetSRA2 = Math.ceil(numSheet/layoutOnSRA2.num);
        // расчет стоимости бумаги
        let idx = printer.costPaper.findIndex(item => item[1] >= material.density);
        let costSheet = printer.costPaper[idx][2];
        let nameMaterial = printer.costPaper[idx][0];
        let adjustPaper = (color != '0+0') ? printer.adjustPaper : 0;
        let costPaper = (adjustPaper + numSheetSRA2) * costSheet;
        // если цветность задана то считаем печать
        let costOffsetForm = 0;
        let costPrepare = 0;
        let costPrint = 0;
        if (color != '0+0') {
            // расчет печати
            let doubleSide = ((color == '1+0') || (color == '4+0')) ? 1 : 2;
            // расчет стоимости самой печати исходя из цветности
            costPrint = printer.costAdjust + (printer.costPreparePrint + printer.costPrint * numSheetSRA2) * (1 + 0.66 * (doubleSide-1));
            // расчет стоимости подготовки к печати
            costPrepare = printer.costPrepare * doubleSide;
            // расчет стоимости форм
            let numColor = Number(color[0]) + Number(color[2]);
            costOffsetForm = printer.costOffsetForm * numColor;
        }
        // расчет стоимости резки
        let costCut = printer.costPrepareCut + Math.ceil(numSheetSRA2/900) * printer.costCut;
        // расчет времени и стоимости подготовки к печати
        let timePrepare = printer.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeOperator = timePrepare;
        let costOperator = timeOperator * ((printer.costOperator > 0) ? printer.costOperator : insaincalc.common.costOperator);
        // окончательный расчет
        result.cost = costOperator + costPaper + costOffsetForm + costPrepare + costPrint + costCut; //полная себестоимость печати тиража
        result.price = costOperator * (1 + insaincalc.common.marginOperation + insaincalc.common.marginPrintOffset)
            + (costPaper + costOffsetForm + costPrepare + costPrint + costCut) * (1 + insaincalc.common.marginMaterial + insaincalc.common.marginPrintOffset);
        result.time = Math.ceil(timeOperator * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = insaincalc.calcWeight(numSheet,material.density,material.thickness,sizeSheet,material.unitDensity)  //считаем вес в кг.
        result.material.set('OffsetPaper', [nameMaterial, printer.maxSize, adjustPaper + numSheetSRA2]);
        return result;
    } catch (err) {
        throw err
    }
};


// Функция расчета стоимости сборников на офсетной печати
insaincalc.calcPrintOffsetPromo = function calcPrintOffsetPromo(numSheet,offsetpromoID,modeProduction = 1) {
    //Входные данные
    //	numSheet - кол-во листов печати
    //	offsetpromoID - ID сборника
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    let material = insaincalc.findMaterial('sheet',offsetpromoID);
    let baseTimeReady = insaincalc.common.baseTimeReadyPrintOffsetPromo[Math.ceil(modeProduction)];
    // проверяем помещается ли материал в принтер
    try {
        numSet = Math.ceil(numSheet/material.numSheet); // кол-во сборных тиражей
        // расчет стоимости тиража
        let costMaterials = numSet * material.cost;
        result.weight =  insaincalc.calcWeight(numSet * material.numSheet, material.density, 0, material.sizeSheet, 'гм2');
        result.material.set(offsetpromoID,[material.name,material.sizeSheet, numSet * material.numSheet]);
        let sizeShipment = [material.sizeSheet[0],material.sizeSheet[1], numSet * material.numSheet * material.density/80/10];
        // Считаем доставку
        let costShipment = insaincalc.calcShipment(1,sizeShipment,result.weight,'Luch');
        // окончательный расчет
        result.cost = costShipment.cost + costMaterials; //себестоимость тиража
        result.price = costShipment.price * (1+insaincalc.common.marginOffsetPromo) +
            costMaterials * (1+insaincalc.common.marginMaterial + insaincalc.common.marginOffsetPromo); //цена тиража
        result.time =  0; // время изготовления
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};