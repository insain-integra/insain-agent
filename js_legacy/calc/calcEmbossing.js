// Функция расчета стоимости тиснения
insaincalc.calcEmbossing = function calcEmbossing(n, size, materialID, embossingID, itemID, sizeItem, options, modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	size - размер клише
    //	materialID - материал поверхности
    //  embossingID - вид тиснения, блинт/фольга
    //  itemID - тип изделия
    //  sizeItem - размер изделия
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
        // Считываем данные по оборудованию и материалам
        let costEmbossing = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCliche = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costShipment = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let baseTimeReady = insaincalc.common.baseTimeReady;
        // Считываем данные по оборудованию и материалам
        let tool = insaincalc.tools['Embossing'];
        if (tool.baseTimeReady != undefined) {
            baseTimeReady = tool.baseTimeReady;
        }
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];

        // расчет клише
        if (options.has('isCliche')) {
            costCliche = insaincalc.calcCliсhe(size, options, modeProduction);
        }
        result.material = insaincalc.mergeMaps(result.material, costCliche.material);
        // расчет стоимости тиснения
        let timePrepare = tool.timePrepare * modeProduction; // время подготовки к прессованию
        // стоимость работы оператора
        let costOperator = tool.timePrepare * modeProduction * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        // стоимость изготовления клише
        let idx = (tool.cost[embossingID].cost.findIndex(item => item[0] > n));
        costEmbossing.cost = Math.max(tool.cost[embossingID].minCost,tool.cost[embossingID].cost[idx][1] * n) + costOperator;
        costEmbossing.price = costEmbossing.cost * (1 + insaincalc.common.marginMaterial) + costOperator * (1 + insaincalc.common.marginOperation);
        costEmbossing.time = timePrepare;

        // Считаем доставку груза на тиснение
        switch (itemID) {
            case 'diary': sizeItem = [150,210,20]; weightItem = 100; break;
            case 'planning': sizeItem = [210,100,10]; weightItem = 100; break;
            case 'cardholder': sizeItem = [100,100,5]; weightItem = 20; break;
            default: break;
        }
        costShipment = insaincalc.calcShipment(n,sizeItem,weightItem,'Own');

        // окончательный расчет
        result.cost = costCliche.cost + costEmbossing.cost + costShipment.cost; //полная себестоимость печати тиража
        result.price = (costCliche.price + costEmbossing.price + costShipment.price) * (1 + insaincalc.common.marginEmbossing);
        result.time =  costCliche.time + costEmbossing.time + costShipment.time;
        result.timeReady = result.time + Math.max(costCliche.timeReady,baseTimeReady); // время готовности
        result.weight = costCliche.weight;
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета стоимости клише
insaincalc.calcCliсhe = function calcCliсhe(size, options,modeProduction = 1) {
    //Входные данные
    //	size - размер клише
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
        let costShipment = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costMaterial = 0;
        let baseTimeReady = insaincalc.common.baseTimeReady;
        // Считываем данные по оборудованию и материалам
        let tool = insaincalc.tools['Cliche'];
        if (tool.baseTimeReady != undefined) {
            baseTimeReady = tool.baseTimeReady;
        }
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];

        // рассчитываем стоимость и время изготовления клише
        let timePrepare = tool.timePrepare * modeProduction; // время подготовки к прессованию
        // стоимость работы оператора
        let costOperator = tool.timePrepare * modeProduction * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        // стоимость изготовления клише
        costMaterial = Math.max(tool.cost * size[0] * size[1] / 100, tool.minCostCliche);

        result.weight = tool.weight * size[0] * size[1] / 100000; //считаем вес в кг.
        // Считаем доставку клише
        costShipment = insaincalc.calcShipment(1,size,result.weight,'Own');

        result.cost = costMaterial + costShipment.cost + costOperator;//полная себестоимость
        result.price = costShipment.price + costMaterial * (1 + insaincalc.common.marginMaterial) + costOperator * (1 + insaincalc.common.marginOperation);
        result.time = timePrepare;
        result.timeReady = timePrepare + baseTimeReady;
        result.material.set('cliche',['Клише',size,1]);

        return result;
    } catch(err) {
        throw err
    }
};