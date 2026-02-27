// Функция расчета стоимости раскроя на роликовых резаках
insaincalc.calcCutRoller = function calcCutRoller(num,size,materialID,cutterID,options,modeProduction = 1) {
    //Входные данные
    //	num - кол-во листов для резки, если рулон то num кол-во изделий
    //	size - размер изделия, [ширина, высота]
    //	materialID - материал изделия в виде ID из данных материалов
    //	cutterID - наименование резака для резки
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

        // материал может иметь несколько размеров
        let setSizeMaterial = [];
        let sizeMaterial = [];
        let saveSizeMaterial = [];
        if (materialID != "") {
            if (typeof material.size[0] == 'number') {
                setSizeMaterial = [material.size];
            } else {
                setSizeMaterial = material.size;
            }
        }

        let baseTimeReady = cutter.baseTimeReady;
        if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];

        let thickness = material.thickness;
        if (thickness == undefined) {thickness = 0}

        let numCut = 0;
        let saveNumCut = 0;
        let numSheet = 0;
        let saveNumSheet = 0;
        let costMaterial = 0;
        let lenMaterial = 0;
        let saveLenMaterial = 0;
        let minCostMaterial = -1;

        for (let sizeMaterial of setSizeMaterial) {
            let numCut = 0;
            if (Math.min(sizeMaterial[0], sizeMaterial[1]) > cutter.maxSize[0]) {continue} // переходим на след. размер материала, если данный не влезает в резак
            if (sizeMaterial[1] == 0) {// если материал рулон, а не листовой
                let layoutOnRoll = insaincalc.calcLayoutOnRoll(num, size, sizeMaterial)
                if (layoutOnRoll.length == 0) {continue}
                numCut = layoutOnRoll.numFar + 1 + layoutOnRoll.numFar * (layoutOnRoll.numWide + 1) - (layoutOnRoll.numWide * layoutOnRoll.numFar - num) ; // фактическое кол-во резов

                lenMaterial = layoutOnRoll.length;
                costMaterial = material.cost;
                // цена материала с учетом объема печати
                if (costMaterial instanceof Array) {
                    let index = material.cost.findIndex(item => item[0] >= lenMaterial / 1000);
                    if (index == -1) {
                        index = material.cost.length - 1;
                    } else {
                        index = index - 1;
                    }
                    costMaterial = material.cost[index][1];
                }
                // стоимость материала с учетом минимального закупа
                if (material.length_min > 0 ) {
                    costMaterial = costMaterial * Math.ceil(lenMaterial / material.length_min) * material.length_min / 1000000 * sizeMaterial[0];
                } else {
                    costMaterial = costMaterial * lenMaterial * sizeMaterial[0] / 1000000;
                }

            } else {
                let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeMaterial, [0, 0, 0, 0], 0); // сколько изделий размещается на лист
                if (layoutOnSheet.num == 0) {continue}

                // считаем кол-во резов
                let numCut1 = layoutOnSheet.numAlongLongSide + layoutOnSheet.numAlongLongSide * layoutOnSheet.numAlongShortSide; // кол-во резов если резать сначала по длинной
                let numCut2 = layoutOnSheet.numAlongShortSide + layoutOnSheet.numAlongShortSide * layoutOnSheet.numAlongLongSide; // кол-во резов если резать сначала по короткой
                if (Math.max(sizeMaterial[0], sizeMaterial[1]) > cutter.maxSize[0]) { // если лист шире резака по длинной стороне, то тогда в начале режем по короткой
                    numCut = numCut2;
                } else {
                    numCut = Math.min(numCut1, numCut2); //выбираем оптимальное количество резов
                }
                numCut = Math.ceil(numCut * num / layoutOnSheet.num);

                // стоимость материала
                // сколько минимальных объемов помещается на лист
                let layoutMinOnSheet = insaincalc.calcLayoutOnSheet(material.minSize, sizeMaterial);
                // кол-во листов для резки
                numSheet = Math.ceil(num / layoutOnSheet.num * layoutMinOnSheet.num) / layoutMinOnSheet.num;
                costMaterial = material.cost;
                // цена материала с учетом объема
                if (costMaterial instanceof Array) {
                    let index = material.cost.findIndex(item => item[0] >= numSheet);
                    if (index == -1) {
                        index = material.cost.length - 1;
                    } else {
                        index = index - 1;
                    }
                    costMaterial = material.cost[index][1];
                }
                costMaterial = costMaterial * numSheet * sizeMaterial[0] * sizeMaterial[1] / 1000000;
            }

            // если задана толщина, те. не 0, тогда увеличиваем кол-во резов вдвое
            // если какая-то из сторон более 1м, то увеличиваем кол-во резов кратно 1м
            if (thickness > 0) {
                numCut = numCut * 2;
                numCut = numCut * Math.ceil(size[0] / 1000) * Math.ceil(size[1] / 1000);
            } else {
                numCut = numCut * Math.ceil(size[0] / 1500) * Math.ceil(size[1] / 1500);
            }

            if ((minCostMaterial == -1) || (costMaterial < minCostMaterial)) {
                minCostMaterial = costMaterial;
                saveSizeMaterial = sizeMaterial;
                saveNumSheet = numSheet;
                saveNumCut = numCut;
                saveLenMaterial= lenMaterial;
            }
        }

        // если изделие не поместилось на материал, то выходим с ошибкой
        if (minCostMaterial == -1) {
            throw (new ICalcError('Изделие не помещается на материал'))
        }
        costMaterial = minCostMaterial;
        sizeMaterial = saveSizeMaterial;
        numSheet = saveNumSheet;
        lenMaterial = saveLenMaterial;
        numCut = saveNumCut;

        // расчет стоимости материала, по умолчанию не считаем
        let isMaterial = 'noMaterial';
        if (options.has('Material')) {
            isMaterial = options.get('Material')
        }
        if (isMaterial == 'isMaterial') {
            if (sizeMaterial[1] == 0) {
                result.material.set(materialID,[material.name,sizeMaterial,lenMaterial/1000]);
            } else {
                result.material.set(materialID,[material.name,sizeMaterial,numSheet]);
            }
        } else {
            costMaterial = 0;
            if (isMaterial == 'isMaterialCustomer') {
                // если материал заказчика то делаем наценку на резку
                numCut *= 1.25;
            }
        }


        let timePrepare = cutter.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeCut = numCut / cutter.cutsPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
        let timeOperator = timeCut; //считаем время затраты оператора участки резки
        let costCutterDepreciationHour = cutter.cost / cutter.timeDepreciation / cutter.workDay / cutter.hoursDay; //стоимость часа амортизации оборудования
        let costCut = costCutterDepreciationHour * timeCut + numCut * cutter.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((cutter.costOperator > 0) ? cutter.costOperator : insaincalc.common.costOperator);
        result.cost = Math.ceil(costMaterial + costCut + costOperator);//полная себестоимость резки
        result.price = Math.ceil(costMaterial * (1 + insaincalc.common.marginMaterial)+
            (costCut + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginCutRoller));
        result.time = Math.ceil(timeCut * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = insaincalc.calcWeight(num,material.density,material.thickness,size,material.unitDensity); //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};