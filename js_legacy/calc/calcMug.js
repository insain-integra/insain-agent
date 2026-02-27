// Функция расчета стоимости кружек с сублимационной печатью
insaincalc.calcMug = function calcMug(n,mugID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //  mugID - вид кружки
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
    // Считываем параметры материалов и оборудование
    let transferID = "sublimation";
    let itemID = "mug";
    let size = [214, 82];
    try {
        let mug = insaincalc.mug.Mug[mugID];
        let heatpress = insaincalc.heatpress["EconopressMUGH"];
        if (n < mug.minNum) {throw (new ICalcError(`Минимальный объем заказа данного вида кружек ${mug.minNum} шт`))}

        let defects = (heatpress.defects.find(item => item[0] >= n))[1];
        defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
        let numWithDefects = Math.round(n*(1+defects)); // кол-во с учетом брака
        let costHeatPress = insaincalc.calcHeatPress(n,size,transferID,itemID,options,modeProduction);
        let timeShipment = 0; // время доставки
        let costShipment = 0; // стоимость доставки
        if (mug.minNum > 0) { // если минимальное кол-во больше нуля, значит остаток на складе не поддерживается и нужно закупать
            timeShipment = 16; // время доставки
            costShipment = 500; // стоимость доставки
        }
        // время распаковки и упаковки изделий
        let timePacking = 0;
        if (options.has('isPacking')) {
            timePacking += 0.006 * n;
        }

        // время подготовки к печати, если макеты все разные то добавляем по 1 мин
        let timePrepare = 0;
        if (options.has('isDifferent')) {
            timePrepare += 1/60 * n;
        }

        let weightMug = mug.weight * n;
        let costMug = mug.cost * numWithDefects; // кол-во кружек с учетом брака
        let timeOperator = timePacking + timePrepare;
        let costOperator = timeOperator * insaincalc.common.costOperator;
        // итог расчетов
        // расход материалов
        result.material = costHeatPress.material;
        result.material.set(mug.name,[mug.size,numWithDefects]);
        // полная себестоимость резки
        result.cost = costHeatPress.cost + costMug;
        // цена с наценкой
        result.price = (costHeatPress.price +
            costMug * (1 + insaincalc.common.marginMaterial) +
            (costShipment + costOperator) * (1 + insaincalc.common.marginOperation)) * (1 + insaincalc.common.marginMug);
        // времязатраты
        result.time = Math.ceil((timeOperator + costHeatPress.time) * 100) / 100;
        //считаем вес в кг.
        result.weight = Math.ceil((costHeatPress.weight + weightMug) * 100) / 100;
        result.timeReady = result.time + timeShipment + costHeatPress.timeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};