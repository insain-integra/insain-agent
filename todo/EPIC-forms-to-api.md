# EPIC-forms-to-api

Статус: в работе
Цель: G1

## Цель

К 30.11.2026 все 45 боевых форм-калькуляторов на https://insain.ru считают через `insaincalc.calcApi`. Переключение пачками по 5–10 форм, копии принимаются выборочно. Форма 10 `_ExternalTest` и не-калькуляторы 71/72/77 в G1 не входят.

Решение человека 22.11.2026: боевое переключение форм ezFC на `insaincalc.calcApi` отложено, пока все 45 форм эпика не получат калькулятор в `calc_service` и принятую копию. `todo/forms-batch-switch.md` не запускать и не расширять, `forms-batch-2` не заводить. Сверка 22.11.2026: все slug эпика зарегистрированы в API; боевая на API — форма 79 `puzzle`; копии приняты у 25 форм — пакет 1 (14), 12, 45, 35, хвост slug 19, 83, 29 и пачка 4 (30, 70, 38, 40, 80), их задачи закрыты. Без копии 19 форм пачек 5–7, их ведут лид-задачи по одной на slug; вторые формы slug — после приёмки лида. Форма 68 вызывает `calcTablets` и идёт через slug `tablets`, не `shild`. Реестр `docs/site/forms.md` снят 25.10.2026 и ещё показывает старый JS — его обновит боевое переключение, не копии.

## Задачи в файлах

Открытые:

- `todo/forms-batch-switch.md` — боевой пакет, 14 принятых копий (список в «Пачки»); отложен решением 22.11.2026, не запускать и не расширять
- `todo/presswall-banner-mode.md` — баннер и чехол `presswall` в режиме формы; правит калькулятор, форму 46 не переключает
- `form-metal-pins` (закрыто 2026-11-23, `docs/history/log.md`) — копия формы 34, slug `metal_pins`
- `form-plastic-cards` (закрыто 2026-11-24, `docs/history/log.md`) — копия формы 56, slug `cards`
- `form-keychain` (закрыто 2026-11-23, `docs/history/log.md`) — копия формы 74, slug `keychain`
- `todo/form-magnet-acrylic.md` — копия формы 75, slug `magnet_acrylic`
- `todo/form-magnet-laminated.md` — лид-копия 54, slug `magnet_laminated`; ждёт `form-magnet-acrylic` (общий `magnets.py`), форма 57 позже
- `form-calendar` (закрыто 2026-11-23, `docs/history/log.md`) — лид-копия 50 (квартальный), slug `calendar`; формы 52 и 66 позже
- `form-badge` (закрыто 2026-11-24, `docs/history/log.md`) — доработка: опция «УФ-печать» расходится с JS. Копия 114 / товар 2586910 уже есть, slug `badge`
- `todo/form-tablets.md` — сверка дефолтов 36, 48, 51, 76, 68 и лид-копия 36, slug `tablets`

Закрытые (файла в `todo/` нет, запись в `docs/history/log.md`):

- `milling-cut-floor`, `form-poly-sticker-pack`, `form-milling`, `form-pad-print`, `form-vizitki-promo` (закрыто 2026-11-22) — пачка 4 и хвост slug: копии 70, 35 (111 / 2586907), 38 (110 / 2586906), 83
- `print-sheet-copy-result`, `print-sheet-big-sheet`, `form-vizitki`, `form-sticker-pack`, `form-poly-sticker`, `form-heat-press` (закрыто 2026-11-21) — блок результата копии 96, лист больше принтера, копии 19, 29, 30, 40
- `form-canvas` (закрыто 2026-11-20) — копия формы 80, slug `canvas`
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

Параллельная группа — задачи, у которых строки «Файлы» не пересекаются. Общие файлы (`docs/site/forms.md`, `todo/forms-batch-switch.md`, `docs/js-runner-cases.md`, `scripts/run_js_calc.mjs`) в ветках копий не править; дописка — в «Результат» задачи. `scripts/js_port_gaps_allowed.txt` каждая задача правит только снятием строк своего префикса.

1. `todo/presswall-banner-mode.md` — в любой момент: только `presswall.py` и его тест. Это не переключение формы 46, задача не отменяется.
2. Параллельно, лид-копии пачек 5–7:
   - `form-plastic-cards` (закрыто 2026-11-24, `docs/history/log.md`), `form-keychain` (закрыто 2026-11-23, `docs/history/log.md`), `todo/form-magnet-acrylic.md`, `form-calendar` (закрыто 2026-11-23, `docs/history/log.md`)
   - `form-badge` (закрыто 2026-11-24, `docs/history/log.md`) (доработка: УФ-печать), `todo/form-tablets.md` — сначала сверка дефолтов всех форм slug, потом лид
   - `todo/form-magnet-laminated.md` — после `form-magnet-acrylic`: общий `magnets.py`
   Запись на проде (дубли форм) — последовательно под `lock prod`.
3. Вторые формы slug — по одной задаче после приёмки лида: `badge` (4 формы), `tablets` (48, 51, 76, 68), `calendar` (52, 66), `magnet_laminated` (57). Файлы заранее не создавать.
4. Боевое переключение отложено, пока у всех 45 форм эпика нет принятой копии: `todo/forms-batch-switch.md` не запускать и не расширять, `forms-batch-2` не заводить. Как переключать оставшиеся формы (одним пакетом или несколькими) — решение человека после пункта 3.

## Пачки

Боевая на API: **79 puzzle**. Копии приняты (25), боевые формы на старом JS: пакет 1 — **69 plaque, 26 uv_print, 41 mug, 85 embossing, 78 acrylic_prizes, 46 presswall, 49 rollup, 73 pennant, 55 flag, 6 print_sheet, 22 sticker, 28 laser, 23 print_roll, 82 print_offset**; вне пакета 1 — **12 button_pins** (101 / 2586896), **45 notebook** (102 / 2586897), **35 milling** (111 / 2586907), **38 pad_print** (110 / 2586906), **19, 83, 29, 30, 70, 40, 80**.

| Пачка | Формы (id, slug) | Статус 22.11.2026 |
| --- | --- | --- |
| 1 бой | 69 `plaque`, 26 `uv_print`, 41 `mug`, 85 `embossing`, 78 `acrylic_prizes`, 49 `rollup`, 73 `pennant`, 55 `flag`, 6 `print_sheet`, 22 `sticker`, 28 `laser`, 46 `presswall`, 23 `print_roll`, 82 `print_offset` | 14 копий приняты, живые формы на старом JS. `forms-batch-switch` отложен решением 22.11.2026 |
| Хвост slug | 19 `print_sheet`, 83 `print_offset`, 29 `sticker` | закрыто: копии приняты (`form-vizitki`, `form-vizitki-promo`, `form-sticker-pack`) |
| 4 копии | 30 `poly_sticker`, 70 `poly_sticker_pack`, 45 `notebook`, 35 `milling`, 38 `pad_print`, 40 `heat_press`, 80 `canvas` | закрыто: все 7 копий приняты |
| 5 копии | 31 60 61 64 84 `badge`, 34 `metal_pins`, 12 `button_pins` | копия 12 принята. `form-badge` (лид после сверки, кандидат 64), `form-metal-pins` |
| 6 копии | 36 48 51 76 68 `tablets`, 50 52 66 `calendar` | `form-tablets` (лид 36; 68 через `tablets`, не `shild`), `form-calendar` (лид 50) |
| 7 копии | 54 57 `magnet_laminated`, 56 `cards`, 74 `keychain`, 75 `magnet_acrylic` | `form-magnet-laminated` (лид 54, ждёт `form-magnet-acrylic`), `form-plastic-cards`, `form-keychain`, `form-magnet-acrylic` |

C1–C11 из `BACKLOG.md` — новых форм в реестре нет, в эти пачки не входят.
