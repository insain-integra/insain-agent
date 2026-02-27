insaincalc.calcMetalPins = function calcMetalPins(n,options,modeProduction = 1) {
  //Входные данные
  //  n - кол-во изделий
  //  options - дополнительные опции в виде коллекция ключ/значение
  //  modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
  //Выходные данные
  let result = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
  //	result.cost = себестоимость тиража
  //	result.price = цена тиража
  //	result.time - время на непосредственное изготовление
  //	result.timeReady - время готовности тиража, те. через сколько часов можно забирать заказ
  //	result.weight - вес тиража
  //	result.material - расход материалов {'materialID':[name,size,n/length/vol]}
  // Считываем параметры материалов и оборудование
  let tool = insaincalc.metalpins['MetalPins'];
  let attachment = insaincalc.metalpins['Attachment'];
  let pack = insaincalc.metalpins['Pack'];
  let baseTimeReady = tool.baseTimeReady;
  if (baseTimeReady == undefined) {baseTimeReady = insaincalc.common.baseTimeReady}
  baseTimeReady = baseTimeReady[Math.ceil(modeProduction)];
  let defects = tool.defects;
  let costPins = {cost:0,price:0,time:0,weight:0};
  try {
    let listStamp = ['Stamp','AddStamp'];
    for (let stamp of listStamp) {
      if (options.has(stamp)) {
        // расчитываем базовую стоимость изготовления значка
        let optionsStamp = options.get(stamp);
        let size = optionsStamp.size;
        // если толщина больше 0 значит это отдельный элемент значка а не обратная сторона
        let costPin = 0;
        if (size[2] > 0) {
          let averSize = Math.sqrt((size[0] * size[0] + size[1] * size[1]) / 2); // среднеквадратичный размер
          let indexScale = Object.values(tool.ScalePCS).findIndex(item => item >= n) + 1;
          costPin = Object.values(tool.CostPins).find(item => item[0] >= averSize)[indexScale];
          // расчитываем стандартную толщину значка для данного размера
          let standartT = Object.values(tool.StandartT).find(item => item[0] >= averSize)[1];
          // высчитываем отклонение заданной толщины от стандартной
          let deltaT = Math.ceil((size[2] - standartT) / 0.2) * 0.06;
          if (deltaT < 0) {
            deltaT = 0
          }
          // увеличиваем стоимость значка в соот. отклонением толщины от заданной
          costPin = costPin * (1 + deltaT);
        }


        // расчитываем базовую стоимость штампа
        let maxSize = Math.max(size[0], size[1]); // максимальный размер
        let costStamp = 0;
        if (optionsStamp.isMould != 'isMould') {
          costStamp = Object.values(tool.CostStamp).find(item => item[0] >= maxSize)[optionsStamp.processID];
        } else {
          costStamp = tool.minCostStamp;
        }

        // расчитываем стоимость эмалей
        let numColors = optionsStamp.numEnamels;
        let costEnamels = Object.values(tool.CostEnamels).find(item => item[0] >= maxSize)[1] * numColors;

        // расчитываем стоимость покрытий
        let CostPlating = tool.CostPlating[optionsStamp.platingID];

        // расчитываем стоимость нанесения смолы
        let CostEpoxy = 0;
        if (optionsStamp.isEpoxy == 'isEpoxy') {
          CostEpoxy = tool.CostEpoxy[0] + tool.CostEpoxy[1] * size[0] * size[1] / 100;
        }

        costPins.cost += (costPin + costEnamels + CostPlating + CostEpoxy) * n + costStamp;
        costPins.weight += size[0]*size[1]*size[2]*tool.Weight[optionsStamp.materialID] * n / 1000000;
      }
    }

    // рассчитываем стоимость подготовки заказа к изготовлению
    let timeOperator = tool.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
    let costOperator = timeOperator * ((tool.costOperator > 0) ? tool.costOperator : insaincalc.common.costOperator)/insaincalc.common.USD;

    // рассчитываем стоимость установки крепления
    let costAttachment = {cost:0,price:0,time:0,weight:0};
    if (options.has('isAttachment')) {
      let idAttachment = options.get('isAttachment')
      costAttachment.cost = attachment[idAttachment].cost * n;
      costAttachment.weight = attachment[idAttachment].weight * n / 1000;
    }
    // рассчитываем стоимость упаковки
    let costPack = {cost:0,price:0,time:0,weight:0};
    if (options.has('isPacking')) {
      let idPack = options.get('isPacking')
      costPack.cost = pack[idPack].cost * n;
      costPack.weight = pack[idPack].weight * n / 1000;
    }

    // рассчитываем стоимость доставки
    let totalWeight = costPins.weight + costAttachment.weight + costPack.weight
    // let costShipment =  Math.ceil(totalWeight/1000)*14+10+Math.trunc(totalWeight/10000)*1.1;
    totalWeight = Math.ceil(totalWeight);
    let calcWeight = totalWeight;
    if ((modeProduction >=1 ) || (calcWeight < 1)) {calcWeight = 1}
    let costShipment =  calcWeight*tool.CostShipmentChinaToRussia[modeProduction] //стоимость доставки из Китая
        +Math.max(tool.CostShipmentChina*totalWeight,5) // стоимость доставки по Китаю
        +(tool.CostShipmentRussia[0] + totalWeight*tool.CostShipmentRussia[1])/insaincalc.common.USD; // стоимость доставки по России

    // итог расчетов
    //полная себестоимость резки
    result.cost = Math.ceil((costPins.cost + costAttachment.cost + costPack.cost + costShipment + costOperator) * (1+defects) * (1+tool.margin) * insaincalc.common.USD);
    // цена с наценкой
    result.price = result.cost * (1 + insaincalc.common.marginMetalPins);
    // времязатраты
    result.time = 0;
    //считаем вес в кг.
    result.weight = Math.ceil((costPins.weight + costAttachment.weight + costPack.weight)* 100) / 100;
    result.timeReady = baseTimeReady; // время готовности
    return result;
  } catch (err) {
    throw err
  }
} 
