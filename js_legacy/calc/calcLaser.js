// Функция расчета стоимости лазерной резки и гравировки
insaincalc.calcLaser = function calcLaser(n,size,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
    //	materialID - материал изделия в виде ID из данных материалов
    //  options - дополнительные опции в виде коллекция ключ/значение
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costAdhesiveLayer = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
    //	result.weight - вес тиража
    //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
    // Считываем параметры материалов и оборудование
    let laser = insaincalc.laser["Qualitech11G1290"];
    // считываем данные материала если они заданы
    let material = [];
    if (materialID != "") {
        material = insaincalc.findMaterial('hardsheet', materialID)
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }

    let baseTimeReady = laser.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    let interval = 5; // интервал размещения изделий на листе
    let margins = laser.margins; // отступы от края материала,мм
    let isFindMark = false;
    let lenCut = 0;
    let timeCut = 0;
    let areaGrave = 0;
    let timeGrave = 0;
    // процент брака от тиража
    let defects = (laser.defects.find(item => item[0] >=n))[1];
    defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
    let numWithDefects = Math.round(n*(1+defects)); // кол-во с учетом брака
    let numSheet = 0;
    try {
        // материал может иметь несколько размеров, например рулоны пленки разной ширины
        // поэтому для начала выбираем размер материал с наиболее оптимальным расходом
        let setSizeMaterial = [];
        let sizeMaterial = [];
        let saveSizeMaterial = [];
        if (materialID != "") {
            sizeMaterial = material.size[0]
            if (typeof sizeMaterial == 'number') {
                setSizeMaterial = [material.size];
            } else {
                setSizeMaterial = material.size;
            }
            sizeMaterial = setSizeMaterial[0];
        }
        let lenMaterial = 0;
        let saveLenMaterial = 0;
        let saveNumSheet = 0;
        let costMaterial = 0;
        let minCostMaterial = -1;
        // считаем лазерную гравировку
        if (options.has('isGrave')) {
            // разрешение/точность гравировки
            let resolution = options.get('isGrave');
            let gravePerHour = laser.gravePerHour[resolution];
            // если задана гравировки области вида [w,h]
            if (options.has('isGraveFill')) {
                let sizeGrave = options.get('isGraveFill');
                areaGrave = sizeGrave[0] * sizeGrave[1] / 1000000;
                let areaGraveWithDefects = areaGrave * numWithDefects;
                timeGrave = areaGraveWithDefects / gravePerHour;
            }
            // если задана гравировки контура вида [w,l]
            if (options.has('isGraveContur')) {
                let sizeGraveContur = options.get('isGraveContur');
                let numContur = Math.ceil(sizeGraveContur[0]/0.1); // кол-во линий
                let lenGraveContur = numWithDefects * numContur * sizeGraveContur[1]; // общая длинна гравировки линиями
                let cutPerHour = laser.cutPerHour[0][1];// скорость гравировки контура = минимальной скорости резки
                timeGrave += lenGraveContur / cutPerHour / 1000; // время гравировки контуров
            }
        }
        // считаем резку и расход материала на изделия
        if (materialID != "") {
            if (options.has('isCutLaser')) {
                let lenCutWithDefects = 0;
                let paramCut = options.get('isCutLaser');
                lenCut = paramCut.lenCut;
                if (lenCut == 0) { // если общая длинна реза не задана тогда вычисляем ее
                    let sizeItem = paramCut.sizeItem;
                    let density = paramCut.density;
                    let difficulty = paramCut.difficulty;
                    lenCut = (size[0] + size[1]) * 2; // длинна внешнего периметр резки одного элемента
                    if (sizeItem != 0) {
                        lenCut += 4 * size[0] * size[1] * density / sizeItem; // длинна внутреннего периметра
                    }
                    lenCut = lenCut * difficulty; // умножаем на коэфф. изогнутости
                }
                let layoutOnLaser = insaincalc.calcLayoutOnSheet(size, laser.maxSize, margins, interval);
                if (layoutOnLaser.num == 0) {
                    throw (new ICalcError('Изделие не помещается в лазер'))
                }
                let numLoad = Math.ceil(numWithDefects / layoutOnLaser.num); // кол-во загрузок материала в лазер
                //  isFindMark - поиск меток при резки по изображению
                if (options.has('isFindMark')) {
                    isFindMark = options.get('isFindMark');
                }
                // Проходим по всем размерам данного материала, чтобы найти оптимальный размер для закупа
                for (let sizeMaterial of setSizeMaterial) {
                    if (sizeMaterial[1] == 0) { // если материал рулон, а не листовой
                        // проверяем помещается ли изделие в лазер и на материал
                        lenCutWithDefects = lenCut * numWithDefects;
                        // изделие должно помещаться на материал короткой стороной
                        layoutOnRoll = insaincalc.calcLayoutOnRoll(numWithDefects, size, sizeMaterial, interval);
                        if (layoutOnRoll.num == 0) {continue}
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
                        if (material.length_min > 0) {
                            costMaterial = costMaterial * Math.ceil(lenMaterial / material.length_min) * material.length_min / 1000000 * sizeMaterial[0];
                        } else {
                            costMaterial = costMaterial * lenMaterial * sizeMaterial[0] / 1000000;
                        }
                    } else { // если материал листовой
                        // сколько изделий размещается на лист
                        let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeMaterial, margins, interval);
                        if (layoutOnSheet.num == 0) {continue}
                        // сколько минимальных объемов помещается на лист
                        let layoutMinOnSheet = insaincalc.calcLayoutOnSheet(material.minSize, sizeMaterial);
                        // кол-во листов для резки
                        numSheet = Math.ceil(numWithDefects / layoutOnSheet.num * layoutMinOnSheet.num) / layoutMinOnSheet.num;
                        lenCutWithDefects = lenCut * numWithDefects;
                        costMaterial = material.cost;
                        // цена материала с учетом объема печати
                        if (costMaterial instanceof Array) {
                            let index = material.cost.findIndex(item => item[0] >= numSheet);
                            if (index == -1) {
                                index = material.cost.length - 1;
                            } else {
                                index = index - 1;
                            }
                            costMaterial = material.cost[index][1];
                        }
                        // стоимость материала
                        costMaterial = costMaterial * numSheet * sizeMaterial[0] * sizeMaterial[1] / 1000000;
                    }
                    if ((minCostMaterial == -1) || (costMaterial < minCostMaterial)) {
                        minCostMaterial = costMaterial;
                        saveSizeMaterial = sizeMaterial;
                        saveNumSheet = numSheet;
                        saveLenMaterial = lenMaterial;
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
                // скорость резки для данного материала
                let cutPerHour = (laser.cutPerHour.find(item => item[0] >= material.thickness))[1];// базовая скорость
                // общее время резки и выборки
                timeCut = lenCutWithDefects / cutPerHour / 1000 + numLoad * laser.timeLoad; // время резки и загрузки материала в лазер
                if (isFindMark) {
                    timeCut += numLoad * laser.timeLoad
                } // время на приладку по изображению
            } else {
                sizeMaterial = setSizeMaterial[0];
                costMaterial = material.cost;
                if (sizeMaterial[1] == 0) {  // если материал рулонный
                    lenMaterial = (numWithDefects * size[0] * size[1]) / sizeMaterial[0];
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
                    if (material.length_min > 0) {
                        costMaterial = costMaterial * Math.ceil(lenMaterial / material.length_min) * material.length_min / 1000000 * sizeMaterial[0];
                    } else {
                        costMaterial = costMaterial * lenMaterial * sizeMaterial[0] / 1000000;
                    }
                } else { // если материал листовой
                    numSheet = (numWithDefects * size[0] * size[1]) / sizeMaterial[0] / sizeMaterial[1]
                    // цена материала с учетом объема печати
                    if (costMaterial instanceof Array) {
                        let index = material.cost.findIndex(item => item[0] >= numSheet);
                        if (index == -1) {
                            index = material.cost.length - 1;
                        } else {
                            index = index - 1;
                        }
                        costMaterial = material.cost[index][1];
                    }
                    // стоимость материала
                    costMaterial = costMaterial * numSheet * sizeMaterial[0] * sizeMaterial[1] / 1000000;
                }
            }


            // расчет стоимости материала, по умолчанию считаем
            let isMaterial = 'isMaterial';
            if (options.has('Material')) {
                isMaterial = options.get('Material')
            }
            if (isMaterial == 'isMaterial') {
                if (sizeMaterial[1] == 0) {
                    result.material.set(materialID,[material.name, sizeMaterial, lenMaterial]);
                } else {
                    result.material.set(materialID,[material.name, sizeMaterial, numSheet]);
                }
            } else {
                costMaterial = 0;
                if (isMaterial == 'isMaterialCustomer') {
                    // если материал заказчика то делаем наценку на резку и гравировку
                    timeCut *= 1.25;
                    timeGrave *= 1.25;
                }
            }
        }

        // рассчитываем стоимость нанесение клеевого слоя
        if (options.has('isAdhesiveLayer')) {
            let adhesiveLayer = options.get('isAdhesiveLayer');
            let idAdhesiveLayer = 'Sheet3M7952';
            switch (adhesiveLayer) {
                case 'AdhesiveLayer50':
                    idAdhesiveLayer = 'Sheet3M7952';
                    break;
                case 'AdhesiveLayer130':
                    idAdhesiveLayer = 'Sheet3M7955';
                    break;
            }
            let materialAdhesiveLayer = insaincalc.findMaterial('misc', idAdhesiveLayer);
            let numAdhesiveSheet = 1.0 * numWithDefects * (size[0] + 5) * (size[1] + 5) / (materialAdhesiveLayer.size[0] * materialAdhesiveLayer.size[1]); // Сколько листов скотча требуется
            costAdhesiveLayer = insaincalc.calcManualRoll(Math.ceil(numAdhesiveSheet),materialAdhesiveLayer.size,options,modeProduction);
            costAdhesiveLayer.cost += numAdhesiveSheet * materialAdhesiveLayer.cost;
            costAdhesiveLayer.price += numAdhesiveSheet * materialAdhesiveLayer.cost * (1 + insaincalc.common.marginMaterial);
            costAdhesiveLayer.weight = numAdhesiveSheet * materialAdhesiveLayer.weight / 1000;
            result.material.set(idAdhesiveLayer,[materialAdhesiveLayer.name,materialAdhesiveLayer.size,numAdhesiveSheet]);
        }

        let timePrepare = laser.timePrepare * modeProduction; // время подготовки
        // время затраты оператора участки резки
        let timeOperator = 0.75 * timeCut + 0.5 * timeGrave + timePrepare;
        // стоимость использование оборудование включая амортизацию
        let costDepreciationHour = laser.cost / laser.timeDepreciation / laser.workDay / laser.hoursDay; //стоимость часа амортизации оборудования
        let costOperator = timeOperator * ((laser.costOperator > 0) ? laser.costOperator : insaincalc.common.costOperator);
        // стоимость резки
        let costCut = costDepreciationHour * timeCut + timeCut * laser.costCut;
        // стоимость гравировки
        let costGrave = costDepreciationHour * timeGrave + timeGrave * laser.costGrave;
        // итог расчетов
        result.cost = Math.ceil(costCut + costGrave + costMaterial + costOperator + costAdhesiveLayer.cost);//полная себестоимость резки
        if (Math.round(n*(1+defects)) == n) {result.cost *= (1+defects)} // учитываем брак в цене, если не учли в кол-ве изделий
        result.price = Math.ceil(costMaterial * (1 + insaincalc.common.marginMaterial) +
            (costCut + costGrave + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginLaser) +
            costAdhesiveLayer.price);
        result.time = Math.ceil((timeCut + timeGrave + timePrepare + costAdhesiveLayer.time) * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = insaincalc.calcWeight(n,material.density,material.thickness,size,material.unitDensity) + costAdhesiveLayer.weight //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};