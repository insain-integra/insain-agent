# js-port-gaps

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: текст станет правилом для агентов (`calc_service/AGENTS.md`, skills) и новой проверкой в `make check`.

## Цель

Полнота порта старого JS проверяется скриптом, а не по памяти. `scripts/js_port_gaps.py` для каждой JS-функции `calcX` печатает её опции и вызовы и то, чего нет в Python-модуле. Известные пропуски перечислены в файле, который только уменьшается; новый пропуск или устранённый, но не вычеркнутый, роняет `make check`. Эпик `todo/EPIC-calc-port-structure.md`, пункт 5.7 плана, шаг 1.

## Контекст и ссылки

- `todo/EPIC-calc-port-structure.md` — порядок задач эпика.
- `js_legacy/calc/*.js` — функции `insaincalc.calcX = function calcX(…)`. Опции — `options.has('…')` и `options.get('…')`, вызовы — `insaincalc.calc…(`. Пример: в `calcTablets` 15 опций `options.has`, в `calc_service/calculators/tablets.py` из них 4.
- `docs/data-formats.md`, раздел «Калькуляторы» — соответствие JS-файл → Python-модуль. Вспомогательные функции (`calcLayoutOnSheet`, `calcCutSaber` и т.п.) лежат в `calc_service/common/`.
- `Makefile`, цель `check`, и `scripts/dev.py check` — запускают `pytest calc_service/tests`. Тест в `calc_service/tests/` попадает в `make check` и в CI без правки `Makefile`. Node в CI нет: скрипт на Python, JS разбирается как текст.
- `.cursor/skills/ezfc-form-to-api/SKILL.md` (раздел «Сверка до перевода») и `.cursor/skills/new-calculator/SKILL.md` (раздел «Подготовка») — сюда шаг 0.
- `calc_service/AGENTS.md` — сюда четыре строки правил.
- Остальное не открывать.

## Scope

1. `scripts/js_port_gaps.py`, сначала отчёт:
   - `python scripts/js_port_gaps.py <calcX>` — блок по функции и по всей цепочке её вызовов (`calcPlaque` → `calcTablets` → `calcLaser`, `calcUVPrint`, `calcHeatPress` → …). Формат блока: строка `calcX -> <python-модуль или «нет порта»>`, строка `options: …`, строка `calls: …`, строка `нет в Python: …` (пусто, если пропусков нет). Код выхода 0.
   - Опция считается перенесённой, если её имя встречается в Python-модуле как есть или в snake_case (`isCutManualMetal` → `cut_manual_metal` / `is_cut_manual_metal`). Вызов перенесён, если модуль импортирует Python-порт вызываемой функции.
   - Соответствие `calcX` → Python-модуль — один словарь в скрипте. Функция без записи — пропуск `нет порта`.
   - Без аргумента — отчёт по всем функциям `js_legacy/calc/*.js`.
2. Файл допустимых пропусков `scripts/js_port_gaps_allowed.txt`, по строке на пропуск: `calcTablets option isFilm`, `calcTablets call calcSticker`, `calcX module`. Создаётся из текущего отчёта целиком.
3. `python scripts/js_port_gaps.py --check` — сравнивает отчёт с файлом. Новый пропуск не из файла — код 1 и строка `новый пропуск: …`. Строка файла, которой больше нет в отчёте, — код 1 и строка `пропуск устранён, удалите строку: …`. Совпало — `ok`, код 0.
4. Файл только уменьшается: тест `calc_service/tests/test_js_port_gaps.py` хранит константу `MAX_ALLOWED`, равную числу строк файла на момент создания, и падает, если строк больше. Устранили пропуск — строка удаляется, константа уменьшается в том же коммите. Тест прогоняет `--check` на репозитории и два негативных случая на временном файле (лишняя строка, недостающая строка).
5. Шаг 0 в двух skills: запустить `python scripts/js_port_gaps.py <calcX>` для калькулятора и его цепочки вызовов; строка `нет в Python` не пустая и пропуск не записан в «не перенесено» — стоп, порт не полон. Нумерацию остальных шагов не менять.
6. Четыре строки в `calc_service/AGENTS.md`, новый раздел «Порт из JS»:
   - порт — вся JS-функция или явный список «не перенесено» (в docstring модуля и в `scripts/js_port_gaps_allowed.txt`);
   - вызов в JS — вызов порта в Python, не пересчёт его логики на месте;
   - приватные функции (`_имя`) чужого модуля не импортируются;
   - эталоны снимаются на каждом уровне вызова: сначала `calcTablets`, потом `calcPlaque`.

## Не-scope

- Перенос пропущенных опций и вызовов — задачи эпика дальше по порядку.
- Правка калькуляторов, `calc_service/data/`, `js_legacy/`, `scripts/run_js_calc.mjs`.
- Правка `Makefile` и CI, если тест в `calc_service/tests/` уже попадает в `make check`.
- Корневой `AGENTS.md` (лимит 150 строк).

## Критерии приёмки

- [ ] `python scripts/js_port_gaps.py calcPlaque` — код 0; в stdout строки `calcPlaque ->` и `calcTablets ->`; в строке `нет в Python` блока `calcTablets` есть `isSublimation`.
- [ ] `python scripts/js_port_gaps.py --check` — stdout `ok`, код 0.
- [ ] `python -m pytest calc_service/tests/test_js_port_gaps.py -q` — `passed`, не меньше 4 тестов, без `failed`.
- [ ] Ратчет и негативные случаи. Stdout `ok`:

```powershell
@'
import subprocess, sys, tempfile
from pathlib import Path
src = Path("scripts/js_port_gaps_allowed.txt").read_text(encoding="utf-8").splitlines()
assert src, "файл пропусков пуст"
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "a.txt"
    p.write_text("\n".join(src[1:]) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "scripts/js_port_gaps.py", "--check", "--allowed", str(p)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1 and "новый пропуск" in r.stdout, r.stdout
    p.write_text("\n".join(src + ["calcFoo option isBar"]) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "scripts/js_port_gaps.py", "--check", "--allowed", str(p)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1 and "пропуск устранён" in r.stdout, r.stdout
t = Path("calc_service/tests/test_js_port_gaps.py").read_text(encoding="utf-8")
assert f"MAX_ALLOWED = {len([s for s in src if s.strip()])}" in t
print("ok")
'@ | python -
```

- [ ] `rg -n "js_port_gaps" .cursor/skills/ezfc-form-to-api/SKILL.md .cursor/skills/new-calculator/SKILL.md` — по одной строке шага 0 в каждом файле.
- [ ] Правила в `calc_service/AGENTS.md`. Stdout `ok`:

```powershell
@'
from pathlib import Path
t = Path("calc_service/AGENTS.md").read_text(encoding="utf-8")
for s in ["## Порт из JS", "вся JS-функция", "не перенесено", "вызов порта", "приватные функции", "сначала `calcTablets`"]:
    assert s in t, s
print("ok")
'@ | python -
```

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет.
- Цены: нет.
- Формы: нет. Шаг 0 в `ezfc-form-to-api` остановит перевод формы, пока цепочка её калькулятора не перенесена или пропуски не записаны в «не перенесено».

## Режим

обычный

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
