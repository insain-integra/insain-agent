// Функция расчета прессвола
insaincalc.calcPresswall = function calcPresswall(n,presswallID,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  presswallID - тип прессвола
    //  materialID - материал баннера на прессвол
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
    let presswall = insaincalc.findMaterial("presswall",presswallID);
    let material = insaincalc.roll.Banner[materialID];
    let toolID = "DWE4257";
    let printerID = "TechnojetXR720";
    try {
        // считаем размер и кол-во сегментов исходя из размера баннера на прессвол
        let costCut = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBanner = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costMaterials = 0;
        let costRent = 0;
        let costBag = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        // Считаем изготовление прессвола
        if (options.has('isPresswall')) {
            for (itemID in presswall) {
                item = insaincalc.findMaterial("presswall",itemID);
                if (item != undefined) {
                    costMaterials += n * presswall[itemID] * item.cost;
                    result.weight += n * presswall[itemID] * item.weight;
                    let sizeItem = item.size;
                    if (sizeItem == undefined) {sizeItem = 0}
                    result.material.set(itemID,[item.name,sizeItem,n * presswall[itemID]])
                }
            }
            costCut = insaincalc.calcCutProfile(n, presswall.segments, toolID, modeProduction);
            result.material = insaincalc.mergeMaps(result.material, costCut.material);
        }
        // Добавляем аренду прессвола
        if (options.has('isRent')) {
            let numDays = options.get('isRent')
            costRent = n * 400 * numDays;
        }
        // Добавляем печать баннера
        if (materialID != "") {
            costBanner = insaincalc.calcPrintRoll(n, presswall.sizeBanner, materialID, printerID, options, modeProduction = 1);
        }
        result.material = insaincalc.mergeMaps(result.material,costBanner.material);
        // Добавляем пошив чехла
        if (options.has('isBag')) {
            bagID = options.get('isBag')
            bag = insaincalc.findMaterial("presswall",bagID);
            if (bag != undefined) {
                let CoversMaterialID = 'Oxford600D'
                costBag = insaincalc.calcSewingCovers(n,bag.size,CoversMaterialID,modeProduction);
            }
        }
        result.material = insaincalc.mergeMaps(result.material,costBag.material);
        // окончательный расчет
        result.cost = costCut.cost + costBanner.cost + costMaterials + costBag.cost + costRent//себестоимость тиража
        result.price = (costCut.price +costBanner.price + costBag.price)*(1+insaincalc.common.marginPresswall) +
            (costMaterials + costRent) * (1+insaincalc.common.marginMaterial + insaincalc.common.marginPresswall); //цена тиража
        result.time =  Math.ceil((costCut.time +costBanner.time + costBag.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costCut.timeReady,costBanner.timeReady,costBag.timeReady); // время готовности
        result.weight += costCut.weight + costBanner.weight + costBag.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};