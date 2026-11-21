# EPIC-forms-to-api

Статус: в работе
Цель: G1

## Цель

К 30.11.2026 все 45 боевых форм-калькуляторов на https://insain.ru считают через `insaincalc.calcApi`. Переключение пачками по 5–10 форм, копии принимаются выборочно. Форма 10 `_ExternalTest` и не-калькуляторы 71/72/77 в G1 не входят.

Сверка 19.11.2026: на бою по-прежнему только форма 79 `puzzle`. Реестр `docs/site/forms.md` снят 25.10.2026 и ещё показывает старый JS — его обновит пакет переключения, не копии. Принятые копии в текущий боевой пакет не дописывать, пока идёт `forms-batch-switch`.

## Задачи в файлах

Открытые:

- `todo/forms-batch-switch.md` — боевой пакет, 14 принятых копий (список в «Пачки»)
- `todo/presswall-banner-mode.md` — баннер и чехол `presswall` в режиме формы; до переключения формы 46
- `print-sheet-copy-result` (закрыто 2026-11-21, `docs/history/log.md`) — на копии 96 показать за шт со скидкой (`htmCost`)
- `form-vizitki` (закрыто 2026-11-21, `docs/history/log.md`) — вторая форма slug `print_sheet`, боевая 19; в пакет 1 не входит
- `print-sheet-big-sheet` (закрыто 2026-11-21, `docs/history/log.md`) — лист больше принтера в `print_sheet`: цена Маджестик на API, копия 107 берёт её без записи в ezFC, боевые формы 6 и 19 на старом JS
- `form-vizitki-promo` (закрыто 2026-11-22, `docs/history/log.md`) — вторая форма slug `print_offset`, боевая 83
- `form-sticker-pack` (закрыто 2026-11-21, `docs/history/log.md`) — вторая форма slug `sticker`, боевая 29
- `form-poly-sticker` (закрыто 2026-11-21, `docs/history/log.md`) — копия формы 30, slug `poly_sticker`
- `todo/form-poly-sticker-pack.md` — копия формы 70, slug `poly_sticker_pack`
- `todo/form-milling.md` — копия формы 35, slug `milling`
- `form-pad-print` (закрыто 2026-11-22, `docs/history/log.md`) — копия формы 38, slug `pad_print`
- `form-heat-press` (закрыто 2026-11-21, `docs/history/log.md`) — копия формы 40, slug `heat_press`
- `form-canvas` (закрыто 2026-11-20, `docs/history/log.md`) — копия формы 80, slug `canvas`

Закрытые (файла в `todo/` нет, запись в `docs/history/log.md`):

- `form-notebook` (закрыто 2026-11-19) — копия формы 45 (102 / 2586897), slug `notebook`; боевая 45 ждёт следующий пакет, не этот
- `form-button-pins` (закрыто 2026-11-17) — калькулятор `button_pins` на проде, копия 101 / 2586896; боевая 12 ждёт следующий пакет, не этот
- `form-print-offset` (закрыто 2026-11-17) — копия формы 82, slug `print_offset`
- `print-offset-promo` (закрыто 2026-11-16) — порт `calcPrintOffsetPromo` в slug `print_offset`
- `form-print-roll` (закрыто 2026-11-16) — копия формы 23, slug `print_roll`
- `form-laser` (закрыто 2026-11-15) — копия формы 28, slug `laser`
- `form-sticker` (закрыто 2026-11-15) — копия формы 22, slug `sticker`
- `sticker-print-wide`, `cut-plotter-sheet-layout` (закрыто 2026-11-14) — предпосылки `form-sticker`
- `form-print-sheet` (закрыто 2026-11-14) — копия формы 6, slug `print_sheet`
- `print-sheet-port-fix`, `print-sheet-margins-minus-one` (закрыто 2026-11-13)
- `form-flag` (закрыто 2026-11-12) — копия 55; `flag-materials-size-mm` закрыт в тот же день
- `form-pennant` (закрыто 2026-11-11) — копия 73
- `form-presswall`, `form-rollup`, `presswall-banner-options` (закрыто 2026-11-09)
- `form-acrylic-prizes` (закрыто 2026-11-08) — копия 78
- `form-mug`, `form-embossing` (закрыто 2026-11-07)

## Порядок

1. `todo/presswall-banner-mode.md` — параллельно пакету: только `presswall.py` и его тест. Форму 46 на бой не переключать, пока новый `price` не на боевом API.
2. `todo/forms-batch-switch.md` — 14 форм из строки «Пакет 1». Форма 46 последней и только после пункта 1. Состав не расширять: формы 12, 19, 83, 29 и пачка 4 в этот файл не дописывать.
3. Параллельно пакету, файлы не пересекаются: хвост уже принятых slug (`form-vizitki`, `form-vizitki-promo`, `form-sticker-pack`) и пачка 4. Общие файлы (`docs/site/forms.md`, `todo/forms-batch-switch.md`, `docs/js-runner-cases.md`) в этих ветках не править. JS первой формы slug не ломать: id и `REF_FORM_DEFAULT` формы 6, 82 и 22 остаются.
4. `print-sheet-copy-result` (закрыто 2026-11-21, `docs/history/log.md`) — только блок результата копии 96. Форму 19 и `print_sheet.js` не трогает.
5. Следующий боевой пакет (`forms-batch-2`) заводить после закрытия `forms-batch-switch`: оба правят `docs/site/forms.md`. Туда входят уже готовая копия 12 и те копии пунктов 3, которые человек принял. Файл заранее не создавать.
6. Пачки 5–7 — задачи не заведены. У `badge`, `tablets`, `shild`, `calendar` (ламинация перекидного), `magnet_laminated` в `scripts/js_port_gaps_allowed.txt` длинные пропуски; форма 68 в реестре вызывает `calcTablets`, в эпике указан slug `shild`. Ставить лид-форму slug после сверки порта, не пачкой заранее. `metal_pins`, `cards`, `keychain`, `magnet_acrylic` ближе к готовым — их задачи писать следующей волной, не сейчас.

## Пачки

Боевая на API: **79 puzzle**. Копии приняты и входят в текущий боевой пакет (14): **69 plaque, 26 uv_print, 41 mug, 85 embossing, 78 acrylic_prizes, 46 presswall, 49 rollup, 73 pennant, 55 flag, 6 print_sheet, 22 sticker, 28 laser, 23 print_roll, 82 print_offset**. Копия готова, в пакет 1 не входит: **12 button_pins** (101 / 2586896), **45 notebook** (102 / 2586897).

| Пачка | Формы (id, slug) | Статус 19.11.2026 |
| --- | --- | --- |
| 1 бой | 69 `plaque`, 26 `uv_print`, 41 `mug`, 85 `embossing`, 78 `acrylic_prizes`, 49 `rollup`, 73 `pennant`, 55 `flag`, 6 `print_sheet`, 22 `sticker`, 28 `laser`, 46 `presswall`, 23 `print_roll`, 82 `print_offset` | 14 копий приняты, живые формы на старом JS. `forms-batch-switch`. 46 — после `presswall-banner-mode` на проде |
| Хвост slug | 19 `print_sheet`, 83 `print_offset`, 29 `sticker` | задачи `form-vizitki`, `form-vizitki-promo`, `form-sticker-pack`. В пакет 1 не входят |
| 4 копии | 30 `poly_sticker`, 70 `poly_sticker_pack`, 45 `notebook`, 35 `milling`, 38 `pad_print`, 40 `heat_press`, 80 `canvas` | задачи заведены. У milling, pad_print, heat_press, canvas есть пропуски порта — чинить в той же задаче, если дефолт формы в них упирается |
| 5 копии | 31 60 61 64 84 `badge`, 34 `metal_pins`, 12 `button_pins` | копия 12 готова, бой не в пакете 1. Задач на badge и metal_pins нет |
| 6 копии | 36 48 51 76 `tablets`, 68 `shild`, 50 52 66 `calendar` | задач нет. Форма 68 в реестре — `calcTablets` |
| 7 копии | 54 57 `magnet_laminated`, 56 `cards`, 74 `keychain`, 75 `magnet_acrylic` | задач нет |

C1–C11 из `BACKLOG.md` — новых форм в реестре нет, в эти пачки не входят.
