# Кейсы JS-раннера

Команды `scripts/run_js_calc.mjs` для сверки старого JS с API. По одному кейсу на функцию; вход — `REF_PARAMS` из `calc_service/tests/test_calculators/test_<slug>.py`. Задачи перевода форм берут команду отсюда.

`price` — вывод раннера на `--data current` 05.11.2026 (после выравнивания портов с JS). При смене прайса число пересчитывается раннером, сверка с API — abs ≤ 0.02 и rel ≤ 0.001.

PowerShell 5.1: кавычки JSON внутри `--args` экранируются `\"`.

| Функция | Slug API | `price` |
| --- | --- | --- |
| `calcFlagPaper` | `flag` | 3934.410784 |
| `calcFlagPaper` form 55 default | `flag` | 4052.296608 |
| `calcPennantPaper` | `pennant` | 2181.133696 |
| `calcRollup` | `rollup` | 7910 |
| `calcRollup` form 49 default | `rollup` | 4482 |
| `calcPresswall` | `presswall` | 11453.624 |
| `calcPresswall` eyelet mode 1 | `presswall` | 13914.624 |
| `calcPresswall` pocket mode 1 | `presswall` | 12659.624 |
| `calcPresswall` eyelet mode 2 | `presswall` | 14040.704 |
| `calcPresswall` eyelet + bag160 | `presswall` | 15932.2415 |
| `calcEmbossing` | `embossing` | 14046 |
| `calcAcrilycPrizes` | `acrylic_prizes` | 3353.72 |
| `calcAcrilycPrizes` form 78 default | `acrylic_prizes` | 8977.92 |
| `calcAcrilycPrizes` form 78 mode 0 | `acrylic_prizes` | 7794.4 |
| `calcAcrilycPrizes` form 78 grave fill | `acrylic_prizes` | 10241.92 |
| `calcUVPrint` plain mode 0 | `uv_print` | 1095 |
| `calcUVPrint` around mode 1 | `uv_print` | 17431 |
| `calcPrintSheet` | `print_sheet` | 5266.918472727273 |
| `calcPrintSheet` mode 0 | `print_sheet` | 4864.332072727273 |
| `calcPrintSheet` margins -1 | `print_sheet` | 1811.964386666667 |
| `calcPrintSheet` margins [2,2,2,2] | `print_sheet` | 3214.3125999999997 |
| `calcPrintSheet` form 6 default | `print_sheet` | 3214.3125999999997 |
| `calcCutPlotter` sheet RAFLACOAT | `cut_plotter` | 571 |
| `calcSticker` form 22 default RAFLACOAT | `sticker` | 662.134 |
| `calcSticker` 50×50 VHI80 4+0 | `sticker` | 1307.5632666666668 |
| `calcSticker` ORAJET3640 без печати | `sticker` | 577.368832 |
| `calcSticker` ORAJET3640 Technojet160ECO | `sticker` | 979.368832 |
| `calcSticker` ORAJET3640 Technojet160ECO + LaminatDLCLAM | `sticker` | 1732.368832 |
| `calcSticker` ORAJET3640 HPLatex335 | `sticker` | 2750.368832 |
| `calcSticker` ORAJET3640 TechnojetXR720 | `sticker` | 1003.368832 |
| `calcSticker` ORAJET3640 LaminatDLCLAM без печати | `sticker` | 1330.368832 |
| `calcSticker` ORAJET3640 1000×1000 1 шт | `sticker` | 890.06336 |
| `calcSticker` ORAJET3640 1000×1000 100 шт | `sticker` | 39485.3264 |
| `calcSticker` ORAJET3640 604×604 1 шт | `sticker` | 555.9914752 |
| `calcCutPlotter` ORAJET3640 1000×1000 1 шт | `cut_plotter` | 368 |
| `calcCutPlotter` ORAJET3640 604×604 1 шт | `cut_plotter` | 322 |
| `calcLaminationWide` 10 шт 1000×500 | `lamination_wide` | 3877.95 |
| `calcPolySticker` 80×80 | `poly_sticker` | 4107.8 |
| `calcPolyStickerPack` 80×80 | `poly_sticker_pack` | 6341.1 |
| `calcLaser` номерки | `laser` | 5631 |
| `calcLaser` простая резка AcrylWhite3 | `laser` | 23638 |
| `calcLaser` без резки AcrylWhite3 | `laser` | 1404 |
| `calcLaser` form 28 default | `laser` | 480 |

```powershell
node scripts/run_js_calc.mjs calcFlagPaper --data current --args '[100,[100,150],\"4+0\",\"PaperCoated115M\",{},1]'

node scripts/run_js_calc.mjs calcFlagPaper --data current --args '[100,[200,99],\"4+0\",\"PaperCoated115M\",{},1]'

node scripts/run_js_calc.mjs calcPennantPaper --data current --args '[50,[80,120],\"4+0\",\"PaperCoated115M\",{},1]'

node scripts/run_js_calc.mjs calcRollup --data current --args '[1,\"Rollup_econom_85\",\"ScrollPaper200\",{},1]'

node scripts/run_js_calc.mjs calcRollup --data current --args '[1,\"Rollup_econom_85\",\"\",{},1]'

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0},1]'

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300]},1]'

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isPocket\":[1,0,1,0],\"isCutting\":[0,1,0,1]},1]'

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300]},2]'

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0,\"isEyelet\":[300,300,300,300],\"isBag\":\"bag160\"},1]'

node scripts/run_js_calc.mjs calcEmbossing --data current --args '[500,[50,30],\"\",\"foil\",\"diary\",[],{\"isCliche\":true},1]'

node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '[10,[{\"materialID\":\"PVC3\",\"size\":[100,100],\"isTop\":false,\"options\":{}},{\"materialID\":\"PVC3\",\"size\":[100,100],\"isTop\":true,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1},\"isUVPrint\":{\"size\":[80,80]}}}],{},1]'

node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '[100,[{\"materialID\":\"AcrylTrans3\",\"size\":[20,20],\"isTop\":true,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1.3},\"isUVPrint\":{\"size\":[20,20]}}},{\"materialID\":\"AcrylTrans3\",\"size\":[20,20],\"isTop\":false,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1.3},\"isUVPrint\":{\"size\":[20,20]}}}],{},1]'

node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '[100,[{\"materialID\":\"AcrylTrans3\",\"size\":[20,20],\"isTop\":true,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1.3},\"isUVPrint\":{\"size\":[20,20]}}},{\"materialID\":\"AcrylTrans3\",\"size\":[20,20],\"isTop\":false,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1.3},\"isUVPrint\":{\"size\":[20,20]}}}],{},0]'

node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '[100,[{\"materialID\":\"AcrylTrans3\",\"size\":[20,20],\"isTop\":true,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1.3},\"isGrave\":1,\"isGraveFill\":[20,20]}},{\"materialID\":\"AcrylTrans3\",\"size\":[20,20],\"isTop\":false,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1.3},\"isUVPrint\":{\"size\":[20,20]}}}],{},1]'

node scripts/run_js_calc.mjs calcUVPrint --data current --args '[100,[20,20],[20,20],null,{\"isUVPrint\":{\"printerID\":\"RimalSuvUV\",\"resolution\":2,\"color\":\"4+1\",\"surface\":\"isPlain\"}},0]'

node scripts/run_js_calc.mjs calcUVPrint --data current --args '[100,[20,20],[20,20],null,{\"isUVPrint\":{\"printerID\":\"RimalSuvUV\",\"resolution\":2,\"color\":\"4+1\",\"surface\":\"isAround\"}},1]'

node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[210,297],\"4+4\",[0,0,0,0],0,\"PaperCoated300M\",{},1]'

node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[210,297],\"4+4\",[0,0,0,0],0,\"PaperCoated300M\",{},0]'

node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[297,210],\"4+0\",-1,0,\"VHI80\",{},1]'

node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[297,210],\"4+0\",[2,2,2,2],0,\"VHI80\",{},1]'

node scripts/run_js_calc.mjs calcPrintSheet --data current --args '[100,[297,210],\"4+0\",[2,2,2,2],4,\"VHI80\",{},1]'

node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[100,[50,50],50,0,1,\"RAFLACOAT\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"RAFLACOAT\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"VHI80\",{\"isPrint\":{\"printerID\":\"KMBizhubC220\",\"color\":\"4+0\"}},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"ORAJET3640\",{\"isPrint\":{\"printerID\":\"Technojet160ECO\",\"color\":\"4+0\"}},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"ORAJET3640\",{\"isPrint\":{\"printerID\":\"Technojet160ECO\",\"color\":\"4+0\"},\"isLamination\":\"LaminatDLCLAM\"},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"ORAJET3640\",{\"isPrint\":{\"printerID\":\"HPLatex335\",\"color\":\"4+0\"}},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"ORAJET3640\",{\"isPrint\":{\"printerID\":\"TechnojetXR720\",\"color\":\"4+0\"}},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[50,50],50,0,1,\"ORAJET3640\",{\"isLamination\":\"LaminatDLCLAM\"},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[1,[1000,1000],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[100,[1000,1000],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[1,[604,604],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[1,[500,500],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcSticker --data current --args '[1,[1000,500],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[1,[1000,1000],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[100,[1000,1000],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[1,[604,604],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[1,[500,500],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcCutPlotter --data current --args '[1,[1000,500],50,0,1,\"ORAJET3640\",{},1]'

node scripts/run_js_calc.mjs calcLaminationWide --data current --args '[10,[1000,500],1]'

node scripts/run_js_calc.mjs calcPolySticker --data current --args '[20,[80,80],1,\"PaperCoated115M\",{\"isPrint\":{\"printerID\":\"KMBizhubC220\",\"color\":\"4+0\"}},1]'

node scripts/run_js_calc.mjs calcPolyStickerPack --data current --args '[20,[80,80],[{\"size\":[30,30],\"difficulty\":1},{\"size\":[30,30],\"difficulty\":1},{\"size\":[30,30],\"difficulty\":1},{\"size\":[30,30],\"difficulty\":1},{\"size\":[30,30],\"difficulty\":1}],\"PaperCoated115M\",{\"isPrint\":{\"printerID\":\"KMBizhubC220\",\"color\":\"4+0\"}},1]'

node scripts/run_js_calc.mjs calcLaser --data current --args '[50,[40,80],\"AcrylColor3\",{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1},\"isGrave\":1,\"isGraveFill\":[30,40]},1]'

node scripts/run_js_calc.mjs calcLaser --data current --args '[100,[50,50],\"AcrylWhite3\",{\"isCutLaser\":{\"sizeItem\":50,\"density\":25,\"difficulty\":1,\"lenCut\":0},\"isFindMark\":false,\"Material\":\"isMaterial\"},1]'

node scripts/run_js_calc.mjs calcLaser --data current --args '[100,[50,50],\"AcrylWhite3\",{\"Material\":\"isMaterial\"},1]'

node scripts/run_js_calc.mjs calcLaser --data current --args '[100,[50,50],\"\",{\"isCutLaser\":{\"sizeItem\":50,\"density\":25,\"difficulty\":1,\"lenCut\":0},\"isFindMark\":false,\"Material\":\"isMaterial\"},1]'

node scripts/run_js_calc.mjs calcLaser --data current --args '[100,[50,50],\"AcrylWhite3\",{\"isCutLaser\":{\"sizeItem\":50,\"density\":25,\"difficulty\":1,\"lenCut\":0},\"isFindMark\":false,\"Material\":\"noMaterial\"},1]'

node scripts/run_js_calc.mjs calcLaser --data current --args '[100,[50,50],\"AcrylWhite3\",{\"isCutLaser\":{\"sizeItem\":50,\"density\":25,\"difficulty\":1,\"lenCut\":0},\"isFindMark\":false,\"Material\":\"isMaterialCustomer\"},1]'

node scripts/run_js_calc.mjs calcBadge --data current --args '[50,[85,55],1,\"PVC3\",{\"isPrint\":\"\",\"isCutLaser\":\"\"},1]'
```

Кейсы `calcLaser` сняты 15.11.2026 (`--data current`). Номерки: `time_ready` 19.05. Простая резка: `time_ready` 27.17. «Без резки»: `time_ready` 16.2. Дефолт формы 28 (пустой материал) раннер не печатает: `weight` становится NaN и скрипт пишет «Поле cost не число (NaN)». На странице `calcLaser` даёт cost 300, price 480, time 0.2, `time_ready` 16.2. В API вес 0 и `materials` пустой — контракт ответа, не NaN. `noMaterial` на простой резке: price 22465, `time_ready` 27.17, вес как у `isMaterial` (0.8925), основной материал в расход не входит. `isMaterialCustomer`: price 27961, `time_ready` 29.92 (рез и гравировка × 1.25), вес тот же.

Листовые кейсы `calcCutPlotter` / `calcSticker` / `calcPolySticker` / `calcPolyStickerPack` сняты 14.11.2026 (`--data current`). У полимерных наклеек `time_hours` Python на 0.01 ч ниже раннера: `print_laser` округляет время через `round`, JS — `Math.ceil`. Вес стикерпака: раннер 0.2, Python 0.19 — `round` веса эпоксидки. Оба остатка вне `cut-plotter-sheet-layout`.

Рулонные кейсы `calcSticker` и `calcLaminationWide` сняты 14.11.2026 (`--data current`, раннер грузит `calcLamination.js` и `laminat.json`). `cost` и `price` совпадают до копейки; `time_ready` Python на 0.01–0.02 ч ниже: резка округляет время через `round`, JS — `Math.ceil`.

ORAJET3640 1000×1000, 604×604 и контроль 500×500 / 1000×500 сняты 15.11.2026 (`--data current`). Запасная ветка рулона: длина с `numBondMaterial`, на 604×604 ширина 1520 мм. У 604×604 `time_ready` Python на 0.01 ч ниже (тот же `round`).

Известные расхождения Python с JS вне этих кейсов: бейдж на кейсе 50 шт. 85×55 PVC3 с печатью — price сходится (JS 6060.5, Python 6061, 15.11.2026, после `material_mode=noMaterial` на второй резке). Не сходятся `time_ready` (JS 17.9, Python 16.55: JS прибавляет `result.time` к max времени операций) и вес (JS 0.87, Python 1.18: JS не включает вес второй резки). Это прежний порт `badge.py`, не цена материала. Вес лазерной листовой печати к JS не выравнивать: `calcPrintLaser` считает весь лист (`numSheet` × `sizeSheet`, с обрезью), Python — тираж × размер изделия. Верный вес — Python, решение 11.11.2026. Вымпел 50×80×120 `PaperCoated115M` без ламинации: JS `weight_kg` 0.1328, Python 0.1052 (лист того же входа: JS 0.0828, Python 0.0552).
