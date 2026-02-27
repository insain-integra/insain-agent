// Функция расчета стоимости дизайна и верстке
insaincalc.calcDesign = function calcDesign(n,designID,difficulty,options,modeProduction = 1) {
    //Входные данные
    //	n - кол-во изделий
    //	designID - тип изделия
    //  difficulty - уровень сложности, 0-только проверка,1 - внесение текстовых изменений,2 - верстка на базе готовых,3 - разработка дизайна
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
        // Считываем данные по дизайну
        let tool = insaincalc.design[designID];
        let baseTimeReady = tool.baseTimeReady;
        if (baseTimeReady == undefined) baseTimeReady = insaincalc.common.baseTimeReady;
        baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];

        // считаем время затраты
        let timePrepare = n * tool.timePrepare * modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeProcess = timePrepare;
        if (difficulty > 0) timeProcess += n * tool.timeProcess[difficulty-1]; //считаем время работы
        let timeOperator = timeProcess; //считаем время затраты дизайнера
        let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator);

        // Рассчитываем стоимость дополнительных опций
        let costOptions = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};

        // окончательный расчет
        result.cost = costOperator + costOptions.cost; //полная себестоимость печати тиража
        result.price = (result.cost * (1 + insaincalc.common.marginOperation) + costOptions.price);
        result.time = timeOperator + costOptions.time;
        result.timeReady = result.time + baseTimeReady; // время готовности
        result.weight = 0; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err
    }
};