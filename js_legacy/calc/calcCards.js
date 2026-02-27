// Функция расчета изготовления пластиковы карт
insaincalc.calcPlasticCards = function calcPlasticCards(n,color,materiaID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  color - цветность печати
    //  materiaID - тип карты
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
        let baseTimeReady = insaincalc.common.baseTimeReady;
        let tool = insaincalc.cards.PlasticCards;
        if (tool.baseTimeReady != undefined) {
            baseTimeReady = tool.baseTimeReady;
        }
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
        let card = insaincalc.cards.PlasticCards.costPlastic[materiaID];
        let idx = (card.cost.findIndex(item => item[0] > n));
        if (idx == -1) {idx = card.cost.length - 1} else {idx -= 1}
        let costMaterial = card.cost[idx][1] * n;
        result.weight = card.weight * n / 1000; //считаем вес в кг.
        // Рассчитываем стоимость дополнительных опций
        let costOptions = 0;
        if (options.has('isLamination')) {
            costOptions += tool.costLamination[options.get('isLamination')];
        }
        if (options.has('isNumber')) {costOptions += tool.costNumber}
        if (options.has('isBarcode')) {costOptions += tool.costBarcode}
        if (options.has('isEmbossingFoil')) {costOptions += tool.costEmbossingFoil}
        if (options.has('isMagneticStripeHiCo')) {costOptions += tool.costMagneticStripeHiCo}
        if (options.has('isEmbossing')) {costOptions += tool.costEmbossing}
        if (options.has('isSignatureStrip')) {costOptions += tool.costSignatureStrip}
        if (options.has('isScratchPanel')) {costOptions += tool.costScratchPanel}
        costOptions *= n;
        let costShipment = tool.costShipment;
        result.cost = costOptions + costMaterial + costShipment;//полная себестоимость
        result.price = result.cost * (1 + insaincalc.common.marginMaterial) ;
        result.time = tool.timePrepare;
        result.timeReady = baseTimeReady;
        result.material.set(materiaID,[card.name,card.size,n]);
        return result;
    } catch(err) {
        throw err
    }
};