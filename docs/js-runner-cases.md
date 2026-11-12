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
```

Известные расхождения Python с JS вне этих кейсов: бейдж (JS 4708, Python ~6509) и стикер 50×50 VHI80 (JS 1308, Python ~1107) — отдельные задачи `badge-vs-js` и `sticker-vs-js`. Вес лазерной листовой печати к JS не выравнивать: `calcPrintLaser` считает весь лист (`numSheet` × `sizeSheet`, с обрезью), Python — тираж × размер изделия. Верный вес — Python, решение 11.11.2026. Вымпел 50×80×120 `PaperCoated115M` без ламинации: JS `weight_kg` 0.1328, Python 0.1052 (лист того же входа: JS 0.0828, Python 0.0552).
