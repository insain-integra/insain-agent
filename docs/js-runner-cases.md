# Кейсы JS-раннера

Команды `scripts/run_js_calc.mjs` для сверки старого JS с API. По одному кейсу на функцию; вход — `REF_PARAMS` из `calc_service/tests/test_calculators/test_<slug>.py`. Задачи перевода форм берут команду отсюда.

`price` — вывод раннера на `--data current` 05.11.2026 (после выравнивания портов с JS). При смене прайса число пересчитывается раннером, сверка с API — abs ≤ 0.02 и rel ≤ 0.001.

PowerShell 5.1: кавычки JSON внутри `--args` экранируются `\"`.

| Функция | Slug API | `price` |
| --- | --- | --- |
| `calcFlagPaper` | `flag` | 3934.410784 |
| `calcPennantPaper` | `pennant` | 2181.133696 |
| `calcRollup` | `rollup` | 8321 |
| `calcPresswall` | `presswall` | 11453.624 |
| `calcEmbossing` | `embossing` | 14046 |
| `calcAcrilycPrizes` | `acrylic_prizes` | 3353.72 |

```powershell
node scripts/run_js_calc.mjs calcFlagPaper --data current --args '[100,[100,150],\"4+0\",\"PaperCoated115M\",{},1]'

node scripts/run_js_calc.mjs calcPennantPaper --data current --args '[50,[80,120],\"4+0\",\"PaperCoated115M\",{},1]'

node scripts/run_js_calc.mjs calcRollup --data current --args '[1,\"Rollup_econom_85\",\"BannerFronlitCoat400\",{},1]'

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0},1]'

node scripts/run_js_calc.mjs calcEmbossing --data current --args '[500,[50,30],\"\",\"foil\",\"diary\",[],{\"isCliche\":true},1]'

node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '[10,[{\"materialID\":\"PVC3\",\"size\":[100,100],\"isTop\":false,\"options\":{}},{\"materialID\":\"PVC3\",\"size\":[100,100],\"isTop\":true,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1},\"isUVPrint\":{\"size\":[80,80]}}}],{},1]'
```

Известные расхождения Python с JS вне этих кейсов: бейдж (JS 4708, Python ~6509) и стикер 50×50 VHI80 (JS 1308, Python ~1107) — отдельные задачи `badge-vs-js` и `sticker-vs-js`.
