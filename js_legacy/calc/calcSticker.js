// Функция расчета стоимости изготовления наклеек
insaincalc.calcSticker = function calcSticker(n,size,sizeItem,density,difficulty,materialID,options,modeProduction = 1) {
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
    try {
        let costCut = insaincalc.calcCutPlotter(n,size,sizeItem,density,difficulty,materialID,options,modeProduction);
        let costMaterial = material.cost;
        let materialCut = costCut.material.get(materialID); // считываем какой объем материала затрачивается на плоттерную резку
        if (materialCut[1][1] == 0) { // если материал рулон, а не листовой
            // цена материала с учетом объема печати
            if (costMaterial instanceof Array) {
                let index = material.cost.findIndex(item => item[0] >= costCut.material[1] / 1000);
                if (index == -1) {
                    index = material.cost.length - 1;
                } else {
                    index = index - 1;
                }
                costMaterial = material.cost[index][1];
            }
            // стоимость материала с учетом минимального закупа
            if (material.length_min > 0 ) {
                costMaterial = costMaterial * Math.ceil(materialCut[2] * 1000 / material.length_min) * material.length_min / 1000000 * materialCut[1][0];
            } else {
                costMaterial = costMaterial * materialCut[1][0] * materialCut[2] / 1000;
            }
            result.material = insaincalc.mergeMaps(result.material,costCut.material);
        } else {// если материал листовой
            // цена материала с учетом объема печати
            if (costMaterial instanceof Array) {
                let index = material.cost.findIndex(item => item[0] >= materialCut[2]);
                if (index == -1) {
                    index = material.cost.length - 1;
                } else {
                    index = index - 1;
                }
                costMaterial = material.cost[index][1];
            }
            // стоимость материала
            costMaterial = costMaterial * materialCut[2];
            result.material = insaincalc.mergeMaps(result.material,costCut.material);
        }
        // Расчет печати
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        if (options.has('isPrint')) {
            let printerID = options.get('isPrint').printerID;
            switch (printerID) {
                case 'KMBizhubC220':
                    let numSheet = materialCut[2];
                    let sizeSheet = materialCut[1];
                    let color = options.get('isPrint').color;
                    costPrint = insaincalc.calcPrintLaser(numSheet, sizeSheet, color, materialID, printerID, modeProduction);
                    break;
                case 'Technojet160ECO':
                case 'HPLatex335':
                case 'TechnojetXR720':
                    let n = 1;
                    costPrint = insaincalc.calcPrintWide(n, materialCut[1], materialID, printerID, options, modeProduction);
                    break;
            }
            result.material = insaincalc.mergeMaps(result.material,costPrint.material);
        }

        // расчет ламинации, если есть
        let costLamination = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        if (options.has('isLamination')) {
            laminatID = options.get('isLamination');
            let laminat = insaincalc.laminat.Laminat[laminatID];
            if (materialCut[1][1] == 0) { //если материал рулон то широкоформатная ламинация, иначе стандартная
                let n = 1;
                let size = materialCut[1];
                costLamination = insaincalc.calcLaminationWide(n,size,modeProduction);
            } else {
                let doubleSideLamination = false; // односторонняя ламинация
                let n = materialCut[2];
                let size = materialCut[1];
                costLamination = insaincalc.calcLamination(n, size, laminatID, doubleSideLamination, modeProduction);
            }
            result.material = insaincalc.mergeMaps(result.material,costLamination.material);
        }
        // расчет накатки монтажной пленки, если есть
        let costMountingFilm = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let isMountingFilm = false;
        if (options.has('isMountingFilm')) {isMountingFilm = options.get('isMountingFilm');}
        if (isMountingFilm) {
            idMountingFilm = 'LGChemLC2000H';
            let film = insaincalc.roll.Film[idMountingFilm] // считываем параметры монтажной пленки
            let costRoll = insaincalc.calcManualRoll(n,size,options,modeProduction);
            let sumArea =  n * (size[0] + 20) * (size[1] + 20) / 1000000; // общая площадь в м2 монтажной пленки с учетом вылетом по 10мм
            costMountingFilm.cost = film.cost * sumArea;
            costMountingFilm.price = costMountingFilm.cost * (1 + insaincalc.common.marginMaterial);
            costMountingFilm.weight = insaincalc.calcWeight(n,film.density,film.thickness,size,film.unitDensity)
            costMountingFilm.cost += costRoll.cost;
            costMountingFilm.price += costRoll.price;
            costMountingFilm.time += costRoll.time;
            costMountingFilm.material.set(idMountingFilm,[film.name,film.size,sumArea/film.size[0]*1000]);
            result.material = insaincalc.mergeMaps(result.material,costMountingFilm.material);
        }

        // итог расчетов
        result.cost = costMaterial + costCut.cost + costPrint.cost + costLamination.cost + costMountingFilm.cost;//полная себестоимость резки
        result.price = costMaterial * (1 + insaincalc.common.marginMaterial) +
            (costCut.price + costPrint.price + costLamination.price + costMountingFilm.price) * (1 + insaincalc.common.marginSticker);
        result.time = Math.ceil((costCut.time + costPrint.time + costLamination.time + costMountingFilm.time) * 100) / 100;
        result.weight = Math.ceil((insaincalc.calcWeight(n,material.density,material.thickness,size,material.unitDensity) + costLamination.weight + costMountingFilm.weight) * 100) / 100; //считаем вес в кг.

        result.timeReady = result.time + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};