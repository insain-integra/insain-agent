// Функция расчета стоимости изготовления бейджей и значков
insaincalc.calcBadge = function calcBadge(n,size,difficulty,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //	size - размер изделия, [ширина, высота]
    //  difficulty - сложность формы, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
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
        let costLaser1 = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costLaser2 = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costRoll = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costAdhesiveLayer = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costUVPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costAttachment = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPocket = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costEpoxy = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costMetalBlank = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetSticker = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};


        // определяем кол-во брака для полимерной заливки
        let n_items = n;
        if (options.has('isEpoxy')) {
            let tool = insaincalc.tools['EpoxyCoating'];
            let defects = (tool.defects.find(item => item[0] >= n))[1];
            defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
            n_items = Math.ceil(n * (1 + defects));
        }

        // рассчитываем стоимость лазерной резки материала на изделия, печати и ламинации пленки
        if (options.has('isPrint')) {
            // рассчитываем стоимость печати
            let optionsPrint = new Map();
            let color = '4+0';
            let margins = [2, 2, 2, 2];
            let interval = 4;
            let materialPrintID = 'RaflatacMW';
            // если параметры не заданы, то оставляем по умолчанию
            if (options.get('isPrint') != '') {
                let paramPrint = options.get('isPrint');
                color = paramPrint['color'];
                margins = paramPrint['margins'];
                interval = paramPrint['interval'];
                materialPrintID = paramPrint['materialID'];
            }
            optionsPrint.set('isLamination','Laminat32G');
            optionsPrint.set('noCut', true);
            costPrint = insaincalc.calcPrintSheet(n_items, size, color, margins, interval, materialPrintID, optionsPrint, modeProduction)
            result.material = insaincalc.mergeMaps(result.material, costPrint.material);

            // рассчитываем стоимость резки материала основы бейджа
            let optionsLaser = new Map();
            let sizeSheet = [320, 450];
            let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeSheet, [5, 5, 5, 5], 4);
            if (layoutOnSheet.num == 0) {
                throw (new ICalcError('Размер изделия больше допустимого'))
            }
            let numSheet = Math.ceil(n_items / layoutOnSheet.num); //Сколько листов всего требуется
            optionsLaser.set('isCutLaser', {'sizeItem': sizeSheet[0], 'density': 0, 'difficulty': 1, 'lenCut': 0});
            costLaser1 = insaincalc.calcLaser(numSheet, sizeSheet, materialID, optionsLaser, modeProduction);
            result.material = insaincalc.mergeMaps(result.material, costLaser1.material);

            // рассчитываем стоимость накатки отпечатанных листов на основу
            costRoll = insaincalc.calcLaminationRoll(numSheet,sizeSheet,modeProduction);
        }

        // рассчитываем стоимость нанесение клеевого слоя
        if (options.has('isAdhesiveLayer')) {
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
            let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, materialAdhesiveLayer.size, [5, 5, 5, 5], 4);
            let numAdhesiveSheet = Math.ceil(n / layoutOnSheet.num); // Сколько листов скотча требуется
            costAdhesiveLayer = insaincalc.calcManualRoll(numAdhesiveSheet,materialAdhesiveLayer.size,options,modeProduction);
            costAdhesiveLayer.cost += n / layoutOnSheet.num * materialAdhesiveLayer.cost;
            costAdhesiveLayer.price += n / layoutOnSheet.num * materialAdhesiveLayer.cost * (1 + insaincalc.common.marginMaterial);
            costAdhesiveLayer.weight = n / layoutOnSheet.num * materialAdhesiveLayer.weight / 1000;
            result.material.set(idAdhesiveLayer,[materialAdhesiveLayer.name,materialAdhesiveLayer.size,n / layoutOnSheet.num]);
        }
        // рассчитываем стоимость лазерной резки и гравировки на изделия
        if (options.has('isCutLaser') || options.has('isGrave')) {
            let optionsLaser = new Map();
            if (options.has('isCutLaser')) {
                if (options.get('isCutLaser') != '') {
                    optionsLaser.set('isCutLaser', options.get('isCutLaser'))
                } else {
                    optionsLaser.set('isCutLaser',{'sizeItem':size[0],'density':0,'difficulty':1,'lenCut':0});
                }
            }
            if (options.has('isGrave')) {
                if (options.get('isGrave') != '') {
                    optionsLaser.set('isGrave',options.get('isGrave'))
                    if (options.has('isGraveFill')) {
                        optionsLaser.set('isGraveFill',options.get('isGraveFill'));
                    }
                    if (options.has('isGraveContur')) {
                        optionsLaser.set('isGraveContur',options.get('isGraveContur'));
                    }
                } else {
                    optionsLaser.set('isGrave',2); // устанавливаем разрешение
                    optionsLaser.set('isGraveFill',size); // устанавливаем размер поверхности гравировки по всему изделию
                }
            }
            if (options.has('isPrint')) {
                optionsLaser.set('Material', 'noMaterial');
            } else {
                optionsLaser.set('Material', 'isMaterial');
            }
            costLaser2 = insaincalc.calcLaser(n_items,size,materialID,optionsLaser,modeProduction);
            result.material = insaincalc.mergeMaps(result.material, costLaser2.material);
        }

        // рассчитываем стоимость нанесения УФ-печати
        if (options.has('isUVPrint')) {
            let optionsUVPrint = new Map();
            // если параметры не заданы, то устанавливаем по умолчанию
            if (options.get('isUVPrint') != '') {
                optionsUVPrint.set('isUVPrint',options.get('isUVPrint'));
            } else {
                optionsUVPrint.set('isUVPrint', {
                    'printerID': 'RimalSuvUV',
                    'resolution': 2,
                    'surface': 'isPlain',
                    'color': '4+0'
                });
            }
            let sizeItem = size;
            costUVPrint = insaincalc.calcUVPrint(n, size, sizeItem, materialID, optionsUVPrint, modeProduction = 1)
            result.material = insaincalc.mergeMaps(result.material, costUVPrint.material);
        }

        // рассчитываем стоимость нанесения полимерного покрытия
        if (options.has('isEpoxy')) {
            let optionsEpoxy = new Map();
            // если параметры не заданы, то устанавливаем по умолчанию
            if (options.get('isEpoxy') != '') {
                optionsEpoxy = options.get('isEpoxy');
            } else {
                optionsEpoxy.set('isLayout', 'true');
            }
            costEpoxy = insaincalc.calcEpoxy(n,size,difficulty,optionsEpoxy,modeProduction);
            result.material = insaincalc.mergeMaps(result.material, costEpoxy.material);
        }

        // добавляем стоимость заготовки
        if (options.has('isMetalBlank')) {
            let metalBlankID = options.get('isMetalBlank');
            let metalBlank = insaincalc.misc.MetalBlankPins[metalBlankID];
            costMetalBlank.cost = metalBlank.cost * n;
            costMetalBlank.price = costMetalBlank.cost * (1 + insaincalc.common.marginMaterial);
            result.material.set(metalBlankID,[metalBlank.name,metalBlank.size,n]);
        }

        // рассчитываем стоимость изготовления и наклейки полимерного стикера на заготовку
        if (options.has('isEpoxySticker')) {
            let optionsEpoxy = new Map();
            let sizeSticker = size;
            let difficultySticker = difficulty;
            let materialStickerID = 'RaflatacMW';
            if (options.get('isEpoxySticker') != '') {
                let paramEpoxy = options.get('isEpoxySticker');
                sizeSticker = paramEpoxy.size;
                difficultySticker = paramEpoxy.difficulty;
                materialStickerID = paramEpoxy.materialID;
            }
            costEpoxy = insaincalc.calcPolySticker(n,sizeSticker,difficultySticker,materialStickerID,optionsEpoxy,modeProduction)
            result.material = insaincalc.mergeMaps(result.material, costEpoxy.material);
            costSetSticker = insaincalc.calcSetSticker(n,size,modeProduction);
        }

        // рассчитываем стоимость установки крепления
        if (options.has('isAttachment')) {costAttachment =  insaincalc.calcAttachment(n,options.get('isAttachment'),modeProduction)}
        result.material = insaincalc.mergeMaps(result.material, costAttachment.material);

        // рассчитываем стоимость установки кармана
        if (options.has('isPocket')) {costPocket =  insaincalc.calcPocket(n,options.get('isPocket'),modeProduction)}
        result.material = insaincalc.mergeMaps(result.material, costPocket.material);

        // рассчитываем стоимость упаковки
        if (options.has('isPacking')) {costPacking =  insaincalc.calcPacking(n,[size[0],size[1],5],options,modeProduction)}
        result.material = insaincalc.mergeMaps(result.material, costPacking.material);

        // итог расчетов
        //полная себестоимость резки
        result.cost = Math.ceil(costPrint.cost
            + costLaser1.cost
            + costRoll.cost
            + costAdhesiveLayer.cost
            + costLaser2.cost
            + costUVPrint.cost
            + costEpoxy.cost
            + costAttachment.cost
            + costPocket.cost
            + costMetalBlank.cost
            + costSetSticker.cost
            + costPacking.cost);
        // цена с наценкой
        result.price = Math.ceil(costPrint.price
            + costLaser1.price
            + costRoll.price
            + costAdhesiveLayer.price
            + costLaser2.price
            + costUVPrint.price
            + costEpoxy.price
            + costAttachment.price
            + costPocket.price
            + costMetalBlank.price
            + costSetSticker.price
            + costPacking.price) * (1 + insaincalc.common.marginBadge);
        // времязатраты
        result.time = Math.ceil((costPrint.time
            + costLaser1.time
            + costRoll.time
            + costAdhesiveLayer.time
            + costLaser2.time
            + costUVPrint.time
            + costEpoxy.time
            + costAttachment.time
            + costPocket.time
            + costMetalBlank.time
            + costSetSticker.time
            + costPacking.time)* 100) / 100;
        //считаем вес в кг.
        result.weight = Math.ceil((costPrint.weight
            + costLaser1.weight
            + costEpoxy.weight
            + costAdhesiveLayer.weight
            + costAttachment.weight
            + costPocket.weight
            + costMetalBlank.weight
            + costPacking.weight)* 100) / 100;
        result.timeReady = result.time + Math.max(costUVPrint.timeReady,
            costPrint.timeReady,
            costLaser1.timeReady,
            costRoll.timeReady,
            costLaser2.timeReady,
            costEpoxy.timeReady,
            costPocket.timeReady,
            costMetalBlank.timeReady,
            costSetSticker.timeReady,
            costPacking.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};