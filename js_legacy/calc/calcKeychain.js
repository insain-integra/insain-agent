// Функция расчета стоимости изготовления акриловых брелоков
insaincalc.calcAcrylicKeychain = function calcAcrylicKeychain(n,keychainID,color,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //	keychainID - ID акриловой заготовки
    //  color - одно или двухсторонняя печать
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
        let costInsert = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetInsert = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costKeychainBlank = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

        // добавляем стоимость заготовки
        let keychain = insaincalc.findMaterial("keychain",keychainID);
        costKeychainBlank.cost = keychain.cost * n;
        costKeychainBlank.price = costKeychainBlank.cost * (1 + insaincalc.common.marginMaterial);
        result.material.set(keychainID,[keychain.name,keychain.size,n]);

        // рассчитываем стоимость изготовления бумажной вставки
        let size = keychain.size;
        let sizeInsert = keychain.sizeInsert;
        let sizeItem = Math.min(sizeInsert[0],sizeInsert[1]);
        let density = 0;
        let difficulty = 1;
        let materialID = 'PaperCoated115M';
        let optionsInsert =  new Map();
        optionsInsert.set('isPrint',{'printerID':'KMBizhubC220','color':color});
        optionsInsert.set('isFindMark','true');
        optionsInsert.set('isLenCut',0);

        costInsert = insaincalc.calcSticker(n,sizeInsert,sizeItem,density,difficulty,materialID,optionsInsert,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costInsert.material);

        // рассчитываем стоимость вставки вкладки в брелок
        costSetInsert =  insaincalc.calcSetInsert(n,modeProduction);

        // рассчитываем стоимость упаковки
        let optionsPacking = new Map();
        optionsPacking.set('isPacking','ZipLockAcrylic');
        costPacking =  insaincalc.calcPacking(n,[size[0],size[1],5],optionsPacking,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costPacking.material);

        // итог расчетов
        //полная себестоимость резки
        result.cost = costInsert.cost
            + costSetInsert.cost
            + costKeychainBlank.cost
            + costPacking.cost;
        // цена с наценкой
        result.price = (costInsert.price
            + costSetInsert.price
            + costKeychainBlank.price
            + costPacking.price) * (1 + insaincalc.common.marginAcrylicKeychain);
        // время затраты
        result.time = costInsert.time
            + costSetInsert.time
            + costKeychainBlank.time
            + costPacking.time;
        //считаем вес в кг.
        result.weight = costInsert.weight
            + costKeychainBlank.weight
            + costPacking.weight;
        result.timeReady = result.time + Math.max(costInsert.timeReady,
            costSetInsert.timeReady,
            costPacking.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};