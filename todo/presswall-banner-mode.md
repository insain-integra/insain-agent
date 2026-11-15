# presswall-banner-mode

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: Grok 4.7
Почему: решение человека 08.11.2026 меняет цену `presswall` на проде относительно JS (`calcPresswall.js:50`); выкатка API — по skill `deploy-api`.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

Печать баннера и чехол в `presswall` считаются в режиме формы (`mode` 0, 1 или 2), а не в режиме 1, который JS записывает в `modeProduction` на строке 50 `js_legacy/calc/calcPresswall.js`. Каркас по-прежнему в режиме формы. Боевая форма 46 остаётся на старом JS, пока её не возьмёт пакет переключения — и только после этой выкатки.

## Контекст и ссылки

- `todo/EPIC-forms-to-api.md` — форма 46 в боевом пакете; переключать её после выкатки этой задачи.
- `calc_service/calculators/presswall.py` — сейчас `banner_bag_mode = 1`, если задан `material_id` (комментарий на строку 50 JS).
- `js_legacy/calc/calcPresswall.js:50` — `modeProduction = 1` внутри вызова `calcPrintRoll`; из-за присваивания чехол ниже тоже получает режим 1, если баннер печатается.
- `calc_service/tests/test_calculators/test_presswall.py` — `EXPECTED_EYELET_MODE2` (`price` 14040.704) фиксирует старое поведение «баннер на mode 1».
- `presswall-banner-options` (закрыто 2026-11-09, `docs/history/log.md`) — крепление и люверсы уже в API; режим не менять повторно.
- Остальное не открывать.

## Scope

- В git (Implementer): в `presswall.py` печать баннера (`PrintRollCalculator`) и чехол (`calc_sewing_covers`) получают `mode` запроса. Без баннера чехол по-прежнему в режиме формы. Каркас (`calc_cut_profile`) не трогать. Docstring модуля описывает расхождение с JS как решение 08.11.2026, не как порт.
- Эталон mode 1 с баннером не менять (`price` 13914.624 у люверсов). Эталон mode 2 с баннером переснять: баннер и чехол в mode 2, не 14040.704. В тесте пометка, что число нарочно не совпадает с JS.
- На проде (Site ops): после слияния в `main` и зелёного CI — выкатка API по `.cursor/skills/deploy-api/SKILL.md`. Боевую форму 46 и копию 92 не править.

## Файлы

- `calc_service/calculators/presswall.py`
- `calc_service/tests/test_calculators/test_presswall.py`

## Не-scope

- `wp-plugin/forms/presswall.js`, боевая форма 46, копия 92, `todo/forms-batch-switch.md`
- Цены в JSON, `marginPresswall`, состав прессвола
- `scripts/js_port_gaps_allowed.txt` — вызов `calcPrintRoll` остаётся, меняется только режим

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests/test_calculators/test_presswall.py -q` — `passed`, `failed` нет. Тест mode 2 с баннером падает, если баннер снова считается в mode 1.
- [ ] Mode 1, люверсы, баннер: `price` 13914.624, как `EXPECTED_EYELET_MODE1` (совпадает с JS).
- [ ] Mode 2, тот же баннер: `price` не 14040.704. В «Результат» — новый `price` и `time_ready` для mode 0 и mode 2 с баннером (и с чехлом `bag160`, если чехол в тесте).
- [ ] `Select-String -Path calc_service\calculators\presswall.py -Pattern "banner_bag_mode = 1"` — совпадений нет.
- [ ] После выкатки: `POST https://insain.ru/api/v1/calc/presswall` с тем же телом, что эталон mode 2, — `price` равен новому эталону из теста, не 14040.704.

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: выкатка меняет цену API для mode 0 и 2, когда задан баннер. Боевая страница формы 46 на JS и до переключения пакета эту цену не показывает. Копия 92 считает через API — ускоренный и экономный режим с баннером на ней изменятся.
- Цены: JSON не менять. Расхождение с JS по режиму баннера и чехла — намеренное, не повод для `port-fix-prerequisite`.
- Формы: форму 46 в `forms-batch-switch` не переключать, пока этот `price` не на боевом API.

## Режим

прод

## Журнал передач

- 15.11.2026 — Analyst, Grok 4.7 — задача заведена, режим баннера и чехла = режим формы — дальше Implementer

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
