// Функция расчета стоимости печати на лазерном или струйном принтере и постобработки листовой продукции
insaincalc.calcPrintSheet = function calcPrintSheet(n,size,color,margins,interval,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	size - размер изделия, [ширина, высота]
    //	color - цветность печати, вида '4+0'
    //  margins - минимальные вылеты для изделия
	//	interval - отступы между изделиями
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
    let baseTimeReady = insaincalc.common.baseTimeReadyPrintSheet;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    try {
        // Считываем данные по оборудованию и материалам
        let printerID = "KMBizhubC220";
        if (options.has('printer')) {
            printerID = options.get('printer')['printerID'];
        }
        let printer = insaincalc.printer[printerID];
        if (printer == undefined) {throw (new ICalcError('Не обнаружены данные для принтера'))}
        let laminator = insaincalc.laminator["FGKFM360"];
        if (laminator == undefined) {throw (new ICalcError('Не обнаружены данные ламинатора'))}
        let cutter = insaincalc.cutter["KWTrio3971"];
        if (cutter == undefined) {throw (new ICalcError('Не обнаружены данные гильотины'))}
        let material = insaincalc.sheet.Paper[materialID];
        if (material == undefined) {throw (new ICalcError('Не обнаружены данные по материалу'))}
        let sizeSheet = material.size;
        let laminatID = 0;
        if (options.has('isLamination')) {laminatID = options.get('isLamination');}
        // Объявляем нулевые стоимости
        let costCut = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costLamination = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCutGuillotine = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let numSheet = 0;
        let layoutOnMaterial = {num:1,numAlongLongSide:1,numAlongShortSide:1};
        let sum_margins = [0,0,0,0]
        if (color != '0+0') {
            if (margins != - 1) {sum_margins = margins.map(function(value, index){ return value + printer.margins[index] });}
        } else {
            interval = 0;
        }
        // проверяем влазит ли материал в принтер, если нет то считаем доп. резку
        let layoutOnPrinter = insaincalc.calcLayoutOnSheet(sizeSheet,printer.maxSize);
        if (layoutOnPrinter.num == 0) {
            sizeSheet = printer.maxSize; // выбираем новый размер листа исходя из размера макс. листа печати принтера
            // сколько печатных листов размещается на материале
            layoutOnMaterial = insaincalc.calcLayoutOnSheet(sizeSheet,material.size);
            let layoutOnSheet = insaincalc.calcLayoutOnSheet(size,sizeSheet,sum_margins,interval);
            if (layoutOnSheet.num == 0) {throw (new ICalcError('Изделие не помещается на материал'))}
            numSheet = Math.ceil(n/layoutOnSheet.num); //Сколько листов всего требуется
            // проверяем влазит ли материал в гильотину, если нет то режем на роликовом
            let layoutOnCutter = insaincalc.calcLayoutOnSheet(material.size,cutter.maxSize);
            if (layoutOnCutter.num > 0) {
                costCut = insaincalc.calcCutGuillotine(numSheet,sizeSheet,material.size,materialID,modeProduction);
            } else {
                costCut = insaincalc.calcCutRoller(numSheet,sizeSheet,materialID,'KWTrio3026',options,modeProduction);
                if (costCut == undefined) {throw (new ICalcError('Материал не помещается в резак'))}
            }
        } else {
            let layoutOnSheet = insaincalc.calcLayoutOnSheet(size,sizeSheet,sum_margins,interval);
            if (layoutOnSheet.num == 0) {throw (new ICalcError('Размер изделия больше допустимого'))}
            numSheet = Math.ceil(n/layoutOnSheet.num); //Сколько листов всего требуется
        }

        let numSheetToPrint = numSheet;
        // Считываем коэф. брака каждого оборудования в обратной последовательности
        let defectsLaminator = (laminator.defects.find(item => item[0] >= numSheet))[1];
        if (laminatID != 0) {numSheetToPrint = Math.ceil(numSheetToPrint * (1 + defectsLaminator))}
        let defectsPrinter = (printer.defects.find(item => item[0] >= numSheetToPrint))[1];

        // расчет печати
        switch (printerID) {
            case "EPSONWF7610":
                let quality = options.get('printer')['quality'];
                if (quality == undefined) {
                    quality = 1
                }
                costPrint = insaincalc.calcPrintInkJet(numSheetToPrint, sizeSheet, quality, color, materialID, printerID, modeProduction);
                break;
            case "DTFTransfer":
                costPrint = insaincalc.calcPrintInkJet(numSheetToPrint, sizeSheet, 0, color, materialID, printerID, modeProduction);
                break;
            case "KMBizhubC220":
                costPrint = insaincalc.calcPrintLaser(numSheetToPrint, sizeSheet, color, materialID, printerID, modeProduction);
                break;

        }
        // расчет ламинации, если есть
        let doubleSideLamination = true; // по умолчанию двухстороння ламинация
        if (laminatID != 0) {
            let laminat = insaincalc.laminat.Laminat[laminatID];
            if (laminat.size[1] == 0) {
                costLamination = insaincalc.calcLamination(numSheet,sizeSheet,laminatID,doubleSideLamination,modeProduction);
            } else {
                costLamination = insaincalc.calcLamination(n,size,laminatID,doubleSideLamination,modeProduction);
            }
            result.material = insaincalc.mergeMaps(result.material,costLamination.material);
        }

        let costMaterial = material.cost*Math.ceil(numSheetToPrint*(1+defectsPrinter))/layoutOnMaterial.num; //считаем расход материала
        result.material.set(materialID,[material.name,material.size,Math.ceil(numSheetToPrint*(1+defectsPrinter)/layoutOnMaterial.num)]);

        // расчет резки на гильотине
        if (! options.has('noCut')) {
            costCutGuillotine = insaincalc.calcCutGuillotine(numSheet, size, sizeSheet, materialID, sum_margins, interval, modeProduction);
        }

        // Рассчитываем стоимость дополнительных опций
        let costOptions = {cost:0,price:0,time:0};

        // добавляем к цене нумерацию
        if (options.has('isNumber')) {
            costOptions.cost += 0.75*n;
            costOptions.price += 1.0*n;
            costOptions.time += 0.05;
        }
        // добавляем к цене штрихкод
        if (options.has('isBarcode')) {
            costOptions.cost += 1.0*n;
            costOptions.price += 2.0*n;
            costOptions.time += 0.1;
        }
        // добавляем к цене переменные данные
        if (options.has('isVariables')) {
            costOptions.cost += 3.0*n;
            costOptions.price += 5.0*n;
            costOptions.time += 0.1;
        }
        // добавляем к цене скругление
        if (options.has('isRounding')) {
            let costRounding = insaincalc.calcRounding(n,materialID,modeProduction);
            costOptions.cost += costRounding.cost;
            costOptions.price += costRounding.price;
            costOptions.time += costRounding.time;
        }
        // добавляем к цене вырубку отверстий
        if (options.has('isHole')) {
            let numHole = options.get('isHole');
            let costPunching = insaincalc.calcPunching(n*numHole,materialID,modeProduction);
            costOptions.cost += costPunching.cost;
            costOptions.price += costPunching.price;
            costOptions.time += costPunching.time;
        }
        // добавляем к цене биговку/перфорацию
        if (options.has('isCrease')) {
            let numCrease = options.get('isCrease');
            let costCrease = insaincalc.calcCrease(n,numCrease,size,materialID,modeProduction);
            costOptions.cost += costCrease.cost;
            costOptions.price += costCrease.price;
            costOptions.time += costCrease.time;
        }
        // окончательный расчет
        result.cost = costMaterial
            +costCut.cost
            +costPrint.cost
            +costLamination.cost
            +costCutGuillotine.cost
            +costOptions.cost; //себестоимость тиража
        result.price = (costMaterial*(1+insaincalc.common.marginMaterial)
            +costCut.price
            +costPrint.price
            +costLamination.price
            +costCutGuillotine.price
            +costOptions.price)*(1+insaincalc.common.marginPrintSheet); //цена тиража
        result.time =  Math.ceil((costCut.time+costPrint.time+costLamination.time+costCutGuillotine.time+costOptions.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(baseTimeReady,costPrint.timeReady); // время готовности
        result.weight = costPrint.weight+costLamination.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};
