// Функция расчета стоимости изготовления табличек
insaincalc.calcTablets = function calcTablets(n,size,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
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

    try {
        let costLaser = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costMilling = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSticker = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costUVPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCutManual = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSublimation = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costManualRoll = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCutBackgroundFilm = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costManualBackgroundRoll = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPockets = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costOptions = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let doubleApplication = 1;
        // рассчитываем стоимость ручной резки
        if (options.has('isCutManual')) {
            let cutterID = options.get('isCutManual');
            costCutManual = insaincalc.calcCutRoller(n, size, materialID, cutterID, options, modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costCutManual.material);
        }
        // рассчитываем стоимость ручной резки на резаке для металла с материалом
        if (options.has('isCutManualMetal')) {
            let cutterID = options.get('isCutManualMetal');
            let margins = [0,0,0,0];
            let interval = 1;
            let sizeSheet = [210,297];
            let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeSheet, margins, interval);
            if (layoutOnSheet.num == 0) {
                sizeSheet = [420,297];
                layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeSheet, margins, interval);
                if (layoutOnSheet.num == 0) {throw (new ICalcError('Изделие не помещается на материал'))}
            }
            let numSheet = n / layoutOnSheet.num;
            costCutManual = insaincalc.calcCutSaber(numSheet,size,sizeSheet,materialID,cutterID,margins,interval,modeProduction);

            let material = insaincalc.findMaterial('hardsheet', materialID);
            let areaMaterial = n * (size[0] + interval) * (size[1] + interval); // площадь расхода материала
            let numMaterialSheet =  areaMaterial / (material.size[0] * material.size[1]); // Сколько листов материала требуется
            costCutManual.cost += numMaterialSheet * material.cost;
            costCutManual.price += numMaterialSheet * material.cost * (1 + insaincalc.common.marginMaterial);
            costCutManual.weight += areaMaterial * material.thickness * material.density / 1000000;
            result.material.set(materialID,[material.name,material.size,numMaterialSheet]);
        }
        // рассчитываем стоимость лазерной резки с материалом
        if (options.has('isCutLaser')) {
            costLaser = insaincalc.calcLaser(n, size, materialID, options, modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costLaser.material);
        }
        // рассчитываем стоимость фрезерной резки с материалом
        if (options.has('isCutMilling')) {
            costMilling = insaincalc.calcMilling(n, size, materialID, options, modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costMilling.material);
        }

        // рассчитываем стоимость сублимационной печати
        if (options.has('isSublimation')) {
            let sizePrint = [210,297];
            let margins = [5,5,5,5];
            let interval = 1;
            let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizePrint, margins, interval);
            if (layoutOnSheet.num == 0) {
                sizePrint = [420,297];
                layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizePrint, margins, interval);
                if (layoutOnSheet.num == 0) {throw (new ICalcError('Изделие не помещается на материал'))}
            }
            let numSheet = Math.ceil(n / layoutOnSheet.num);
            transferID = 'sublimation';
            itemID = 'metal';
            costSublimation = insaincalc.calcHeatPress(numSheet,sizePrint,transferID,itemID,options,modeProduction)
            result.material = insaincalc.mergeMaps(result.material,costSublimation.material);
        }

        // рассчитываем стоимость нанесения УФ-печати
        if (options.has('isUVPrint')) {
            let sizePrint = options.get('isUVPrint')['size'];
            if (sizePrint == undefined) {sizePrint = [...size]}
            let sizeItem = sizePrint;
            costUVPrint = insaincalc.calcUVPrint(n,sizePrint,sizeItem,materialID,options,modeProduction)
            result.material = insaincalc.mergeMaps(result.material,costUVPrint.material);
        }

        // рассчитываем стоимость нанесения пленкой с ЭКО-сольвентной и латексной печатью
        if (options.has('isPrint')) {
            let printerID = options.get('isPrint').printerID;
            let sizePrint = options.get('isPrint')['size'];
            if (sizePrint == undefined) {sizePrint = [...size]}
            doubleApplication = options.get('isPrint')['isDoubleApplication'] ? 2:1;
            costPrint = insaincalc.calcPrintRoll(n * doubleApplication, sizePrint,'ORAJET3640',printerID,options,modeProduction);
            costManualRoll = insaincalc.calcManualRoll(n * doubleApplication,sizePrint,options,modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costPrint.material);
        }

        // рассчитываем стоимость нанесения аппликации
        if (options.has('isFilm')) {
            let paramSticker = options.get('isFilm');
            // расчитываем стоимость нанесения аппликации
            let optionsSticker = options;
            optionsSticker.set('isMountingFilm',true);
            doubleApplication = options.get('isFilm')['isDoubleApplication'] ? 2:1;
            costSticker = insaincalc.calcSticker(n * doubleApplication * paramSticker.color,paramSticker.size,paramSticker.sizeItem,paramSticker.density,
                paramSticker.difficulty,paramSticker.materialID,optionsSticker,modeProduction);
            costManualRoll = insaincalc.calcManualRoll(n * doubleApplication * paramSticker.color,size,options,modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costSticker.material);
        }
        // расчитываем стоимость нанесения фона
        if (options.has('isBackgroundFilm')) {
            let optionsBackground = new Map();
            doubleApplication = options.get('isFilm')['isBackgroundFilm'] ? 2:1;
            optionsBackground.set('isEdge',options.get('isBackgroundFilm')['isEdge']);
            optionsBackground.set('Material','isMaterial');
            let sizeBackgroundFilm = options.get('isBackgroundFilm')['size'];
            if (sizeBackgroundFilm == undefined) {sizeBackgroundFilm = [...size]}
            let cutterID = 'KWTrio3026';
            costCutBackgroundFilm = insaincalc.calcCutRoller(n * doubleApplication,sizeBackgroundFilm,options.get('isBackgroundFilm').materialID,cutterID,optionsBackground,modeProduction);
            costManualBackgroundRoll = insaincalc.calcManualRoll(n * doubleApplication,sizeBackgroundFilm,optionsBackground,modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costCutBackgroundFilm.material);
        }

        // добавляем к цене древко
        if (options.has('isShaft')) {
            let shaftID = options.get('isShaft')['shaftID'];
            let lenShaft = options.get('isShaft')['length'];
            let shaft = '';
            if (shaftID != "") {
                shaft = insaincalc.findMaterial('misc', shaftID)
                if (shaft == undefined) {
                    throw (new ICalcError('Параметры древка не найдены'))
                }
            }
            let clips = insaincalc.findMaterial('misc', 'PlasticClips');
            let timeOperator = 0.13 * n;
            costOptions.cost += (shaft.cost * lenShaft / shaft.length + clips.cost * 2) * n + timeOperator * insaincalc.common.costOperator;
            costOptions.price += (shaft.cost * lenShaft / shaft.length + clips.cost * 2) * (1 + insaincalc.common.marginMaterial) * n
                + timeOperator * insaincalc.common.costOperator * (1 + insaincalc.common.marginOperation);
            costOptions.time +=  timeOperator;
            costOptions.weight += shaft.weight * lenShaft * n;
            result.material.set(shaftID,[shaft.name,shaft.length, lenShaft * n / shaft.length]);
            result.material.set('PlasticClips',[clips.name,0,2 * n]);
        }

        // добавляем к цене карманы
        if (options.has('isPocket')) {
            let pockets = options.get('isPocket');
            pockets.forEach(function(pocket) {
                let costPocket = insaincalc.calcPockets(pocket.n * n, pocket.size, pocket.pocketID, pocket.materialID, pocket.borderID, options, modeProduction)
                costPockets.cost += costPocket.cost;
                costPockets.price += costPocket.price;
                costPockets.time += costPocket.time;
                costPockets.weight += costPocket.weight;
                if (costPocket.timeReady > costPockets.timeReady) {costPockets.timeReady = costPocket.timeReady}
                costPockets.material = insaincalc.mergeMaps(costPockets.material,costPocket.material);
            });
            result.material = insaincalc.mergeMaps(result.material,costPockets.material);
        }
        // рассчитываем стоимость нанесение клеевого слоя
        if ((options.has('isAdhesiveLayer')) && !options.has('isCutLaser'))  { // поставили условие, так как в расчете резке тоже есть учет клеевого слоя
            let adhesiveLayer = options.get('isAdhesiveLayer');
            let idAdhesiveLayer = 'Sheet3M7952';
            switch (adhesiveLayer) {
                case 'AdhesiveLayer50':
                    idAdhesiveLayer = 'Sheet3M7952';
                    break;
                case 'AdhesiveLayer130':
                    idAdhesiveLayer = 'Sheet3M7955';
                    break;
            }
            let materialAdhesiveLayer = insaincalc.findMaterial('misc', idAdhesiveLayer);
            let areaAdhesiveSheet = n * (size[0] + 5) * (size[1] + 5); // Сколько листов скотча требуется
            let numAdhesiveSheet =  areaAdhesiveSheet / (materialAdhesiveLayer.size[0] * materialAdhesiveLayer.size[1]); // Сколько листов скотча требуется
            let optionsManualRollAdhesiveLayer = new Map();
            let margins = [0,0,0,0];
            let interval = 0;
            let layoutOnAdhesiveLayer = insaincalc.calcLayoutOnSheet(size, materialAdhesiveLayer.size, margins, interval);
            let costManualRoll = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
            if (layoutOnAdhesiveLayer.num == 0) { // если изделие больше чем лист скотча, тогда считаем как накатку целого листа по размеру изделия
                costManualRoll = insaincalc.calcManualRoll(n,size,optionsManualRollAdhesiveLayer,modeProduction);
            } else {
                if (numAdhesiveSheet < 1) {  // иначе считаем как накатку по общей площади затрачиваемого скотча
                    costManualRoll = insaincalc.calcManualRoll(1, [size[0]*Math.sqrt(n),size[1]*Math.sqrt(n)], optionsManualRollAdhesiveLayer, modeProduction);
                } else {  // иначе считаем как накатку по общей площади затрачиваемого скотча округляя кол-во листов
                    costManualRoll = insaincalc.calcManualRoll(Math.ceil(numAdhesiveSheet), materialAdhesiveLayer.size, optionsManualRollAdhesiveLayer, modeProduction);
                }
            }
            costOptions.cost += costManualRoll.cost + numAdhesiveSheet * materialAdhesiveLayer.cost;
            costOptions.price += (costManualRoll.cost + numAdhesiveSheet * materialAdhesiveLayer.cost) * (1 + insaincalc.common.marginMaterial);
            costOptions.weight += numAdhesiveSheet * materialAdhesiveLayer.weight / 1000;
            costOptions.time +=  costManualRoll.time;
            result.material.set(idAdhesiveLayer,[materialAdhesiveLayer.name,materialAdhesiveLayer.size,numAdhesiveSheet]);
        }

        // добавляем к цене рамку
        if (options.has('isFrame')) {
            segments = options.get('isFrame')['segments'];
            profileID = options.get('isFrame')['profileID'];
            optionsFrame = options;
            let costFrame = insaincalc.calcFrame(n,segments,profileID,optionsFrame,modeProduction);
            costOptions.cost += costFrame.cost;
            costOptions.price += costFrame.price;
            costOptions.weight += costFrame.weight;
            costOptions.time +=  costFrame.time;
            result.material = insaincalc.mergeMaps(result.material,costFrame.material);
        }

        // добавляем к цене EVA-лист
        if (options.has('isEVAFoam')) {
            let evaFoamID = options.get('isEVAFoam')['evaFoamID'];
            let sizeFoam = options.get('isEVAFoam')['size'];
            // рассчитываем стоимость ручной резки резины
            let cutterID = 'KeencutEvolutionE2';
            let optionsFoam = new Map();
            optionsFoam.set('Material','isMaterial');
            let costCutManual = insaincalc.calcCutRoller(n, sizeFoam, evaFoamID, cutterID, optionsFoam, modeProduction);
            // рассчитываем стоимость накатки
            let costManualRoll = insaincalc.calcManualRoll(n,sizeFoam,optionsFoam,modeProduction);

            costOptions.cost += costCutManual.cost + costManualRoll.cost;
            costOptions.price += costCutManual.price + costManualRoll.price;
            costOptions.weight += costCutManual.weight;
            costOptions.time +=  costCutManual.time + costManualRoll.time;
            result.material = insaincalc.mergeMaps(result.material,costCutManual.material);
        }

        // итог расчетов
        //полная себестоимость резки
        result.cost = costUVPrint.cost
            + costPrint.cost
            + costSublimation.cost
            + costLaser.cost
            + costMilling.cost
            + costCutManual.cost
            + costSticker.cost
            + costManualRoll.cost
            + costCutBackgroundFilm.cost
            + costManualBackgroundRoll.cost
            + costPockets.cost
            + costOptions.cost;
        // цена с наценкой
        result.price = (costUVPrint.price
            + costPrint.price
            + costSublimation.price
            + costLaser.price
            + costMilling.price
            + costCutManual.price
            + costSticker.price
            + costManualRoll.price
            + costCutBackgroundFilm.price
            + costManualBackgroundRoll.price+
            + costPockets.price
            + costOptions.price) * (1 + insaincalc.common.marginTablets);
        // времязатраты
        result.time = Math.ceil((costUVPrint.time
            + costPrint.time
            + costSublimation.time
            + costLaser.time
            + costMilling.time
            + costCutManual.time
            + costSticker.time
            + costManualRoll.time
            + costCutBackgroundFilm.time
            + costManualBackgroundRoll.time
            + costPockets.time
            + costOptions.time
        ) * 100) / 100;
        //считаем вес в кг.
        result.weight = Math.ceil((costUVPrint.weight
            + costPrint.weight
            + costSublimation.weight
            + costLaser.weight
            + costMilling.weight
            + costSticker.weight
            + costCutManual.weight
            + costCutBackgroundFilm.weight
            + costPockets.weight
            + costOptions.weight)* 100) / 100;
        result.timeReady = result.time + Math.max(costUVPrint.timeReady,
            costPrint.timeReady,
            costSublimation.timeReady,
            costLaser.timeReady,
            costMilling.timeReady,
            costSticker.timeReady,
            costPockets.timeReady,
            costCutManual.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};


// Функция расчета стоимости карманов для стендов
insaincalc.calcPockets = function calcPockets(n,size,pocketID,materialID,borderID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота] // не используется если задан pocketID
    //	pocketID - тип изделия в виде ID
    //	materialID - материал изделия в виде ID // не используется если задан pocketID
    //	borderID - материал окантовки кармана в виде ID материалов
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
    let baseTimeReady = insaincalc.common.baseTimeReady[Math.ceil(modeProduction)];

    try {
        let costPocket = {cost: 0, price: 0, time: 0, timeReady: 0, weight: 0, material: new Map()};
        let costPut = {cost: 0, price: 0, time: 0, timeReady: 0, weight: 0, material: new Map()};
        let timePutPocket = 0;
        let costOperator = 0;
        let timeOperator = 0;
        let pocket = {};
        pocket = insaincalc.findMaterial('misc', pocketID);
        if (pocket == undefined) {
            pocket = {size: size, materialID: materialID};
        } else {
            modeProduction = 0; // если в списке стандартных карманов pocketID есть, то считаем что времени на подготовку не тратится.
        }
        // стоимость кармана
        if (pocket.cost == undefined) {
            let optionsCutLaser = new Map();
            optionsCutLaser.set('Material','isMaterial');
            let sizeItem = Math.min(pocket.size[0],pocket.size[1]);
            optionsCutLaser.set('isCutLaser',{'sizeItem':sizeItem,'density':0,'difficulty':1,'lenCut':0});
            costPocket = insaincalc.calcLaser(n, pocket.size, pocket.materialID, optionsCutLaser, modeProduction);
        } else {
            costPocket.cost = pocket.cost * n;
            costPocket.price = costPocket.cost * (1 + insaincalc.common.marginMaterial);
            costPocket.weight = pocket.weight * n /1000;
            costPocket.material.set(pocketID,[pocket.name,pocket.size,n])
        }
        result.material = insaincalc.mergeMaps(result.material, costPocket.material);

        // стоимость монтажа кармана
        switch (pocket.mountID) {
            case 'tape': //  на скотч
                // стоимость наклейки двухстороннего скотча
                let tapeID = pocket.tapeID;
                if (tapeID != undefined) {
                    let segments = [[1, pocket.size[0]], [2, pocket.size[1]]];
                    let costPutTape = insaincalc.calcPutTape(n, segments, tapeID, difficult = 2, options, modeProduction);
                    result.material = insaincalc.mergeMaps(result.material, costPutTape.material);
                    costPut.cost += costPutTape.cost;
                    costPut.price += costPutTape.price;
                    costPut.weight += costPutTape.weight;
                    costPut.time += costPutTape.time;
                    costPut.timeReady = Math.max(costPut.timeReady, costPutTape.timeReady);
                }
                // стоимость наклейки окантовочной ленты
                if (borderID != undefined) {
                    let segments = [[1, pocket.size[0]], [2, pocket.size[1]]];
                    let costPutBorder = insaincalc.calcPutTape(n, segments, borderID, difficult = 2, options, modeProduction);
                    result.material = insaincalc.mergeMaps(result.material, costPutBorder.material);
                    costPut.cost += costPutBorder.cost;
                    costPut.price += costPutBorder.price;
                    costPut.weight += costPutBorder.weight;
                    costPut.time += costPutBorder.time;
                    costPut.timeReady = Math.max(costPut.timeReady, costPutBorder.timeReady);
                }
                // стоимость и время установки кармана на стенд
                timePutPocket = n * 2 / 60; // поклейка одного кармана занимает 2 мин
                timeOperator = timePutPocket; //считаем время затраты оператора участка
                costOperator = timeOperator * insaincalc.common.costOperator;
                costPut.cost += costOperator;
                costPut.price += costOperator * (1 + insaincalc.common.marginOperation);
                costPut.time += timePutPocket;
                break;
            case 'metalcap': // монтаж на декоративные заглушки
            case 'standoff': // монтаж на дистанционные держатели
                let costFurniture = {cost: 0, price: 0, time: 0, timeReady: 0, weight: 0, material: new Map()};
                timePutPocket = 0; // установка одного кармана занимает 1/2 мин
                let fasteners = pocket.setFasteners;
                fasteners.forEach(function(item) {
                    let fastenerID = item[0];
                    let numFastener = item[1] * n;
                    let fastener = insaincalc.findMaterial('misc', fastenerID);
                    timePutPocket += 0.5 / 60 * numFastener; // установка одного кармана занимает 1/2 мин
                    costFurniture.cost += fastener.cost * numFastener ;
                    costFurniture.weight += fastener.weight * numFastener / 1000;
                    costFurniture.material.set(fastenerID, [fastener.name, fastener.size, numFastener]);
                });
                costFurniture.price = costFurniture.cost * (1 + insaincalc.common.marginMaterial);
                result.material = insaincalc.mergeMaps(result.material, costFurniture.material);
                // стоимость и время установки кармана на стенд
                timeOperator = timePutPocket; //считаем время затраты оператора участка
                costOperator = timeOperator * insaincalc.common.costOperator;
                costPut.cost += costFurniture.cost + costOperator;
                costPut.price += costFurniture.price + costOperator * (1 + insaincalc.common.marginOperation);
                costPut.time += timePutPocket;
                break;
        }
        // итог расчетов
        //полная себестоимость резки
        result.cost = costPocket.cost + costPut.cost;
        // цена с наценкой
        result.price = (costPocket.price +  costPut.price) * (1 + insaincalc.common.marginTablets)
        result.time = costPocket.time + costPut.time; // время затраты
        result.weight = costPocket.weight + costPut.weight; //считаем вес в кг.
        result.timeReady = result.time + Math.max(costPocket.timeReady, costPut.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета нанесения скотча
insaincalc.calcPutTape = function calcPutTape(n,segments,tapeID,difficult,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во наборов для нанесения
    //	segments - массив отрезков ленты нужного кол-ва и длинны [n,len]
    //	tapeID - тип скотча в виде ID
    //  difficult - сложность нанесения в виде коэфф. увеличения времени нанесения от 1 до 2
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
    let baseTimeReady = insaincalc.common.baseTimeReady[Math.ceil(modeProduction)];
    let tape = insaincalc.findMaterial("misc",tapeID);
    let numCut = segments.reduce((sum,elem) => sum + n * elem[0],0);// общее число сегментов скотча
    let lenTape = segments.reduce((sum,elem) => sum + n * elem[1],0);// общая длинна скотча
    try {
        let costMaterial = lenTape / tape.size[1] * tape.cost; // стоимость скотча
        let timeProcess = difficult * (numCut * 10/3600  + Math.ceil(lenTape/1000) * 30 / 3600) //считаем время на поклейку скотча
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costOperator = timeOperator * insaincalc.common.costOperator;
        // итог расчетов
        //полная себестоимость резки
        result.cost = costMaterial + costOperator;//полная себестоимость нанесения скотча
        // цена с наценкой
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + costOperator * (1 + insaincalc.common.marginOperation);
        // времязатраты
        result.time = Math.ceil(timeProcess * 100) / 100;
        //считаем вес в кг.
        result.weight = tape.weight * lenTape / tape.size[1];
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.material.set(tapeID,[tape.name,tape.size,lenTape / tape.size[1]])
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета изготовления и установки профиля на стенд
insaincalc.calcFrame = function calcFrame(n,segments,profileID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во наборов профилей
    //	segments - массив отрезков профилей нужного кол-ва и длинны [len,n]
    //	profileID - ID профиля
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

    // Функция для расчета оптимального кол-ва профилей
    function minProfiles(lenProfile, segments) {
        let sortSegments =  JSON.parse(JSON.stringify(segments));
        console.log(sortSegments === segments);
        sortSegments.sort((a, b) => b[0] - a[0]); // Сортируем сегменты по убыванию длины
        let count = 0;
        let countProfile = 1;
        let index = 0;
        let len = lenProfile;
        const countSegments = sortSegments.reduce((acc, curr) => acc + curr[1], 0);
        console.log(countSegments)

        while (count < countSegments) {
            if ((len >= sortSegments[index][0]) && (sortSegments[index][1] > 0)) {
                len -= sortSegments[index][0];
                sortSegments[index][1] -= 1;
                count += 1;
            } else {
                index++;
                if (index == sortSegments.length) {
                    index = 0;
                    len = lenProfile;
                    countProfile++;
                }
            }
        }

        return countProfile;
    }

    // Считываем параметры материалов и оборудование
    let baseTimeReady = insaincalc.common.baseTimeReady[Math.ceil(modeProduction)];
    let profile = insaincalc.findMaterial("profile",profileID);
    let costCut = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costSetProfile = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costSetHanger = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    try {
        // вычисляем сколько палок профилей нужно
        let nsegments = segments.map((x) => [x[0],x[1] * n]);
        let numProfile = minProfiles(profile.len, nsegments);
        // вычисляем общую длину профиля
        let lenProfile = nsegments.reduce((acc, curr) => acc + curr[0]*curr[1], 0);
        // вычисляем сколько резов нужно сделать
        let numCut = 2 * nsegments.reduce((acc, curr) => acc + curr[1], 0);
        let costMaterial = numProfile * profile.cost; // стоимость профиля
        // Расчет стоимости резки профиля
        let toolID = 'DWE713XPS';
        costCut = insaincalc.calcCutProfile(n,segments,toolID,modeProduction);
        // Расчет стоимости установки профиля
        costSetProfile = insaincalc.calcSetProfile(n,segments,profileID,modeProduction);
        result.material.set(profileID,[profile.name,profile.size,numProfile])
        // Расчет стоимости установки подвесов
        if (options.has('isHanger')) {
            let hangerID = options.get('isHanger')['hangerID'];
            let numHanger = options.get('isHanger')['numHanger'] * n;
            let hanger = insaincalc.findMaterial("profile",hangerID);
            let timeSetHanger = (numHanger * 10) / 3600;
            let timeOperator = timeSetHanger; //считаем время затраты оператора участка
            let costOperator = timeOperator * insaincalc.common.costOperator;
            costSetHanger.cost = numHanger * hanger.cost + costOperator;
            costSetHanger.price = numHanger * hanger.cost * (1 + insaincalc.common.marginMaterial)
                + costOperator * (1 + insaincalc.common.marginOperation);
            costSetHanger.time = timeOperator;
            costSetHanger.weight = hanger.weight * numHanger / 1000;
            costSetHanger.material.set(hangerID,[hanger.name,hanger.size,numHanger]);
        }
        // итог расчетов
        //полная себестоимость резки
        result.cost = costMaterial + costCut.cost + costSetProfile.cost + costSetHanger.cost;//полная себестоимость нанесения скотча
        // цена с наценкой
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial)
            + costCut.price
            + costSetProfile.price
            + costSetHanger.price;
        // время затраты
        result.time = costCut.time + costSetProfile.time + costSetHanger.time;
        //считаем вес в кг.
        result.weight = profile.weight * lenProfile / 1000 + costSetProfile.weight + costSetHanger.weight;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.material.set(profileID,[profile.name,profile.size,numProfile])
        result.material = insaincalc.mergeMaps(result.material, costSetProfile.material);
        result.material = insaincalc.mergeMaps(result.material, costSetHanger.material);
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета стоимости изготовления табличек
insaincalc.calcPlaque = function calcPlaque(n,plaqueID,materialID,applicationID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	plaqueID - тип плакетки в виде ID
    //	materialID - материал изделия в виде ID из данных материалов
    //  applicationID - способ нанесения
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
    let costPlaque = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costPlate = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costSet = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

    try {
        let plaque = insaincalc.findMaterial("misc",plaqueID);
        // находим стоимость основы
        costPlaque.weight = plaque.weight * n;
        costPlaque.cost = plaque.cost * n;
        costPlaque.price = costPlaque.cost * (1 + insaincalc.common.marginMaterial);
        costPlaque.material.set(plaqueID,[plaque.name,plaque.size,n]);
        result.material = insaincalc.mergeMaps(result.material, costPlaque.material);
        // считаем стоимость пластины
        // параметры нанесения
        let sizeItem = Math.min(plaque.sizePlate[0],plaque.sizePlate[1]);
        let density = 0;
        let lenCut = 0;
        let color = '4+1';
        let resolution = 2;
        let sizeGrave = plaque.sizePlate;
        let optionsApplication = new Map();
        switch (applicationID) {
            case 'isUVPrint':
                optionsApplication.set('isCutLaser',{'sizeItem':sizeItem,'density':density,'difficulty':1,'lenCut':lenCut});
                optionsApplication.set(applicationID,{'printerID':'RimalSuvUV',
                    'resolution':2,
                    'surface':'isPlain',
                    'color':color })
                break;
            case 'isGrave':
                optionsApplication.set('isCutLaser',{'sizeItem':sizeItem,'density':density,'difficulty':1,'lenCut':lenCut});
                optionsApplication.set('isGrave',resolution);
                optionsApplication.set('isGraveFill',sizeGrave);
                break;
            case 'isSublimation':
                optionsApplication.set('isCutManualMetal','AccusheadPro12');
                optionsApplication.set('isSublimation',true);
                break;
            default:
        }
        costPlate = insaincalc.calcTablets(n,plaque.sizePlate,materialID,optionsApplication,modeProduction = 1)
        result.material = insaincalc.mergeMaps(result.material, costPlate.material);
        // считаем стоимость монтажа пластины на скотч
        // итог расчетов
        //полная себестоимость резки
        result.cost = costPlate.cost + costPlaque.cost + costSet.cost;
        // цена с наценкой
        result.price = (costPlate.price
            + costPlaque.price
            + costSet.price) * (1 + insaincalc.common.marginPlaque);
        // время затраты
        result.time = costPlate.time + costPlaque.time + costSet.time;
        //считаем вес в кг.
        result.weight = Math.ceil((costPlate.weight + costPlaque.weight)* 100) / 100;
        result.timeReady = result.time + Math.max(costPlate.timeReady,
            costPlaque.timeReady,
            costSet.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};