# EPIC-forms-to-api

Статус: в работе
Цель: G1

## Цель

К 30.11.2026 все 45 боевых форм-калькуляторов на https://insain.ru считают через `insaincalc.calcApi`. Переключение пачками по 5–10 форм, копии принимаются выборочно. Форма 10 `_ExternalTest` и не-калькуляторы 71/72/77 в G1 не входят.

Сверка 07.11.2026: публичный slug в `calc_service/calculators/__init__.py` есть у **44 из 45** боевых форм. Нет slug у формы **12** (`calcButtonPins`: логика в `calc_button_pins`, в реестр API не входит) — сначала обёртка-калькулятор. На 15.11.2026 обёртки всё ещё нет.

## Задачи в файлах

Открытые:

- `todo/forms-batch-switch.md` — боевой пакет, 12 принятых копий (список в «Пачки»)
- `todo/presswall-banner-mode.md` — баннер и чехол `presswall` в режиме формы; до переключения формы 46
- `todo/form-button-pins.md` — калькулятор `button_pins` + копия формы 12
- `todo/print-sheet-copy-result.md` — на копии 96 показать за шт со скидкой (`htmCost`)
- `todo/form-print-offset.md` — копия формы 82, slug `print_offset` (`calcPrintOffsetPromo`)
- `form-print-roll` (закрыто 2026-11-16, `docs/history/log.md`) — копия формы 23, slug `print_roll` (форма CalcPrintWide)

Закрытые (файла в `todo/` нет, запись в `docs/history/log.md`):

- `form-mug` (закрыто 2026-11-07) — копия 41 (88 / 2586882)
- `form-embossing` (закрыто 2026-11-07) — копия 85
- `form-acrylic-prizes` (закрыто 2026-11-08) — копия 78
- `form-rollup` (закрыто 2026-11-09) — копия 49 (93 / 2586886)
- `presswall-banner-options` (закрыто 2026-11-09) — крепление, люверсы, режим баннера и чехол в API
- `form-presswall` (закрыто 2026-11-09) — копия 46
- `form-pennant` (закрыто 2026-11-11) — копия 73
- `flag-materials-size-mm` (закрыто 2026-11-12) — `size_mm` в ответе `flag`
- `form-flag` (закрыто 2026-11-12) — копия 55 (95 / 2586888)
- `print-sheet-port-fix` (закрыто 2026-11-13) — ceil времени печати и `timePrepare * mode` в `print_sheet`
- `print-sheet-margins-minus-one` (закрыто 2026-11-13) — при `margins == -1` не прибавлять поля принтера
- `form-print-sheet` (закрыто 2026-11-14) — копия формы 6, slug `print_sheet`
- `cut-plotter-sheet-layout` (закрыто 2026-11-14) — раскладка листа в `cut_plotter.py` для `form-sticker`
- `sticker-print-wide` (закрыто 2026-11-14) — порт широкой печати и ламинации в `sticker.py`
- `form-sticker` (закрыто 2026-11-15) — копия формы 22, slug `sticker`
- `form-laser` (закрыто 2026-11-15) — копия формы 28, slug `laser`

## Порядок

1. `todo/presswall-banner-mode.md` — параллельно пакету: правит только `presswall.py` и его тест. Форму 46 на бой не переключать, пока новый `price` не на боевом API.
2. `todo/forms-batch-switch.md` — одно подтверждение на 12 форм ниже. Форма 46 в очереди последней и только после пункта 1.
3. Параллельно пакету, файлы не пересекаются: `todo/form-button-pins.md`, `todo/form-print-offset.md`, `form-print-roll` (закрыто 2026-11-16, `docs/history/log.md`), `todo/print-sheet-copy-result.md` (только `htmCost` копии 96).
4. После принятия копии своего slug — отдельные задачи, не строки этого пакета: форма 19 (`print_sheet`), 83 (`print_offset`), 29 (`sticker`).
5. Пачки 4–7 — новые файлы задач. Их бой — новая `forms-batch-N`. Состав текущего пакета не расширять.

## Пачки

Боевая на API: **79 puzzle**. Копии приняты и входят в текущий боевой пакет: **69 plaque, 26 uv_print, 41 mug, 85 embossing, 78 acrylic_prizes, 46 presswall, 49 rollup, 73 pennant, 55 flag, 6 print_sheet, 22 sticker, 28 laser**.

| Пачка | Формы (id, slug) | Заметка |
| --- | --- | --- |
| 1 бой | 69 `plaque`, 26 `uv_print`, 41 `mug`, 85 `embossing`, 78 `acrylic_prizes`, 49 `rollup`, 73 `pennant`, 55 `flag`, 6 `print_sheet`, 22 `sticker`, 28 `laser`, 46 `presswall` | `forms-batch-switch`, 12 форм. 46 — после `presswall-banner-mode` на проде |
| 3 остаток | 82 и 83 `print_offset`, 23 `print_roll`, 19 `print_sheet`, 29 `sticker` | открыты копии 82 и 23. 19, 83, 29 — после первой копии slug; в пакет 1 не входят |
| 4 копии | 30 `poly_sticker`, 70 `poly_sticker_pack`, 35 `milling`, 38 `pad_print`, 40 `heat_press`, 45 `notebook`, 80 `canvas` | 7, файлов задач ещё нет |
| 5 копии | 31 60 61 64 84 `badge`, 34 `metal_pins`, 12 `button_pins` | 12 после обёртки (`form-button-pins`) |
| 6 копии | 36 48 51 76 `tablets`, 68 `shild`, 50 52 66 `calendar` | 8 |
| 7 копии | 54 57 `magnet_laminated`, 56 `cards`, 74 `keychain`, 75 `magnet_acrylic` | 5 |

C1–C11 из `BACKLOG.md` — новых форм в реестре нет, в эти пачки не входят.
