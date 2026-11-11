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
- `todo/form-flag.md` — копия 55
- `todo/forms-batch-switch.md` — пачка 1 на боевые: 69, 26, 41
- `todo/form-button-pins.md` — калькулятор `button_pins` + копия формы 12

## Порядок

1. ~~Довести копию кружки до принятия~~ — `form-mug` закрыта 07.11.2026.
2. `todo/forms-batch-switch.md` — пачка 1 (69 + 26 + 41). Параллельно копии пачки 2 (embossing … flag): «Файлы» `forms/<slug>.js` не пересекаются; общий `todo/forms-batch-switch.md` дописывает строку только после принятия копии и не во время выкатки пачки 1.3. `todo/form-button-pins.md` — можно параллельно пачке 2.
4. Копия 46 принята (`form-presswall` закрыта 09.11.2026) — Analyst заводит задачу `presswall-banner-mode`: баннер и чехол в `presswall` получают режим формы вместо режима 1 из JS (`calcPresswall.js:50`, решение человека 08.11.2026). Меняет цену на сайте — до или вместе с переключением формы 46 на бой.
5. Дальше Analyst заводит файлы следующей пачки копий, когда предыдущая копия принята хотя бы выборочно. Переключение — новая задача `forms-batch-N`, не расширение пачки 1 без решения человека.

## Пачки (ещё без файлов)

Боевая на API: **79 puzzle**. Копии приняты / в ревью: **69 plaque, 26 uv_print, 41 mug, 85 embossing, 78 acrylic_prizes, 46 presswall, 49 rollup**.

| Пачка | Формы (id, slug) | Заметка |
| --- | --- | --- |
| 1 бой | 69 `plaque`, 26 `uv_print`, 41 `mug` | `forms-batch-switch` |
| 2 копии | 85 `embossing`, 78 `acrylic_prizes`, 49 `rollup`, 46 `presswall`, 73 `pennant`, 55 `flag` | embossing, acrylic_prizes, presswall и rollup приняты |
| 3 копии | 6 и 19 `print_sheet`, 82 и 83 `print_offset`, 23 `print_roll`, 28 `laser`, 22 и 29 `sticker` | 8 форм, 5 slug |
| 4 копии | 30 `poly_sticker`, 70 `poly_sticker_pack`, 35 `milling`, 38 `pad_print`, 40 `heat_press`, 45 `notebook`, 80 `canvas` | 7 |
| 5 копии | 31 60 61 64 84 `badge`, 34 `metal_pins`, 12 `button_pins` | 12 после обёртки |
| 6 копии | 36 48 51 76 `tablets`, 68 `shild`, 50 52 66 `calendar` | 8 |
| 7 копии | 54 57 `magnet_laminated`, 56 `cards`, 74 `keychain`, 75 `magnet_acrylic` | 5 |

C1–C11 из `BACKLOG.md` — новых форм в реестре нет, в эти пачки не входят.
