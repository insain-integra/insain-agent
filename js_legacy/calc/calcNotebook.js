// Функция расчета стоимости блокнотов
insaincalc.calcNotebook = function calcNotebook(n,size,cover,inner,binding,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	size - размер изделия, [ширина, высота]
    //  cover - параметры обложки в виде словаря {'coverTop':{'materialID','laminatID','color'},'coverBottom':{'materialID','laminatID','color'}}
    //  inner - параметры внутреннего блока [{'materialID','numSheet','color'}]
    //	binding - параметры переплета {'bindingID','edge'}
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
        // Объявляем нулевые стоимости
        let costCovers = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costInners = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBinding = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let numWithDefects = n;
        // расчет обложки
        let margins =[2,2,2,2];
        let interval = 4;
        if ((cover['cover']['materialID'] == cover['backing']['materialID']) &&
        (cover['cover']['laminatID'] == cover['backing']['laminatID']) &&
        (cover['cover']['color'] == cover['backing']['color'])) {
            let optionsCover = new Map();
            optionsCover.set('isLamination',cover['cover']['laminatID']);
            costCovers = insaincalc.calcPrintSheet(2 * numWithDefects, size, cover['cover']['color'], margins, interval, cover['cover']['materialID'], optionsCover, modeProduction)
        } else {
            for (let dataCover in cover) {
                let value = cover[dataCover];
                let optionsCover = new Map();
                optionsCover.set('isLamination',value['laminatID']);
                let costCover = insaincalc.calcPrintSheet(numWithDefects, size, value['color'], margins, interval, value['materialID'], optionsCover, modeProduction)
                costCovers.cost += costCover.cost;
                costCovers.price += costCover.price;
                costCovers.time += costCover.time;
                costCovers.weight += costCover.weight;
                if (costCovers.timeReady < costCover.timeReady) {costCovers.timeReady = costCover.timeReady}
                costCovers.material = insaincalc.mergeMaps(costCovers.material,costCover.material);
            }
        }
        result.material = insaincalc.mergeMaps(result.material,costCovers.material);
        // расчет внутреннего блока, который может состоят из нескольких разных частей
        isOffset = false;
        for (let value of inner) {
            let optionsInner = new Map();
            let layoutOnA4 = insaincalc.calcLayoutOnSheet(size, [320,225]);
            let numSheetA4 = Math.ceil(numWithDefects * value['numSheet']/layoutOnA4.num);
            let costInner = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
            if ((numSheetA4 < 1000) || (options.has('isPrintLaser')) || ((value['color'] == '0+0') && (Math.ceil(numWithDefects / layoutOnA4.num) <= 200)) ) {
                let marginsInner =[2,2,2,2];
                let intervalInner = 4;
                if (value['materialID'] == 'VHI80') {
                    marginsInner =-1;
                    intervalInner = 0;
                }
                costInner = insaincalc.calcPrintSheet(numWithDefects * value['numSheet'], size, value['color'], marginsInner, intervalInner, value['materialID'], optionsInner, modeProduction)
            } else {
                costInner = insaincalc.calcPrintOffset(numWithDefects * value['numSheet'], size, value['color'], value['materialID'], modeProduction);
                if (numSheetA4 > 2500) {isOffset = true};
            }
            costInners.cost += costInner.cost;
            costInners.price += costInner.price;
            costInners.time += costInner.time;
            costInners.weight += costInner.weight;
            if (costInners.timeReady < costInner.timeReady) {costInners.timeReady = costInner.timeReady}
            costInners.material = insaincalc.mergeMaps(costInners.material,costInner.material);
        }
        result.material = insaincalc.mergeMaps(result.material, costInners.material);
        // расчет переплета
        let optionsBinding = new Map();
        // Если печать делали на офсете то и переплет считаем на офсете
        if (isOffset) {
            optionsBinding.set('bindingID','BindOffset')
        } else {
            optionsBinding.set('bindingID','BindRenzSRW')
        }
        costBinding = insaincalc.calcBinding(n, size, cover, inner, binding, optionsBinding, modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costBinding.material);
        // окончательный расчет
        result.cost = costCovers.cost +costInners.cost +costBinding.cost; //себестоимость тиража
        result.price = (costCovers.price +costInners.price +costBinding.price)*(1+insaincalc.common.marginNotebook); //цена тиража
        result.time =  Math.ceil((costCovers.time +costInners.time +costBinding.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costCovers.timeReady,costInners.timeReady,costBinding.timeReady); // время готовности
        result.weight = costCovers.weight +costInners.weight +costBinding.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};
