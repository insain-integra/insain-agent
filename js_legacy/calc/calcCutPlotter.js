// Функция расчета стоимости плоттерной резки
insaincalc.calcCutPlotter = function calcCutPlotter(n,size,sizeItem,density,difficulty,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер изделия, [ширина, высота]
    //  sizeItem - средний размер элементов/букв для резки внутри наклейки
    //  density - плотность заполнения элементами в наклейке от 0 до 1 (иначе от о до 100%).
    //  difficulty - сложность формы для резки, 1 - форма без вогнутостей, 1..1.4 - форма с вогнутостями, 1.5..2 - форма с пустотами
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
    // Считываем параметры материалов и оборудование
    let plotter = insaincalc.plotter["GraphtecCE5000-60"];
    let material = insaincalc.sheet.Paper[materialID];
    if (material == undefined) {material = insaincalc.roll.Film[materialID]}
    let baseTimeReady = plotter.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    let interval = 4; // интервал размещения изделий на листе
    if (options.has('interval')) {
        interval = options.get('interval')
    }
    let margins = plotter.margins; // отступы от края материала,мм
    let isFindMark = false;
    let isDelFilm = true;
    let lenCut = 0;
    //  isFindMark - поиск меток при резки по изображению
    if (options.has('isFindMark')) {isFindMark = options.get('isFindMark');}
    //  isDelFilm - удаление облоя, по умолчанию да
    if (options.has('isDelFilm')) {isDelFilm = options.get('isDelFilm');}
    //  lenCut - длинна реза одного элемента, если 0, то рассчитывается на основании размеров
    if (options.has('isLenCut')) {lenCut = options.get('isLenCut');}
    if (isFindMark) {margins = margins.map(function(value){ return value + plotter.marginsMark })}
    if (options.has('isCarrier')) {margins = margins.map(function(value){ return Math.min.apply(null, margins) })}
    // процент брака от тиража
    let defects = (plotter.defects.find(item => item[0] >=n))[1];
    defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
    let numWithDefects = Math.ceil(n*(1+defects)); // кол-во с учетом брака
    // скорость резки для данного материала
    let thickness = material.thickness;
    if (thickness == undefined) {thickness = material.density/80 * 100} // переводим плотность в толщину
    let processPerHour = (plotter.processPerHour.find(item => item[0] >= thickness))[1];// базовая скорость
    let minSize =  Math.min(size[0], size[1]) // определяем наиболее узкую сторону изделия
    let maxSize =  Math.max(size[0], size[1])  // определяем наиболее широкую сторону изделия
    let numSheet = 0;
    let elemDelFilm = 0; // кол-во элементов для выборки
    // вычисляем суммарную длинну резки
    try {
        if (lenCut == 0) { // если общая длинна реза не задана тогда вычисляем ее
            lenCut = (size[0] + size[1]) * 2; // длинна внешнего периметр резки одного элемента
            lenCut+=  4*size[0]*size[1]*density/sizeItem; // длинна внутреннего периметра
            lenCut = lenCut*difficulty/1000; // умножаем на коэфф. изогнутости
            if (isDelFilm) {
                if (difficulty >= 1.5) {
                    elemDelFilm = Math.ceil(size[0]*size[1]*density/(sizeItem*sizeItem));
                } else {elemDelFilm = 1;}
            }
        }
        // материал может иметь несколько размеров, например рулоны пленки разной ширины
        // поэтому для начала выбираем размер материал с наиболее оптимальным расходом
        let setSizeMaterial = [];
        let sizeMaterial = material.size[0]
        if (typeof sizeMaterial == 'number') {
            setSizeMaterial = [material.size];
        } else {
            setSizeMaterial = material.size;
        }
        let saveSizeMaterial = setSizeMaterial[0];
        let lenMaterial = 0;
        let saveLenMaterial = 0;
        let costMaterial = 0;
        let minCostMaterial = -1;
        for (let sizeMaterial of setSizeMaterial) {
            if (sizeMaterial[1] == 0) { // если материал рулон, а не листовой
                // проверяем помещается ли изделие в плоттер и на материал
                lenCutWithDefects = lenCut * numWithDefects;
                let layoutOnPlotter = insaincalc.calcLayoutOnRoll(numWithDefects, size, plotter.maxSize, interval);
                // считаем размещение на материале вдоль
                let sizeWithMargins = [size[0] + margins[0] + margins[2], size[1] + margins[1] + margins[3]];
                let layoutOnRoll = insaincalc.calcLayoutOnRoll(numWithDefects, sizeWithMargins, sizeMaterial, interval);
                // считаем размещение на материале поперек, если вдоль не размещается
                if (layoutOnRoll.length == 0) {
                    sizeWithMargins = [size[0] + margins[1] + margins[3], size[1] + margins[0] + margins[2]];
                    layoutOnRoll = insaincalc.calcLayoutOnRoll(numWithDefects, sizeWithMargins, sizeMaterial, interval);
                }
                if (layoutOnRoll.length > 0 && layoutOnPlotter.length > 0) { // если изделие поместилось, то тогда
                    // ищем оптимальный способ раскроя материала на плоттер, для этого
                    // перебираем варианты раскроя материала и варианты расположения на раскрое изделий
                    let numSheetWide = 1;

                    // = способ 1 = раскраиваем поперек рулона, изделие размещаем короткой стороной по ширине рулона
                    if (maxSize <= plotter.maxSize[0]) {
                        layoutOnRoll = insaincalc.calcLayoutOnRoll(numWithDefects, size, [sizeMaterial[0] - margins[0] - margins[2], 0], interval, -1);
                        let numSheetFar = Math.ceil(layoutOnRoll.length / plotter.maxSize[0]);
                        let l = layoutOnRoll.length + numSheetFar * (margins[1] + margins[3]);
                        if (lenMaterial == 0 || (lenMaterial > l && l > 0)) {
                            numSheet = numSheetWide * numSheetFar;
                            lenMaterial = l;
                        }
                    }

                    // = способ 2 = раскраиваем поперек рулона, изделие размещаем широкой стороной по ширине рулона
                    layoutOnRoll = insaincalc.calcLayoutOnRoll(numWithDefects, size, [sizeMaterial[0] - margins[0] - margins[2], 0], interval, 1);
                    numSheetFar = Math.ceil(layoutOnRoll.length / plotter.maxSize[0]);
                    l = layoutOnRoll.length + numSheetFar * (margins[1] + margins[3]);
                    if (lenMaterial == 0 || (lenMaterial > l && l > 0)) {
                        numSheet = numSheetWide * numSheetFar;
                        lenMaterial = l;
                    }

                    // = способ 3 = раскраиваем вдоль рулона, изделие короткой стороной вдоль
                    let w = Math.floor(plotter.maxSize[0] / minSize) * minSize + margins[1] + margins[3];
                    numSheetWide = Math.floor(sizeMaterial[0] / w); // сколько целых полос
                    if (numSheetWide > 0) {
                        let numWide = numSheetWide * Math.floor(plotter.maxSize[0] / minSize) // сколько изделий поперек в целых блоках
                        let w_ = sizeMaterial[0] - w * numSheetWide; // ширина остатка
                        if (w_ - margins[0] - margins[2] > minSize) {
                            numWide = numWide + Math.floor((w_ - margins[0] - margins[2]) / minSize);
                            numSheetWide += 1;
                        }
                        l = Math.ceil(numWithDefects / numWide) * maxSize;
                        numSheetFar = Math.ceil(l / plotter.maxSize[1]); // сколько целых полос в длинну
                        l = l + numSheetFar * (margins[0] + margins[2]);
                        if (lenMaterial == 0 || (lenMaterial > l && l > 0)) {
                            numSheet = numSheetWide * numSheetFar;
                            lenMaterial = l;
                        }
                    }

                    // = способ 4 = раскраиваем вдоль рулона, изделие широкой стороной вдоль
                    if (maxSize < plotter.maxSize[0]) {
                        w = Math.floor(plotter.maxSize[0] / maxSize) * maxSize + margins[1] + margins[3];
                        numSheetWide = Math.floor(sizeMaterial[0] / w); // сколько целых полос в ширину
                        if (numSheetWide > 0) {
                            numWide = numSheetWide * Math.floor(plotter.maxSize[0] / maxSize) // сколько изделий поперек в целых блоках
                            w_ = sizeMaterial[0] - w * numSheetWide; // ширина остатка
                            if (w_ - margins[0] - margins[2] > maxSize) {
                                numWide = numWide + Math.floor((w_ - margins[0] - margins[2]) / maxSize);
                                numSheetWide += 1;
                            }
                            l = Math.ceil(numWithDefects / numWide) * minSize;
                            numSheetFar = Math.ceil(l / plotter.maxSize[1]); // сколько целых полос в длинну
                            l = l + numSheetFar * (margins[0] + margins[2]);
                            if (lenMaterial == 0 || (lenMaterial > l && l > 0)) {
                                numSheet = numSheetWide * numSheetFar;
                                lenMaterial = l;
                            }
                        }
                    }
                } else { // разбиваем изделие на оптимальные куски
                    let sizeMaterialWithMargins = sizeMaterial[0] - margins[1] - margins[3];
                    let numBondPlotter = 1;
                    let numBondMaterial = 0;
                    if (sizeMaterialWithMargins < plotter.maxSize[0]) {
                        numBondMaterial = Math.ceil(minSize / sizeMaterialWithMargins); // кол-во полос материала для одного изделия
                    } else {
                        numBondPlotter = Math.ceil(minSize / plotter.maxSize[0]); // кол-во полос на плоттерную резку в ширину
                        numBondMaterial = 1 / Math.ceil(sizeMaterial[0] / (minSize / numBondPlotter + margins[1] + margins[3])); // доля ширины материала на одно изделие
                    }
                    numSheet = Math.ceil(maxSize * numWithDefects * numBondPlotter / Math.min(plotter.maxSize[1], maxSize)); // сколько полос на плоттерную резку в длинну
                    lenMaterial = ((maxSize * numWithDefects * numBondPlotter + numSheet * (margins[0] + margins[2])) * numBondMaterial);
                }
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
            } else { // если материал листовой
                // сколько изделий размещается на лист
                let layoutOnSheet = insaincalc.calcLayoutOnSheet(size, sizeMaterial, margins, interval);
                if (layoutOnSheet.num == 0) {
                    throw (new ICalcError('Размер изделия больше допустимого'))
                }
                // кол-во листов для резки
                numSheet = Math.ceil(numWithDefects / layoutOnSheet.num);
                if (numSheet == 1) {
                    lenCutWithDefects = lenCut * numWithDefects;
                } else {
                    lenCutWithDefects = lenCut * layoutOnSheet.num * numSheet;
                }
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
                costMaterial = costMaterial * numSheet;
            }
            if ((minCostMaterial == -1) || (costMaterial < minCostMaterial)) {
                minCostMaterial = costMaterial;
                saveSizeMaterial = sizeMaterial;
                saveNumSheet = numSheet;
                saveLenMaterial = lenMaterial;
            }
        }
        costMaterial = minCostMaterial;
        sizeMaterial = saveSizeMaterial;
        numSheet = saveNumSheet;
        lenMaterial = saveLenMaterial;
        if (sizeMaterial[1] == 0) {
            result.material.set(materialID,[material.name,sizeMaterial,lenMaterial/1000]);
        } else {
            result.material.set(materialID,[material.name,sizeMaterial,numSheet]);
        }

        // общее время резки и выборки
        let timePrepare = plotter.timePrepare * modeProduction; // время подготовки
        let timeCut = lenCutWithDefects / processPerHour  + timePrepare + numSheet*plotter.timeLoadSheet ; // время непосредственной резки
        if (isFindMark) {timeCut = timeCut + numSheet * plotter.timeFindMark} // время на поиск меток
        let timeDelFilm = 0;
        if (isDelFilm) {
            let lenElem = lenCutWithDefects / elemDelFilm / numWithDefects
            // коэффициент скорости удаления пленки в зависимости от периметра изделия
            let koeffDiffDelFilm = 2 * Math.ceil(lenElem / 0.2); // на каждые 200мм тратим 2 сек и не менее 2 сек.
            // увеличиваем коэфф. на сложность от толщины пленки.
            koeffDiffDelFilm = koeffDiffDelFilm * thickness / 80;
            timeDelFilm = elemDelFilm * koeffDiffDelFilm * numWithDefects / 3600;
            if (timeDelFilm > lenCutWithDefects / processPerHour) { // можно выбирать пока плоттер режет
                timeDelFilm -= lenCutWithDefects / processPerHour;
            } else {
                timeDelFilm = 0;
            }
        }
        // время затраты оператора участки резки
        let timeOperator = timeCut+timeDelFilm;
        // стоимость использование оборудование включая амортизацию
        let costDepreciationHour = plotter.cost / plotter.timeDepreciation / plotter.workDay / plotter.hoursDay; //стоимость часа амортизации оборудования
        let costCut = costDepreciationHour * timeCut + lenCutWithDefects * plotter.costProcess;
        let costOperator = timeOperator * ((plotter.costOperator > 0) ? plotter.costOperator : insaincalc.common.costOperator);
        // итог расчетов
        result.cost = Math.ceil(costCut + costOperator);//полная себестоимость резки
        result.price = Math.ceil((costCut + costOperator) * (1 + insaincalc.common.marginOperation + insaincalc.common.marginPlotter));
        result.time = Math.ceil(timeCut * 100) / 100;
        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};