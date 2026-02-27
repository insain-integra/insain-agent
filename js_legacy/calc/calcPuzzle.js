// Функция расчета стоимости изготовления пазлов
insaincalc.calcPuzzle = function calcPuzzle(n,puzzleID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	puzzleID - тип пазла в виде ID
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

    let costPuzzle = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costApplication = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
    let costPacking = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

    try {
        // Считываем параметры материалов
        let puzzle = insaincalc.findMaterial("misc",puzzleID);
        let applicationID = puzzle.applicationID;
        // считаем стоимость нанесения
        let sizeItem = Math.min(puzzle.size[0],puzzle.size[1]);
        let density = 0;
        let lenCut = 0;
        let color = '4+1';
        let resolution = 2;
        let sizeGrave = puzzle.size;
        let optionsApplication = new Map();
        let materialID ='';
        switch (applicationID) {
            case 'isUVPrint':
                materialID = puzzle.materialID;
                optionsApplication.set('isCutLaser',{'sizeItem':sizeItem,'density':density,'difficulty':1,'lenCut':lenCut});
                optionsApplication.set(applicationID,{'printerID':'RimalSuvUV',
                    'resolution':2,
                    'surface':'isPlain',
                    'color':color })
                costPuzzle = insaincalc.calcTablets(n,puzzle.size,materialID,optionsApplication,modeProduction = 1)
                break;
            case 'isGrave':
                materialID = puzzle.materialID;
                optionsApplication.set('isCutLaser',{'sizeItem':sizeItem,'density':density,'difficulty':1,'lenCut':lenCut});
                optionsApplication.set('isGrave',resolution);
                optionsApplication.set('isGraveFill',sizeGrave);
                costPuzzle = insaincalc.calcTablets(n,puzzle.size,materialID,optionsApplication,modeProduction = 1)
                break;
            case 'isSublimation':
                // находим стоимость основы пазла
                costPuzzle.weight = puzzle.weight * n;
                costPuzzle.cost = puzzle.cost * n;
                costPuzzle.price = costPuzzle.cost * (1 + insaincalc.common.marginMaterial);
                costPuzzle.material.set(puzzleID,[puzzle.name,puzzle.size,n]);
                // время распаковки и упаковки изделий
                costPacking.time += 0.006 * n;
                costPacking.cost = costPacking.time * insaincalc.common.costOperator;
                costPacking.price = costPacking.cost * (1 + insaincalc.common.marginOperation);
                // стоимость нанесения
                let transferID = 'sublimation';
                let itemID = 'metal';
                costApplication = insaincalc.calcHeatPress(n,puzzle.sizePrint,transferID,itemID,options,modeProduction)
                result.material = insaincalc.mergeMaps(result.material,costApplication.material);
                break;
            default:
        }
        result.material = insaincalc.mergeMaps(result.material, costPuzzle.material);
        // считаем стоимость монтажа пластины на скотч
        // итог расчетов
        //полная себестоимость резки
        result.cost = costPuzzle.cost + costPacking.cost + costApplication.cost;
        // цена с наценкой
        result.price = (costPuzzle.price + costPacking.price + costApplication.price) * (1 + insaincalc.common.marginPuzzle);
        // время затраты
        result.time = costPuzzle.time + costPacking.time + costApplication.time;
        //считаем вес в кг.
        result.weight = costPuzzle.weight;
        result.timeReady = result.time + Math.max(costPuzzle.timeReady, costPacking.timeReady, costApplication.timeReady); // время готовности
        return result;
    } catch (err) {
        throw err
    }
};