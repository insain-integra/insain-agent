/**
 * Прогон старого калькулятора из js_legacy в Node (без npm).
 *
 * Сейчас считается только calcPlaque. Поднимаются файлы, без которых
 * его ветки isUVPrint / isGrave / isSublimation / noApplication не считаются.
 * loadData из icdc_ls.js ходит в icalc/ через XMLHttpRequest — в Node
 * этот вызов снимается, JSON читается с диска и передаётся в StructDat.
 *
 * Скрипты:
 *   js_legacy/calc/icdc_ls.js
 *   js_legacy/calc/common.js
 *   js_legacy/calc/calcLayout.js
 *   js_legacy/calc/calcLaser.js
 *   js_legacy/calc/calcUVPrint.js
 *   js_legacy/calc/calcTablets.js
 *   js_legacy/calc/calcHeatPress.js
 *   js_legacy/calc/calcPrintSheet.js
 *   js_legacy/calc/calcPrintInkJet.js
 *   js_legacy/calc/calcCutGuillotine.js
 *   js_legacy/calc/calcCutRoller.js
 *   js_legacy/calc/calcProcessTools.js
 * Прайс legacy:
 *   js_legacy/calc/common.json
 *   js_legacy/material/misc.json
 *   js_legacy/material/hardsheet.json
 *   js_legacy/material/sheet.json
 *   js_legacy/material/roll.json
 *   js_legacy/equipment/laser.json
 *   js_legacy/equipment/printer.json
 *   js_legacy/equipment/cutter.json
 *   js_legacy/equipment/heatpress.json
 *   js_legacy/equipment/laminator.json
 * --data current подменяет числа в памяти из calc_service/data (файлы не пишутся):
 *   common.json, materials/plaque.json, materials/misc.json,
 *   materials/hardsheet.json, materials/sheet.json, materials/roll.json,
 *   equipment/laser.json, equipment/printer.json, equipment/cutter.json,
 *   equipment/heatpress.json, equipment/laminator.json
 */

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const JS_FILES = [
    'js_legacy/calc/icdc_ls.js',
    'js_legacy/calc/common.js',
    'js_legacy/calc/calcLayout.js',
    'js_legacy/calc/calcLaser.js',
    'js_legacy/calc/calcUVPrint.js',
    'js_legacy/calc/calcTablets.js',
    'js_legacy/calc/calcHeatPress.js',
    'js_legacy/calc/calcPrintSheet.js',
    'js_legacy/calc/calcPrintInkJet.js',
    'js_legacy/calc/calcCutGuillotine.js',
    'js_legacy/calc/calcCutRoller.js',
    'js_legacy/calc/calcProcessTools.js',
];

const LEGACY_DATA = [
    ['common', 'js_legacy/calc/common.json'],
    ['misc', 'js_legacy/material/misc.json'],
    ['hardsheet', 'js_legacy/material/hardsheet.json'],
    ['sheet', 'js_legacy/material/sheet.json'],
    ['roll', 'js_legacy/material/roll.json'],
    ['laser', 'js_legacy/equipment/laser.json'],
    ['printer', 'js_legacy/equipment/printer.json'],
    ['cutter', 'js_legacy/equipment/cutter.json'],
    ['heatpress', 'js_legacy/equipment/heatpress.json'],
    ['laminator', 'js_legacy/equipment/laminator.json'],
];

// Коды оборудования и бумаги, которые ветка читает напрямую, не из параметров.
const BRANCH_CODES = {
    isUVPrint: ['Qualitech11G1290', 'RimalSuvUV'],
    isGrave: ['Qualitech11G1290'],
    isSublimation: [
        'AccusheadPro12',
        'SahokSH49BD',
        'PaperSublimation128',
        'EPSONWF7610',
        'FGKFM360',
        'KWTrio3971',
    ],
    noApplication: [],
};

const RATE_KEYS = new Set([
    'cutPerHour',
    'gravePerHour',
    'meterPerHour',
    'sheetsPerHour',
    'defects',
    'lifeLaserTube',
    'powerPerHour',
    'timeDepreciation',
    'workDay',
    'hoursDay',
    'timePrepare',
    'timeLoad',
    'timePrepareAround',
    'baseTimeReady',
]);

function fail(message) {
    process.stderr.write(String(message).replace(/\s+$/, '') + '\n');
    process.exit(1);
}

function isRateKey(key) {
    if (key.endsWith('_source') || key.endsWith('_date')) {
        return false;
    }
    return key.startsWith('cost') || key.startsWith('margin') || RATE_KEYS.has(key);
}

function isRateValue(value) {
    if (typeof value === 'number' || Array.isArray(value)) {
        return true;
    }
    if (typeof value !== 'string') {
        return false;
    }
    const text = value.trim();
    // Формула прайса ($11600, ^.costLaserTube/...) или число строкой. Подписи не трогаем.
    return /[$#^@]/.test(text) || /^-?\d+(\.\d+)?$/.test(text);
}

function parseArgs(argv) {
    const name = argv[0];
    if (!name || name.startsWith('--')) {
        fail('Укажите имя калькулятора: node scripts/run_js_calc.mjs <имя> --params \'<json>\' [--data legacy|current]');
    }
    let dataMode = 'legacy';
    let paramsRaw = null;
    for (let i = 1; i < argv.length; i += 1) {
        const arg = argv[i];
        if (arg === '--data') {
            dataMode = argv[i + 1];
            if (!dataMode || dataMode.startsWith('--')) {
                fail('После --data нужно legacy или current');
            }
            i += 1;
        } else if (arg === '--params') {
            paramsRaw = argv[i + 1];
            if (paramsRaw === undefined) {
                fail('После --params нужен JSON');
            }
            i += 1;
        } else {
            fail(`Неизвестный аргумент: ${arg}`);
        }
    }
    if (dataMode !== 'legacy' && dataMode !== 'current') {
        fail(`Неизвестный режим прайса: ${dataMode}`);
    }
    return { name, dataMode, paramsRaw };
}

function readText(rel) {
    return fs.readFileSync(path.join(root, rel), 'utf8');
}

function loadJs(context, rel) {
    let code = readText(rel);
    if (rel.endsWith('icdc_ls.js')) {
        // В браузере loadData тянет icalc/ по XHR. Здесь прайс читается с диска.
        if (!code.includes('_.loadData("icalc/calc/common.json")')) {
            fail('В icdc_ls.js не найден вызов loadData("icalc/calc/common.json")');
        }
        code = code.replace('_.loadData("icalc/calc/common.json");', '');
        code += '\nglobalThis.ICalcError = ICalcError;\n';
    }
    vm.runInContext(code, context, { filename: rel });
}

// delComments из icdc_ls.js режет «//» даже внутри строк ("руб/шт //").
// Для текущего прайса комментарии снимаются с учётом кавычек.
function stripJsonComments(text) {
    let out = '';
    let i = 0;
    while (i < text.length) {
        const ch = text[i];
        const next = text[i + 1];
        if (ch === '"') {
            out += ch;
            i += 1;
            while (i < text.length) {
                const cur = text[i];
                out += cur;
                if (cur === '\\') {
                    i += 1;
                    if (i < text.length) {
                        out += text[i];
                    }
                } else if (cur === '"') {
                    i += 1;
                    break;
                }
                i += 1;
            }
            continue;
        }
        if (ch === '/' && next === '/') {
            i += 2;
            while (i < text.length && text[i] !== '\n') {
                i += 1;
            }
            continue;
        }
        if (ch === '/' && next === '*') {
            i += 2;
            while (i < text.length && !(text[i] === '*' && text[i + 1] === '/')) {
                i += 1;
            }
            i += 2;
            continue;
        }
        out += ch;
        i += 1;
    }
    return out.replace(/,\s*(?=[}\]])/g, '');
}

const CURRENT_FILES = [
    'calc_service/data/common.json',
    'calc_service/data/materials/plaque.json',
    'calc_service/data/materials/misc.json',
    'calc_service/data/materials/hardsheet.json',
    'calc_service/data/materials/sheet.json',
    'calc_service/data/materials/roll.json',
    'calc_service/data/equipment/laser.json',
    'calc_service/data/equipment/printer.json',
    'calc_service/data/equipment/cutter.json',
    'calc_service/data/equipment/heatpress.json',
    'calc_service/data/equipment/laminator.json',
];

function loadLegacyStruct(context, name, rel) {
    const text = readText(rel);
    context.__jsonText = text;
    vm.runInContext(
        `insaincalc[${JSON.stringify(name)}] = new insaincalc.StructDat(__jsonText);`,
        context,
        { filename: rel },
    );
}

function indexRecords(node, into) {
    if (!node || typeof node !== 'object' || Array.isArray(node)) {
        return;
    }
    for (const [key, value] of Object.entries(node)) {
        if (key === 'Default' || key === 'Links' || key === 'calendar') {
            continue;
        }
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
            continue;
        }
        const children = Object.values(value).filter(
            (item) => item && typeof item === 'object' && !Array.isArray(item),
        );
        const nested = children.some(
            (item) => 'cost' in item
                || 'costProcess' in item
                || 'costPrintSheet' in item
                || 'costCut' in item
                || 'name' in item
                || 'description' in item,
        );
        const self = 'cost' in value
            || 'costProcess' in value
            || 'costPrintSheet' in value
            || 'costCut' in value
            || 'sizePlate' in value
            || 'cutPerHour' in value
            || 'meterPerHour' in value;
        if (self && !nested) {
            into.set(key, value);
        } else {
            indexRecords(value, into);
        }
    }
}

function installSetRate(context) {
    vm.runInContext(`
        insaincalc._setRate = function (record, key, value) {
            if (typeof value === 'string') {
                var expr = value;
                expr = expr.replace(/\\$(?=\\d)/g, 'insaincalc.common.USD*');
                expr = expr.replace(/#(?=\\.)/g, 'insaincalc');
                expr = expr.replace(/\\^(?=\\.)/g, 'this');
                expr = expr.replace(/@(?!\\w)/g, "Object.getPrototypeOf(this)['" + key + "']");
                Object.defineProperty(record, key, {
                    get: new Function('return ' + expr),
                    enumerable: true,
                    configurable: true,
                });
                return;
            }
            var stored = value;
            if (Array.isArray(value)) {
                stored = JSON.parse(JSON.stringify(value));
            }
            Object.defineProperty(record, key, {
                value: stored,
                writable: true,
                enumerable: true,
                configurable: true,
            });
        };
    `, context);
}

function overlayRecord(context, target, source) {
    for (const [key, value] of Object.entries(source)) {
        if (!isRateKey(key) || !isRateValue(value)) {
            continue;
        }
        context.__rateTarget = target;
        context.__rateKey = key;
        context.__rateValue = value;
        vm.runInContext('insaincalc._setRate(__rateTarget, __rateKey, __rateValue);', context);
    }
}

function walkAndOverlay(context, node, byCode) {
    if (!node || typeof node !== 'object' || Array.isArray(node)) {
        return;
    }
    for (const key of Object.keys(node)) {
        const child = node[key];
        if (!child || typeof child !== 'object' || Array.isArray(child)) {
            continue;
        }
        if (byCode.has(key)) {
            overlayRecord(context, child, byCode.get(key));
        }
        walkAndOverlay(context, child, byCode);
    }
}

function applyCurrentPrices(context) {
    installSetRate(context);
    const byCode = new Map();
    let common = null;
    for (const rel of CURRENT_FILES) {
        let parsed;
        try {
            parsed = JSON.parse(stripJsonComments(readText(rel)));
        } catch (err) {
            fail(`Не разобран текущий прайс ${rel}: ${err.message}`);
        }
        if (rel.endsWith('/common.json') || rel.endsWith('\\common.json')) {
            common = parsed;
            continue;
        }
        indexRecords(parsed, byCode);
    }
    if (!common) {
        fail('В calc_service/data нет common.json');
    }
    for (const [key, value] of Object.entries(common)) {
        if (key === 'calendar' || !isRateKey(key)) {
            continue;
        }
        if (typeof value !== 'number' && !Array.isArray(value)) {
            continue;
        }
        context.__rateTarget = context.insaincalc.common;
        context.__rateKey = key;
        context.__rateValue = value;
        vm.runInContext('insaincalc._setRate(__rateTarget, __rateKey, __rateValue);', context);
    }
    for (const [name] of LEGACY_DATA) {
        if (name === 'common') {
            continue;
        }
        walkAndOverlay(context, context.insaincalc[name], byCode);
    }
    return byCode;
}

function requireCurrentCodes(byCode, params) {
    const codes = [params.plaque_id];
    if (params.application !== 'noApplication') {
        codes.push(params.material_id);
    }
    const extra = BRANCH_CODES[params.application];
    if (extra) {
        codes.push(...extra);
    }
    for (const code of codes) {
        if (!code || !byCode.has(code)) {
            fail(`Кода ${code} нет в текущем прайсе, кейс в режиме current не считается`);
        }
    }
}

function roundHalfEven(value, digits) {
    const sign = value < 0 ? -1 : 1;
    const factor = 10 ** digits;
    const scaled = Math.abs(value) * factor;
    const floor = Math.floor(scaled);
    const diff = scaled - floor;
    let rounded;
    if (Math.abs(diff - 0.5) < 1e-9) {
        rounded = floor % 2 === 0 ? floor : floor + 1;
    } else if (diff > 0.5) {
        rounded = floor + 1;
    } else {
        rounded = floor;
    }
    return (sign * rounded) / factor;
}

function runPlaque(params, dataMode) {
    const sandbox = {
        console: {
            log: (...args) => process.stderr.write(`${args.map(String).join(' ')}\n`),
            error: (...args) => process.stderr.write(`${args.map(String).join(' ')}\n`),
            warn: (...args) => process.stderr.write(`${args.map(String).join(' ')}\n`),
        },
    };
    sandbox.globalThis = sandbox;
    const context = vm.createContext(sandbox);
    for (const rel of JS_FILES) {
        loadJs(context, rel);
    }
    if (typeof context.insaincalc?.StructDat !== 'function') {
        fail('StructDat не поднялся из icdc_ls.js');
    }
    for (const [name, rel] of LEGACY_DATA) {
        loadLegacyStruct(context, name, rel);
    }
    if (dataMode === 'current') {
        const byCode = applyCurrentPrices(context);
        requireCurrentCodes(byCode, params);
    }
    context.__params = params;
    let caught = null;
    try {
        vm.runInContext(`
            __opts = new Map();
            __raw = insaincalc.calcPlaque(
                __params.quantity,
                __params.plaque_id,
                __params.material_id,
                __params.application,
                __opts,
                __params.mode
            );
            __result = {
                cost: __raw.cost,
                price: __raw.price,
                time: __raw.time,
                timeReady: __raw.timeReady,
                weight: __raw.weight
            };
        `, context, { filename: 'calcPlaque-call.js' });
    } catch (err) {
        caught = err;
    }
    if (caught) {
        const message = caught && caught.message ? caught.message : String(caught);
        fail(message);
    }
    const raw = context.__result;
    if (!raw) {
        fail('calcPlaque не вернул результат');
    }
    const n = Math.max(1, Number(params.quantity) || 1);
    const price = Number(raw.price);
    const fields = {
        cost: Number(raw.cost),
        price,
        unit_price: roundHalfEven(price / n, 2),
        time_hours: Number(raw.time),
        time_ready: Number(raw.timeReady),
        weight_kg: Number(raw.weight),
    };
    for (const [key, value] of Object.entries(fields)) {
        if (!Number.isFinite(value)) {
            fail(`Поле ${key} не число (${value})`);
        }
    }
    return fields;
}

const { name, dataMode, paramsRaw } = parseArgs(process.argv.slice(2));
if (name !== 'calcPlaque') {
    fail(`Калькулятор не подключён: ${name}`);
}
if (paramsRaw === null) {
    fail('Нужен --params с JSON');
}
let params;
try {
    params = JSON.parse(paramsRaw);
} catch (err) {
    fail(`params не JSON: ${err.message}`);
}
if (!params || typeof params !== 'object' || Array.isArray(params)) {
    fail('params должен быть объектом');
}
for (const key of ['quantity', 'plaque_id', 'material_id', 'application', 'mode']) {
    if (!(key in params)) {
        fail(`В params нет поля ${key}`);
    }
}

const fields = runPlaque(params, dataMode);
process.stdout.write(`${JSON.stringify(fields)}\n`);
