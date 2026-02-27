// Функция расчета стоимости изготовления шильдов с сублимацией
insaincalc.calcShildSublimaton = function calcShildSublimaton(n,size,shape,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
    //  shape - форма изделия,
    //	materialID - материал изделия в виде ID из данных материалов
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
    try {
        let costHeatPress = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCut = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

        costHeatPress = insaincalc.calcHeatPress(n,size,transferID,itemID,options,modeProduction = 1);
        result.material = insaincalc.mergeMaps(result.material, costHeatPress.material);
        // рассчитываем кол-во листов алюминия
        let sizeSheet = costPrint.material.get(materialPrintID)[1];
        let sizeCutSheet = [sizeSheet[0] - 10, sizeSheet[1] - 10]; //подрезаем листы для лучшего размещения на виниле
        let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeSheet, margins, interval);
        let numSheet = Math.ceil(n/layoutOnSheet.num);
        // рассчитываем стоимость алюминия и стоимость нарезки
        let cutterID = 'KWTrio3026';
        let optionsCut = new Map();
        optionsCut.set('Material','isMaterial');
        costCut = insaincalc.calcCutRoller(numSheet,sizeCutSheet,materialID,cutterID,optionsCut,modeProduction)
        result.material = insaincalc.mergeMaps(result.material, costCut.material);
        // рассчитываем стоимость резки листов на конечные изделия
        switch (shape) {
            case 'rectangular':
                cutterID = 'Ideal1046';
                costCutSaber = insaincalc.calcCutSaber(numSheet,size,sizeSheet,materialID,cutterID,modeProduction);
                break;
            default:
                costPress = insaincalc.calcManualPress(n,materialID,modeProduction);
                break;
        }
        // Рассчитываем стоимость дополнительных опций
        let costOptions = {cost:0,price:0,time:0};
        // добавляем к цене нумерацию
        if (options.has('isNumber')) {
            costOptions.cost += 0.75*n;
            costOptions.price += 1.0*n;
            costOptions.time += 0.05;
        }
        // добавляем к цене штрихкод
        if (options.has('isBarcode')) {
            costOptions.cost += 1.0*n;
            costOptions.price += 2.0*n;
            costOptions.time += 0.1;
        }
        // добавляем к цене переменные данные
        if (options.has('isVariables')) {
            costOptions.cost += 3.0*n;
            costOptions.price += 5.0*n;
            costOptions.time += 0.1;
        }
        // добавляем к цене скругление
        if (options.has('isRounding')) {
            let costRounding = insaincalc.calcRounding(n,materialID,modeProduction);
            costOptions.cost += costRounding.cost;
            costOptions.price += costRounding.price;
            costOptions.time += costRounding.time;
        }
        // рассчитываем стоимость упаковки
        if (options.has('isPacking')) {costPacking =  insaincalc.calcPacking(n,[size[0],size[1],1],options,modeProduction)}
        result.material = insaincalc.mergeMaps(result.material, costPacking.material);
        let baseTimeReady = Math.max(costPrint.timeReady,costCut.timeReady,costRoll.timeReady,costForm.timeReady);

        // итог расчетов
        //полная себестоимость резки
        result.cost = Math.ceil(costPrint.cost
            + costRoll.cost
            + costCut.cost
            + costCutSaber.cost
            + costPress.cost
            + costOptions.cost
            + costForm.cost
            + costPacking.cost);
        // цена с наценкой
        result.price = Math.ceil(costPrint.price
            + costRoll.price
            + costCut.price
            + costCutSaber.price
            + costPress.price
            + costOptions.price
            + costForm.price
            + costPacking.price) * (1 + insaincalc.common.marginBadge);
        // времязатраты
        result.time = Math.ceil((costPrint.time
            + costRoll.time
            + costCut.time
            + costCutSaber.time
            + costPress.time
            + costOptions.time
            + costForm.time
            + costPacking.time)* 100) / 100;
        //считаем вес в кг.
        result.weight = Math.ceil((costPrint.weight
            + costCut.weight
            + costPacking.weight)* 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};