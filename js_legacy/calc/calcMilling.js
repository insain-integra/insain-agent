// Функция расчета стоимости фрезеровки
insaincalc.calcMilling = function calcMilling(n,size,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
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
    // Считываем параметры материалов и оборудование
    let milling = insaincalc.milling["MillingMachine"];
    // считываем данные материала если они заданы
    let material = [];
    if (materialID != "") {
        material = insaincalc['hardsheet'][materialID];
        if (material == undefined) {
            for (let key in insaincalc['hardsheet']) {
                if (insaincalc['hardsheet'].hasOwnProperty(key)) {
                    material = insaincalc['hardsheet'][key][materialID];
                    if (material != undefined) break;
                }
            }
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
    let costCutPerMeter = 0;
    for (let key in milling.costCut) {
        if (materialID.indexOf(key) == 0) {
            if (milling.costCut.hasOwnProperty(key)) {
                costCutPerMeter = milling.costCut[key].find(item => item[0] >= material.thickness)[1];
                break;
            }
        }
    }


    let baseTimeReady = milling.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    let interval = 8; // интервал размещения изделий на листе
    let margins = milling.margins; // отступы от края материала,мм
    let lenCut = 0;
    let timeCut = 0;
    // процент брака от тиража
    let defects = (milling.defects.find(item => item[0] >=n))[1];
    defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
    let numSheet = 0;
    try {
        // материал может иметь несколько размеров
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
        let costCut = 0;
        let minCostMaterial = -1;

        // считаем резку и расход материала на изделия
        if (materialID != "") {
            if (options.has('isCutMilling')) {
                //  lenCut - длинна реза одного изделия, если 0, то рассчитывается на основании размеров
                let paramCut = options.get('isCutMilling');
                lenCut = paramCut.lenCut;
                if (lenCut == 0) { // если общая длинна реза не задана тогда вычисляем ее
                    let sizeItem = paramCut.sizeItem;
                    let density = paramCut.density;
                    let difficulty = paramCut.difficulty;
                    lenCut = (size[0] + size[1]) * 2; // длинна внешнего периметр резки одного элемента
                    lenCut += 4 * size[0] * size[1] * density / sizeItem; // длинна внутреннего периметра
                    lenCut = lenCut * difficulty; // умножаем на коэфф. изогнутости
                }
                // определение стоимости резки материала
                let len = Math.ceil(n * lenCut / 1000);
                let idx = (milling.discountCostCut.findIndex(item => item[0] > len)) - 1;
                let discount = 0;
                if (idx >= 0) {discount = milling.discountCostCut[idx][1]}
                costCut = len * costCutPerMeter * (1-discount);
            }
            let layoutOnMilling = insaincalc.calcLayoutOnSheet(size, milling.maxSize, margins, interval);
            if (layoutOnMilling.num == 0) {
                throw (new ICalcError('Изделие не помещается во фрезер'))
            }
            // Проходим по всем размерам данного материала, чтобы найти оптимальный размер для закупа
            for (let sizeMaterial of setSizeMaterial) {
                // сколько изделий размещается на лист
                // если не поместилось ни одного то идем на проверку след. варианта размера
                let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeMaterial, margins, interval);
                if (layoutOnSheet.num == 0) {continue}
                // сколько изделий размещается на половине листа
                let sizeHalfMaterial = [];
                if (sizeMaterial[0] > sizeMaterial[1]) {
                    sizeHalfMaterial[0] = sizeMaterial[0] / 2;
                    sizeHalfMaterial[1] = sizeMaterial[1];
                } else {
                    sizeHalfMaterial[0] = sizeMaterial[0];
                    sizeHalfMaterial[1] = sizeMaterial[1] / 2;
                }
                let layoutOnHalfSheet = insaincalc.calcLayoutOnSheet(size, sizeHalfMaterial, margins, interval);
                // сколько минимальных объемов помещается на лист
                let layoutMinOnSheet = insaincalc.calcLayoutOnSheet(material.minSize, sizeMaterial);
                // кол-во листов для резки
                //numSheet = Math.ceil(n / layoutOnSheet.num * layoutMinOnSheet.num) / layoutMinOnSheet.num;
                numSheet = Math.trunc(n / layoutOnSheet.num); // считаем сколько нужно целых листов
                let fracSheet = n / layoutOnSheet.num - numSheet; // доля листа для размещения остатка деталей которые не влезли на целые листы
                let fracNum = n - numSheet*layoutOnSheet.num; // остаток деталей которые не влезли на целые листы
                // проверяем помещается ли остаток на половину листа
                if (layoutOnHalfSheet.num >= fracNum) {
                    // если помещается то смотрим что выгоднее купить поллиста или использовать остатки материала поставщика
                    if (fracSheet * 1.5 >= 0.5) {
                        numSheet += 0.5;
                        fracSheet = 0;
                    }
                } else {
                    numSheet += 1;
                    fracSheet = 0;
                }

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
                // стоимость материала
                costMaterial = costMaterial * (numSheet + fracSheet*1.5) * sizeMaterial[0] * sizeMaterial[1] / 1000000;
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

            // расчет стоимости материала, по умолчанию считаем
            let isMaterial = 'isMaterial';
            if (options.has('Material')) {
                isMaterial = options.get('Material')
            }
            if (isMaterial == 'isMaterial') {
                result.material.set(materialID,[material.name,sizeMaterial,numSheet]);
            } else {
                costMaterial = 0;
                if (isMaterial == 'isMaterialCustomer') {
                    // если материал заказчика то делаем наценку на резку
                    costCut *= 1.25;
                }
            }
        }

        let timePrepare = milling.timePrepare * modeProduction; // время подготовки
        // время затраты оператора участки резки
        let timeOperator = timePrepare;
        // стоимость работы оператора
        let costOperator = timeOperator * ((milling.costOperator > 0) ? milling.costOperator : insaincalc.common.costOperator);
        // стоимость доставки от габаритов
        let costShipment = 0;
        for (let paramShipment of milling.costShipment) {
            let sizeTransport = [paramShipment[0],paramShipment[1]];
            let layoutOnTransport = insaincalc.calcLayoutOnSheet(size, sizeTransport);
            if (layoutOnTransport.num > 0) {
                costShipment = paramShipment[2];
                break;
            }
        }
        costShipment *=  modeProduction == 0 ? 0.5 : modeProduction;
        // итог расчетов
        if (costCut + costMaterial + costOperator > 500) {
            result.cost = (costCut + costMaterial + costShipment + costOperator) * (1 + milling.margin);//полная себестоимость резки
            if (Math.round(n * (1 + defects)) == n) {
                result.cost *= (1 + defects)
            } // учитываем брак в цене, если не учли в кол-ве изделий
            result.price = (costMaterial * (1 + defects + insaincalc.common.marginMaterial) +
                (costCut + costShipment + costOperator) * (1 + defects + insaincalc.common.marginOperation + insaincalc.common.marginMilling));
        } else {
            result.cost = (500 + costShipment) * (1 + milling.margin);//полная себестоимость резки
            result.price = (500 + costShipment) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginMilling);
        }
        result.time = Math.ceil((timeCut + timePrepare) * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = insaincalc.calcWeight(n,material.density,material.thickness,size,material.unitDensity)  //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};

