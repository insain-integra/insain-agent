# EPIC-forms-to-api

Статус: в работе
Цель: G1

## Цель

К 30.11.2026 все 45 боевых форм-калькуляторов на https://insain.ru считают через `insaincalc.calcApi`. Переключение пачками по 5–10 форм, копии принимаются выборочно. Форма 10 `_ExternalTest` и не-калькуляторы 71/72/77 в G1 не входят.

Сверка 07.11.2026: публичный slug в `calc_service/calculators/__init__.py` есть у **44 из 45** боевых форм. Нет slug у формы **12** (`calcButtonPins`: логика в `calc_button_pins`, в реестр API не входит) — сначала обёртка-калькулятор.

## Задачи в файлах

- `form-mug` (закрыто 2026-11-07, `docs/history/log.md`) — копия 41 (88 / 2586882) принята
- `form-embossing` (закрыто 2026-11-07, `docs/history/log.md`) — копия 85
- `form-acrylic-prizes` (закрыто 2026-11-08, `docs/history/log.md`) — копия 78
- `form-rollup` (закрыто 2026-11-09, `docs/history/log.md`) — копия 49 (93 / 2586886) принята
- `presswall-banner-options` (закрыто 2026-11-09, `docs/history/log.md`) — предпосылка формы 46: крепление, люверсы, режим баннера и чехол в `presswall` API
- `form-presswall` (закрыто 2026-11-09, `docs/history/log.md`) — копия 46
- `form-pennant` (закрыто 2026-11-11, `docs/history/log.md`) — копия 73
- `flag-materials-size-mm` (закрыто 2026-11-12, `docs/history/log.md`) — предпосылка копии 55: `size_mm` в ответе `flag`
- `form-flag` (закрыто 2026-11-12, `docs/history/log.md`) — копия 55 (95 / 2586888)
- `todo/forms-batch-switch.md` — пачка 1 на боевые: 69, 26, 41
- `todo/form-button-pins.md` — калькулятор `button_pins` + копия формы 12
- `print-sheet-port-fix` (закрыто 2026-11-13, `docs/history/log.md`) — предпосылка `form-print-sheet`: ceil времени печати и `timePrepare * mode` в `print_sheet`
- `print-sheet-margins-minus-one` (закрыто 2026-11-13, `docs/history/log.md`) — предпосылка `form-print-sheet`: при `margins == -1` не прибавлять поля принтера
- `form-print-sheet` (закрыто 2026-11-14, `docs/history/log.md`) — копия формы 6, slug `print_sheet`
- `todo/print-sheet-copy-result.md` — на копии 96 показать за шт со скидкой (`htmCost`)
- `todo/form-print-offset.md` — копия формы 82, slug `print_offset` (`calcPrintOffsetPromo`)
- `todo/form-print-roll.md` — копия формы 23, slug `print_roll` (форма CalcPrintWide)
- `todo/form-laser.md` — копия формы 28, slug `laser`
- `todo/cut-plotter-sheet-layout.md` — предпосылка `form-sticker`: раскладка листа в `cut_plotter.py`, снятие `ceil` цены `sticker` и обновление эталонов `50×50 VHI80` / `poly_sticker`
- `todo/form-sticker.md` — копия формы 22, slug `sticker`

## Порядок

1. ~~Довести копию кружки до принятия~~ — `form-mug` закрыта 07.11.2026.
2. `todo/forms-batch-switch.md` — пачка 1 (69 + 26 + 41). Параллельно копии пачки 2 (embossing … flag): «Файлы» `forms/<slug>.js` не пересекаются; общий `todo/forms-batch-switch.md` дописывает строку только после принятия копии и не во время выкатки пачки 1.
3. `todo/form-button-pins.md` — можно параллельно пачке 2.
4. Копия 46 принята (`form-presswall` закрыта 09.11.2026) — Analyst заводит задачу `presswall-banner-mode`: баннер и чехол в `presswall` получают режим формы вместо режима 1 из JS (`calcPresswall.js:50`, решение человека 08.11.2026). Меняет цену на сайте — до или вместе с переключением формы 46 на бой.
5. Пачка 3: ~~`form-print-sheet` (6) закрыта 14.11.2026~~; параллельно `form-print-offset` (82), `form-print-roll` (23), `form-laser` (28), `form-sticker` (22). Форма 19 после копии 6 — `print-sheet-copy-result` / отдельная задача; 83 и 29 — после первой копии своего slug.
6. Копия 6 принята выборочно — Analyst может заводить файлы следующей пачки. Переключение — новая задача `forms-batch-N`, не расширение пачки 1 без решения человека.

## Пачки

Боевая на API: **79 puzzle**. Копии приняты: **69 plaque, 26 uv_print, 41 mug, 85 embossing, 78 acrylic_prizes, 46 presswall, 49 rollup, 73 pennant, 55 flag, 6 print_sheet**.

| Пачка | Формы (id, slug) | Заметка |
| --- | --- | --- |
| 1 бой | 69 `plaque`, 26 `uv_print`, 41 `mug` | `forms-batch-switch` |
| 2 копии | 85 `embossing`, 78 `acrylic_prizes`, 49 `rollup`, 46 `presswall`, 73 `pennant`, 55 `flag` | копии приняты 07–12.11.2026 |
| 3 копии | 6 и 19 `print_sheet`, 82 и 83 `print_offset`, 23 `print_roll`, 28 `laser`, 22 и 29 `sticker` | файлы: 6, 82, 23, 28, 22. Формы 19, 83, 29 — после первой копии slug |
| 4 копии | 30 `poly_sticker`, 70 `poly_sticker_pack`, 35 `milling`, 38 `pad_print`, 40 `heat_press`, 45 `notebook`, 80 `canvas` | 7 |
| 5 копии | 31 60 61 64 84 `badge`, 34 `metal_pins`, 12 `button_pins` | 12 после обёртки |
| 6 копии | 36 48 51 76 `tablets`, 68 `shild`, 50 52 66 `calendar` | 8 |
| 7 копии | 54 57 `magnet_laminated`, 56 `cards`, 74 `keychain`, 75 `magnet_acrylic` | 5 |

C1–C11 из `BACKLOG.md` — новых форм в реестре нет, в эти пачки не входят.
