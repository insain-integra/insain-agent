// Функция расчета стоимости настольных флажков
insaincalc.calcFlagPaper = function calcFlagPaper(n,size,color,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	size - размер флажка
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
        let costSetStaples = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetShaft = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let numWithDefects = n;
        // расчет обложки
        let margins =[2,2,2,2];
        let interval = 4;
        let optionsPrint = new Map();
        // расчет топа
        if (options.has('isLamination')) {optionsPrint.set('isLamination',options.get('isLamination'))}
        costPrint = insaincalc.calcPrintSheet(numWithDefects, size, color, margins, interval, materialID, optionsPrint, modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costPrint.material);
        // добавляем стоимость установки скрепок
        costSetStaples = insaincalc.calcSetStaples(n, modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSetStaples.material);
        // добавляем стоимость установки флажка на палочку
        let shaftID = 'PlasticShaft380';
        costSetShaft = insaincalc.calcSetShaft(n,shaftID,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSetShaft.material);
        // окончательный расчет
        result.cost = costPrint.cost + costSetStaples.cost + costSetShaft.cost; //себестоимость тиража
        result.price = (costPrint.price + costSetStaples.price + costSetShaft.price)*(1+insaincalc.common.marginFlag); //цена тиража
        result.time =  Math.ceil((costPrint.time +costSetStaples.time +costSetShaft.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costPrint.timeReady,costSetStaples.timeReady,costSetShaft.timeReady); // время готовности
        result.weight = costPrint.weight + costSetShaft.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};