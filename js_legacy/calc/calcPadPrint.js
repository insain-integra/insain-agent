// Функция расчета стоимости тампопечати
insaincalc.calcPadPrint = function calcPadPrint(n,sizeItem,materialID,color,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	sizeItem - размер изделия, [ширина, длинна, высота]
    //	materialID - материал поверхности, типа plastic, metal, glass
    //  color - кол-во цветов 1-2
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
        let tool = insaincalc.tools['TIC177'];
        let camera = insaincalc.tools['TICUV300'];
        if ((tool == undefined) || (camera == undefined)){
            throw (new ICalcError('Не обнаружены данные для оборудования тампопечати'))
        }

        let baseTimeReady = tool.baseTimeReady;
        if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady};
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];

        // проверяем как задан размер, и определяем сложность печати и соот. скорость печати в 1 цвет
        let diffPrint = 0;
        if (sizeItem instanceof Array) {
            if (Math.max(sizeItem[0],sizeItem[1],sizeItem[1]) > 50) {
                diffPrint = 1;
            }
        } else {
            // сложность печати от размера
            const diff = {
                'isSmallItems':0,
                'isLargeItems':1
            }
            diffPrint = diff[sizeItem];
        }
        let processPerHour = tool.processPerHour[diffPrint];

        // объем брака от тиража
        let defects = (tool.defects.find(item => item[0] >= n))[1]; //находим процент брака от тиража
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства

        // расчет расхода материалов при печати
        let costMaterial = 0;
        const nameMaterials = ['costSmallTampon','costLargeTampon','costPaint', 'costSolvent', 'costCleaner', 'costFilm'];
        for (let nameMaterial of nameMaterials) {
            costMaterial += tool[nameMaterial][0] * (tool[nameMaterial][1] + tool[nameMaterial][2] * (Math.ceil(n/100) - 1));
        }
        if (diffPrint == 0) {
            costMaterial += tool['costSmallTampon'][0] * (tool['costSmallTampon'][1] + tool['costSmallTampon'][2] * (Math.ceil(n/100) - 1));
        } else {
            costMaterial += tool['costLargeTampon'][0] * (tool['costLargeTampon'][1] + tool['costLargeTampon'][2] * (Math.ceil(n/100) - 1));
        }
        costMaterial = costMaterial * color; // считаем расход для каждого цвета
        costMaterial += tool['costCliche'] * (1 + diffPrint * (color - 1));
        costMaterial *= insaincalc.common.USD;// перевели в руб.

        // время подготовки клише
        let timePrepareCliche = 0.25 * (1 + diffPrint * (color - 1));
        // время замеса краски
        let timePreparePaint = 0.02 * color;
        if (options.has('isPantone')) {
            timePreparePaint += 0.2 * color;
        }
        // время распаковки и упаковки изделий
        let timePacking = 0;
        if (options.has('isPacking')) {
            timePacking += 0.003 * n;
        }
        // время приладки и печати
        let timePrepare = tool.timePrepare * modeProduction; // время подготовки к тампопечати
        let timePrint = (n / processPerHour  + timePrepare) * color + timePacking;// время печати
        // стоимость использование тампонного станка включая амортизацию
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации тампонного станка
        let costPrint = costDepreciationHour * timePrint; //стоимость использования
        // стоимость использование уф-сушки включая амортизацию
        costDepreciationHour = camera.cost / camera.timeDepreciation / camera.workDay / camera.hoursDay; //стоимость часа амортизации тампонного станка
        let timeDry = 0.5; // время сушки
        let costDry = costDepreciationHour * timeDry; //стоимость использования сушки
        let costProcess = costPrint + costDry;
        let timeOperator = timePrepareCliche + timePreparePaint + timePrint;
        // стоимость работы оператора
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);

        // добавляем к цене
        let isMaterial = 'isMaterial';
        if (options.has('Material')) {
            isMaterial = options.get('Material')
        }
        if (isMaterial == 'isMaterialCustomer') {
            // если материал заказчика то делаем наценку на печать
            defects += 0.25;
        }

        // окончательный расчет
        result.cost = Math.ceil(costMaterial + costProcess + costOperator) * (1 + defects); //полная себестоимость печати тиража
        result.price = Math.ceil((costProcess + costOperator) * (1 + defects + insaincalc.common.marginOperation + insaincalc.common.marginPadPrint) +
            costMaterial * (1 + defects + insaincalc.common.marginMaterial + insaincalc.common.marginPadPrint));
        result.time = Math.ceil((timeOperator + timeDry)* 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = 0; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    };
};