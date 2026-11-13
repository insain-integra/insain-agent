# sticker-print-wide

Статус: выкатка
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: предпосылка `form-sticker`: новый модуль `lamination_wide` + вызовы `print_wide`/`lamination_wide` в `sticker.py`; skill `new-calculator` и `port-fix-prerequisite`; ответ API меняется.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

`POST /api/v1/calc/sticker` с широкими принтерами (`Technojet160ECO`, `HPLatex335`, `TechnojetXR720`) и рулонной широкой ламинацией (`LaminatDLCLAM`) сходится с раннером `calcSticker` на эталонах из блокера `form-sticker` («Факты: интерьерная печать»). В реестре есть slug `lamination_wide` (порт `calcLaminationWide`). Строки `calcLaminationWide module`, `calcSticker call calcPrintWide`, `calcSticker call calcLaminationWide` сняты из `scripts/js_port_gaps_allowed.txt`.

## Контекст и ссылки

- `todo/form-sticker.md` — раздел «Факты: интерьерная печать» (числа раннера и текущий API), блокер и журнал.
- `.cursor/skills/new-calculator/SKILL.md` — заведение `lamination_wide`.
- `.cursor/skills/port-fix-prerequisite/SKILL.md` — эталоны с раннера, тест падает без правки, соседи, `deploy-api`, возврат к `form-sticker`.
- `js_legacy/calc/calcSticker.js` — ветки печати (~66–80) и ламинации (~87–99): лазер vs `calcPrintWide`; рулон (`height == 0`) → `calcLaminationWide`, лист → `calcLamination`.
- `js_legacy/calc/calcLamination.js` — `calcLaminationWide` (ламинатор `LaminatorWide`, материал `LaminatDLCLAM`, наценка `marginLaminationWide`).
- `calc_service/calculators/print_wide.py` — уже в реестре; образец вызова из `print_roll.py`.
- `calc_service/calculators/sticker.py` — сейчас печать только лист + `PrintLaserCalculator` при `color`; широкие принтеры игнорируются.
- `scripts/js_port_gaps_allowed.txt` — три строки пропуска; `calcPrintRoll call calcLaminationWide` после этой задачи остаётся.
- `docs/js-runner-cases.md` — дописать команды эталонов одной строкой каждая.
- Данные уже в git: `calc_service/data/equipment/laminator.json` (`LaminatorWide`), `materials/laminat.json` (`LaminatDLCLAM`), `common.json` (`marginLaminationWide`). Цены не менять.
- Остальное не открывать.

## Scope

- В git (Implementer):
  - Новый калькулятор `lamination_wide` по skill `new-calculator`: копия `_template.py`, эталон логики `calcLaminationWide`, регистрация в `__init__.py`, тесты `test_lamination_wide.py` с эталонами раннера (`# JS, ДД.ММ.ГГГГ`).
  - В `sticker.py`: при `printer_code` ∈ {`Technojet160ECO`, `HPLatex335`, `TechnojetXR720`} вызывать `PrintWideCalculator` как в JS (`quantity`/`n` = 1, размер = размер расхода резки `materialCut[1]`, тот же `material_id` и `printer_code`, `mode`). Лазер `KMBizhubC220` — без регресса (лист + `PrintLaserCalculator`).
  - Листовой материал + широкий принтер: не молча отдавать цену «без печати». Как в JS (`calcPrintWide` ищет материал в roll) — ошибка с русским текстом / HTTP 400, не `price` резки.
  - Рулон + `lamination_id` (в т.ч. `LaminatDLCLAM`): `LaminationWideCalculator`, не `LaminationCalculator`. Лист + листовая ламинация — по-прежнему `LaminationCalculator`.
  - Снять из `scripts/js_port_gaps_allowed.txt`: `calcLaminationWide module`, `calcSticker call calcPrintWide`, `calcSticker call calcLaminationWide`. Строку `calcPrintRoll call calcLaminationWide` не трогать.
  - При необходимости для снятия эталонов — подключить в `scripts/run_js_calc.mjs` загрузку каталога ламината (`insaincalc.laminat` / `laminat.json`), иначе `calcLaminationWide` падает. Правка только для раннера, не для прода.
  - Эталоны `test_sticker.py` (и при необходимости `test_lamination_wide.py`) с `rel=0.001` по `cost`/`price`/`time_ready`. Команды раннера — в комментарии теста и в `docs/js-runner-cases.md`.
  - Соседи, вызывающие правленые модули, не сдвигаются: `print_roll`, `lamination` (листовая), лазерная ветка `sticker`, `poly_sticker` / `poly_sticker_pack` / `keychain` на своих эталонах.
- На проде (Site ops, после слияния в `main` и зелёного CI, skill `deploy-api`): выкатка API; smoke на телах эталонов блокера (рулон ORAJET3640 + широкая печать ± ламинация; лист RAFLACOAT + широкий принтер → ошибка). Боевую форму 22 и копию 97 не трогать.
- Ветка `task/sticker-print-wide` от `main`.
- После `close` этой задачи `form-sticker` станет `черновик`: там — правка `wp-plugin/forms/sticker.js` (передача `printer_code` / `color` / `lamination_id` из `dpdRollWideLaminat`) и перезапись JS копии 97. В эту задачу JS и копия не входят.

## Файлы

- `calc_service/calculators/lamination_wide.py` — новый
- `calc_service/calculators/__init__.py`
- `calc_service/calculators/sticker.py`
- `calc_service/tests/test_calculators/test_lamination_wide.py` — новый
- `calc_service/tests/test_calculators/test_sticker.py`
- `scripts/js_port_gaps_allowed.txt`
- `scripts/run_js_calc.mjs` — только если без загрузки ламината нельзя снять эталон
- `docs/js-runner-cases.md` — строки команд эталонов (общий файл; если не внесли — в «Результат»)

## Не-scope

- `wp-plugin/forms/sticker.js`, перезапись custom JS копии 97, `read_file` / переключение боевой формы 22, `deploy-wp-plugin`.
- Вызов `lamination_wide` из `print_roll.py` (остаётся в `js_port_gaps_allowed.txt` как `calcPrintRoll call calcLaminationWide`).
- Правка цен, наценок, курсов в `calc_service/data/` (данные для широкой ламинации уже есть).
- Расхождение рулона без печати ORAJET3640 (раннер 577.37 vs API 558.59) — оба округляются в 600 ₽; не эталон этой задачи.
- Расхождение 50×50 VHI80 / `sticker-vs-js`.
- Форма 29 CalcStickerPack и остальные формы эпика.
- Приёмка и `finish-task` для `form-sticker`.

## Критерии приёмки

- [ ] `Select-String -Path calc_service\calculators\__init__.py -Pattern '"lamination_wide"'` — есть строка; `python -c "from calculators import CALCULATORS; print('lamination_wide' in CALCULATORS)"` из `calc_service` — `True`.
- [ ] `python scripts/js_port_gaps.py calcSticker` — в блоке `calcSticker` нет `call calcPrintWide` / `call calcLaminationWide`; `calcLaminationWide module` отсутствует в `нет в Python` (или файла gaps без этих трёх строк).
- [ ] Раннер и `StickerCalculator` / `POST` на эталонах (100 шт, 50×50, size_item 50, density 0, difficulty 1, mode 1), `price`/`time_ready` abs ≤ 0.02 и rel ≤ 0.001:
  - ORAJET3640 + `Technojet160ECO`, без ламинации — JS `price` 979.368832, `time_ready` 16.32;
  - ORAJET3640 + `Technojet160ECO` + `LaminatDLCLAM` — JS `price` 1732.368832, `time_ready` 16.33;
  - ORAJET3640 + `HPLatex335` — JS `price` 2750.368832, `time_ready` 16.68;
  - RAFLACOAT + `Technojet160ECO` или `HPLatex335` — не HTTP 200 с ценой резки; ошибка (как падение JS на `name` / обнуление на форме 22).
- [ ] Лазер без регресса: RAFLACOAT без печати — `price` 662.134; при необходимости лист + `KMBizhubC220` — прежние эталоны `test_sticker.py` `passed`.
- [ ] Новые тесты без правки `sticker.py` / без модуля `lamination_wide` падают; соседи `print_roll`, листовая `lamination`, `poly_sticker`, `poly_sticker_pack`, `keychain` на старых эталонах — `passed`.
- [ ] `python -m pytest calc_service/tests/test_calculators/test_lamination_wide.py calc_service/tests/test_calculators/test_sticker.py -q` — `passed`, `failed` нет.
- [ ] После слияния в `main`, зелёный CI, skill `deploy-api`: боевой `POST https://insain.ru/api/v1/calc/sticker` на тех же телах даёт те же `price`/`time_ready` (или HTTP 400 на листовом + широком). Форма 22 и копия 97 не менялись.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: `sticker` пока не на боевых формах API (`docs/site/forms.md`). После деплоя меняется ответ `POST /calc/sticker` и появляется `POST /calc/lamination_wide` для прямых вызовов. Боевую страницу формы 22 не трогаем.
- Цены: JSON не править. Меняется только сборка стикера при широкой печати/ламинации и новый slug.
- Формы: копия 97 без правки `sticker.js` по-прежнему не шлёт широкий `printer_code` — сходимость на копии проверяет возобновлённый `form-sticker`.

## Режим

прод

## Журнал передач

14.11.2026 — Analyst, Grok 4.7 — задача оформлена по блокеру `form-sticker` (интерьерная печать) — дальше Implementer, Opus 5.5
14.11.2026 — Implementer, Opus 5.5 — сделано, `make check` зелёный. Сверх «Файлов» три правки, без них критерии не закрывались: `cut_plotter.py` — расход рулона без округления до 0.01 м (иначе `sticker` ниже раннера на 0.91 ₽, abs ≤ 0.02 не выполняется; калькулятор не на боевых формах — правило `workflow.md`, «Находки вне scope»), тест к нему в `test_cut_plotter.py`; `scripts/js_port_gaps.py` — строка `calcLaminationWide` в `PORTS` (иначе `calcLaminationWide module` не снимается). Побочно рулон ORAJET3640 без печати сошёлся с раннером (558.59 → 577.368832) — дальше Reviewer, Grok 4.7
14.11.2026 — Reviewer, Grok 4.7 — принято; три правки сверх «Файлов» в scope — дальше человек: слияние и выкатка
14.11.2026 — человек — принято — выкатка

## Найдено вне scope

- `sticker.py`, рулон с `length_min > 0`: стоимость плёнки умножается на ширину в метрах, в JS — в мм (Python в 1000 раз ниже). ORAJET3640 не задет (`length_min` 0).
- `print_wide.py`: время подготовки `time_prepare * max(1, mode)`, в JS `timePrepare * modeProduction` — расхождение в режиме 0.
- JS `calcLaminationWide` не задаёт `timeReady` (0); в `lamination_wide` — `time_hours` + базовый срок, отмечено в docstring.

## Результат

- Ветка, PR или коммит: `task/sticker-print-wide`, не закоммичено (коммит — по просьбе человека).
- Период: 14.11.2026
- Часы человека:
- Работа агентов: Implementer, Opus 5.5 — одна сессия.
- Было / стало: ORAJET3640 + Technojet160ECO 558.59 → 979.368832; + LaminatDLCLAM 558.59 → 1732.368832; HPLatex335 558.59 → 2750.368832; RAFLACOAT + широкий принтер HTTP 200 662.134 → HTTP 400.
- Сделано: новый калькулятор `lamination_wide` (порт `calcLaminationWide`, `LaminatorWide` + `LaminatDLCLAM`, `marginLaminationWide`; `costOperation` читается из `laminator.json`, в `EquipmentSpec` его нет), регистрация в реестре. `sticker.py`: `Technojet160ECO` / `HPLatex335` / `TechnojetXR720` → `PrintWideCalculator(1, [ширина рулона из резки, 0])`, `color` не нужен; лист + широкий принтер → `ValueError` «Широкоформатная печать доступна только на рулонном материале» (HTTP 400); рулон + любой `lamination_id` → `LaminationWideCalculator`, лист — по-прежнему `LaminationCalculator`; ширина рулона для стоимости плёнки — выбранная резкой (была первая из `sizes`). `cut_plotter.py`: расход рулона `round(…, 6)` вместо `round(…, 2)`. Раннер грузит `calcLamination.js` и `laminat.json` (legacy + `--data current`). Из `js_port_gaps_allowed.txt` сняты три строки, `calcPrintRoll call calcLaminationWide` осталась. Команды и цены эталонов — `docs/js-runner-cases.md`.
- Чем проверено: `python scripts/dev.py check` — код 0, `588 passed` + `81 passed`. `python -c "from calculators import CALCULATORS; print('lamination_wide' in CALCULATORS)"` — `True`; `Select-String … '"lamination_wide"'` — строка 60. `python scripts/js_port_gaps.py calcSticker` — у `calcSticker` и `calcLaminationWide -> calc_service/calculators/lamination_wide.py` «нет в Python» пусто; `--check` — `ok`. Раннер = Python (`TestClient` POST): 979.368832 (JS `time_ready` 16.32 / Py 16.31), 1732.368832 (16.33 / 16.32), 2750.368832 (16.68 / 16.67), TechnojetXR720 1003.368832, рулон без печати 577.368832, RAFLACOAT без печати 662.134 (без регресса); RAFLACOAT + Technojet160ECO / HPLatex335 — HTTP 400. `calcLaminationWide` на 4 кейсах (режимы 0/1/2, минимум 1 м²) — `cost`/`price`/`time_hours`/`weight_kg` до копейки. Тест ловит поломку: со старым `sticker.py` — `9 failed`; с `round(…, 2)` в резке — `7 failed`. Соседи `print_roll`, `lamination`, `poly_sticker`, `poly_sticker_pack`, `keychain`, `print_wide`, `cut_plotter` — `122 passed` вместе с новыми.
- Не сделано и почему: прод (деплой API и smoke) — Site ops после слияния в `main` и зелёного CI, skill `deploy-api`.
- Требуется решение: нет. Три правки сверх «Файлов» приняты в «Ревью 1».

## Ревью 1

**Итог:** принято. Статус остаётся `ревью` — дальше человек: слияние в `main`, затем Site ops (skill `deploy-api`). Прод-критерий этим кругом не закрывается.

### Критерии (git / локально)

| Критерий | Проверка |
| --- | --- |
| Реестр `lamination_wide` | `Select-String` — `calculators/__init__.py:60`. `python -c "from calculators import CALCULATORS; …"` из `calc_service` — `True` |
| `js_port_gaps.py calcSticker` | У `calcSticker`, `calcPrintWide`, `calcLaminationWide` строка `нет в Python:` пустая. `call calcPrintWide` / `call calcLaminationWide` / `calcLaminationWide module` нет. `--check` — `ok`. `calcPrintRoll call calcLaminationWide` в `js_port_gaps_allowed.txt` на месте |
| Эталоны 100 шт, 50×50, ORAJET3640, mode 1 | Раннер `--data current` и `StickerCalculator.execute`: `price` совпадает. `time_ready` Python на 0.01 ч ниже (16.31 / 16.32, 16.32 / 16.33, 16.67 / 16.68): abs 0.01 ≤ 0.02, rel ≈ 0.0006 ≤ 0.001 |
| RAFLACOAT + широкий принтер | Раннер: `Cannot read properties of undefined (reading 'name')`, exit 1. `POST /api/v1/calc/sticker` — HTTP 400, `detail` «Широкоформатная печать доступна только на рулонном материале» |
| Лазер без регресса | RAFLACOAT без печати — `price` 662.134. Прежние тесты `test_sticker.py` в прогоне `122 passed` |
| Соседи | `test_lamination_wide.py`, `test_sticker.py`, `test_cut_plotter.py`, `test_print_roll.py`, `test_lamination.py`, `test_poly_sticker.py`, `test_poly_sticker_pack.py`, `test_keychain.py`, `test_print_wide.py` — `122 passed` |
| pytest двух файлов | В том же прогоне `test_lamination_wide.py` и `test_sticker.py` без `failed` |

Числа раннера: Technojet160ECO `price` 979.368832 / `time_ready` 16.32; + LaminatDLCLAM 1732.368832 / 16.33; HPLatex335 2750.368832 / 16.68; без печати 577.368832 / 16.17 (Python 16.16); TechnojetXR720 1003.368832 / 16.32 (Python 16.31). `calcLaminationWide` `[1,[1270,0],1]` — `cost` 465, `price` 753, `time_hours` 0.01, `weight_kg` 0.09 (`time_ready` в JS 0, в Python — срок ламинатора, уже в «Найдено вне scope»).

Рулон + ламинация без печати (не в списке критериев по `time_ready`): `price` 1330.368832 совпал; `time_ready` JS 16.19 / Python 16.17. Это прежний `round` времени резки против `Math.ceil` в JS, не новая ошибка сборки.

### Три правки сверх «Файлов»

Приняты, без них критерии не выполняются.

- `cut_plotter.py`: `round(…, 6)` вместо `round(…, 2)` у расхода рулона в метрах. Иначе стоимость плёнки в `sticker` ниже раннера примерно на 0.91 ₽ и abs ≤ 0.02 не сходится. `cost`/`price` самой резки от этого поля не зависят. `cut_plotter` и `sticker` не на боевых формах (`docs/site/forms.md`) — правка на месте по `workflow.md`, «Находки вне scope». Побочно рулон ORAJET3640 без печати совпал с раннером (577.368832); на форме оба значения всё равно в 600 ₽.
- `test_cut_plotter.py`: эталон 0.232 м на ORAJET3640 100×50×50, ширина 1520. Без него регрессия округления не ловится.
- `scripts/js_port_gaps.py`: `calcLaminationWide` → `calculators.lamination_wide` в `PORTS`. Иначе после снятия строки из allowed остаётся пропуск `module`, и `--check` не `ok`.

### Diff

- Новые, **не в индексе:** `calc_service/calculators/lamination_wide.py`, `calc_service/tests/test_calculators/test_lamination_wide.py`.
- `sticker.py` — широкие принтеры → `PrintWideCalculator(1, [ширина рулона из резки, 0])`; лист + широкий принтер → `ValueError`; рулон + любой `lamination_id` → `LaminationWideCalculator` (плёнка всегда `LaminatDLCLAM`, как в JS); лист — прежний `LaminationCalculator`.
- `__init__.py`, `js_port_gaps_allowed.txt` (три строки сняты), `run_js_calc.mjs` (каталог ламината), `docs/js-runner-cases.md`, `test_sticker.py`.
- `cut_plotter.py`, `test_cut_plotter.py`, `scripts/js_port_gaps.py` — см. выше.
- `todo/sticker-print-wide.md`, `docs/dashboard.md` — статус и дашборд.

Инварианты: цен в Python нет (`costOperation` читается из `laminator.json`; `0.0011` — коэффициент веса из JS). Ответ `lamination_wide` содержит обязательные поля; у материала есть `code`, `name`, `title`. Наценка `max(MARGIN_OPERATION + marginLaminationWide, MARGIN_MIN)`.

### Критерии на проде

Открыт: после слияния, зелёного CI и `deploy-api` — боевой `POST /api/v1/calc/sticker` на тех же телах. Форму 22 и копию 97 не трогать.

### Замечания

- **желательно:** в коммит слияния включить оба новых файла (`lamination_wide.py`, `test_lamination_wide.py`). Они untracked: `git commit -a` их не возьмёт.
