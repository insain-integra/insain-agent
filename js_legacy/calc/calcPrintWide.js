// Функция расчета стоимости печати на широкоформатном принтере
insaincalc.calcPrintWide = function calcPrintWide(n,size,materialID,printerID,options,modeProduction = 1) {
    //Входные данные
    //	size - размер печати, [ширина, длинна]
    //	materialID - материал изделия в виде ID из данных материалов
    //	printerID - принтер для печати
    //  options - дополнительные опции в виде коллекция ключ/значение
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
    let material = insaincalc.roll.Film[materialID];
    if (material == undefined) {material = insaincalc.roll.Banner[materialID]}
    if (material == undefined) {material = insaincalc.roll.Paper[materialID]}
    let baseTimeReady = printer.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    let timePrepare = printer.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let minVolPrint = printer.minVolPrint;
    if (minVolPrint == undefined) {minVolPrint = 0};
    try {
        // расчет печати
        let defects = (printer.defects.find(item => item[0] >= n))[1]; //находим процент брака от тиража
        defects +=  modeProduction > 1 ? defects * (modeProduction-1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        let volPrint = size[0] * size[1] * (1 + defects) / 1000000; // объем печати в м2
        if (volPrint <= minVolPrint) {volPrint = minVolPrint}
        let timePrint = volPrint / printer.meterPerHour  + timePrepare; // время печати
        let timeOperator = (timePrint + timePrepare) * 0.5; //считаем время затраты оператора печати
        let costDepreciationHour = printer.cost / printer.timeDepreciation / printer.workDay / printer.hoursDay; //стоимость часа амортизации оборудования
        // расчет стоимости самой печати исходя из цветности
        let costPrint = costDepreciationHour * timePrint + printer.costPrint * volPrint; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((printer.costOperator > 0) ? printer.costOperator : insaincalc.common.costOperator);
        // окончательный расчет
        result.cost = Math.ceil(costPrint + costOperator); //себестоимость печати
        result.price = Math.ceil(result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginPrintWide));
        result.time =  Math.ceil(timePrint * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.material.set(materialID,[material.name,material.size,volPrint/material.size[0]]);

        return result;
    } catch (err) {
        throw err
    }
};