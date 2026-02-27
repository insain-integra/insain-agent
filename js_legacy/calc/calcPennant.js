// Функция расчета стоимости бумажных вымпелов
insaincalc.calcPennantPaper = function calcPennantPaper(n,size,color,materialID,options,modeProduction = 1) {
    //Входные данные

    //	n - тираж изделий
    //	size - размер вымпела
    //	color - цветность печати, вида '4+0'
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

    try {
        // Объявляем нулевые стоимости
        let costPrint = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetRope = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let numWithDefects = n;
        // расчет
        let margins =[2,2,2,2];
        let interval = 4;
        let optionsPrint = new Map();
        // расчет основы вымпела
        if (options.has('isLamination')) {optionsPrint.set('isLamination',options.get('isLamination'))}
        optionsPrint.set('isHole',2);
        costPrint = insaincalc.calcPrintSheet(numWithDefects, size, color, margins, interval, materialID, optionsPrint, modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costPrint.material);
        // добавляем стоимость установки шнура
        let ropeID = 'RopeForPack';
        costSetRope = insaincalc.calcSetRope(n,ropeID,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSetRope.material);
        // окончательный расчет
        result.cost = costPrint.cost + costSetRope.cost; //себестоимость тиража
        result.price = (costPrint.price + costSetRope.price)*(1+insaincalc.common.marginPennantPaper); //цена тиража
        result.time =  Math.ceil((costPrint.time +costSetRope.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costPrint.timeReady,costSetRope.timeReady); // время готовности
        result.weight = costPrint.weight + costSetRope.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};