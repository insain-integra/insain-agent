// Функция расчета стоимости печати на УФ принтере
insaincalc.calcUVPrint = function calcUVPrint(n,size,sizeItem,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	size - размер области печати, [ширина, длинна]
    //	sizeItem - размер изделия, [ширина, длинна]
    //	materialID - материал поверхности
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
        // Считываем данные по оборудованию и материалам
        let paramPrint = options.get('isUVPrint');
        //  resolution - разрешение качества печати, 0 - стандарт, 1, 2
        let resolution = paramPrint['resolution'];
        //	color - цветность печати, вида '4+0'
        let color = paramPrint['color'];
        //	surface - вид печати, плоская или круговая
        let surface = paramPrint['surface'];
        let printerID = paramPrint['printerID'];
        let doubleApplication = paramPrint['isDoubleApplication'] ? 2:1;

        let printer = insaincalc.printer[printerID];
        if (printer == undefined) {
            throw (new ICalcError('Не обнаружены данные для принтера'))
        }
        let interval = 5; // интервал раскладки изделий на принтере
        let margins = printer.margins;
        let baseTimeReady = printer.baseTimeReady;
        if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady};
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
        // проверяем влазит ли изделие в принтер
        let layoutOnPrinter = insaincalc.calcLayoutOnSheet(sizeItem, printer.maxSize, margins, interval);
        if (layoutOnPrinter.num == 0) {
            throw (new ICalcError('Размер изделия больше допустимого'))
        }
        // проверяем верно ли заданы размеры области печати
        let layoutOnItem = insaincalc.calcLayoutOnSheet(size,sizeItem);
        if (layoutOnItem.num == 0) {
            throw (new ICalcError('Область печати больше изделия'))
        }

        let defects = (printer.defects.find(item => item[0] >= n))[1]; //находим процент брака от тиража
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства

        // считаем раскладку изделий на уф-ке
        let volPrint = 0;
        let volMaterial = 0;
        let numLoad = 0;
        let timePrepare = 0;
        if (surface == 'isPlain') {
            // располагаем изделия по возможности наиболее длинной стороной области печати
            let alongLong = 0;
            if ((size[0] > size[1] && sizeItem[0] > sizeItem[1]) || (size[0] < size[1] && sizeItem[0] < sizeItem[1])) {
                alongLong = 1;
            } else {
                alongLong = -1;
            }
            layoutOnPrinter = insaincalc.calcLayoutOnSheet(sizeItem, printer.maxSize, margins, interval, alongLong);
            if (layoutOnPrinter.num == 0) {
                layoutOnPrinter = insaincalc.calcLayoutOnSheet(sizeItem, printer.maxSize, margins, interval);
            }
            if (layoutOnPrinter.alongLong) {
                let w = (layoutOnPrinter.numAlongLongSide - 1) * Math.max(sizeItem[0], sizeItem[1]) + (layoutOnPrinter.numAlongLongSide - 1) * interval;
                let h = 0;
                if (alongLong == 1) {
                    h = layoutOnPrinter.numAlongShortSide * Math.min(size[0], size[1]) + (layoutOnPrinter.numAlongShortSide - 1) * interval;
                    w += Math.max(size[0], size[1]);
                } else {
                    h = layoutOnPrinter.numAlongShortSide * Math.max(size[0], size[1]) + (layoutOnPrinter.numAlongShortSide - 1) * interval;
                    w += Math.min(size[0], size[1]);
                }
                volPrint = w * h * n / layoutOnPrinter.num;
            } else {
                let w = (layoutOnPrinter.numAlongLongSide - 1) * Math.min(sizeItem[0], sizeItem[1]) + (layoutOnPrinter.numAlongLongSide - 1) * interval;
                let h = 0;
                if (alongLong == 1) {
                    h = layoutOnPrinter.numAlongShortSide * Math.max(size[0], size[1]) + (layoutOnPrinter.numAlongShortSide - 1) * interval;
                    w += Math.min(size[0], size[1]);
                } else {
                    h = layoutOnPrinter.numAlongShortSide * Math.min(size[0], size[1]) + (layoutOnPrinter.numAlongShortSide - 1) * interval;
                    w += Math.max(size[0], size[1]);
                }
                volPrint = w * h * n / layoutOnPrinter.num;
            }
            volMaterial = size[0]*size[1]*n*(1+defects);
            numLoad = Math.ceil(n / layoutOnPrinter.num); // кол-во загрузок изделий в принтер
            timePrepare = printer.timePrepare * modeProduction;
        } else {
            numLoad = Math.ceil(n*(1+defects));
            volMaterial = size[0]*size[1]*numLoad;
            volPrint = volMaterial;
            timePrepare = printer.timePrepareAround * modeProduction;
        }
        volPrint /= 1000000; // переводим в м2
        volMaterial /= 1000000; // переводим в м2
        volPrint *= doubleApplication; // умножаем объем печати на коэф.двухсторонней печати
        numLoad *=  doubleApplication; // умножаем кол-во загрузок  на коэф.двухсторонней печати
        // расчет печати
        let coeff = 1; // коэффициент скорости печати зависит от цветности
        coeff += color == '4+1' ? 1 : 0;
        coeff += color == '4+2' ? 2 : 0;
        let meterPerHour = printer.meterPerHour[resolution] / coeff; // скорость печати в зависимости от разрешения и цветности
        timePrepare += printer.timeLoad * numLoad; // добавляем время загрузки изделий в принтер
        let timePrint = volPrint * (1 + defects) /  meterPerHour + timePrepare; //считаем время на печать с учетом времени на подготовку к запуску
        let timeOperator = 0.5 * (timePrint + timePrepare); //считаем время затраты оператора печати
        let costDepreciationHour = printer.cost / printer.timeDepreciation / printer.workDay / printer.hoursDay; //стоимость часа амортизации оборудования

        //расчет скидки от объема если она есть
        let discount = 0;
        if (printer.discount != undefined) {
            let idx = (printer.discount.findIndex(item => item[0] > volPrint)) - 1;
            if (idx >= 0) {discount = printer.discount[idx][1]}
        }

        // расчет стоимости самой печати исходя из цветности
        let costPrintMeter = 0;
        costPrintMeter += color == '4+0' ? printer.costProcess[0] : 0;
        costPrintMeter += color == '1+0' ? printer.costProcess[0] : 0;
        costPrintMeter += color == '4+1' ? printer.costProcess[0] + printer.costProcess[1] : 0;
        costPrintMeter += color == '4+2' ? printer.costProcess[0] + printer.costProcess[1] + printer.costProcess[2]: 0;
        if (costPrintMeter == 0) {
            throw (new ICalcError('Не задана или неверно задана цветность печати'))
        }
        let costPrint = costDepreciationHour * timePrint + costPrintMeter * (1 - discount) * volPrint; //считаем стоимость включая амортизацию оборудования, краски, голову и др. расходники
        let costOperator = timeOperator * ((printer.costOperator > 0) ? printer.costOperator : insaincalc.common.costOperator);

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

        // добавляем к цене
        let isMaterial = 'isMaterial';
        if (options.has('Material')) {
            isMaterial = options.get('Material')
        }
        let coeffMaterialCustomer = 1;
        if (isMaterial == 'isMaterialCustomer') {
            // если материал заказчика то делаем наценку на печать
            coeffMaterialCustomer = 1.25;
        }

        // окончательный расчет
        result.cost = Math.ceil(costPrint + costOperator + costOptions.cost) * coeffMaterialCustomer; //полная себестоимость печати тиража
        result.price = Math.ceil(result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginUVPrint) + costOptions.price);
        result.time = Math.ceil((timePrint  + costOptions.time)* 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = 0; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    };
};