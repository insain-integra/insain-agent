// Функция расчета стоимости ламинации
insaincalc.calcLamination = function calcLamination(n,size,laminatID,doubleSide = true,modeProduction = 1) {
    // Входные данные:
    //	n - тираж изделий
    //	size - размер изделия, [ширина, высота]
    //	laminatID - пленка для ламинации в виде ID из данных материалов
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    // Выходные данные:
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    let WEIGHTLAMINAT = 0.0011 // вес 1мкм/1м2 пленки для ламинации
    let laminator = insaincalc.laminator["FGKFM360"];
    let laminat = insaincalc.laminat.Laminat[laminatID];
    if (laminat.size[1] == 0) { // если выбрана рулонная ламинация
       let num = doubleSide ? n : Math.ceil(n/2);
       let layoutOnRoll = insaincalc.calcLayoutOnRoll(1, size, laminat.size,20); // считаем что листы подавать можем только последовательно
       let defects = (laminator.defects.find(item => item[0] >=num))[1]; //находим процент брака от тиража
       defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
       let length = (layoutOnRoll.length+20)*num*(1+defects)/1000; // длинна ламинации с учетом брака
       let meterPerHour = (laminator.meterPerHour.find(item => item[0] >= laminat.density))[1]; //находим скорость ламинации для данного материала
        // расчет стоимости ламинации
       let timePrepare = laminator.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
       let timeLamination  = length/meterPerHour+timePrepare; //считаем время ламинации с учетом времени на подготовку к запуску
       let timeCut = 2*num*(10/3600); // считаем время ручной подрезки заламинированных изделий, 5 сек на рез
       let timeOperator = timeLamination + timeCut; //считаем время затраты оператора ламинации
       let costLaminationDepreciationHour = laminator.cost/laminator.timeDepreciation/laminator.workDay/laminator.hoursDay; //стоимость часа амортизации оборудования
       let costMaterial = laminat.cost*2*length; //считаем стоимость материала с учетом что расход материала идет сразу с двух валов
       let costLamination = costLaminationDepreciationHour*timeLamination //считаем стоимость использование оборудование
       let costOperator = timeOperator*((laminator.costOperator > 0)?printer.costOperator:insaincalc.common.costOperator);
       // окончательный расчет
        result.cost = costMaterial+costLamination+costOperator; //полная себестоимость ламинации тиража
        result.price = costMaterial*(1+insaincalc.common.marginMaterial+insaincalc.common.marginLamination)
            +(costLamination+costOperator)*(1+insaincalc.common.marginOperation+insaincalc.common.marginLamination);
       result.time =  timeLamination;
       result.weight = n * (doubleSide ? 2 : 1) * laminat.density*size[0]*size[1]*WEIGHTLAMINAT/1000000; //считаем вес в кг.
       result.material.set(laminatID,[laminat.name,laminat.size,2 * length]);
    } else { // если не рулонная, значит пакетная ламинация
       let num = n;
       let defects = (laminator.defects.find(item => item[0] >=num))[1]; //находим процент брака от тиража
       defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
       let numWithDefects = Math.ceil(num*(1+defects)); // расход материала с учетом брака
       let meterPerHour = (laminator.meterPerHour.find(item => item[0] >= laminat.density))[1]; //находим скорость ламинации для данного материала
       let layoutOnLaminator = insaincalc.calcLayoutOnRoll(1,laminat.size,laminator.maxSize);
       let sheetPerHour = Math.ceil(meterPerHour/(layoutOnLaminator.length/1000));
       // расчет стоимости ламинации
       let timePrepare = laminator.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
       let timePacking = numWithDefects*(20/3600); // считаем время упаковки изделий в пакетный ламинат, 20 сек на лист
       let timeLamination  = numWithDefects/sheetPerHour+timePrepare+timePacking; //считаем время ламинации с учетом времени на подготовку к запуску
       let timeOperator = timeLamination; //считаем время затраты оператора ламинации
       let costLaminationDepreciationHour = laminator.cost/laminator.timeDepreciation/laminator.workDay/laminator.hoursDay; //стоимость часа амортизации оборудования
       let costMaterial = laminat.cost*numWithDefects; //считаем стоимость материала
       let costLamination = costLaminationDepreciationHour*timeLamination; //считаем стоимость использование оборудование
       let costOperator = timeOperator*((laminator.costOperator > 0)?laminator.costOperator:insaincalc.common.costOperator);
       // окончательный расчет
       result.cost = costMaterial+costLamination+costOperator; //полная себестоимость ламинации тиража
       result.price = costMaterial*(1+insaincalc.common.marginMaterial+insaincalc.common.marginLamination)
           +(costLamination+costOperator)*(1+insaincalc.common.marginOperation+insaincalc.common.marginLamination);
       result.time =  timeLamination;
       result.weight = num*laminat.density*laminat.size[0]*laminat.size[1]*WEIGHTLAMINAT/1000000; //считаем вес в кг.
       result.material.set(laminatID,[laminat.name,laminat.size,numWithDefects]);
    }
    return result;
};

// Функция расчета стоимости широкоформатной ламинации
insaincalc.calcLaminationWide = function calcLaminationWide(n,size,modeProduction = 1) {
    // Входные данные:
    //	n - тираж изделий
    //	size - размер изделия, [ширина, высота]
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    // Выходные данные:
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    let WEIGHTLAMINAT = 0.0011 // вес 1мкм/1м2 пленки для ламинации
    let laminator = insaincalc.laminator["LaminatorWide"];
    let laminatID = "LaminatDLCLAM";
    let laminat = insaincalc.laminat.Laminat[laminatID];
    let defects = (laminator.defects.find(item => item[0] >=n))[1]; //находим процент брака от тиража
    defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
    let meterPerHour = laminator.meterPerHour; //находим скорость ламинации для данного материала
    // расчет стоимости ламинации
    let volMaterial = n*size[0]*size[1]*(1+defects)/1000000;
    if (volMaterial < 1) {volMaterial = 1}
    let timePrepare = laminator.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let timeProcess  = volMaterial/meterPerHour+timePrepare; //считаем время ламинации с учетом времени на подготовку к запуску
    let timeOperator = timeProcess; //считаем время затраты оператора ламинации
    let costDepreciationHour = laminator.cost/laminator.timeDepreciation/laminator.workDay/laminator.hoursDay; //стоимость часа амортизации оборудования
    let costMaterial = laminat.cost*volMaterial; //считаем стоимость материала
    let costLamination = costDepreciationHour*timeProcess+volMaterial*laminator.costOperation; //считаем стоимость использование оборудование
    let costOperator = timeOperator*((laminator.costOperator > 0)?laminator.costOperator:insaincalc.common.costOperator);
    // окончательный расчет
    result.cost = costMaterial+costLamination+costOperator; //полная себестоимость печати тиража
    result.price = costMaterial * (1 + insaincalc.common.marginMaterial) +
        (costLamination + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginLaminationWide );
    result.time =  Math.ceil(timeProcess*100)/100;
    result.weight = Math.ceil((volMaterial*laminat.density*WEIGHTLAMINAT)*100)/100; //считаем вес в кг.
    result.material.set(laminat.name,[laminat.size,volMaterial/laminat.size[0]]);
    return result;
};


// Функция расчета стоимости накатки на ламинаторе
insaincalc.calcLaminationRoll = function calcLaminationRoll(n,size,modeProduction = 1) {
    // Входные данные:
    //	n - тираж изделий
    //	size - размер изделия, [ширина, высота]
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    // Выходные данные:
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    let laminator = insaincalc.laminator["FGKFM360"];
    let defects = (laminator.defects.find(item => item[0] >= n))[1]; //находим процент брака от тиража
    defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
    let numWithDefects = Math.ceil(n*(1+defects)); // расход материала с учетом брака
    let meterPerHour = 25; // зададим скорость прикатки 25мп/час с учетом что работает один человек
    let layoutOnLaminator = insaincalc.calcLayoutOnRoll(1,size,laminator.maxSize);
    let sheetPerHour = Math.ceil(meterPerHour/(layoutOnLaminator.length/1000));
    // расчет стоимости ламинации
    let timePrepare = laminator.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let timeRoll  = numWithDefects/sheetPerHour+timePrepare; //считаем время прикатки с учетом времени на подготовку к запуску
    let timeOperator = timeRoll; //считаем время затраты оператора ламинации
    let costLaminationDepreciationHour = laminator.cost/laminator.timeDepreciation/laminator.workDay/laminator.hoursDay; //стоимость часа амортизации оборудования
    let costRoll = costLaminationDepreciationHour*timeRoll; //считаем стоимость использование оборудование
    let costOperator = timeOperator*((laminator.costOperator > 0)?laminator.costOperator:insaincalc.common.costOperator);
    // окончательный расчет
    result.cost = Math.ceil(costRoll+costOperator); //полная себестоимость накатки тиража
    result.price = Math.ceil((costRoll+costOperator)*(1+insaincalc.common.marginOperation+insaincalc.common.marginLamination));
    result.time =  Math.ceil(timeOperator*100)/100;
    result.weight = 0; //считаем вес в кг.
    return result;
};
