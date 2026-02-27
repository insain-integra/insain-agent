// Функция расчета стоимости печати на холсте и картин на подрамнике
insaincalc.calcCanvas = function calcCanvas(n,size,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделей
    //	size - размер изделия, [ширина, высота]
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
    let printerID = 'HPLatex335';
    let materialID = 'CanvasDLCNM320';
    let frameID = 'CanvasFrame4520';
    try {
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costFrame = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetCanvas = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

        // расчет печати
        costPrint = insaincalc.calcPrintRoll(n,size,materialID,printerID,options,modeProduction)
        result.material = insaincalc.mergeMaps(result.material, costPrint.material);
        // расчет стоимости натяжки на раму
        let isFrame = false;
        if (options.has('isFrame')) {isFrame = options.get('isFrame')}
        if (isFrame) {
            let segments = [[size[0],2],[size[1],2]];
            costFrame = insaincalc.calcBaguette(n,segments,frameID,options,modeProduction);
            costSetCanvas = insaincalc.calcSetCanvasFrame(n,size,modeProduction);
            result.material = insaincalc.mergeMaps(result.material, costFrame.material);
        }

        // окончательный расчет
        result.cost = costPrint.cost + costFrame.cost + costSetCanvas.cost ; //полная себестоимость печати тиража
        result.price = (costPrint.price + costFrame.price + costSetCanvas.price) * (1 + insaincalc.common.marginCanvas);
        result.time =  costPrint.time + costFrame.time + costSetCanvas.time;
        result.timeReady = result.time + Math.max(costPrint.timeReady,costFrame.timeReady,costSetCanvas.timeReady); // время готовности
        result.weight = costPrint.weight + costFrame.weight;
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета натяжки холста на раму
insaincalc.calcSetCanvasFrame = function calcSetCanvasFrame(n,size,modeProduction = 1) {
    //Входные данные
    //  n - кол-во
    //  size - размер рамы
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["SetCanvasFrame"];
    let len = [size[0],size[1],size[0],size[1]]; // задаем длины сторон изделия
    let sumLen = 0;
    try {
        // считаем длинну натяжки
        sumLen = len.reduce((sum, x) => sum + x, 0);
        if (sumLen > 0) {
            sumLen *= n / 1000; // умножили на кол-во изделий, перевели длинну из мм в м
            let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
            let timeProcess = sumLen / tool.processPerHour + timePrepare; //считаем время натяжки с учетом времени на подготовку к запуску
            let timeOperator = timeProcess; //считаем время затраты оператора участка
            let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
            let costProcess = costDepreciationHour * timeProcess + sumLen * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
            let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
            result.cost = costProcess + costOperator;//полная себестоимость резки
            result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
            result.time = Math.ceil(timeProcess * 100) / 100;
        }
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета стоимости изготовления багета/подрамника
insaincalc.calcBaguette = function calcBaguette(n,segments,profileID,options,modeProduction = 1) {
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
    let costAsseblingFrame = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
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
        // Расчет стоимости стыковки рамы
        let timeAsseblingFrame = (numCut/2 * 480) / 3600;
        let timeOperator = timeAsseblingFrame; //считаем время затраты оператора участка
        let costOperator = timeOperator * insaincalc.common.costOperator;
        costAsseblingFrame.cost = costOperator;
        costAsseblingFrame.price = costAsseblingFrame.cost * (1 + insaincalc.common.marginOperation);
        costAsseblingFrame.time = timeOperator;
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
        result.cost = costMaterial + costCut.cost + costAsseblingFrame.cost + costSetHanger.cost;//полная себестоимость нанесения скотча
        // цена с наценкой
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial)
            + costCut.price
            + costAsseblingFrame.price
            + costSetHanger.price;
        // время затраты
        result.time = costCut.time + costAsseblingFrame.time;
        //считаем вес в кг.
        result.weight = profile.weight * lenProfile / 1000 + costSetHanger.weight;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.material.set(profileID,[profile.name,profile.size,numProfile])
        result.material = insaincalc.mergeMaps(result.material, costSetHanger.material);
        return result;
    } catch (err) {
        throw err
    }
};