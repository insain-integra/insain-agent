// Функция расчета стоимости изготовления магнитов ламинированных c полимерной заливкой и без
insaincalc.calcMagnetLamination = function calcMagnetLamination(n,size,shape,difficulty,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
    //  shape - форма изделия,
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
    try {
        // рассчитываем стоимость лазерной печати и ламинации листовой продукции
        let color = '4+0';
        let margins = [0, 0, 0, 0];
        let interval = 0;
        let isMakeForm = false;
        let n_items = n;
        // определяем кол-во брака для полимерной заливки

        switch (shape) {
            case 'rectangular':
                break;
            case 'standart':
                margins = [2, 2, 2, 2];
                interval = 4;
                break;
            case 'nonstandart':
                margins = [2, 2, 2, 2];
                interval = 4;
                isMakeForm = true;
                break;
        }
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCut = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costRoll = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCutSaber = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPress = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costForm = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costEpoxy = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

        let materialPrintID = "RAFLACOAT"; // используемый по умолчанию материал для печати
        // рассчитываем стоимость нанесения полимерного покрытия
        if (options.has('isEpoxy')) {
            let optionsEpoxy = options.get('isEpoxy');
            materialPrintID = optionsEpoxy.get('materialPrintID'); // указываем материал печати подходящего для заливки
            costEpoxy = insaincalc.calcEpoxy(n, size, difficulty, optionsEpoxy, modeProduction);
            result.material = insaincalc.mergeMaps(result.material, costEpoxy.material);
            let tool = insaincalc.tools['EpoxyCoating'];
            let defects = (tool.defects.find(item => item[0] >= n))[1];
            defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
            n_items = Math.ceil(n * (1 + defects));
        }
        // рассчитываем стоимость печати листов
        let optionsPrint = new Map();
        if (options.has('isLamination')) {optionsPrint.set('isLamination',options.get('isLamination'))}
        optionsPrint.set('noCut', true);
        costPrint = insaincalc.calcPrintSheet(n_items,size,color,margins,interval,materialPrintID,optionsPrint,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costPrint.material);
        // рассчитываем кол-во листов магнитного винила
        let sizeSheet = costPrint.material.get(materialPrintID)[1];
        let sizeCutSheet = [sizeSheet[0] - 10, sizeSheet[1] - 10]; //подрезаем листы для лучшего размещения на виниле
        let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeSheet, margins, interval);
        let numSheet = Math.ceil(n_items/layoutOnSheet.num);
        // рассчитываем стоимость магнитного винила и стоимость нарезки
        let cutterID = 'KWTrio3026';
        let optionsCut = new Map();
        optionsCut.set('Material','isMaterial');
        costCut = insaincalc.calcCutRoller(numSheet,sizeCutSheet,materialID,cutterID,optionsCut,modeProduction)
        result.material = insaincalc.mergeMaps(result.material, costCut.material);
        // рассчитываем стоимость накатки листов на материал с учетом материала
        costRoll = insaincalc.calcLaminationRoll(numSheet,sizeSheet,modeProduction);
        // рассчитываем стоимость вырубки или резки на конечные изделия
        switch (shape) {
            case 'rectangular':
                cutterID = 'Ideal1046';
                costCutSaber = insaincalc.calcCutSaber(numSheet,size,sizeSheet,materialID,cutterID,margins,interval,modeProduction);
                break;
            default:
                // рассчитываем стоимость вырубки
                // рассчитываем стоимость резки листов на полосы для вырубки
                costPress = insaincalc.calcManualPress(n_items,materialID,modeProduction);
                break;
        }

        // Рассчитываем стоимость дополнительных опций
        let costOptions = {cost:0,price:0,time:0};
        // добавляем к цене нумерацию
        if (options.has('isNumber')) {
            costOptions.cost += 0.75*n_items;
            costOptions.price += 1.0*n_items;
            costOptions.time += 0.05;
        }
        // добавляем к цене штрихкод
        if (options.has('isBarcode')) {
            costOptions.cost += 1.0*n_items;
            costOptions.price += 2.0*n_items;
            costOptions.time += 0.1;
        }
        // добавляем к цене переменные данные
        if (options.has('isVariables')) {
            costOptions.cost += 3.0*n_items;
            costOptions.price += 5.0*n_items;
            costOptions.time += 0.1;
        }
        // добавляем к цене скругление
        if (options.has('isRounding')) {
            let costRounding = insaincalc.calcRounding(n_items,materialID,modeProduction);
            costOptions.cost += costRounding.cost;
            costOptions.price += costRounding.price;
            costOptions.time += costRounding.time;
        }

        if (isMakeForm) {costForm = insaincalc.calcForm(size,1,difficulty,modeProduction)}

        // рассчитываем стоимость упаковки
        if (options.has('isPacking')) {costPacking =  insaincalc.calcPacking(n,[size[0],size[1],1],options,modeProduction)}
        result.material = insaincalc.mergeMaps(result.material, costPacking.material);
        let baseTimeReady = Math.max(costPrint.timeReady,costCut.timeReady,costRoll.timeReady,costForm.timeReady,costEpoxy.timeReady);

        // итог расчетов
        //полная себестоимость резки
        result.cost = Math.ceil(costPrint.cost
            + costRoll.cost
            + costCut.cost
            + costCutSaber.cost
            + costPress.cost
            + costOptions.cost
            + costForm.cost
            + costEpoxy.cost
            + costPacking.cost);
        // цена с наценкой
        result.price = Math.ceil(costPrint.price
            + costRoll.price
            + costCut.price
            + costCutSaber.price
            + costPress.price
            + costOptions.price
            + costForm.price
            + costEpoxy.price
            + costPacking.price) * (1 + insaincalc.common.marginBadge);
        // времязатраты
        result.time = Math.ceil((costPrint.time
            + costRoll.time
            + costCut.time
            + costCutSaber.time
            + costPress.time
            + costOptions.time
            + costForm.time
            + costEpoxy.time
            + costPacking.time)* 100) / 100;
        //считаем вес в кг.
        result.weight = Math.ceil((costPrint.weight
            + costCut.weight
            + costEpoxy.weight
            + costPacking.weight)* 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета стоимости изготовления акриловых магнитов
insaincalc.calcAcrylicMagnets = function calcAcrylicMagnets(n,magnetID,color,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //	magnetID - ID акриловой заготовки
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
        let costМagnetBlank = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

        // добавляем стоимость заготовки
        let magnet = insaincalc.findMaterial("magnet",magnetID);
        costМagnetBlank.cost = magnet.cost * n;
        costМagnetBlank.price = costМagnetBlank.cost * (1 + insaincalc.common.marginMaterial);
        result.material.set(magnetID,[magnet.name,magnet.size,n]);

        // рассчитываем стоимость изготовления бумажной вставки
        let size = magnet.size;
        let sizeInsert = magnet.sizeInsert;
        let materialID = 'PaperCoated115M';
        let margins = [2,2,2,2];
        let interval = 4;
        let optionsInsert =  new Map();
        costInsert = insaincalc.calcPrintSheet(n,sizeInsert,color,margins,interval,materialID,optionsInsert,modeProduction);
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
            + costМagnetBlank.cost
            + costPacking.cost;
        // цена с наценкой
        result.price = (costInsert.price
            + costSetInsert.price
            + costМagnetBlank.price
            + costPacking.price) * (1 + insaincalc.common.marginAcrylicKeychain);
        // время затраты
        result.time = costInsert.time
            + costSetInsert.time
            + costМagnetBlank.time
            + costPacking.time;
        //считаем вес в кг.
        result.weight = costInsert.weight
            + costМagnetBlank.weight
            + costPacking.weight;
        result.timeReady = result.time + Math.max(costInsert.timeReady,
            costSetInsert.timeReady,
            costPacking.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};