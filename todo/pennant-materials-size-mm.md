# pennant-materials-size-mm

Статус: закрытие
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: в ответе `pennant` нет `size_mm` у материалов (бумага отбрасывается, плёнка и шнур не ставятся в общих `lamination` / `calc_set_rope`); держит приёмку копии `form-pennant`; после merge — деплой API по skill.
Чат: человек открывает новый чат с моделью из поля Implementer.

## Цель

На дефолте формы 73 (100 шт., 148×210, `PaperCoated170M`, `4+0`, `Laminat32G`, mode 1) ответ `POST /api/v1/calc/pennant` содержит `size_mm` у трёх строк `materials` как на боевой таблице: плёнка `[330, 0]`, бумага `[320, 450]`, шнур `[4, 350]`. Цена и срок на этом входе и у соседних вызовов `lamination` / `calc_set_rope` не сдвигаются. После выкатки API то же на боевом `https://insain.ru/api/v1/calc/pennant`.

## Контекст и ссылки

- Держит `todo/form-pennant.md` (копия 94 / товар 2586887). Блокер Implementer 2026-11-11 в журнале form-pennant: колонка «Размер» пустая.
- Причина: `pennant.py` при сборке `materials_out` копирует `code`/`name`/`title`/`quantity`/`unit` и отбрасывает `size_mm` бумаги из `print_sheet`; `lamination.py` и `calc_set_rope` (`process_tools.py`) `size_mm` не ставят. В каталоге: `Laminat` Default `[330, 0]`, бумага листа `[320, 450]`, `RopeForPack` `[4, 350]`.
- Эталон UI: боевая форма 73, `showMaterials` — плёнка `330,0`; бумага `320,450`; шнур `4,350`.
- Контракт `materials` / `size_mm` — `calc_service/calculators/base.py` (`material_line`), `docs/data-formats.md`.
- Выкатка — `.cursor/skills/deploy-api/SKILL.md`.
- Остальное не открывать.

## Scope

- В git (Implementer): прокинуть `size_mm` в ответ `pennant` (бумага из `print_sheet` не отбрасывать); в `lamination.py` и `calc_set_rope` класть `size_mm` из каталога материала; тест на дефолте формы 73 падает без правки; эталоны цены `lamination` и вызовов через `calc_set_rope` не переснимать — должны остаться зелёными.
- На проде (Site ops): после ревью, слияния в `main` и зелёного CI — `bash infra/deploy.sh` (skill `deploy-api`); smoke `size_mm` на теле дефолта формы 73.

## Файлы

- `calc_service/calculators/pennant.py`
- `calc_service/calculators/lamination.py`
- `calc_service/common/process_tools.py` — только `calc_set_rope`
- `calc_service/tests/test_calculators/test_pennant.py` — assert `size_mm` (и связанные) на дефолте формы
- `calc_service/tests/test_calculators/test_lamination.py` — только если без правки падает контракт `materials`; эталоны `price` не переснимать
- `calc_service/tests/test_process_tools.py` — только если нужен кейс `size_mm` / цена `calc_set_rope` без сдвига

## Не-scope

- `wp-plugin/forms/pennant.js`, bridge, дубль формы 73 / копия 94, `todo/form-pennant.md` кроме снятия «ждёт» через `close`.
- Правка цен, наценок, `calc_service/data/` (размеры уже в каталоге).
- Выравнивание веса с JS, правка `print_sheet.py` ради размера бумаги (размер листа там уже есть).
- Другие process_tools и калькуляторы, кроме прохода `size_mm` через общие `lamination` / `calc_set_rope`.
- Выкладка плагина и переключение боевой формы 73.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. В PowerShell 5.1 кавычки JSON внутри аргумента экранируются `\"`. Скрипт через `@'…'@ | python -` — первой строкой `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`.

- [x] Локальный `pennant` на дефолте формы 73: у материалов `size_mm` плёнка `[330, 0]`, бумага `[320, 450]`, шнур `[4, 350]` (порядок строк как в ответе; сравнение чисел с `rel=0` / точным равенством float). `price` тот же, что до правки на этом теле (`5976.340906666667`, rel ≤ 0.001 к эталону формы). Stdout: `ok`.

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
@'
from calculators.pennant import PennantCalculator
r = PennantCalculator().execute({
    "quantity": 100, "width_mm": 148, "height_mm": 210,
    "material_id": "PaperCoated170M", "color": "4+0",
    "lamination_id": "Laminat32G", "mode": 1,
})
mats = r["materials"]
assert len(mats) >= 3, mats
by_code = {m["code"]: m for m in mats}
assert by_code["Laminat32G"]["size_mm"] == [330.0, 0.0], by_code["Laminat32G"]
assert by_code["PaperCoated170M"]["size_mm"] == [320.0, 450.0], by_code["PaperCoated170M"]
assert by_code["RopeForPack"]["size_mm"] == [4.0, 350.0], by_code["RopeForPack"]
assert abs(r["price"] - 5976.340906666667) / 5976.340906666667 <= 0.001, r["price"]
print("ok", [(m["code"], m.get("size_mm")) for m in mats], r["price"])
'@ | python -
```

- [x] Тест падает без правки. Новый assert `size_mm` в `test_pennant.py` (пометка даты рядом). Откат только трёх файлов калькулятора → кейс `size_mm` `failed`; эталоны цены `test_lamination.py` где возможно `passed`. После возврата — снова `passed`.

```powershell
git stash push -- calc_service/calculators/pennant.py calc_service/calculators/lamination.py calc_service/common/process_tools.py
python -m pytest calc_service/tests/test_calculators/test_pennant.py calc_service/tests/test_calculators/test_lamination.py -q
git stash pop
```

- [x] Соседи по цене. `lamination` и `calc_set_rope` общие: эталоны цены в `test_lamination.py` зелёные без пересъёма; `price` прямого `calc_set_rope` и/или существующих кейсов в `test_process_tools.py` не сдвинулся. Упал эталон цены соседа — стоп, `заблокировано: аналитик`, не переснимать в этой задаче.

```powershell
python -m pytest calc_service/tests/test_calculators/test_lamination.py calc_service/tests/test_process_tools.py calc_service/tests/test_calculators/test_pennant.py -q
```

- [x] Боевой API после деплоя. На теле дефолта формы 73 те же `size_mm` и `price` с rel ≤ 0.001 к локальному эталону.

```powershell
Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/pennant -ContentType 'application/json' -Body '{"quantity":100,"width_mm":148,"height_mm":210,"material_id":"PaperCoated170M","color":"4+0","lamination_id":"Laminat32G","mode":1}' | Select-Object price, @{n='sizes';e={$_.materials | ForEach-Object { '{0}:{1}' -f $_.code, ($_.size_mm -join ',') }}}
```

## Проверки

- [x] `python scripts/dev.py check` — код выхода 0.
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md). Diff только scope; JSON цен не менялись; внутренние `code` в UI не светятся (только в assert теста).

## Риски

- Прод: деплой API меняет ответ `materials` у всех расчётов через `lamination` и `calc_set_rope` (вымпелы и др.). Откат — предыдущий образ по skill `deploy-api`.
- Цены: JSON не трогать. Если при добавлении `size_mm` сдвинется `price`/`cost` — стоп и эскалация Analyst.
- Формы: боевые формы не переключать. `form-pennant` ждёт закрытия; перепроверка колонки «Размер» на копии 94 — уже в form-pennant (Site ops), не здесь.

## Режим

прод

## Журнал передач

2026-11-11 — Analyst, Grok 4.7 — заведена предпосылка `size_mm` в ответе `pennant` (бумага / плёнка / шнур); `form-pennant` ждёт; `lamination` и `calc_set_rope` общие — критерий цены соседей — дальше Implementer, Grok 4.7
2026-11-11 — Implementer, Grok 4.7 — `size_mm` в ответе `pennant` на дефолте формы 73: плёнка `[330, 0]`, бумага `[320, 450]`, шнур `[4, 350]`; price `5976.340906666667` не сдвинулся; эталоны цены `lamination` зелёные без пересъёма — дальше Reviewer, Auto
2026-11-11 — Reviewer, Auto — принято по незакоммиченному diff; локальные критерии size_mm/price/соседи зелёные; боевой API — Site ops после слияния — дальше человек: коммит и слияние в main
2026-11-11 — человек — принято — выкатка (коммит и слияние в main; деплой API — Site ops)
2026-11-11 — Site ops, Grok 4.7 — API `6a9e14b` на проде (`297c7fb` → `6a9e14b`); smoke дефолта формы 73: `size_mm` бумага `[320, 450]`, плёнка `[330, 0]`, шнур `[4, 350]`, price `5976.340906666667` (rel 0) — дальше человек: закрытие

## Ревью 1

принято

Проверено по незакоммиченному diff ветки `task/pennant-materials-size-mm` (коммита нет).

- Дефолт формы 73: `ok [('PaperCoated170M', [320.0, 450.0]), ('Laminat32G', [330.0, 0.0]), ('RopeForPack', [4.0, 350.0])] 5976.340906666667`
- Откат трёх файлов калькулятора: `test_form73_materials_size_mm` FAILED (`KeyError: size_mm`); `test_lamination.py` без пересъёма — 12 passed; `git stash pop` вернул правки
- Соседи: `66 passed` (`test_lamination.py`, `test_process_tools.py`, `test_pennant.py`); diff эталонов цены `test_lamination.py` / `test_process_tools.py` / `calc_service/data/` — пустой
- Боевой API — не этот круг (критерий после деплоя, Site ops)

Scope и инварианты: diff только `pennant` / `lamination` / `calc_set_rope` + тест `size_mm` + `docs/dashboard.md` / todo; цены в JSON не трогались; `code` только в assert теста.

## Найдено вне scope

- `todo/print-sheet-weight-port-fix.md` всё ещё в `todo/` со статусом `черновик`, хотя form-pennant считает предпосылку по весу закрытой решением 11.11.2026 (вес Python). Закрытие leftover — человеку, не эта задача.
- В worktree `task/form-pennant` лежит незакоммиченный хвост `calc_service/tests/test_calculators/test_pennant.py` (`test_form_default_laminat`) и черновик этого же `todo/pennant-materials-size-mm.md`. Ветка задачи собрана от `main`, тот черновик не переносился и не удалялся. При слиянии хвост теста может конфликтовать.

## Результат

- Ветка, PR или коммит: `main` `6a9e14b` (код `size_mm` — `4cf89c2`). CI `check` на `6a9e14b` — success. На VDS было `297c7fb`.
- Период: 2026-11-11
- Часы человека:
- Работа агентов: Site ops, Grok 4.7, одна сессия (деплой). До этого Implementer и Reviewer — в журнале.
- Было / стало: прод был на `297c7fb`, в ответе `pennant` не было `size_mm`. Стало: `6a9e14b`, дефолт формы 73 — `PaperCoated170M` `[320, 450]`, `Laminat32G` `[330, 0]`, `RopeForPack` `[4, 350]`, price `5976.340906666667` (rel 0 к эталону).
- Сделано: `bash infra/deploy.sh` на `insain-prod`. Скрипт: fast-forward `297c7fb` → `6a9e14b`, образ `insain-agent-calc-api:rollback` (`d52bfa699d78`), сборка, контейнер `insain-calc-api` healthy на `127.0.0.1:8002`. В этот же pull вошли коммиты `main` после `297c7fb`, включая вес `print_sheet` (`8960a31`).
- Чем проверено: smoke скрипта — `GET /api/v1/calculators` 200, `POST /api/v1/calc/puzzle` 200. Снаружи `curl -fsS https://insain.ru/api/v1/calculators` — 200, в списке есть `pennant`. `POST https://insain.ru/api/v1/calc/pennant` на теле дефолта формы 73: price `5976.340906666667`, rel 0; `size_mm` бумага `320,450`, плёнка `330,0`, шнур `4,350`.
- Не сделано и почему: боевую форму 73 не открывал и не переключал — колонка «Размер» на копии 94 остаётся в `form-pennant`. Плагин не выкладывал.
- Требуется решение: нет. Дальше человек: закрытие. Коммит отчёта в задаче — когда попросит человек.
- Откат: на VDS образ `insain-agent-calc-api:rollback` и коммит `297c7fb`. Повтор скрипта с падающим smoke откатывает сам; вручную — `git reset --hard 297c7fb`, `docker tag insain-agent-calc-api:rollback insain-agent-calc-api:latest`, `docker compose -f docker-compose.calc-only.yml up -d --no-build --force-recreate` в `/opt/insain-agent`. Откат снимет и `size_mm`, и всё, что выехало между `297c7fb` и `6a9e14b`.
