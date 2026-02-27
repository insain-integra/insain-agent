// Функция расчета стоимости печати на лазерном принтере
insaincalc.calcPrintLaser = function calcPrintLaser(numSheet,sizeSheet,color,materialID,printerID,modeProduction = 1) {
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
    let printer = insaincalc.printer[printerID];
    let material = insaincalc.sheet.Paper[materialID];
    let timePrepare = printer.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let baseTimeReady = printer.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];

    // проверяем помещается ли материал в принтер
    try {
        // если цветность задана то считаем
        if (color != '0+0') {
            let layoutOnPrinter = insaincalc.calcLayoutOnSheet(sizeSheet, printer.maxSize);
            // рассчитываем коэффициент размера бумаги SRА4 или SRA3
            let coeffSizeSheet = 1;
            let layoutOnHalfSheet = insaincalc.calcLayoutOnSheet(sizeSheet, [printer.maxSize[0],printer.maxSize[1]/2]);
            if (layoutOnHalfSheet.num > 0) {coeffSizeSheet = 0.5}
            if (layoutOnPrinter.num == 0) {throw (new ICalcError('Размер изделия больше допустимого'))}
                    // расчет лазерной печати
            let sheetsPerHour = (printer.sheetsPerHour.find(item => item[0] >= material.density))[1]; //находим скорость печати для данного материала
            let defects = (printer.defects.find(item => item[0] >= numSheet))[1]; //находим процент брака от тиража
            defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
            let doubleSide = ((color == '1+0') || (color == '4+0')) ? 1 : 2;
            let timePrint = Math.ceil(numSheet * (1 + defects)) / sheetsPerHour * coeffSizeSheet * doubleSide + timePrepare; //считаем время на печать с учетом времени на подготовку к запуску
            let timeOperator = timePrint * 0.5 * (1 + defects) + timePrepare; //считаем время затраты оператора печати
            let costPrinterDepreciationHour = printer.cost / printer.timeDepreciation / printer.workDay / printer.hoursDay; //стоимость часа амортизации оборудования
            // расчет стоимости самой печати исходя из цветности
            let costPrintSheet = 0;
            costPrintSheet += color == '1+0' ? printer.costPrintSheet[0] : 0;
            costPrintSheet += color == '1+1' ? 2 * printer.costPrintSheet[0] : 0;
            costPrintSheet += color == '4+0' ? printer.costPrintSheet[1] : 0;
            costPrintSheet += color == '4+1' ? printer.costPrintSheet[0] + printer.costPrintSheet[1] : 0;
            costPrintSheet += color == '4+4' ? 2 * printer.costPrintSheet[1] : 0;
            if (costPrintSheet == 0) {
                throw (new ICalcError('Не задана или неверно задана цветность печати'))
            }
            let costPrint = costPrinterDepreciationHour * timePrint + costPrintSheet * coeffSizeSheet * numSheet * (1 + defects); //считаем стоимость использование оборудование включая амортизацию
            let costOperator = timeOperator * ((printer.costOperator > 0) ? printer.costOperator : insaincalc.common.costOperator);

            // окончательный расчет
            result.cost = costPrint + costOperator; //полная себестоимость печати тиража
            result.price = costPrint * (1 + insaincalc.common.marginMaterial + insaincalc.common.marginPrintLaser) +
                costOperator * (1 + insaincalc.common.marginOperation + insaincalc.common.marginPrintLaser);
            result.time = Math.ceil(timePrint * 100) / 100;
            result.timeReady = result.time + baseTimeReady; // время готовности
            result.weight = insaincalc.calcWeight(numSheet,material.density,material.thickness,sizeSheet,material.unitDensity)  //считаем вес в кг.
        } else {
            result.weight = insaincalc.calcWeight(numSheet,material.density,material.thickness,sizeSheet,material.unitDensity)  //считаем вес в кг.
        }
        return result;
    } catch (err) {
        throw err
    }
};