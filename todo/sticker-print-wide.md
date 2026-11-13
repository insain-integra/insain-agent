# sticker-print-wide

Статус: черновик
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

## Найдено вне scope

-

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
