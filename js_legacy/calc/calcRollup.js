// Функция расчета прессвола
insaincalc.calcRollup = function calcRollup(n,rollupID,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  rollupID - тип роллапа
    //  materialID - материал баннера на роллап
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
    let rollup = insaincalc.findMaterial("presswall",rollupID);
    let material = insaincalc.findMaterial("roll",materialID);
    let printerID = "TechnojetXR720";
    try {
        baseTimeReady = [40,24,8];
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
        let costBanner = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costShipment = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costInstall = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costMaterials = 0;
        // Считаем роллап
        costMaterials += n * rollup.cost;
        result.weight += n * rollup.weight;
        result.material.set(rollupID,[rollup.name,rollup.sizeBanner,n]);
        // Считаем доставку роллапа
        costShipment = insaincalc.calcShipment(n,rollup.size,rollup.weight,'Own');
        // Добавляем печать постера в роллап
        if (materialID != "") {
            options.set('isJoing',1);
            costBanner = insaincalc.calcPrintRoll(n, rollup.sizeBanner, materialID, printerID, options, modeProduction = 1);
            costInstall.time = 0.5;
            costInstall.cost = costInstall.time * insaincalc.common.costOperator;
            costInstall.price = costInstall.cost * (1 + insaincalc.common.marginOperation);
        }
        result.material = insaincalc.mergeMaps(result.material,costBanner.material);
        // окончательный расчет
        result.cost = costInstall.cost + costBanner.cost + costShipment.cost + costMaterials; //себестоимость тиража
        result.price = (costInstall.price +costBanner.price + costShipment.price)*(1+insaincalc.common.marginRollup) +
            costMaterials * (1+insaincalc.common.marginMaterial + insaincalc.common.marginRollup); //цена тиража
        result.time =  Math.ceil((costInstall.time +costBanner.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(baseTimeReady,costBanner.timeReady); // время готовности
        result.weight += costBanner.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};