// Функция расчета стоимости квартальных календарей
insaincalc.calcCalendarQuarterly = function calcCalendarQuarterly(n,calendarID,blockID,top,bottom,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	calendarID - ID календаря (Mini,Midi,Maxi)
    //  blockID - ID блока
    //  top - параметры топа
    //  bottom - параметры подложек
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
        let costTop = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBottom = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costEyelet = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBinding = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetCursor = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let numWithDefects = n;
        // расчет обложки
        let margins =[2,2,2,2];
        let interval = 4;
        let calendar = insaincalc.findMaterial("calendar",calendarID);
        let block = insaincalc.findMaterial("calendar",blockID);
        let optionsTop = new Map();
        // расчет топа
        optionsTop.set('isLamination',top.laminatID);
        costTop = insaincalc.calcPrintSheet(numWithDefects, calendar.sizeTop, top.color, margins, interval, top.materialID, optionsTop, modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costTop.material);
        costEyelet = insaincalc.calcEyeletSheet(n,modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costEyelet.material);
        // расчет нижних блоков календаря
        // расчет печати подложек
        let optionsBottom = new Map();
        let color = bottom.color;
        optionsBottom.set('isLamination', bottom.laminatID);
        for (let sizeBlock of calendar.sizeBottom) {
            let delta = Math.abs(Math.min(sizeBlock[0],sizeBlock[1])-Math.min(block.size[0],block.size[1])) +
                Math.abs(Math.max(sizeBlock[0],sizeBlock[1])-Math.max(block.size[0],block.size[1]));
            if (delta < 10) {color = '0+0'}
            else color = bottom.color;
            costBlock = insaincalc.calcPrintSheet(numWithDefects, sizeBlock, color, margins, interval, bottom.materialID, optionsBottom, modeProduction)
            costBottom.cost += costBlock.cost;
            costBottom.price += costBlock.price;
            costBottom.time += costBlock.time;
            costBottom.weight += costBlock.weight;
            if (costBottom.timeReady < costBlock.timeReady) {costBottom.timeReady = costBlock.timeReady}
            costBottom.material = insaincalc.mergeMaps(costBottom.material,costBlock.material);
        }
        // расчет брошюровки
        let cover = {'cover':{'materialID':top.materialID,'laminatID':top.laminatID,'color':top.color},
            'backing':{'materialID':bottom.materialID,'laminatID':bottom.laminatID,'color':bottom.color}};
        let inner = [{'materialID':'PaperCoated115M','numSheet':12,'color':'0+0'}];
        let binding = {'bindingID':'metallwire','edge':'long'};
        let numBlock = calendar.sizeBottom.length * numWithDefects;
        let optionsBinding = new Map();
        optionsBinding.set('bindingID','BindRenzSRW')
        costBinding = insaincalc.calcBinding(numBlock, block.size, cover, inner, binding, optionsBinding, modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costBinding.material);
        // добавляем стоимость сеток
        let numSetBlock = Math.ceil(n / 50) * 50;
        costBottom.cost += block.cost * numSetBlock;
        costBottom.price += block.cost * numSetBlock * (1 + insaincalc.common.marginMaterial);
        costBottom.weight += block.weight * numSetBlock;
        result.material.set(blockID,[block.name,block.size,numSetBlock]);
        // добавляем стоимость курсоров с установкой
        let cursorID = 'Cursor';
        costSetCursor = insaincalc.calcSetCursor(n,cursorID,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSetCursor.material);
        // окончательный расчет
        result.cost = costTop.cost + costBottom.cost + costBinding.cost + costEyelet.cost + costSetCursor.cost; //себестоимость тиража
        result.price = (costTop.price + costBottom.price + costBinding.price + costEyelet.price + costSetCursor.price)*(1+insaincalc.common.marginCalendar); //цена тиража
        result.time =  Math.ceil((costTop.time +costBottom.time +costBinding.time + costEyelet.time + costSetCursor.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costTop.timeReady,costBottom.timeReady,costBinding.timeReady,costSetCursor.timeReady); // время готовности
        result.weight = costTop.weight + costBottom.weight + costBinding.weight + costEyelet.weight + costSetCursor.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};

// Функция расчета стоимости перекидных календарей
insaincalc.calcCalendarFlip = function calcCalendarFlip(n,size,edge,blockID,materialID,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	size - размер календаря
    //  edge - переплет календаря по короткой или длинной стороне
    //  blockID - ID блока
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
        let costBlock = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBinding = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costSetRigel = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        // расчет обложки
        let margins =[2,2,2,2];
        let interval = 4;
        let block = insaincalc.findMaterial("calendar",blockID);
        let optionsBlock = new Map();
        // расчет блока
        if (options.has('isLamination')) optionsBlock.set('isLamination',options.get('isLamination'));
        costBlock = insaincalc.calcPrintSheet(n * block.numSheet, size, block.color, margins, interval, materialID, optionsBlock, modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costBlock.material);
        // расчет брошюровки
        let cover = {'cover':{'materialID':'','laminatID':'','color':''},
            'backing':{'materialID':'','laminatID':'','color':''}};
        let inner = [{'materialID':materialID,'numSheet':block.numSheet,'color':block.color}];
        let binding = {'bindingID':'metallwire','edge':edge};
        let optionsBinding = new Map();
        optionsBinding.set('bindingID','BindRenzSRW')
        costBinding = insaincalc.calcBinding(n, size, cover, inner, binding, optionsBinding, modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costBinding.material);
        // добавляем к цене установку ригеля
        let rigelID = 'Rigel';
        if (edge == 'short') lenEdge = Math.min(size[0],size[1])
        else lenEdge = Math.max(size[0],size[1]);
        costSetRigel = insaincalc.calcSetRigel(n,lenEdge,block.numSheet,materialID,modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costSetRigel.material);
        // окончательный расчет
        result.cost = costBlock.cost + costBinding.cost + costSetRigel.cost; //себестоимость тиража
        result.price = (costBlock.price + costBinding.price + costSetRigel.price)*(1+insaincalc.common.marginCalendar); //цена тиража
        result.time =  Math.ceil((costBlock.time + costBinding.time + costSetRigel.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costBlock.timeReady,costBinding.timeReady,costSetRigel.timeReady); // время готовности
        result.weight = costBlock.weight + costBinding.weight + costSetRigel.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};

// Функция расчета стоимости настольных перекидных календарей
insaincalc.calcCalendarTableFlip = function calcCalendarTableFlip(n,calendarID,blockID,base,block,options,modeProduction = 1) {
    //Входные данные
    //	n - тираж изделий
    //	calendarID - ID календаря
    //  blockID - ID блока
    //  base - параметры основы
    //  block - параметры блока
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
        let costBase = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBlock = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let costBinding = {cost:0,price:0,time:0,timeReady:0,weight:0,material:new Map()};
        let numWithDefects = n;
        // расчет основы
        let margins =[2,2,2,2];
        let interval = 4;
        let calendar = insaincalc.findMaterial("calendar",calendarID);
        let optionsBase = new Map();
        optionsBase.set('isLamination',base.laminatID);
        optionsBase.set('isCrease',3);
        costBase = insaincalc.calcPrintSheet(numWithDefects, calendar.sizeSheet, base.color, margins, interval, base.materialID, optionsBase, modeProduction);
        result.material = insaincalc.mergeMaps(result.material,costBase.material);

        // расчет перекидного блока
        let flipBlock = insaincalc.findMaterial("calendar",blockID);
        let optionsBlock= new Map();
        let color = block.color;
        costBlock = insaincalc.calcPrintSheet(numWithDefects * flipBlock.numSheet, calendar.sizeBlock, block.color, margins, interval, block.materialID, optionsBlock, modeProduction)
        result.material = insaincalc.mergeMaps(result.material, costBlock.material);
        // расчет брошюровки
        let cover = {'cover':{'materialID':base.materialID,'laminatID':base.laminatID,'color':base.color},
            'backing':{'materialID':base.materialID,'laminatID':base.laminatID,'color':base.color}};
        let inner = [{'materialID':block.materialID,'numSheet':flipBlock.numSheet,'color':'0+0'}];
        let binding = {'bindingID':'metallwire','edge':'long'};
        let numBlock = numWithDefects;
        let optionsBinding = new Map();
        optionsBinding.set('bindingID','BindRenzSRW')
        costBinding = insaincalc.calcBinding(numBlock, calendar.sizeBlock, cover, inner, binding, optionsBinding, modeProduction);
        result.material = insaincalc.mergeMaps(result.material, costBinding.material);
        // окончательный расчет
        result.cost = costBase.cost + costBlock.cost + costBinding.cost; //себестоимость тиража
        result.price = (costBase.price + costBlock.price + costBinding.price)*(1+insaincalc.common.marginCalendar); //цена тиража
        result.time =  Math.ceil((costBase.time +costBlock.time +costBinding.time)*100)/100; // время изготовления
        result.timeReady = result.time + Math.max(costBase.timeReady,costBlock.timeReady,costBinding.timeReady); // время готовности
        result.weight = costBase.weight + costBlock.weight + costBinding.weight; //считаем вес в кг.
        return result;
    } catch (err) {
        throw err;
    }
};
