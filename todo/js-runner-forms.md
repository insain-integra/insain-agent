# js-runner-forms

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: меняет `scripts/run_js_calc.mjs` — инструмент, которым задачи форм сверяют цены.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`node scripts/run_js_calc.mjs <функция> --data current --args '…'` считает `calcFlagPaper`, `calcPennantPaper`, `calcRollup`, `calcPresswall`, `calcEmbossing`, `calcAcrilycPrizes`. На одном кейсе каждая — вход `REF_PARAMS` её `test_<slug>.py`. `price` раннера и боевого API совпадают: абсолютная разница ≤ 0.02 и относительная ≤ 0.001.

## Контекст и ссылки

- `scripts/run_js_calc.mjs` — что уже загружено (`calcUVPrint`, `calcMug`) и как устроены `--args` и `--data current`. `calcPlaque` не трогать.
- `js_legacy/calc/calcFlag.js`, `calcPennant.js`, `calcRollup.js`, `calcPresswall.js`, `calcEmbossing.js`, `calcAcrilycPrizes.js` — сигнатуры позиционных аргументов.
- `calc_service/tests/test_calculators/test_flag.py`, `test_pennant.py`, `test_rollup.py`, `test_presswall.py`, `test_embossing.py`, `test_acrylic_prizes.py` — единственный кейс, `REF_PARAMS`. Числа `price` в этих файлах не порог приёмки.
- `todo/EPIC-forms-to-api.md` — эта задача первая. Шесть `todo/form-*.md` берут команду из «Результата».
- Остальное не открывать.

## Scope

- Поднять в раннере шесть функций и зависимости, без которых вызов падает: в том числе `calcPrintLaser`, каталоги данных, подмена прайсов `--data current` для JSON, которые эти функции читают.
- Один кейс на функцию, из таблицы ниже. Новый сценарий не придумывать.
- В «Результат» — точная команда `node … --args` и `price` каждого прогона.
- Ветка `task/js-runner-forms` от `main`.

## Не-scope

- Формы ezFC, `wp-plugin/forms/`, дубли, прод WordPress.
- Калькуляторы, `calc_service/data/`, `scripts/js_port_gaps_allowed.txt`. Расхождение JS и API — стоп и эскалация, раннер под цену не подгонять.
- Пересъём эталонов в `test_<slug>.py` — это задачи форм, после зелёного сравнения здесь.
- `calcUVPrint` и `calcMug` — уже в раннере.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`. Позиционные `--args` собирает Implementer по сигнатуре JS из входа кейса. Число `price` в критерий заранее не подставлять: его печатают команды, сравнение обязано дать `ok`.

Для каждой строки таблицы: раннер печатает `price`, `POST` на том же входе печатает `price`, скрипт сравнения печатает `ok`. Иначе стоп. Калькулятор и JSON цен не менять.

| Функция | Вход | Slug API |
| --- | --- | --- |
| `calcFlagPaper` | 100 шт., 100×150, `PaperCoated115M`, `4+0`, mode 1 | `flag` |
| `calcPennantPaper` | 50 шт., 80×120, `PaperCoated115M`, `4+0`, mode 1 | `pennant` |
| `calcRollup` | 1 шт., `Rollup_econom_85`, `BannerFronlitCoat400`, mode 1 | `rollup` |
| `calcPresswall` | 1 шт., `Joker30_20_eyelet`, `BannerFronlitCoat400`, каркас, аренда 0, mode 1 | `presswall` |
| `calcEmbossing` | 500 шт., клише 50×30, foil, diary, mode 1 | `embossing` |
| `calcAcrilycPrizes` | 10 шт., два слоя PVC3 100×100, верхний — рез лазером и УФ 80×80, mode 1 | `acrylic_prizes` |

- [ ] `calcFlagPaper`. В stdout есть `price`.

```powershell
node scripts/run_js_calc.mjs calcFlagPaper --data current --args '<аргументы кейса>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/flag -ContentType 'application/json' -Body '{"quantity":100,"width_mm":100,"height_mm":150,"material_id":"PaperCoated115M","color":"4+0","mode":1}' | Select-Object price
```

- [ ] `calcPennantPaper`. В stdout есть `price`.

```powershell
node scripts/run_js_calc.mjs calcPennantPaper --data current --args '<аргументы кейса>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/pennant -ContentType 'application/json' -Body '{"quantity":50,"width_mm":80,"height_mm":120,"material_id":"PaperCoated115M","color":"4+0","mode":1}' | Select-Object price
```

- [ ] `calcRollup`. В stdout есть `price`.

```powershell
node scripts/run_js_calc.mjs calcRollup --data current --args '<аргументы кейса>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/rollup -ContentType 'application/json' -Body '{"quantity":1,"rollup_id":"Rollup_econom_85","material_id":"BannerFronlitCoat400","mode":1}' | Select-Object price
```

- [ ] `calcPresswall`. В stdout есть `price`.

```powershell
node scripts/run_js_calc.mjs calcPresswall --data current --args '<аргументы кейса>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/presswall -ContentType 'application/json' -Body '{"quantity":1,"presswall_id":"Joker30_20_eyelet","material_id":"BannerFronlitCoat400","is_presswall":true,"is_rent":0,"mode":1}' | Select-Object price
```

- [ ] `calcEmbossing`. В stdout есть `price`.

```powershell
node scripts/run_js_calc.mjs calcEmbossing --data current --args '<аргументы кейса>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/embossing -ContentType 'application/json' -Body '{"quantity":500,"cliche_width_mm":50,"cliche_height_mm":30,"embossing_type":"foil","item_type":"diary","is_cliche":true,"mode":1}' | Select-Object price
```

- [ ] `calcAcrilycPrizes`. В stdout есть `price`.

```powershell
node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '<аргументы кейса>'
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/acrylic_prizes -ContentType 'application/json' -Body '{"quantity":10,"layers":[{"materialID":"PVC3","size":[100,100],"isTop":false,"options":{}},{"materialID":"PVC3","size":[100,100],"isTop":true,"options":{"isCutLaser":{},"isUVPrint":{"size":[80,80]}}}],"mode":1}' | Select-Object price
```

- [ ] Сравнение каждой пары. Подставить `price` раннера и API этой функции. Stdout начинается с `ok`. Абсолютная разница > 0.02 или относительная > 0.001 — стоп.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
js = JS_PRICE
api = API_PRICE
abs_d = abs(js - api)
rel = abs_d / max(abs(api), 1e-9)
assert abs_d <= 0.02 and rel <= 0.001, (js, api, abs_d, rel)
print("ok", js, api, abs_d, rel)
'@ | python -
```

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет. Боевой API только читается.
- Цены: `calc_service/data/` не менять. Расхождение JS и API — стоп, раннер и калькулятор под число не подгонять.
- Формы: нет.

## Режим

обычный

## Результат

- пазл 1171→1152 принято человеком 05.11.2026; smoke infra/deploy.sh число не проверяет. Бейдж JS 4708 и стикер JS 1308 — отдельные задачи, не этот PR.
- Ветка, PR или коммит: `task/js-runner-forms` (поверх `main` @ `5f9dfd0`). Push/merge не делались. Эталоны после ceil: puzzle/badge/sticker/notebook/calendar/keychain/poly_sticker/poly_sticker_pack/print_laser/print_sheet, rel=0.001.
- Период: 04.11.2026
- Часы человека: не учтено
- Работа агентов: Implementer (Opus 5.5), продолжение после эскалации расхождений
- Решение человека (05.11.2026): порты Python разрешено править, чтобы совпали с JS. Отклонение от «Не-scope» принято; раннер под цену не подгоняли.
- Было / стало: порты Python расходились с JS; после правок локальный Python = JS на всех шести кейсах (abs=0).
- Сделано:
  - раннер: шесть функций + зависимости (`calcPrintLaser`/`PrintRoll`/`PrintWide`, `presswall`/`tools`);
  - порты: embossing (`findIndex > n`), acrylic (`isCutLaser:{}` + `sizeItem=sizePrint`), print_laser/print_sheet (расходники без ceil, price float), flag/pennant (margins/interval, is_hole, без ceil price), print_roll (`isJoing` всегда + `wide` из layout), presswall (`price_cut` не `cost_cut`), layout_on_roll.wide;
  - эталоны тестов пересняты; `js_port_gaps_allowed` — убран `calcPrintRoll option isJoing`;
  - `python scripts/dev.py check` зелёный.
- Чем проверено: JS runner vs локальный Python — все шесть `ok` abs=0; `python scripts/dev.py check` 498+81.
- Не сделано и почему: боевой API ещё на старом коде — после merge нужен деплой `infra/deploy.sh` с `main`, иначе `Invoke-RestMethod` на prod снова разойдётся.
- Требуется решение: Reviewer (Grok 4.7). После merge — деплой API (`infra/deploy.sh` с `main`), иначе `Invoke-RestMethod` на prod снова разойдётся.
- Команды и `price` (их копируют задачи форм):

```powershell
node scripts/run_js_calc.mjs calcFlagPaper --data current --args '[100,[100,150],\"4+0\",\"PaperCoated115M\",{},1]'
# price 3934.410784

node scripts/run_js_calc.mjs calcPennantPaper --data current --args '[50,[80,120],\"4+0\",\"PaperCoated115M\",{},1]'
# price 2181.133696

node scripts/run_js_calc.mjs calcRollup --data current --args '[1,\"Rollup_econom_85\",\"BannerFronlitCoat400\",{},1]'
# price 8321

node scripts/run_js_calc.mjs calcPresswall --data current --args '[1,\"Joker30_20_eyelet\",\"BannerFronlitCoat400\",{\"isPresswall\":true,\"isRent\":0},1]'
# price 11453.624

node scripts/run_js_calc.mjs calcEmbossing --data current --args '[500,[50,30],\"\",\"foil\",\"diary\",[],{\"isCliche\":true},1]'
# price 14046

node scripts/run_js_calc.mjs calcAcrilycPrizes --data current --args '[10,[{\"materialID\":\"PVC3\",\"size\":[100,100],\"isTop\":false,\"options\":{}},{\"materialID\":\"PVC3\",\"size\":[100,100],\"isTop\":true,\"options\":{\"isCutLaser\":{\"lenCut\":0,\"sizeItem\":0,\"density\":0,\"difficulty\":1},\"isUVPrint\":{\"size\":[80,80]}}}],{},1]'
# price 3353.72
```
