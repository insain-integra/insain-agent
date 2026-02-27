// Функция расчета стоимости изготовления акриловых призов
insaincalc.calcAcrilycPrizes = function calcAcrilycPrizes(n,layers,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	layers - массив параметров слоев приза, вида [{"materialID","size","isTop","options"}]
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
        let costLayers = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costGluing = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costOptions = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costLaser = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costUVPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costLayer = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let modeProductionLaser = modeProduction;
        let modeProductionUVPrint = modeProduction;
        let modeProductionGluing = modeProduction;

        // рассчитываем максимальный размер основания
        let maxSizeBase = [0,0];
        layers.forEach(layer => {
            if (!layer.isTop) {
                maxSizeBase[0] = Math.max(maxSizeBase[0], layer.size[0]);
                maxSizeBase[1] = Math.max(maxSizeBase[1], layer.size[1]);
            }
        });

        // рассчитываем стоимость изготовление каждого слоя
        layers.forEach(function(layer) {
            costLayer = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
            costLaser = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
            costUVPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
            costGlue = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

            // рассчитываем стоимость лазерной резки и гравировки
            if (layer.options.has('isGrave') || layer.options.has('isCutLaser')) {
                costLaser = insaincalc.calcLaser(n, layer.size, layer.materialID, layer.options, modeProductionLaser);
                costLayer.cost += costLaser.cost;
                costLayer.price += costLaser.price;
                costLayer.time += costLaser.time;
                costLayer.weight += costLaser.weight;
                if (modeProductionLaser > 0) {
                    modeProductionLaser = 0;
                    costLayer.timeReady =  Math.max(costLaser.timeReady,costLayer.timeReady);
                }
                costLayer.material = insaincalc.mergeMaps(costLayer.material,costLaser.material);
            }


            // рассчитываем стоимость нанесения УФ-печати
            if (layer.options.has('isUVPrint')) {
                const sizePrint = layer.options.get('isUVPrint')['size'];
                const optionsUVPrint = new Map();
                // если параметры не заданы, то устанавливаем по умолчанию
                optionsUVPrint.set('isUVPrint', {
                    'printerID': 'RimalSuvUV',
                    'resolution': 2,
                    'surface': 'isPlain',
                    'color': '4+1'
                });
                const sizeItem = sizePrint;
                costUVPrint = insaincalc.calcUVPrint(n,sizePrint,sizeItem,layer.materialID,optionsUVPrint,modeProductionUVPrint)
                costLayer.cost += costUVPrint.cost;
                costLayer.price += costUVPrint.price;
                costLayer.time += costUVPrint.time;
                costLayer.weight += costUVPrint.weight;
                if (modeProductionUVPrint > 0) {
                    modeProductionUVPrint = 0;
                    costLayer.timeReady =  Math.max(costUVPrint.timeReady,costLayer.timeReady);
                }
                costLayer.material = insaincalc.mergeMaps(costLayer.material,costUVPrint.material);
            }

            // рассчитываем стоимость приклейки лицевой части к основанию
            if (layer.isTop) {
                costGluing = insaincalc.calcUVGluing(n,maxSizeBase,modeProductionGluing)
                costLayer.cost += costGluing.cost;
                costLayer.price += costGluing.price;
                costLayer.time += costGluing.time;
                costLayer.weight += costGluing.weight;
                if (modeProductionGluing > 0) {
                    modeProductionGluing = 0;
                    costLayer.timeReady =  Math.max(costGluing.timeReady,costLayer.timeReady);
                }
                costLayer.material = insaincalc.mergeMaps(costLayer.material,costGluing.material);
            }

            costLayers.cost += costLayer.cost;
            costLayers.price += costLayer.price;
            costLayers.time += costLayer.time;
            costLayers.weight += costLayer.weight;
            if (costLayer.timeReady > costLayers.timeReady) {costLayers.timeReady = costLayer.timeReady}
            costLayers.material = insaincalc.mergeMaps(costLayers.material,costLayer.material);
        });
        result.material = insaincalc.mergeMaps(result.material,costLayers.material);


        // итог расчетов
        //полная себестоимость резки
        result.cost = costLayers.cost
            + costOptions.cost;
        // цена с наценкой
        result.price = (costLayers.price
            + costOptions.price) * (1 + insaincalc.common.marginAcrilycPrizes);
        // времязатраты
        result.time = Math.ceil((costLayers.time
            + costOptions.time
        ) * 100) / 100;
        //считаем вес в кг.
        result.weight = costLayers.weight + costOptions.weight;
        // время готовности
        result.timeReady = result.time + Math.max(costLayers.timeReady,costOptions.timeReady);
        return result;
    } catch (err) {
        throw err
    }
};

