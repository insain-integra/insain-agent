// Функция расчета стоимости изготовления бейджей с уф-печатью
insaincalc.calcUVBadge = function calcUVBadge(n,size,difficulty,color,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
    //  difficulty - сложность формы для резки, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
    //	materialID - материал изделия в виде ID из данных материалов
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
    let printerID = 'RimalSuvUV';
    let printer = insaincalc.printer[printerID];
    let baseTimeReady = printer.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    try {
        // определяем кол-во брака для уф-печати
        let defects = (printer.defects.find(item => item[0] >= n))[1];
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        let n_items = Math.ceil(n * (1 + defects));
        // рассчитываем стоимость лазерной резки с материалом
        let optionsLaser = new Map();
        let lenCut = (size[0] + size[1]) * 2 * difficulty; // длинна внешнего периметр резки одного элемента c учетом изогнутости
        if (options.has('isPocket')) {lenCut += 180} // длинна среднего размера окошка, мм
        optionsLaser.set('isCutLaser',{'sizeItem':size[0],'density':0,'difficulty':difficulty,'lenCut':lenCut});
        let costLaser = insaincalc.calcLaser(n_items,size,materialID,optionsLaser,modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costLaser.material);
        // рассчитываем стоимость нанесения УФ-печати
        let sizeItem = size;
        let optionsUVPrint = options;
        optionsUVPrint.set('isUVPrint',{'printerID':printerID,'resolution':2,'surface':'isPlain','color':color});
        let costUVPrint = insaincalc.calcUVPrint(n,size,sizeItem,materialID,optionsUVPrint,modeProduction = 1)
        result.material = insaincalc.mergeMaps(result.material,costUVPrint.material);
        // рассчитываем стоимость установки крепления
        let costAttachment = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        if (options.has('isAttachment')) {
            costAttachment =  insaincalc.calcAttachment(n,options.get('isAttachment'),modeProduction)
            result.material = insaincalc.mergeMaps(result.material,costUVPrint.material);
        }
        // рассчитываем стоимость установки кармана
        let costPocket = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        if (options.has('isPocket')) {
            costPocket =  insaincalc.calcPocket(n,options.get('isPocket'),modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costPocket.material);
        }
        // рассчитываем стоимость упаковки
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        if (options.has('isPacking')) {
            costPacking =  insaincalc.calcPacking(n,[size[0],size[1],5],options,modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costPacking.material);
        }

        // итог расчетов
        //полная себестоимость резки
        result.cost = Math.ceil(costUVPrint.cost
            + costLaser.cost
            + costAttachment.cost
            + costPocket.cost
            + costPacking.cost);
        // цена с наценкой
        result.price = Math.ceil(costUVPrint.price
            + costLaser.price
            + costAttachment.price
            + costPocket.price
            + costPacking.price) * (1 + insaincalc.common.marginBadge);
        // времязатраты
        result.time = Math.ceil((costUVPrint.time
            + costLaser.time
            + costAttachment.time
            + costPocket.time
            + costPacking.time)* 100) / 100;
        //считаем вес в кг.
        result.weight = Math.ceil((costUVPrint.weight
            + costLaser.weight
            + costPocket.weight
            + costPacking.weight)* 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};