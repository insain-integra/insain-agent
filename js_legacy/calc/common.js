insaincalc.timeToWords = function timeToWords(time) {
    let titlesDay = ['день', 'дня', 'дней'];
    let titlesHour = ['час', 'часа', 'часов'];
    let cases = [2, 0, 1, 1, 1, 2];
    let day =  Math.round(time/8);
    let hour = Math.ceil(time % 8);
    if (day > 0) return day+' '+titlesDay[ (day%100>4 && day%100<20)? 2 : cases[(day%10<5)?day%10:5] ]
    else return hour+' '+titlesHour[ (hour%100>4 && hour%100<20)? 2 : cases[(hour%10<5)?hour%10:5] ];
}

insaincalc.calcDateReady = function calcDateReady(time) {
    let d = new Date();
    work_day = Math.floor(time / 8);
    work_hour = time % 8;
    if (d.getHours() < 10) {d.setHours(10)}
    if (d.getHours() + work_hour > 18) {
        d.setDate(d.getDate() + 1);
    }
    d.setHours(11);
    d.setMinutes(0);

    workingDays = insaincalc.common.calendar.workingDays;
    weekEnd = insaincalc.common.calendar.weekEnd;

    // Находим ближайщий рабочий день от текущей даты, если данный день рабочий то оставляем его
    isWorkDay = false;
    while (!isWorkDay) {
        let day = String(d.getDate()) + '.' + String(d.getMonth()+1);
        if ((d.getDay()>=1) && (d.getDay()<=5)) {
            if (workingDays.indexOf(day) == -1) {
                break;
            } else {
                d.setDate(d.getDate() + 1);
            }
        } else {
            if (weekEnd.indexOf(day) != -1) {
                break;
            } else {
                d.setDate(d.getDate() + 1);
            }
        }
    }
    let dayStart = d.toLocaleString('ru', {
        year: '2-digit',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    // Отсчитываем рабочие дни от ближайщего рабочего дня
    while (work_day > 0) {
        let day = String(d.getDate()) + '.' + String(d.getMonth()+1);
        if ((d.getDay()>=1) && (d.getDay()<=5)) {
            if (workingDays.indexOf(day) == -1) {work_day -= 1;}
        } else {
            if (weekEnd.indexOf(day) == -1) {work_day -= 1;}
        }
        d.setDate(d.getDate() + 1);
    }
    d.setHours(15);
    let dayFinish = d.toLocaleString('ru', {
        year: '2-digit',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });

    return [dayStart, dayFinish];
}

insaincalc.mergeMaps = function mergeMaps(map1,map2) {
    let result = map1;
    for ([key,value] of map2) {
        if (map1.has(key)) {
            value1 = map1.get(key);
            result.set(key,[value[0],value[1],value[2]+value1[2]]);
        } else {
            result.set(key,value);
        }
    }
    return result;
}

insaincalc.showMaterials = function showMaterials(materials) {
    let nameCol = ["Материал","Размер","Кол-во"];
    let head = nameCol.map(i=>`<th>${i}</th>`).join("");
    let thead = `<thead><tr>${head}</tr></thead>`;
    let arr = [...materials.entries()];
    let body = arr.map(i=>`<tr>${[i[1][0],i[1][1],Math.ceil(i[1][2]*100)/100].map(i=>`<td>${i}</td>`).join("")}</tr>`).join("");
    let tbody = `<tbody>${body}</tbody>`;
    let table = `<table class="ezfc-summary-table ezfc-summary-table-default">${thead}${tbody}</table>`;
    return table;
}

// insaincalc.round = function round(price, N, precision=10) {
//     return Math.round(Math.ceil(price / precision) * precision / N * 100) / 100 * N;
// }

insaincalc.round = function round(price, N, threshold= 100) {
    // Порог округления для цены одного изделия
    let threshold_1 = threshold/N;
    // Исходный модуль округления - ближайшая сверху к порогу степень десятки
    let module = Math.max(10**Math.ceil(Math.log10(threshold_1)), 0.01);
    // Цена одного изделия
    let itemPrice = price / N;
    // Округляем вверх по модулю
    let newItemPrice = Math.ceil(itemPrice/module)*module;
    // Если не получилось уложиться в допустимую разность, уменьшаем модуль округления
    if ((Math.abs(itemPrice - newItemPrice) > threshold_1) && (module > 0.01)) {
        module /= 10;
        newItemPrice = Math.ceil(itemPrice / module) * module;
    }
    // На всякий случай отбрасываем все цифры меньше копейки
    newItemPrice =  Math.round(newItemPrice*100)/100;

    // Считаем округлённую полную стоимость
    return newItemPrice * N;
}

insaincalc.findMaterial = function findMaterial(category, materialID) {
    let material = insaincalc[category][materialID];
    if (material == undefined) {
        for (let key in insaincalc[category]) {
            if (insaincalc[category].hasOwnProperty(key)) {
                material = insaincalc[category][key][materialID];
                if (material != undefined) break;
            }
        }
    }
    return material;
}

insaincalc.calcWeight = function calcWeight(n, density, thickness, size, unitDensity = 'гсм3', unitThickness = 'мм', unitSize = 'мм') {
    //Входные данные
    //	n - кол-во изделий
    //	density - плотность материала, поверхностная или объемная
    //	thickness - толщина материала, мм, мкм итд
    //	size - размер изделия, [ширина, высота]
    //	unitsDensity - единица измерения плотности, например гм2 или гсм3
    //	unitsThickness - единица измерения толщина, например мкм, мм
    //	unitSize - единица измерения размеров, например мм
    //Выходные данные
    //  weight - вес суммарный в кг
    let unit = {
        "мкм": 0.000001,
        "мм": 0.001,
        "см": 0.01,
        "дм": 0.1,
        "м": 1,
        "гсм2" : 10,
        "гм2" : 0.001,
        "гсм3" : 1000
    };

    let uDensity = unitDensity;
    if (uDensity == undefined) {uDensity = 'гсм3'}
    let uThickness = unitThickness;
    if (uThickness == undefined) {uThickness = 'мм'}
    let uSize = unitSize;
    if (uSize == undefined) {uSize = 'мм'}

    let normDensity = density * unit[uDensity];
    let normThickness = thickness * unit[uThickness];
    if ((uDensity == 'гсм2') || (uDensity == 'гм2')) normThickness = 1;
    let normSize = size.map(x => x * unit[uSize]);
    let weight = n * normDensity * normThickness * normSize[0] * normSize[1];

    return weight;
}