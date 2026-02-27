// Функция расчета стоимости печати на широкоформатном принтере
insaincalc.calcPrintRoll = function calcPrintRoll(n,size,materialID,printerID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделей
    //	size - размер изделия, [ширина, высота]
    //	materialID - материал изделия в виде ID из данных материалов
    //	printerID - принтер для печати
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
    let printer = insaincalc.printer[printerID];
    let material = insaincalc.roll.Film[materialID];
    if (material == undefined) {material = insaincalc.roll.Banner[materialID]}
    if (material == undefined) {material = insaincalc.roll.Paper[materialID]}
    let margins = printer.margins; // отступы от края материала,мм
    let setSizeMaterial = [];
    let layoutOnRoll = [];
    let lenJoing = 0;
    let edgeJoing = [];

    try {
        // материал может иметь несколько размеров, например рулоны баннера разной ширины
        // поэтому для начала выбираем размер материал с наиболее оптимальным расходом
        sizeMaterial = material.size[0];
        if (typeof sizeMaterial == 'number') {
            setSizeMaterial = [material.size];
        } else {
            setSizeMaterial = material.size;
        }
        let saveSizeMaterial = material.size[0];
        let saveLenMaterial = 0;
        let minVolMaterial = -1;
        let volMaterial = 0;
        for (let sizeMaterial of setSizeMaterial) {
            // проверяем помещается ли материал в принтер
            if (Math.min(sizeMaterial[0], sizeMaterial[1]) == 0) {
                if (Math.max(sizeMaterial[0], sizeMaterial[1]) > printer.maxSize[0]) {
                    continue;
                }
            } else {
                let layoutOnRoll = insaincalc.calcLayoutOnRoll(1, sizeMaterial, printer.maxSize);
                if (layoutOnRoll.length == 0) {
                    continue;
                }
            }
            let sizeMaterialWithMargins = [sizeMaterial[0] - margins[1] - margins[3], sizeMaterial[1]];

            // проверяем помещается ли изделия на материал
            layoutOnRoll = insaincalc.calcLayoutOnRoll(n, size, sizeMaterialWithMargins);
            let lenMaterial =  layoutOnRoll.length;
            let wide = layoutOnRoll.wide;
            // если в опциях указана стыковка, делим изделие на полосы
            if (options.has('isJoing')) {
                if (lenMaterial == 0) { // делим изделие вдоль его наибольшей стороны
                    let numBondMaterial = Math.ceil(Math.max(size[0], size[1]) / sizeMaterialWithMargins[0]);
                    lenJoing = n * (numBondMaterial - 1) * Math.max(size[0], size[1]);
                    if (size[0] > size[1]) {edgeJoing = [numBondMaterial-1,0,0,0]} else {edgeJoing = [0,numBondMaterial-1,0,0]}
                    lenMaterial = n * numBondMaterial * Math.min(size[0], size[1]); // общая длинна материала
                    wide =  sizeMaterialWithMargins[0];
                } else { // делим изделие вдоль его короткой стороны
                    let numBondMaterial = Math.ceil(Math.max(size[0], size[1]) / sizeMaterialWithMargins[0]);
                    lenJoing = n*(numBondMaterial-1) * Math.min(size[0], size[1]);
                    if (size[0] < size[1]) {edgeJoing = [numBondMaterial-1,0,0,0]} else {edgeJoing = [0,numBondMaterial-1,0,0]}
                    lenMaterial = n * numBondMaterial * Math.min(size[0], size[1]); // общая длинна материала
                    wide =  sizeMaterialWithMargins[0];
                }
            }
            if (lenMaterial > 0) {
                sizePrint = [wide, lenMaterial];
                volMaterial = (lenMaterial + printer.margins[0] + printer.margins[2]) * sizeMaterial[0] / 1000000; // расход материала в м2
                // запоминаем наиболее оптимальный вариант по расходу материала
                if (minVolMaterial == -1 || volMaterial < minVolMaterial) {
                    minVolMaterial = volMaterial;
                    saveSizeMaterial = sizeMaterial;
                    saveSizePrint = sizePrint;
                    saveLenMaterial = lenMaterial;
                    saveEdgeJoing = edgeJoing;
                    saveLenJoing = lenJoing;
                }
            }
        }
        //if (minVolMaterial == -1) {throw (new ICalcError('Материал не помещается в принтер'))}

        sizeMaterial = saveSizeMaterial;
        sizePrint = saveSizePrint;
        lenMaterial = saveLenMaterial;
        edgeJoing = saveEdgeJoing;
        lenJoing = saveLenJoing;
        sizeMaterialWithMargins = [sizeMaterial[0] - margins[1] - margins[3], sizeMaterial[1]];

        if (lenMaterial == 0) {throw (new ICalcError('Изделие не помещается на материал, укажите возможность стыковки'))}

        // расчет печати
        let costPrint = insaincalc.calcPrintWide(n,sizePrint,materialID,printerID,options,modeProduction);
        // расчет расхода материала
        let costMaterial = material.cost;
        // цена материала с учетом объема печати
        if (costMaterial instanceof Array) {
            let index = material.cost.findIndex(item => item[0] >= lenMaterial/1000);
            if (index == - 1) {
                index = material.cost.length-1;
            } else {
                index = index - 1;
            }
            costMaterial = material.cost[index][1];
        }

        let defects = (printer.defects.find(item => item[0] >= n))[1]; //находим процент брака от тиража
        defects +=  modeProduction > 1 ? defects * (modeProduction-1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        lenMaterial = saveLenMaterial + margins[0] + margins[2]; // добавляем вылеты материала вдоль печати
        lenMaterial = lenMaterial * (1 + defects); // учитываем брак печати
        // стоимость материала с учетом минимального закупа
        if (lenMaterial < material.length_min) {
            lenMaterial = material.length_min;
        }
        costMaterial = costMaterial*lenMaterial*sizeMaterial[0]/1000000;
        result.material.set(materialID,[material.name,sizeMaterial,lenMaterial/1000]);

        // считаем стоимость доп. опций обработки (резка в край, люверсовка, и тд)
        let costOptions = {cost:0,price:0,time:0,timeReady:0,weight:0};
        // добавляем к цене резку в край
        if (options.has('isCutting') || options.has('isJoing')) {
            let edge = [0,0,0,0];
            if (options.has('isCutting')) {edge = options.get('isCutting')};
            // добавляем к цене резку в край и склейку для стыковки
            if (lenJoing > 0) {edge = edge.map(function(value, index){return value + edgeJoing[index]*2})};
            let costCutting = insaincalc.calcCuttingEdge(n,size,edge,modeProduction);
            costOptions.cost += costCutting.cost;
            costOptions.price += costCutting.price;
            costOptions.time += costCutting.time;
        }
        // добавляем к цене проклейку кармана
        if (options.has('isPocket')) {
            let edge = options.get('isPocket');
            let costPocket = insaincalc.calcGluingBanner(n,size,edge,modeProduction);
            costOptions.cost += costPocket.cost;
            costOptions.price += costPocket.price;
            costOptions.time += costPocket.time;
            result.material = insaincalc.mergeMaps(result.material,costPocket.material);
        }
        // добавляем к цене проклейку края
        if (options.has('isGluing') || options.has('isJoing')) {
            let edge = [0,0,0,0];
            if (options.has('isGluing')) {edge = options.get('isGluing')};
            // добавляем к цене резку в край и склейку для стыковки
            if (lenJoing > 0) {edge = edge.map(function(value, index){ return value + edgeJoing[index]})};
            let costGluing = insaincalc.calcGluingBanner(n,size,edge,modeProduction);
            costOptions.cost += costGluing.cost;
            costOptions.price += costGluing.price;
            costOptions.time += costGluing.time;
            result.material = insaincalc.mergeMaps(result.material,costGluing.material);
        }
        // добавляем к цене люверсовку с проклейкой
        if (options.has('isEyelet')) {
            let step = options.get('isEyelet');
            let costEyelet = insaincalc.calcEyelet(n,size,step,modeProduction);
            costOptions.cost += costEyelet.cost;
            costOptions.price += costEyelet.price;
            costOptions.time += costEyelet.time;
            result.material = insaincalc.mergeMaps(result.material,costEyelet.material);
            // считаем автоматически проклейку края, там где есть люверсовка.
            let edge = step.map((s) => {let l;if (s > 0) l = 1; else l = 0; return l});
            let costGluing = insaincalc.calcGluingBanner(n,size,edge,modeProduction);
            costOptions.cost += costGluing.cost;
            costOptions.price += costGluing.price;
            costOptions.time += costGluing.time;
            result.material = insaincalc.mergeMaps(result.material,costGluing.material);
        }
        // добавляем к цене ламинацию
        if (options.has('isLamination')) {
            let costLamination = insaincalc.calcLaminationWide(n,size,modeProduction);
            costOptions.cost += costLamination.cost;
            costOptions.price += costLamination.price;
            costOptions.time += costLamination.time;
            costOptions.weight += costLamination.weight;
            result.material = insaincalc.mergeMaps(result.material,costLamination.material);
        }

        // окончательный расчет
        result.cost = Math.ceil(costPrint.cost + costMaterial + costOptions.cost); //полная себестоимость печати тиража
        result.price = Math.ceil(costMaterial * (1 + insaincalc.common.marginMaterial + insaincalc.common.marginPrintRoll) + (costPrint.price + costOptions.price) * (1 + insaincalc.common.marginPrintRoll));
        result.time =  Math.ceil((costOptions.time + costPrint.time) * 100) / 100;
        result.timeReady = result.time + Math.max(costOptions.timeReady,costPrint.timeReady); // время готовности
        result.weight = Math.ceil((insaincalc.calcWeight(n,material.density,material.thickness,size,material.unitDensity) + costOptions.weight) * 100) / 100; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};

