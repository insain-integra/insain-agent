// Функция расчета стоимости изготовления полимерных наклеек
insaincalc.calcPolySticker = function calcPolySticker(n,size,difficulty,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
    //  difficulty - сложность формы для резки, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
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
    // Считываем параметры материалов и оборудование
    let tool = insaincalc.tools['EpoxyCoating'];
    let baseTimeReady = tool.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    try {
        // sizeItem - средний размер элементов/букв для резки внутри наклейки
        let sizeItem = size[0];
        // density - плотность заполнения элементами в наклейке от 0 до 1 (иначе от 0 до 100%).
        let density = 0;
        // определяем кол-во брака для полимерной заливки
        let defects = (tool.defects.find(item => item[0] >= n))[1];
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        let n_stickers = Math.ceil(n * (1 + defects));
        let costSticker = insaincalc.calcSticker(n_stickers,size,sizeItem,density,difficulty,materialID,options,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSticker.material);
        let optionsEpoxy = new Map();
        let costEpoxy = insaincalc.calcEpoxy(n,size,difficulty,optionsEpoxy,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costEpoxy.material);

        // итог расчетов
        result.cost = Math.ceil(costSticker.cost + costEpoxy.cost);//полная себестоимость резки
        result.price = Math.ceil(costSticker.price + costEpoxy.price) * (1 + insaincalc.common.marginStickerPoly);
        result.time = Math.ceil((costEpoxy.time + costSticker.time) * 100) / 100;
        result.weight = Math.ceil((costEpoxy.weight + costSticker.weight) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета стоимости изготовления полимерных стикерпаков
insaincalc.calcPolyStickerPack = function calcPolyStickerPack(n,size,stickers,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во стикерпаков
    //	size - размер стикерпака, [ширина, высота]
    //  stickers - массив параметров наклеек стикерпака, в виде словаря {size,difficulty}
    //  size - размеры наклейки
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
    // Считываем параметры материалов и оборудование
    let tool = insaincalc.tools['EpoxyCoating'];
    let baseTimeReady = tool.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    try {
        let sizeItem = 0;
        let density = 0;
        let difficulty = 0;
        let areaItem = 0;
        let numStickers = stickers.length;
        for (sticker of stickers) {
            sizeItem += (sticker.size[0] + sticker.size[1]) / 2;
            difficulty += sticker.difficulty;
            density += sticker.size[0] * sticker.size[1];
        }
        // sizeItem - средний размер элементов/букв для резки внутри наклейки
        sizeItem /= numStickers;
        // Если фон остается, то считаем что средний размер элементов/букв в 3 раза меньше
        if (options.has('isBackground')) {
            if (options.get('isBackground')) {
                sizeItem /= 3;
            }
        }
        // difficulty - сложность формы наклейки для резки, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
        // высчитываем среднюю сложность и дополняем сложность тем, что это стикерпак *1.1
        difficulty /= numStickers * 1.1;
        // sizeItem - средняя площадь одной наклейки в стикерпаке
        areaItem = density / numStickers;
        // density - плотность заполнения элементами в наклейке от 0 до 1 (иначе от 0 до 100%).
        density /= size[0] * size[1];


        // определяем кол-во брака для полимерной заливки
        let defects = (tool.defects.find(item => item[0] >= n))[1];
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        let n_stickers = Math.ceil(n * (1 + defects));
        // расчет печати наклеек
        let costSticker = insaincalc.calcSticker(n_stickers,size,sizeItem,density,difficulty,materialID,options,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSticker.material);
        // расчет нарезки на отдельные стикерпаки
        //let optionsCut = new Map();
        //let cutterID = 'KWTrio3026';
        //let costCut = insaincalc.calcCutRoller(n,size,materialID,cutterID,optionsCut,modeProduction);
        let cutterID = 'Ideal1046';
        let margins = [2, 2, 2, 2];
        let interval = 4;
        let numSheet = costSticker.material.get(materialID)[2];
        let sizeSheet = costSticker.material.get(materialID)[1];
        let costCut = insaincalc.calcCutSaber(numSheet,size,sizeSheet,materialID,cutterID,margins,interval,modeProduction);
        // расчет заливки
        let optionsEpoxy = new Map();
        let costEpoxy = insaincalc.calcEpoxy(n * numStickers,[Math.sqrt(areaItem),Math.sqrt(areaItem)],difficulty,optionsEpoxy,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costEpoxy.material);

        // итог расчетов
        result.cost = Math.ceil(costSticker.cost + costEpoxy.cost + costCut.cost);//полная себестоимость резки
        result.price = Math.ceil(costSticker.price + costEpoxy.price + costCut.price) * (1 + insaincalc.common.marginStickerPoly);
        result.time = Math.ceil((costEpoxy.time + costSticker.time + costCut.time) * 100) / 100;
        result.weight = Math.ceil((costEpoxy.weight + costSticker.weight) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};