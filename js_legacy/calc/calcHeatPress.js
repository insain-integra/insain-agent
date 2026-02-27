// Функция расчета стоимости термотрансферного переноса на различных видах прессов
insaincalc.calcHeatPress = function calcHeatPress(n,size,transferID,itemID,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий для резки
    //	size - размер нанесения, [ширина, высота]
    //	transferID - тип трансфера в виде ID
        // silk - шелкотрансфер (по любым тканям)
        // sublimation - трансфер сублимационный (по белым синт.тканям)
        // film - трансфер пленками с плоттерной резкой (по любым тканям)
        // filmSublimation- трансфер пленками с сублимационной печатью (по любым тканям)
        // filmEcosolvent- трансфер пленками с экосольвентной печатью (по любым тканям)
        // paperLaser - трансфер бумажный с лазерной печатью (по белым тканям)
    //  itemID - тип изделия
        // hat - головной убор
        // mug - кружки
        // tshirt - футболка, легкая ткань
        // clothes - плотная одежда
        // bag - рюкзаки, сумки
        // metal -  металлические пластины
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
    let heatpress = '';
    let itemDifficulty = 0; // сложность нанесения на изделие
    switch (itemID) {
        case 'hat': heatpress = insaincalc.heatpress["Grafalex"];break;
        case 'mug': heatpress = insaincalc.heatpress["EconopressMUGH"];break;
        case 'clothes':
            heatpress = insaincalc.heatpress["SahokSH49BD"];
            itemDifficulty = 1;
            break;
        case 'bag':
            heatpress = insaincalc.heatpress["SahokSH49BD"];
            itemDifficulty = 1;
            break;
        default: heatpress = insaincalc.heatpress["SahokSH49BD"]
    }
    let timeLoad = heatpress.timeLoad[itemDifficulty];
    let baseTimeReady = heatpress.baseTimeReady;
    if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
    baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
    // процент брака от тиража
    let defects = (heatpress.defects.find(item => item[0] >=n))[1];
    defects +=  modeProduction > 1 ? defects*(modeProduction-1):0; // учитываем увеличение брака в ускоренном режиме производства
    let numWithDefects = Math.round(n*(1+defects)); // кол-во с учетом брака
    let timePress = 0;
    try {
        // расчитываем трансфер в зависимости от заданного ID
        let costTransfer = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costCut = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        switch (transferID) {
            case 'silk': //  шелкотрансфер (по любым тканям)
                optionsTransfer = options[transferID];
                if (optionsTransfer == undefined) {optionsTransfer = new Map();}
                color = options.get(transferID).color;
                costTransfer = insaincalc.calcSilkPrint(numWithDefects,size,color,'transfer',options = new Map(),modeProduction);
                timePress = 10/3600;// время одного переноса 10 сек
                break;
            case 'sublimation': // трансфер сублимационный (по белым синт.тканям)
                materialID = 'PaperSublimation128';
                printerID = 'EPSONWF7610';
                optionsTransfer = options[transferID];
                if (optionsTransfer == undefined) {optionsTransfer = new Map();}
                optionsTransfer.set('printer',{'printerID':printerID});
                margins = [0,0,0,0];
                interval = 2;
                costTransfer = insaincalc.calcPrintSheet(numWithDefects,size,'4+0',margins,interval,materialID,optionsTransfer,modeProduction)
                timePress = 35/3600 // время одного переноса 35 сек
                break;
            case 'film': // трансфер пленками с плоттерной резкой (по любым тканям)
                optionsTransfer = options[transferID];
                if (optionsTransfer == undefined) {optionsTransfer = new Map();}
                sizeItem = options.get(transferID).sizeItem;
                density =  options.get(transferID).density;
                difficulty = options.get(transferID).difficulty * 2; // умножаем на 2, так как пленка сложная для выборки
                materialID = options.get(transferID).materialID;
                color = options.get(transferID).color;
                costTransfer = insaincalc.calcSticker(numWithDefects * color,size,sizeItem,density,difficulty,materialID,optionsTransfer,modeProduction);
                timePress = 20/3600 // время одного переноса 20 сек
                break;
            case 'filmSublimation': // трансфер пленками с сублимационной печатью (по любым тканям)
                // расчитываем сублимацию по пленке
                materialID = 'PaperSublimation128';
                printerID = 'EPSONWF7610';
                plotterID = 'GraphtecCE5000-60';
                let plotter = insaincalc.plotter[plotterID];
                optionsTransfer = options[transferID];
                if (optionsTransfer == undefined) {optionsTransfer = new Map();}
                optionsTransfer.set('printer',{'printerID':printerID});
                margins = plotter.margins;
                interval = 2;
                material = insaincalc.findMaterial("sheet",materialID);
                sizeSheet = material.size;
                layoutOnSheet = insaincalc.calcLayoutOnSheet(size,sizeSheet,margins,interval);
                numSheet = Math.ceil(numWithDefects/layoutOnSheet.num);
                costTransfer = insaincalc.calcHeatPress(numSheet,sizeSheet,'sublimation','',optionsTransfer,modeProduction);
                // расчитываем плоттерную резку трансферов
                sizeItem = Math.max(size[0],size[1]);
                density = 1;
                difficulty = 1.7;
                materialID = 'POLIFLEX4675';
                optionsCut = new Map();
                optionsCut.set('isFindMark',true);
                costCut = insaincalc.calcCutPlotter(numSheet,sizeSheet,sizeItem,density,difficulty,materialID,optionsCut,modeProduction);
                timePress = 45/3600 // время одного переноса 15 сек
                break;
            case 'filmEcosolvent': // трансфер пленками с экосольвентной печатью (по любым тканям)
                materialID = 'POLIFLEX4030';
                printerID = 'Technojet160ECO';
                costTransfer = insaincalc.calcPrintRoll(numWithDefects,size,materialID,printerID,options,modeProduction);
                // расчитываем плоттерную резку трансферов
                sizeItem = Math.max(size[0],size[1]);
                density = 1;
                difficulty = 1.7;
                optionsCut = new Map();
                optionsCut.set('isFindMark',true);
                costCut = insaincalc.calcCutPlotter(numWithDefects,size,sizeItem,density,difficulty,materialID,optionsCut,modeProduction);
                timePress = 15/3600 // время одного переноса 15 сек
                break;
            case 'dtf': // трансфер dtf (по любым тканям)
                materialID = 'PaperDTFTransfer';
                printerID = 'DTFTransfer';
                optionsTransfer = options[transferID];
                if (optionsTransfer == undefined) {optionsTransfer = new Map();}
                optionsTransfer.set('printer',{'printerID':printerID});
                optionsTransfer.set('noCut',true);
                margins = [2,2,2,2];
                interval = 2;
                costTransfer = insaincalc.calcPrintSheet(numWithDefects,size,'4+0',margins,interval,materialID,optionsTransfer,modeProduction)
                material = insaincalc.findMaterial("sheet",materialID);
                sizeSheet = material.size;
                layoutOnSheet = insaincalc.calcLayoutOnSheet(size,sizeSheet,margins,interval);
                numSheet = Math.ceil(numWithDefects/layoutOnSheet.num);
                let cutterID = 'Ideal1046';
                costCut = insaincalc.calcCutSaber(numSheet,size,sizeSheet,materialID,cutterID,margins,interval,modeProduction);
                timePress = 15/3600 // время одного переноса 15 сек
                break;
            case 'paperLaser': // трансфер бумажный с лазерной печатью (по белым тканям)
                materialID = 'PaperFOREVERLASERTRANSPARENT';
                printerID = 'KMBizhubC220';
                optionsTransfer = options[transferID];
                if (optionsTransfer == undefined) {optionsTransfer = new Map();}
                optionsTransfer.set('printer',{'printerID':printerID});
                margins = [2,2,2,2];
                interval = 2;
                costTransfer = insaincalc.calcPrintSheet(numWithDefects,size,'4+0',margins,interval,materialID,optionsTransfer,modeProduction)
                timePress = 45/3600 // время одного переноса 45 сек
                break;
        }
        result.material = insaincalc.mergeMaps(result.material,costTransfer.material);
        timePress = (timePress + timeLoad) * numWithDefects;
        let timePrepare = heatpress.timePrepare * modeProduction; // время подготовки
        // время затраты оператора участки резки
        let timeOperator = timePress + timePrepare;
        // стоимость использование оборудование включая амортизацию
        let costDepreciationHour = heatpress.cost / heatpress.timeDepreciation / heatpress.workDay / heatpress.hoursDay; //стоимость часа амортизации оборудования
        let costOperator = timeOperator * ((heatpress.costOperator > 0) ? heatpress.costOperator : insaincalc.common.costOperator);
        // стоимость нанесения
        let costPress = costDepreciationHour * timePress + heatpress.costPress * timePress;

        // итог расчетов
        //полная себестоимость резки
        result.cost = costOperator +
            costPress +
            costTransfer.cost +
            costCut.cost;
        // цена с наценкой
        result.price = (costOperator * (1 + insaincalc.common.marginOperation) +
            costPress * (1 + insaincalc.common.marginMaterial) +
            (costTransfer.price + costCut.price)) * (1 + insaincalc.common.marginHeatPress);
        // времязатраты
        result.time = timeOperator + costTransfer.time + costCut.time;
        //считаем вес в кг.
        result.weight = costTransfer.weight + costCut.weight;
        result.timeReady = result.time + costTransfer.timeReady + baseTimeReady; // время готовности
        return result;
    } catch (err) {
        throw err
    }
};