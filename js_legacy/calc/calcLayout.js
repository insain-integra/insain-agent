// Функция расчета раскладки изделий на листе
insaincalc.calcLayoutOnSheet = function calcLayoutOnSheet(size, sizeSheet, margins=[0,0,0,0], interval=0,alongLong = 0) {
    //Входные данные
    //	size - размер изделия, size[ширина, высота]
    //	sizeSheet -  размеры листа, sizeSheet[ширина, высота]
    //	margins - оступы от края листа margins[слева, сверху, справа, снизу]
    //	interval - отступы между изделиями
    //  alongLong - если 0, тогда размещать наиболее выгодным образом,
    //                   1 - длинной по ширине рулона,
    //                   -1 - короткой по ширине рулона,
    //Выходные данные
    //  alongLong - если True, тогда размещать выгодно длинной по ширине рулона, иначе вдоль рулона
    //  num - кол-во изделий
    //	numAlongLongSide - кол-во изделий вдоль широкой стороны
    //	numAlongShortSide - кол-во изделий вдоль узкой стороны
    let result = {alongLong:true,num:0,numAlongLongSide:0,numAlongShortSide:0};
    let widthPrint = sizeSheet[0] - margins[0] - margins[2]; // определяем область печати по ширине
    let heightPrint = sizeSheet[1] - margins[1] - margins[3]; // определяем область печати по высоте
    let minSize =  Math.min(size[0], size[1]) + interval; // определяем наиболее узкую часть изделия
    let maxSize =  Math.max(size[0], size[1]) + interval; // определяем наиболее широкую часть изделия
    let minSizeSheet =  Math.min(widthPrint, heightPrint)+ interval; // определяем наиболее узкую часть листа
    let maxSizeSheet =  Math.max(widthPrint, heightPrint)+ interval; // определяем наиболее широкую часть листа
    let amountMaxAlongLongSide = Math.floor(maxSizeSheet / maxSize) * Math.floor(minSizeSheet / minSize); // считаем кол-во изделий если изделие длинной стороной располагать вдоль длинной стороны листа
    let amountMaxAlongShortSide = Math.floor(maxSizeSheet / minSize) * Math.floor(minSizeSheet / maxSize); // считаем кол-во изделий если изделие длинной стороной располагать вдоль короткой стороны листа
    if ((amountMaxAlongLongSide == 0) &&  (amountMaxAlongShortSide == 0)) {return result}
    if (amountMaxAlongLongSide > amountMaxAlongShortSide && (alongLong == 1 || alongLong == 0)) {
        result.numAlongLongSide = Math.floor(maxSizeSheet / maxSize);
        result.numAlongShortSide = Math.floor(minSizeSheet / minSize);
        result.num = amountMaxAlongLongSide;
    } else {
        result.numAlongLongSide = Math.floor(maxSizeSheet / minSize);
        result.numAlongShortSide = Math.floor(minSizeSheet / maxSize);
        result.num = amountMaxAlongShortSide;
        result.alongLong = false;
    }
    return result;
}

// Функция расчета оптимальной раскладки изделий на рулоне
insaincalc.calcLayoutOnRoll = function calcLayoutOnRoll(num, size, sizeRoll, interval = 0,alongLong = 0) {
    //Входные данные
    //  num - кол-во изделий
    //	size - размер изделия, size[ширина, высота]
    //	sizeRoll -  размеры рулона, sizeRoll[ширина, длинна]
    //  interval - расстояние между изделиями
    //  alongLong - если 0, тогда размещать наиболее выгодным образом,
    //                   1 - длинной по ширине рулона,
    //                   -1 - короткой по ширине рулона,
    //Выходные данные
    let result = {alongLong:true,numWide:0,numFar:0,wide:0,length:0};
    //  alongLong - если True, тогда размещать выгодно длинной по ширине рулона, иначе вдоль рулона
    //	numWide - кол-во изделий по ширине рулона
    //	numFar - кол-во изделий вдоль рулона
    //	wide - ширина которую изделия занимают на материале
    //	length - длинна рулона для раскроя
    let minSize =  Math.min(size[0], size[1]) // определяем наиболее узкую сторону изделия
    let maxSize =  Math.max(size[0], size[1])  // определяем наиболее широкую сторону изделия
    if (minSize>sizeRoll[0]) return result; // если изделие не влазит на рулон, то выходим
    if (maxSize<sizeRoll[0]) { // если изделие помещается в ширину рулона любой ориентацией
        let numWideMin = Math.floor((sizeRoll[0] + interval) / (minSize + interval)); // сколько изделий помещается вдоль ширины рулона короткой стороной
        let numWideMax = Math.floor((sizeRoll[0] + interval) / (maxSize + interval)); // сколько изделий помещается вдоль ширины рулона длинной стороной
        let numFarMin = Math.ceil(num / numWideMin); // сколько рядов изделий вдоль рулона если размещать по ширине короткой стороной
        let numFarMax = Math.ceil(num / numWideMax); // сколько рядов изделий вдоль рулона если размещать по ширине длинной стороной
        let lengthMin = numFarMin * maxSize + (numFarMin - 1) * interval; // длинна рулона в двух случаях
        let lengthMax = numFarMax * minSize + (numFarMax - 1) * interval;
        if (lengthMin < lengthMax && (alongLong == -1 || alongLong == 0))  { // если экономичнее расход при размещение короткой стороной по ширине
            result.alongLong = false;
            result.numWide = numWideMin;
            result.numFar = numFarMin;
            result.wide = numWideMin * (minSize + interval) - interval ;
            result.length = lengthMin;
        } else {  // если экономичнее расход при размещение длинной стороной по ширине
            result.alongLong = true;
            result.numWide = numWideMax;
            result.numFar = numFarMax;
            result.wide = numWideMax * (maxSize + interval) - interval;
            result.length = lengthMax;
        }
    } else {
        if (alongLong == 1) {return result;} // указано размещать длинной, а не получается
        let numWideMin = Math.floor((sizeRoll[0] + interval) / (minSize + interval));
        let numFarMin = Math.ceil(num / numWideMin);
        let lengthMin = numFarMin * maxSize + (numFarMin - 1) * interval;
        result.alongLong = false;
        result.numWide = numWideMin;
        result.numFar = numFarMin;
        result.wide = numWideMin * (minSize + interval) - interval;
        result.length = lengthMin;
    }
    return result;
}