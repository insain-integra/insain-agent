// Функция расчета стоимости резки на гильотине
insaincalc.calcCutGuillotine = function calcCutGuillotine(numSheet,size,sizeSheet,materialID,margins=[0,0,0,0],interval=0,modeProduction = 1) {
    let hevisaid =  (a) => (a == 0)?0:1;
    //Входные данные
    //	numSheet - кол-во листов для резки
    //	size - размер изделия, [ширина, высота]
	//	sizeSheet -  размеры листа, sizeSheet[ширина, высота]
	//  interval - интервал между изделиями на листе, если 0 - то считаем одним резом
	//  margins - поля печати, если 0 - то края не подрезаем
	//	materialID - материал изделия в виде ID из данных материалов
    //	modeProduction - режим работы: 0 - экономичный, 1 - стандартный (по умолчанию), 2 - ускоренный
    //Выходные данные
    let result = {cost:0,price:0,time:0};
    //	result.cost = себестоимость тиража
    //	result.price = цена тиража
    //	result.time - время на непосредственное изготовление
    let cutter = insaincalc.cutter["KWTrio3971"];
    let typesMaterial = ['sheet','roll','hardsheet']; // список типов материалов в которых ищем данные по нашему материалу.
    let material = new Map();
    if (materialID != "") {
        for (let typeMaterial of typesMaterial) {
            material = insaincalc.findMaterial(typeMaterial, materialID);
            if (material != undefined) break;
        }
        if (material == undefined) {
            throw (new ICalcError('Параметры материала не найдены'))
        }
    }
	let NumSheet80 = Math.ceil(numSheet*material.density/80); // пересчитываем пачку в листы плотностью 80гр
    let numStack = Math.ceil(NumSheet80/cutter.maxSheet); // на сколько "базовых" пачек надо разделить стопу чтобы засунуть в резак
    NumSheet80 = NumSheet80/numStack; // кол-во листов в "базовой" пачке
	let layoutOnSheet = insaincalc.calcLayoutOnSheet(sizeSheet,cutter.maxSize,[0,0,0,0],0); // влазят ли листы в резак
	if (layoutOnSheet.num == 0) return 0; // листы не помещается в резак, выходим
    layoutOnSheet = insaincalc.calcLayoutOnSheet(size,sizeSheet,margins,interval); // сколько изделий размещается на лист
    if (layoutOnSheet.num == 0) return 0; // изделия не помещаются на листе, выходим
    let numStackLongSide = Math.ceil(layoutOnSheet.numAlongLongSide/Math.floor(cutter.maxSheet/NumSheet80));
    let numStackShortSide= Math.ceil(layoutOnSheet.numAlongShortSide/Math.floor(cutter.maxSheet/NumSheet80));
    let margin = [0,0,0,0];
    margin[0] = hevisaid(margins[0]+margins[2]+Math.abs(sizeSheet[1]-size[1]));
    margin[1] = hevisaid(margins[1]+margins[3]+Math.abs(sizeSheet[0]-size[0]));
    margin[2] = hevisaid(hevisaid(margins[0])*hevisaid(margins[2])+interval);
    margin[3] = hevisaid(hevisaid(margins[1])*hevisaid(margins[3])+interval);
    let numCutLongSide = layoutOnSheet.numAlongLongSide-1+((interval == 0)?0:numStackLongSide-1)+numStackLongSide*(layoutOnSheet.numAlongShortSide-1+((interval == 0)?0:numStackShortSide-1));
    let numCutShortSide = layoutOnSheet.numAlongShortSide-1+((interval == 0)?0:numStackShortSide-1)+numStackShortSide*(layoutOnSheet.numAlongLongSide-1+((interval == 0)?0:numStackLongSide-1));
    let numCut = (margin[0]+margin[1]+margin[2]+margin[3])+Math.min(numCutLongSide,numCutShortSide); //выбираем оптимальное количество резов
    numCut = numCut * numStack // умножаем на кол-во базовых пачек
    if (numCut >= 0) {
        let timePrepare = cutter.timePrepare*modeProduction; // учитываем время подготовки в зависимости от режима подготовки
        let timeCut = numCut / cutter.cutsPerHour + timePrepare; //считаем время на резку с учетом времени на подготовку к запуску
        let timeOperator = timeCut; //считаем время затраты оператора участки резки
        let costCutterDepreciationHour = cutter.cost / cutter.timeDepreciation / cutter.workDay / cutter.hoursDay; //стоимость часа амортизации оборудования
        let costCut = costCutterDepreciationHour * timeCut + numCut * cutter.costProcess; //считаем стоимость использование оборудование включая амортизацию
        let costOperator = timeOperator * ((cutter.costOperator > 0) ? cutter.costOperator : insaincalc.common.costOperator);
        result.cost = Math.ceil(costCut + costOperator);//полная себестоимость резки
        result.price = Math.ceil(result.cost * (1 + insaincalc.common.marginOperation + insaincalc.common.marginCutGuillotine));
        result.time = Math.ceil(timeCut * 100) / 100;
    }
    return result;
};
