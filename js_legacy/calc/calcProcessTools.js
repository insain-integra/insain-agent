// Функция расчета стоимости пробивки отверстия в листовой продукции
insaincalc.calcPunching = function calcPunching(n,materialID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для скругления
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

    let tool = insaincalc.tools["Warrior"];
    let typesMaterial = ['sheet','roll','hardsheet']; // список типов материалов в которых ищем данные по нашему материалу.
    let material = new Map();
    if (materialID != "") {
        for (let typeMaterial of typesMaterial) {
            material = insaincalc.findMaterial(typeMaterial, materialID);
            if (material != undefined) break;
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
    let NumSheet80 = Math.ceil(n*material.density/80); // пересчитываем пачку в листы плотностью 80гр
    // let numPunches = Math.ceil(NumSheet80/tool.maxSheet); // на сколько пачек нужно разделить стопу для скругления
    let numPunches = n; // на сколько пачек нужно разделить стопу для скругления
    let timePrepare = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let timeProcess = numPunches / tool.processPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
    let timeOperator = timeProcess; //считаем время затраты оператора участки резки
    let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
    let costProcess = costDepreciationHour * timeProcess + numPunches * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
    let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
    result.cost = costProcess + costOperator;//полная себестоимость резки
    result.price =result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
    result.time = Math.ceil(timeProcess * 100) / 100;
    return result;
};

// Функция расчета стоимости скругления листовой продукции
insaincalc.calcRounding = function calcRounding(n,materialID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для скругления
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

    let tool = insaincalc.tools["WarriorAD1"];
    let typesMaterial = ['sheet','roll','hardsheet']; // список типов материалов в которых ищем данные по нашему материалу.
    let material = new Map();
    if (materialID != "") {
        for (let typeMaterial of typesMaterial) {
            material = insaincalc.findMaterial(typeMaterial, materialID);
            if (material != undefined) break;
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
    // let NumSheet80 = Math.ceil(n*material.density/80); // пересчитываем пачку в листы плотностью 80гр
    let NumSheet80 = n;
    let numStack = Math.ceil(NumSheet80/tool.maxSheet); // на сколько пачек нужно разделить стопу для скругления
    let numRounding = 4*numStack; // кол-во скруглений
    let timePrepare = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let timeProcess = numRounding / tool.processPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
    let timeOperator = timeProcess; //считаем время затраты оператора участки резки
    let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
    let costProcess = costDepreciationHour * timeProcess + numRounding * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
    let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
    result.cost = costProcess + costOperator;//полная себестоимость резки
    result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
    result.time = Math.ceil(timeProcess * 100) / 100;
    return result;
};

// Функция расчета стоимости биговки/перфорации отверстия в листовой продукции
insaincalc.calcCrease = function calcCrease(n,crease,size,materialID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для биговки/перфорации
    //  crease - кол-во бигов на изделии
    //  size - размер изделия
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

    let material = insaincalc.sheet.Paper[materialID];
    if (material == undefined) {material = insaincalc.roll.Film[materialID]}
    let tool = insaincalc.tools["CyklosGPM315"];
    let numCrease = n*crease // общее число бигов
    // проверяем помещается ли изделие в биговщик
    try {
        let layoutOnCreaser = insaincalc.calcLayoutOnRoll(1,size,tool.maxSize);
        if (layoutOnCreaser.num == 0) {throw (new ICalcError('Размер изделия больше допустимого для биговки'))}
        let timePrepare = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = numCrease / tool.processPerHour + timePrepare+0.5*timePrepare*(crease-1); //считаем время на резку с учетом времени на подготовку к запуску и приладку к каждому бигу
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + numCrease * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost = costProcess + costOperator;//полная себестоимость резки
        result.price =result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета переплета
insaincalc.calcBinding = function calcBinding(n,size,cover,inner,binding,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для переплета
    //	size - размер изделия, [ширина, высота]
    //  cover - параметры обложки в виде словаря {'coverTop':{'materialID','laminatID','color'},'coverBottom':{'materialID','laminatID','color'}}
    //  inner - параметры внутреннего блока {'materialID','color','numSheet'}
    //	binding - параметры переплета ['bindingID','edge']
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
        let bindingID = options.get('bindingID');
        let tool = insaincalc.tools[bindingID];
        let baseTimeReady = tool.baseTimeReady;
        if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
        // Рассчитываем толщину блокнота
        let numSheet80 = 0;
        let materialCover = insaincalc.findMaterial('sheet',cover['cover']['materialID']);
        if (materialCover != undefined) numSheet80 += materialCover.density;
        let materialBacking = insaincalc.findMaterial('sheet',cover['backing']['materialID']);
        if (materialBacking != undefined) numSheet80 += materialBacking.density;
        for (let value of inner) {
            let materialInner = insaincalc.findMaterial('sheet', value['materialID']);
            numSheet80 += materialInner.density * value['numSheet'];
        }
        numSheet80 = Math.ceil(numSheet80/80); // кол-во листов в пересчете на 80гр
        let numStack = Math.ceil(numSheet80/tool.maxSheetCrease); // на сколько "базовых" пачек надо разделить стопу чтобы проперфорировать
        let thinknessStack = numSheet80/10; // толщина блокнота в мм

        let timePrepare = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки

        let lengthWire = 0;
        if (binding['edge'] == 'short') {
            lengthWire = Math.min(size[0],size[1]);
        } else {
            lengthWire = Math.max(size[0],size[1]);
        }
        numStack = numStack * Math.ceil(lengthWire/tool.maxSize[0]);
        let wire = undefined;
        let wireID = undefined;
        for (let value in insaincalc.misc["MetallBindindWire"]) {
            if (insaincalc.misc["MetallBindindWire"][value].size[0] > thinknessStack + 1) {
                wire = insaincalc.misc["MetallBindindWire"][value];
                wireID = value;
                break;
            }
        }
        if (wire == undefined) {throw (new ICalcError('Размер изделия больше допустимого для переплета'))}
        result.material.set('MetallBindindWire',[wire.name,wire.size,Math.ceil(n * lengthWire/8.75)/wire.size[1]]) // сохраняем расход в долях от рулона
        let timeProcess = timePrepare + n * numStack / tool.сreasePerHour + n / tool.bindingPerHour;
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costMaterial = wire.cost/wire.size[1] * n * lengthWire/8.75; //считаем стоимость пружины
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * numStack * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);

        result.cost = costProcess + costOperator + costMaterial;//полная себестоимость переплета
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial + insaincalc.common.marginProcessManual)
            + (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.weight = Math.ceil(n * lengthWire/8.75) * wire.weight / 1000 //считаем вес в кг.
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета степлирования
insaincalc.calcSetStaples = function calcSetStaples(n,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для переплета
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

    let tool = insaincalc.tools["Bookletmac"];
    let staplesID = 'Staples26_6';
    let staples = insaincalc.findMaterial("misc",staplesID);
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let costMaterial = staples.cost * 2 * n; //считаем стоимость скрепок
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.weight = Math.ceil((staples.weight * n) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time; // время готовности
        result.material.set(staplesID,[staples.name,staples.size,n]);
        return result;
    } catch(err) {
        throw err
    }
};



// Функция расчета люверсовки баннерной продукции
insaincalc.calcEyelet = function calcEyelet(n,size,step,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для люверсовки
    //  size - размер изделия
    //  step - шаг установки люверсов по каждой стороне изделия
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["AMGPPROLUX"];
    let margin = 25; // отступы центров люверсов от краев изделия
    // проверяем помещается ли изделие в биговщик
    let len = [size[0],size[1],size[0],size[1]]; // задаем длины сторон изделия
    let numEyelet = 0;
    try {
        // считаем сколько всего люверсов
        for (let i = 0; i < 4; i++) {
            if (step[i] > 0) {
                numEyelet += Math.round((len[i]-margin*2)/step[i]);
                if ((i < 3) && (step[i+1] == 0)) {numEyelet += 1}
                if ((i == 3) && (step[0] == 0)) {numEyelet += 1}
            }
        }
        if (numEyelet > 0) {
            numEyelet *= n;
            let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
            let timeProcess = numEyelet / tool.processPerHour + timePrepare; //считаем время проклейки с учетом времени на подготовку к запуску
            let timeOperator = timeProcess; //считаем время затраты оператора участка
            let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
            let costProcess = costDepreciationHour * timeProcess + numEyelet * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
            let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
            result.cost = costProcess + costOperator;//полная себестоимость резки
            result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
            result.time = Math.ceil(timeProcess * 100) / 100;
            result.material.set('Люверсы',['Люверсы',0,numEyelet]);
        }
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета люверсовки полиграфической продукции
insaincalc.calcEyeletSheet = function calcEyeletSheet(n,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для люверсовки
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["JOINERC4"];
    let margin = 25; // отступы центров люверсов от краев изделия
    try {
        let numEyelet = n;
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = numEyelet / tool.processPerHour + timePrepare; //считаем время проклейки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + numEyelet * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost = costProcess + costOperator;//полная себестоимость резки
        result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.material.set('Люверсы',['Люверсы 4мм',0,numEyelet]);
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета проклейки края баннерной продукции
insaincalc.calcGluingBanner = function calcGluingBanner(n,size,edge,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  size - размер изделия
    //  edge - края для проклейки
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["GluingBanner"];
    let len = [size[0],size[1],size[0],size[1]]; // задаем длины сторон изделия
    let sumLen = 0;
    try {
        // считаем длинну проклейки
        for (let i = 0; i < 4; i++) {
            if (edge[i] > 0) {sumLen += len[i]*edge[i];}
        }
        if (sumLen > 0) {
            sumLen *= n / 1000; // умножили на кол-во изделий, перевели длинну из мм в м
            let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
            let timeProcess = sumLen / tool.processPerHour + timePrepare; //считаем время проклейки с учетом времени на подготовку к запуску
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

// Функция расчета подрезки материала
insaincalc.calcCuttingEdge = function calcCuttingEdge(n,size,edge,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  size - размер изделия
    //  edge - края для резки
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["CuttingKnife"];
    let len = [size[0], size[1], size[0], size[1]]; // задаем длины сторон изделия
    let sumLen = 0;
    try {
        // считаем номинальную длинну резки (длинна резки менее 1м считается за 1м)
        for (let i = 0; i < 4; i++) {
            if (edge[i] > 0) {
                if (edge[i] > 0) {
                    if (len[i] < 1) {
                        sumLen += 1;
                    } else {
                        sumLen += len[i]*edge[i];
                    }
                }
            }
        }
        if (sumLen > 0) {
            sumLen *= n / 1000; // умножили на кол-во изделий, перевели длинну из мм в м)
            let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
            let timeProcess = sumLen / tool.processPerHour + timePrepare; //считаем время проклейки с учетом времени на подготовку к запуску
            let timeOperator = timeProcess; //считаем время затраты оператора участка
            let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
            let costProcess = costDepreciationHour * timeProcess + sumLen * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
            let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
            result.cost = costProcess + costOperator;//полная себестоимость резки
            result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
            result.time = Math.ceil(timeProcess * 100) / 100;
        }
        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета установки курсора
insaincalc.calcSetCursor = function calcSetCursor(n,cursorID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  cursorID - ID курсора
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["SetCursor"];
    let cursor = insaincalc.findMaterial("calendar",cursorID);
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let costMaterial = cursor.cost * n; //считаем стоимость пружины
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.weight = Math.ceil((cursor.weight * n) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time; // время готовности
        result.material.set(cursorID,[cursor.name,cursor.size,n]);

        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета наклейки стикера на изделие
insaincalc.calcSetSticker = function calcSetSticker(n,size,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  размер стикера
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["SetSticker"];
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost = costProcess + costOperator;//полная себестоимость резки
        result.price = (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.timeReady = result.time; // время готовности

        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета установки ригеля
insaincalc.calcSetRigel = function calcSetRigel(n, width, numSheet, materialID, modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  width - ширина стороны на которую ставиться ригель
    //  numSheet - кол-во листов в пачке
    //  materialID - материал
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let costPunching = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let tool = insaincalc.tools["SetRigel"];
    let rigelID = 'Rigel';
    if (width <= 210) rigelID = rigelID + '150'
    else if (width <= 297) rigelID = rigelID + '200'
    else rigelID = rigelID + '250';
    let rigel = insaincalc.findMaterial("calendar",rigelID);
    try {
        costPunching = insaincalc.calcPunching(n,materialID,modeProduction);
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let costMaterial = rigel.cost * n; //считаем стоимость пружины
        result.cost = costMaterial + costProcess + costOperator + costPunching.cost;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) +
            (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual)+
            costPunching.price;
        result.time = timeProcess + costPunching.time;
        result.weight = Math.ceil((rigel.weight / 1000 * n) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time; // время готовности
        result.material.set(rigelID,[rigel.name,rigel.size,n]);
        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета полимерной заливки
insaincalc.calcEpoxy = function calcEpoxy(n,size,difficulty,options= new Map(),modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  size - размер изделия
    //  difficulty - сложность формы для резки, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
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

    let material = insaincalc.misc.Epoxy['EpoxyPoly'];
    let mixer = insaincalc.tools['VacuumMixerUZLEX'];
    let tool = insaincalc.tools['EpoxyCoating'];
    try {
        let baseTimeReady = tool.baseTimeReady[Math.ceil(modeProduction)];
        let defects = (tool.defects.find(item => item[0] >= n))[1];
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        let numCoating = n * (1 + defects);
        // размеры площади которую нужно залить см2 и кол-во затрачиваемой смолы гр
        let volCoating = numCoating * size[0] * size[1] / 100;
        let volMaterial = volCoating * tool.epoxyPerCM2;
        // скорость заливки для данного изделия
        let speedCoating = (difficulty == 1) ? ((size[0] * size[1]  <= 600) ? tool.processPerHour[2] : ((size[0] * size[1] <= 3600) ? tool.processPerHour[1] : tool.processPerHour[0])) : tool.processPerHour[2]
        // время затраты на заливку и подготовку к заливке
        let timeLayout = 0;
        if (options.has('isLayout')) {timeLayout = numCoating / 1800}
        let timeCoating = volCoating / speedCoating + timeLayout;
        let timePrepare = tool.timePrepare * modeProduction; // время подготовки к заливке
        // кол-во замесов в миксере и время затраты на замесы
        let numMix = Math.ceil(timeCoating / material.exptime); // кол-во замесов
        let volMix = volMaterial / numMix  // вес одного замеса
        let timeMix = numMix * mixer.timeMix + tool.timePrepare * modeProduction; // время затраты на замесы
        // время затраты оператора участка заливки
        timeCoating += timePrepare;
        // стоимость использование оборудование включая амортизацию
        let costDepreciationHour = mixer.cost / mixer.timeDepreciation / mixer.workDay / mixer.hoursDay; //стоимость часа амортизации миксера
        let costProcess = costDepreciationHour * timeMix + numMix * mixer.costProcess; //стоимость использования миксера
        costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации столов для заливки
        costProcess += costDepreciationHour * timeCoating + volMaterial / tool.costProcess; //стоимость использования миксера и столов
        // стоимость работы оператора
        let costOperator = timeMix * ((mixer.costOperator > 0) ? mixer.costOperator : insaincalc.common.costOperator);
        costOperator += timeCoating * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        // стоимость материала
        let costMaterial = volMaterial / 1000 * material.cost;
        // итог расчетов
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость заливки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + (costProcess + costOperator) * (1 + insaincalc.common.marginOperation);
        result.time = Math.ceil((timeMix + timeCoating) * 100) / 100;
        result.weight = Math.ceil((volMaterial / 1000) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.material.set('EpoxyPoly',[material.name,0,volMaterial / 1000]);
        return result;

    } catch(err) {
        throw err
    }
};

// Функция расчета установки крепления
insaincalc.calcAttachment = function calcAttachment(n,attachmentID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во креплений
    //  attachmentID - тип крепления
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let attachment = insaincalc.misc.Attachment[attachmentID];
    try {
        let timePrepare = 0.1 * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let processPerHour = 400 // установка креплений в час
        let timeProcess = n / processPerHour + timePrepare; //считаем время установки
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costOperator = timeOperator * insaincalc.common.costOperator;
        // стоимость креплений
        let costMaterial = n * attachment.cost;
        result.cost = costMaterial + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + costOperator * (1 + insaincalc.common.marginOperation);
        result.time = Math.ceil(timeOperator * 100) / 100;
        result.weight = Math.ceil((n * attachment.weight / 1000) * 100) / 100; //считаем вес в кг.
        result.material.set(attachmentID,[attachment.name,attachment.size,n]);
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета установки кармана
insaincalc.calcPocket = function calcPocket(n,pocketID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во карманов
    //  pocketID - тип крепления
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.weight - вес тиража
    let pocket = insaincalc.misc.Pocket[pocketID];
    try {
        let timePrepare = 0.1 * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let processPerHour = 400 // шт/час
        let timeProcess = n / processPerHour + timePrepare; //считаем время упаковки
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costOperator = timeOperator * insaincalc.common.costOperator;
        // стоимость упаковки
        let costMaterial = n * pocket.cost;
        result.cost = costMaterial + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + costOperator * (1 + insaincalc.common.marginOperation);
        result.time = Math.ceil(timeOperator * 100) / 100;
        result.weight = Math.ceil((n * pocket.weight / 1000) * 100) / 100; //считаем вес в кг.
        result.material.set(pocketID,[pocket.name,pocket.size,n]);
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета упаковки
insaincalc.calcPacking = function calcPacking(n,size,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во креплений
    //	size - размер изделия [ширина, длинна, высота]
    //  options - параметры упаковки
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let pack = undefined;
    let packID = undefined;
    if (options.has('isPacking')) {
        packID = options.get('isPacking');
        if (packID != '') {
            pack = insaincalc.misc.Pack[packID]
        } else {
            // минимальный размер пакета для упаковки с учетом толщины изделия
            minSizePack = [size[0]+size[2]+5,size[1]+size[2]+5];
            // подбираем оптимальный по размеру пакет
            for (let packID_ in insaincalc.misc.Pack) {
                // если пакет подходит по размеру, то проверим насколько он оптимальный
                pack_ = insaincalc.misc.Pack[packID_];
                size_ = pack_.size;
                if (((size_[0] > minSizePack[0]) && (size_[1] > minSizePack[1])) || ((size_[0] > minSizePack[1]) && (size_[1] > minSizePack[0]))) {
                    if ((pack == undefined) || (pack.size[0]*pack.size[1] > pack_.size[0]*pack_.size[1])) {
                        pack = pack_;
                        packID = packID_;
                    }
                }
            }
        }
    }

    try {
        let timePrepare = 0.1 * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let processPerHour = 400 // упаковка шт/час
        let timeProcess = n / processPerHour + timePrepare; //считаем время упаковки
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costOperator = timeOperator * insaincalc.common.costOperator;
        // стоимость упаковки
        let costMaterial = n * pack.cost;
        result.cost = costMaterial + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + costOperator * (1 + insaincalc.common.marginOperation);
        result.time = Math.ceil(timeOperator * 100) / 100;
        result.weight = Math.ceil((n * pack.weight / 1000) * 100) / 100; //считаем вес в кг.
        result.material.set(packID,[pack.name,pack.size,n]);
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета ручной накатки пленки на плоские поверхности
insaincalc.calcManualRoll = function calcManualRoll(n,size,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  size - размер изделия
    //  isEdge - делать край с подгибкой или нет
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["ManualRoll"];
    let len = 0;
    let rollPerHour = 0;
    let edgePerHour = tool.edgePerHour;
    let area = size[0]*size[1]/1000000;
    try {
        let paramEdge = options.get('isEdge');
        // считаем скорость подрезки и поклейки
        if (paramEdge == 'isBendEdge') {
            if (area < tool.rollPerHour[0][0]) {
                area = tool.rollPerHour[0][0]; // минимальный расчетная площадь табличка
                len = 0.2; // минимальный расчетная длинна подгибки края, м
                rollPerHour = tool.rollPerHour[0][1];
            } else {
                len = (size[0] + size[1]) * 2 / 1000;
                rollPerHour = (tool.rollPerHour.find(item => item[0] >= area))[1];
            }
        } else {
            rollPerHour = (tool.rollPerHour.find(item => item[0] >= area * n))[1];
        }

        let sumLen = len * n; // умножили на кол-во изделий, перевели длинну из мм в м)
        let sumArea = area * n; // умножили на кол-во изделий, перевели длинну из мм в м)
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = sumArea / rollPerHour + sumLen / edgePerHour + timePrepare; //считаем время проклейки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost = costProcess + costOperator;//полная себестоимость
        result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;

        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета шелкографии по футболкам
insaincalc.calcSilkPrint = function calcSilkPrint(n,size,color,itemID,options= new Map(),modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  size - размер изделия
    //  цветность печати
    //  itemID - тип изделия
    // tshirtwhite - футболка, белая
    // tshirtcolor - футболка, цветная
    // transfer - трансфер
    // hat -  бейсболка
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

    let tool = '';
    let colorWhite = 0;
    let isRotate = options.has('isRotate') ? options.get('isRotate') : true;
    let isPacking10pcs = options.has('isPacking10pcs') ? options.get('isPacking10pcs') : false;
    let isUnPacking10pcs = options.has('isUnPacking10pcs') ? options.get('isUnPacking10pcs') : false;
    let isPackingIndiv = options.has('isPackingIndiv') ? options.get('isPackingIndiv') : true;
    let isUnPackingIndiv = options.has('isUnPackingIndiv') ? options.get('isUnPackingIndiv') : true;
    let coeffMesh = 0;
    switch (itemID) {
        case 'tshirtwhite':
            tool = insaincalc.tools['SilkTShirtWhite'];
            break;
        case 'tshirtcolor':
            tool = insaincalc.tools["SilkTShirtColor"];
            if (n < 150) coeffMesh = -0.5;
            colorWhite = 2;
            isRotate = false;
            break;
        case 'transfer':
            tool = insaincalc.tools["SilkTransfer"];
            isRotate = false;
            isPackingIndiv = false;
            isUnPackingIndiv = false;
            break;
        case 'hat': tool = insaincalc.tools["SilkHat"];break;
        default: tool = insaincalc.tools['SilkTShirtWhite'];
    }
    try {
        let baseTimeReady = tool.baseTimeReady[Math.ceil(modeProduction)];
        let defects = (tool.defects.find(item => item[0] >= n))[1];
        defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
        let numSilk = n * (1 + defects);
        // стоимость материалов для печати
        let numMesh =  Math.ceil(numSilk/2000) * (color + colorWhite + coeffMesh);
        let costMesh = numMesh * tool.costMesh;
        let costGlue = Math.ceil(numSilk/50) * tool.costGlue[0] * tool.costGlue[1] / 1000;
        let costPaintWhite = numSilk * size[0] * size[1] * tool.costPaintWhite[0] * tool.costPaintWhite[1] / 1000000000;
        let costPaint = numSilk * size[0] * size[1] * tool.costPaint[0] * tool.costPaint[1] / 1000000000;
        let costPaper = 0;
        let area = size[0] * size[1] / 1000000;
        let numSheet = numSilk;
        if (tool.hasOwnProperty('costPaper')) {
            costPaper = numSilk * area * tool.costPaper[0] * tool.costPaper[1];
            partPaper = [[0.015,1/6], [0.0315,1/2],[0.0609,1],[0.1218,1/5],[1,2]]; // доля затраты листа от площади трансфера
            numSheet = numSilk * (partPaper.find(item => item[0] >= area))[1];
            if (color == 1) {costPaint = 0}
        }
        let costMaterial = costMesh + costGlue + costPaint + costPaper + costPaintWhite;
        // время затраты
        let timePrepareMesh = tool.timePrepareMesh * numMesh;
        let timeAdjustment = tool.timeAdjustment[0] + tool.timeAdjustment[1] * (numMesh - 1);
        let timeSilkPrint =  numSheet / tool.processPerHour[color-1];
        let timeMix =  tool.timeMix * color / 2;
        let timePacking = 0;
        if (isRotate) {timePacking += numSilk / tool.processPerHourRotate}
        if (isUnPacking10pcs) {timePacking += numSilk / tool.processPerHourPacking10pcs[0]}
        if (isUnPackingIndiv) {timePacking += numSilk / tool.processPerHourPackingIndiv[0]}
        if (isPacking10pcs) {timePacking += numSilk / tool.processPerHourPacking10pcs[1]}
        if (isPackingIndiv) {timePacking += numSilk / tool.processPerHourPackingIndiv[1]}
        let coeefRasterPrint = 1;
        if (options.has('isRasterPrint')) {
            coeefRasterPrint = 1.25;
        }
        let timePutGlue = 0;
        let timeCut = 0;
        let timeTransfer = 0;
        if (tool.hasOwnProperty('costPaper')) {
            let processPerHourTrans = (tool.processPerHourTrans.find(item => item[0] >= area))[1];
            timeTransfer = numSilk / processPerHourTrans;
            timePutGlue = numSheet / tool.processPerHourGlue;
            timeCut = numSilk / tool.processPerHourCut;
        }
        let timeOperatorPack = timePrepareMesh + timePacking + timePutGlue + timeTransfer + timeCut;
        let timeOperatorSilk = timeAdjustment + timeSilkPrint + timeMix;
        let timePrepare = tool.timePrepare * modeProduction; // время подготовки к печати

        // стоимость использование оборудование включая амортизацию
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * (timeAdjustment + timeSilkPrint + timeMix); //стоимость использования оборудования
        // стоимость работы операторов
        let costOperator = timeOperatorSilk * ((tool.costOperatorSilk > 0) ? tool.costOperatorSilk : insaincalc.common.costOperator);
        costOperator += timeOperatorPack * ((tool.costOperatorPack > 0) ? tool.costOperatorPack : insaincalc.common.costOperator);

        // итог расчетов
        let coeffSoulfly = (tool.coeffSoulfly.find(item => item[0] >= n))[1];
        result.cost = (costMaterial + costProcess + costOperator * (1 + tool.coeffOverhead)) * coeefRasterPrint * (1 + coeffSoulfly);//полная себестоимость печати
        result.price = result.cost * (1 + insaincalc.common.marginOperation);
        result.cost *= (1 + tool.margin) // наценка на зарплату менеджера 20%, рентабельность 10%, доля от себестоимости изготовления
        result.time = Math.ceil((timeOperatorPack + timeOperatorSilk + timePrepare) * 100) / 100;
        result.weight = 0; //считаем вес в кг.
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;

    } catch(err) {
        throw err
    }
};

// Функция расчета изготовления закатных значков
insaincalc.calcButtonPins = function calcButtonPins(n,pinID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  size - размер изделия
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
        // Получаем размер значка
        let baseTimeReady = insaincalc.common.baseTimeReady;
        let size = [];
        // если тираж не большой то делаем сами, иначе в Амалит
        if (n <= 2000) {
            let pin = insaincalc.misc.ButtonPins[pinID];
            size = pin.size;
            let tool = {};
            // Выбираем станок (насадку) в зависимости от размера значка
            switch (String(pinID)) {
                case "D25":
                    tool = insaincalc.tools.PressButtonPin25;
                    break;
                case "D38":
                    tool = insaincalc.tools.PressButtonPin38;
                    break;
                case "D56":
                    tool = insaincalc.tools.PressButtonPin56;
                    break;
                case "D78":
                    tool = insaincalc.tools.PressButtonPin78;
                    break;
            }
            if (tool.baseTimeReady != undefined) {
                baseTimeReady = tool.baseTimeReady;
            }
            baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
            // учитываем брак
            let defects = (tool.defects.find(item => item[0] >= n))[1];
            defects += modeProduction > 1 ? defects * (modeProduction - 1) : 0; // учитываем увеличение брака в ускоренном режиме производства
            let numWithDefects = Math.ceil(n * (1 + defects));
            // расчитываем стоимость и время закатки
            let timePrepare = tool.timePrepare * modeProduction; // время подготовки к прессованию
            // время затраты оператора участка закатки значков
            let timePress = timePrepare + numWithDefects / tool.processPerHour;
            // стоимость использование оборудование включая амортизацию
            let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации станка
            let costProcess = costDepreciationHour * timePress + numWithDefects * tool.costProcess; //стоимость закатки
            // стоимость работы оператора
            let costOperator = timePress * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
            // стоимость материала
            let costMaterial = pin.cost * numWithDefects;

            // расчитываем стоимость изготовления бумажных вставок
            let sizeInsert = pin.sizeInsert; //добавляем вылеты для подгиба
            let sizeItem = sizeInsert[0];
            let density = 0;
            let difficulty = 1.0;
            let materialID = "ColotechPlus90M";
            let optionsInsert = new Map();
            optionsInsert.set('isPrint', "KMBizhubC220");
            optionsInsert.set('isFindMark', true);
            optionsInsert.set('isLamination', "Laminat75G");
            optionsInsert.set('isCarrier', true);
            optionsInsert.set('interval', 2);
            let costInsert = insaincalc.calcSticker(numWithDefects, sizeInsert, sizeItem, density, difficulty, materialID, optionsInsert, modeProduction);
            result.material = insaincalc.mergeMaps(result.material,costInsert.material);
            // итог расчетов
            result.cost = costMaterial + costProcess + costOperator + costInsert.cost;//полная себестоимость
            result.price = costMaterial * (1 + insaincalc.common.marginMaterial + insaincalc.common.marginButtonPins) +
                (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginButtonPins) +
                costInsert.price * (1 + insaincalc.common.marginButtonPins);
            result.time = timePress + costInsert.time;
            result.weight = pin.weight * n / 1000; //считаем вес в кг.
            result.material = costInsert.material;
            result.material.set(pinID,[pin.name,pin.size,numWithDefects]);
        } else {
            // итог расчетов
            let pin = insaincalc.misc.ButtonPinsAmalit[pinID];
            size = pin.size;
            let idx = (pin.cost.findIndex(item => item[0] > n));
            if (idx == -1) {idx = pin.cost.length - 1} else {idx -= 1}
            let costMaterial = pin.cost[idx][1] * n;
            let timePress = 8 * (n / 2000);
            result.weight = pin.weight * n / 1000; //считаем вес в кг.
            let thinknessPin = 5; // толщина значка в мм
            let volShipment = size[0] * size[1] * thinknessPin * n * 1.1; // считаем объем груза
            let numShipment = Math.ceil(volShipment/300/200/400); // считаем кол-во мест
            let sizeShipment = [Math.cbrt[volShipment],Math.cbrt[volShipment],Math.cbrt[volShipment]];
            let costShipment = insaincalc.calcShipment(numShipment,sizeShipment,result.weight/numShipment);
            result.cost = costMaterial + costShipment.cost;//полная себестоимость
            result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + costShipment.price;
            result.time = timePress + costShipment.time;
            result.timeReady = costShipment.timeReady;
            baseTimeReady = 0;
            result.material.set(pinID,[pin.name,pin.size,n]);
        }
        // рассчитываем стоимость упаковки
        let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        if (options.has('isPacking')) {costPacking =  insaincalc.calcPacking(n,[size[0],size[1],5],options,modeProduction)}
        result.material = insaincalc.mergeMaps(result.material,costPacking.material);

        result.cost += costPacking.cost;//полная себестоимость
        result.price += costPacking.price * (1 + insaincalc.common.marginButtonPins);
        result.time += costPacking.time;
        result.weight += costPacking.weight; //считаем вес в кг.
        result.timeReady += result.time + baseTimeReady; // время готовности
        return result;

    } catch(err) {
        throw err
    }
};

// Функция расчета доставки
insaincalc.calcShipment = function calcShipment(n,size,weight,cargoID = 'Dellin') {
    //Входные данные
    //  n - кол-во мест
    //  size - размер места
    //	weight - вес груза
    //	cargoID - ID транспортной
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    // функция проверки вместимости детали в коробку
    function checkFit(volDetal, volBox) {
        // Сортируем размеры детали по возрастанию
        volDetal.sort((a, b) => a - b);
        // Сортируем размеры коробки по возрастанию
        volBox.sort((a, b) => a - b);

        // Проверяем каждое измерение детали
        for (let i = 0; i < 3; i++) {
            // Если размер детали больше размера коробки по этому измерению, то деталь не поместится
            if (volDetal[i] > volBox[i]) {
                return false;
            }
        }
        // Если все измерения детали меньше или равны соответствующим измерениям коробки, то деталь поместится
        return true;
    }

    let costShipment = 0;
    let baseCostShipment = 500;
    switch (cargoID) {
        case "Dellin":
            baseCostShipment = 1000;
            result.cost = baseCostShipment + n * weight * 30;
            result.price = result.cost * (1 + insaincalc.common.marginMaterial);
            result.time = 0.5;
            result.timeReady = 40;
            break;
        case "Luch":
            let baseTariffLuch = [ // себестоимость доставки Лучом из Челябинска в Снежинск от веса, габаритов, мест
                [3,0.004,1,200,200,200],
                [30,0.125,1,250,250,200],
                [60,0.25,2,500,250,200],
                [100,0.343,3,750,300,300],
                [140,0.5,5,1000,300,300],
                [200,1.0,8,1250,300,300],
                [400,2.0,11,3000,400,300]
            ];
            // находим минимальную стоимость доставки
            let volShipment = size[0]*size[1]*size[2]/1000000000;
            for (let paramShipment of baseTariffLuch) {
                costShipment = paramShipment[3] + paramShipment[5];
                if ((weight <= paramShipment[0]) && (volShipment <= paramShipment[1]) && (n <= paramShipment[2])) {
                    break;
                }
            }
            result.cost = costShipment;
            result.price = result.cost * (1 + insaincalc.common.marginMaterial);
            result.time = 0.5;
            result.timeReady = 16;
            break;
        case "Own":
            let baseCostShipmentSize = [[800,800,500,500],[1000,1400,200,1000],[4000,2000,200,2000],[4000,2000,3000,6000]]; // себестоимость доставки от габаритов
            // находим минимальную стоимость доставки
            for (let paramShipment of baseCostShipmentSize) {
                let sizeTransport = [paramShipment[0], paramShipment[1], paramShipment[2]];
                for (let i = 0; i < 3; i++) {
                    sizeShipment = [size[0],size[1],size[2]];
                    sizeShipment[i] *= n;
                    if (checkFit(sizeShipment,sizeTransport)) {
                        if ((costShipment == 0) || (costShipment > paramShipment[3])) {costShipment = paramShipment[3]}
                    }
                }
            }

            result.cost = costShipment;
            result.price = result.cost * (1 + insaincalc.common.marginMaterial);
            result.time = 0.5;
            result.timeReady = 40;
            break;
    }
    return result;
}

// Функция расчета стоимости нарезки профиля
insaincalc.calcCutProfile = function calcCutProfile(n,segments,toolID,modeProduction = 1) {
    //Входные данные
    //  n - кол-во таких наборов
    //	segments - массив отрезков труб нужного кол-ва и длинны [len,n]
    //	toolID - тип отрезного устройства
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools[toolID];
    let numCut = segments.reduce((sum,elem) => sum + 2 * n * elem[1],0);// общее число резов
    let baseTimeReady = tool.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = numCut / tool.processPerHour + timePrepare //считаем время на резку с учетом времени на подготовку к запуску и приладку к каждому бигу
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + numCut * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost = costProcess + costOperator;//полная себестоимость резки
        result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.timeReady = result.time + baseTimeReady;
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета пошива чехла
insaincalc.calcSewingCovers = function calcSewingCovers(n,size,materialID,modeProduction = 1) {
    //Входные данные
    //  n - кол-во чехлов
    //	size - размер чехла
    //	materialID - материал чехла
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["Sewing"];
    let material = insaincalc.findMaterial("presswall",materialID);
    let baseTimeReady = tool.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare //считаем время на пошив
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let sizeMaterial = [size[0]+Math.max(size[1],size[2])+100,(size[1]+size[2])/2*3.14 + 100];
        let layoutOnRoll = insaincalc.calcLayoutOnRoll(n, sizeMaterial, material.size);
        let costMaterial = layoutOnRoll.length * material.size[0] * material.cost / 1000000;
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость резки
        result.price = (costProcess + costOperator) * (1 + insaincalc.common.marginOperation) + costMaterial * (1 + insaincalc.common.marginMaterial);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.timeReady = result.time + baseTimeReady;
        result.weight = n * material.density * sizeMaterial[0] * sizeMaterial[1] /1000000;
        result.material.set(materialID,[material.name,material.size,layoutOnRoll.length/1000]);
        return result;
    } catch (err) {
        throw err
    }
};

// Функция расчета резки на сабельном резаке
insaincalc.calcCutSaber = function calcCutSaber(numSheet,size,sizeSheet,materialID,cutterID,margins,interval,modeProduction = 1) {
    let hevisaid =  (a) => (a == 0)?0:1;
    //Входные данные
    //	numSheet - кол-во листов для резки
    //	size - размер изделия, [ширина, высота]
    //	sizeSheet -  размеры листа, sizeSheet[ширина, высота]
    //  interval - интервал между изделиями на листе, если 0 - то считаем одним резом
    //  margins - поля печати, если 0 - то края не подрезаем
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
    let cutter = insaincalc.cutter[cutterID];
    let typesMaterial = ['sheet','roll','hardsheet']; // список типов материалов в которых ищем данные по нашему материалу.
    let material = new Map();
    if (materialID != "") {
        for (let typeMaterial of typesMaterial) {
            material = insaincalc.findMaterial(typeMaterial, materialID);
            if (material != undefined) break;
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
    let numDoubleCut = hevisaid(interval) + 1;
    if (Math.min(sizeSheet[0],sizeSheet[1]) > Math.max(cutter.maxSize[0],cutter.maxSize[1])) return 0; // листы не помещается в резак, выходим
    let layoutOnSheet = insaincalc.calcLayoutOnSheet(size,sizeSheet,margins,interval); // сколько изделий размещается на лист
    if (layoutOnSheet.num == 0) return 0; // изделия не помещаются на листе, выходим
    // считаем кол-во резов
    let numCut = 4 + (layoutOnSheet.numAlongLongSide - 1) * numDoubleCut + layoutOnSheet.numAlongLongSide * (layoutOnSheet.numAlongShortSide - 1) * numDoubleCut; // кол-во резов если резать сначала по длинной
    numCut = numCut * numSheet; // умножаем на кол-во листов
    if (numCut >= 0) {
        let timePrepare = cutter.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeCut = numCut / cutter.cutsPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
        let timeOperator = timeCut; //считаем время затраты оператора участки резки
        let costCutterDepreciationHour = cutter.cost / cutter.timeDepreciation / cutter.workDay / cutter.hoursDay; //стоимость часа амортизации оборудования
        let costCut = costCutterDepreciationHour * timeCut + numCut * cutter.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((cutter.costOperator > 0) ? cutter.costOperator : insaincalc.common.costOperator);
        result.cost = Math.ceil(costCut + costOperator);//полная себестоимость резки
        result.price = Math.ceil(result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginCutGuillotine));
        result.time = Math.ceil(timeCut * 100) / 100;
    }
    return result;
};

// Функция расчета ручной вырубки
insaincalc.calcManualPress = function calcManualPress(n,materialID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для скругления
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

    let tool = insaincalc.tools["PressManual"];
    let typesMaterial = ['sheet','roll','hardsheet']; // список типов материалов в которых ищем данные по нашему материалу.
    let material = new Map();
    if (materialID != "") {
        for (let typeMaterial of typesMaterial) {
            material = insaincalc.findMaterial(typeMaterial, materialID);
            if (material != undefined) break;
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
    let timePrepare = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let timeProcess = n / tool.processPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
    let timeOperator = timeProcess; //считаем время затраты оператора участки резки
    let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
    let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
    let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
    result.cost = costProcess + costOperator;//полная себестоимость резки
    result.price =result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
    result.time = Math.ceil(timeProcess * 100) / 100;
    return result;
};

// Функция расчета вырубки на прессе
insaincalc.calcPress = function calcPress(n,materialID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для скругления
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

    let tool = insaincalc.tools["Press"];
    let typesMaterial = ['sheet','roll','hardsheet']; // список типов материалов в которых ищем данные по нашему материалу.
    let material = new Map();
    if (materialID != "") {
        for (let typeMaterial of typesMaterial) {
            material = insaincalc.findMaterial(typeMaterial, materialID);
            if (material != undefined) break;
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
    let timePrepare = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let timeProcess = n / tool.processPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
    let timeOperator = timeProcess; //считаем время затраты оператора участки резки
    let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
    let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
    let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
    result.cost = costProcess + costOperator;//полная себестоимость резки
    result.price =result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
    result.time = Math.ceil(timeProcess * 100) / 100;
    return result;
};

// Функция расчета изготовления вырубной формы
insaincalc.calcForm = function calcForm(sizeItem,numItems,difficulty,modeProduction = 1) {
    //Входные данные
    //	sizeItem - размер одного элемента вырубной формы
    //	numItems - кол-во элементов на вырубной форме
    //  difficulty - сложность формы для резки, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    const costKnife = 1000; // стоимость ножей для формы руб/мп
    const minCostForm = 1000; // минимальная стоимость вырубной формы

    let baseTimeReady = [32,24,16];
    let lenForm = numItems * (sizeItem[0]+sizeItem[1])*2 * difficulty;
    let costForm = costKnife * lenForm / 1000; //считаем стоимость формы
    costForm = Math.max(costForm,minCostForm);
    let costShipment =  insaincalc.calcShipment(1,[200,300,20],1,'Own');
    result.cost = costForm + costShipment.cost;//полная себестоимость резки
    result.price = costForm * (1 + insaincalc.common.marginOperation) + costShipment.price;
    result.time = 0;
    result.timeReady = baseTimeReady[modeProduction] + costShipment.timeReady;
    return result;
}

// Функция расчета установки пластиковой трубочки
insaincalc.calcSetShaft = function calcSetShaft(n,shaftID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //  shaftID - тип палочки
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["SetShaft"];
    let shaft = insaincalc.findMaterial("misc",shaftID);
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let costMaterial = shaft.cost * n; //считаем стоимость скрепок
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        result.weight = Math.ceil((shaft.weight * n) * 100) / 100; //считаем вес в кг.
        result.timeReady = result.time; // время готовности
        result.material.set(shaftID,[shaft.name,shaft.size,n]);
        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета установки шнура на вымпел
insaincalc.calcSetRope = function calcSetRope(n,ropeID,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
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

    let tool = insaincalc.tools["SetRope"];
    let rope = insaincalc.findMaterial("misc",ropeID);
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let costMaterial = rope.cost * n; //считаем стоимость шнуроа
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) + (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = timeProcess;
        result.weight = rope.weight * n / 1000; //считаем вес в кг.
        result.timeReady = result.time; // время готовности
        result.material.set(ropeID,[rope.name,rope.size,n]);
        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета установки профиля на стенд
insaincalc.calcSetProfile = function calcSetProfile(n,segments,profileID,modeProduction = 1) {
    //Входные данные
    //  n - кол-во таких наборов
    //	segments - массив отрезков труб нужного кол-ва и длинны [len,n]
    //	profileID - тип профиля
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["SetProfile"];
    let profile = insaincalc.findMaterial("profile",profileID);
    let spring = insaincalc.findMaterial("profile",profile.spring);
    let corner = insaincalc.findMaterial("profile",profile.corner);
    try {
        // вычисляем сколько уголков нужно
        let numCorner = n * segments.reduce((acc, curr) => acc + curr[1], 0);
        // вычисляем сколько нужно установить пружин
        let numSpring = n * segments.reduce((acc, curr) => acc + Math.ceil(curr[0] / spring.step + 1) * curr[1], 0);

        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = numSpring / tool.processPerHourSetSpring
            + numCorner / tool.processPerHourSetCorner
            + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        let costMaterial = spring.cost * numSpring + corner.cost * numCorner; //считаем стоимость пружины
        result.cost = costMaterial + costProcess + costOperator;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) +
            (costProcess + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = timeProcess;
        result.weight = spring.weight / 1000 * numSpring + corner.weight / 1000 * numCorner; //считаем вес в кг.
        result.timeReady = result.time; // время готовности
        result.material.set(profile.spring,[spring.name,spring.size,numSpring]);
        result.material.set(profile.corner,[corner.name,corner.size,numCorner]);
        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета установки вставки в акриловую заготовку
insaincalc.calcSetInsert = function calcSetInsert(n,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
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

    let tool = insaincalc.tools["SetInsert"];
    try {
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = n / tool.processPerHour + timePrepare; //считаем время установки с учетом времени на подготовку к запуску
        let timeOperator = timeProcess; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + n * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost =  costProcess + costOperator;//полная себестоимость резки
        result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = timeProcess;
        result.timeReady = result.time; // время готовности
        return result;
    } catch(err) {
        throw err
    }
};

// Функция расчета уф-склейки
insaincalc.calcUVGluing = function calcUVGluing(n,size,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для люверсовки
    //	size - размер склеиваемой детали по нижней площади
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}

    let tool = insaincalc.tools["TICUV300"];
    try {
        const layoutOnSheet = insaincalc.calcLayoutOnSheet(size, tool.maxSize);
        const numSheet = Math.ceil(n/layoutOnSheet.num);
        let timePrepare = tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = numSheet / tool.processPerHour + timePrepare; //считаем время проклейки с учетом времени на подготовку к запуску
        let timeOperator = timePrepare + n * 1/60; //считаем время затраты оператора участка
        let costDepreciationHour = tool.cost / tool.timeDepreciation / tool.workDay / tool.hoursDay; //стоимость часа амортизации оборудования
        let costProcess = costDepreciationHour * timeProcess + numSheet * tool.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);
        result.cost = costProcess + costOperator;//полная себестоимость резки
        result.price = result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginProcessManual);
        result.time = Math.ceil(timeProcess * 100) / 100;
        return result;
    } catch (err) {
        throw err
    }
};
