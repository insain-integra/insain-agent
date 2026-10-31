---
name: new-calculator
description: Заведение нового калькулятора в calc_service, когда решение завести его уже принято (есть задача в todo/). Шаги от копии шаблона до регистрации, тестов и зелёного make check. Применять при переносе калькулятора из js_legacy или при новом калькуляторе API. Сам калькулятор skill не создаёт и решения «нужен ли калькулятор» не принимает.
---

# Новый калькулятор calc_service

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.

Ориентир по переносу формул, наценок и сроков — `docs/migration-guide.md`. Здесь только порядок рук и проверки после каждого шага; содержимое гайда не повторяется.

Ниже `<slug>` — имя калькулятора в API (`POST /api/v1/calc/<slug>`), `<Name>` — имя класса.

## Подготовка

0. Порт полон: `python scripts/js_port_gaps.py <calcX>` для JS-функции, которую переносит калькулятор, печатает её и всю цепочку вызовов. Если строка `нет в Python` хоть в одном блоке не пустая и этот пропуск не записан в «не перенесено» (docstring модуля и файл допустимых пропусков рядом со скриптом) — стоп, порт не полон.

1. Ветка от свежего `main`:

   ```powershell
   git switch main; git pull --ff-only; git switch -c task/<имя-задачи>
   ```

   Ожидается: `Switched to a new branch 'task/<имя-задачи>'`.

2. Слаг свободен:

   ```powershell
   Select-String -Path calc_service\calculators\__init__.py -Pattern '"<slug>"'
   ```

   Ожидается: пустой вывод. Есть совпадение — калькулятор уже заведён, стоп, вопрос в отчёт.

3. Данные на месте. Все цены, наценка `margin…`, сроки и материалы калькулятора лежат в `calc_service/data/` (`common.json`, `materials/*.json`, `equipment/*.json`). Проверка по каждому коду и ключу:

   ```powershell
   Select-String -Path calc_service\data\common.json,calc_service\data\materials\*.json,calc_service\data\equipment\*.json -Pattern '<код или margin-ключ>'
   ```

   Ожидается: строка с кодом в своём файле категории. Нет — позиция дописывается в JSON своей категории в этой же ветке (с комментарием даты и источника цены). В Python числа цен, наценок и сроков не пишутся.

## Код

4. Копия шаблона `calc_service/calculators/_template.py`:

   ```powershell
   Copy-Item calc_service\calculators\_template.py calc_service\calculators\<slug>.py
   ```

   Ожидается: файл `calc_service/calculators/<slug>.py` создан.

5. Заполнить по эталону `calc_service/calculators/laser.py`: `slug`, `name`, класс `<Name>Calculator`, `get_options`, `get_tool_schema` (и `get_param_schema`, если её переопределяет эталон), `calculate`. Наценка — `get_margin("margin…")` поверх `MARGIN_OPERATION`, не ниже `MARGIN_MIN`. Комментарии и тексты ошибок — по-русски.

   Ответ `calculate` содержит `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`, `materials`. Каждый элемент `materials` — с `code`, `name`, `title`. `share_url` не добавлять: его дописывает `BaseCalculator.execute()`.

6. Чисел цен в коде нет:

   ```powershell
   Select-String -Path calc_service\calculators\<slug>.py -Pattern '\b\d+\.\d+\b|\b\d{3,}\b'
   ```

   Ожидается: только размеры, индексы, округления и коэффициенты единиц (мм → м), ни одной цены, наценки, курса или срока. Найдено — перенести в JSON и читать через каталог или `common.markups`.

7. Регистрация в `calc_service/calculators/__init__.py`: импорт `from .<slug> import <Name>Calculator` и строка `"<slug>": <Name>Calculator(),` в `CALCULATORS`. Проверка:

   ```powershell
   cd calc_service; python -c "from calculators import CALCULATORS; print('<slug>' in CALCULATORS)"; cd ..
   ```

   Ожидается: `True`.

## Тесты

8. Файл `calc_service/tests/test_calculators/test_<slug>.py` по образцу соседних тестов. Обязательно:

   - эталон на тираже ≥ 2 со сверкой чисел `cost`, `price`, `unit_price` (не только наличие полей);
   - тест падает, если из ответа пропало обязательное поле или у элемента `materials` нет `code`, `name` или `title`;
   - `time_ready > time_hours > 0`, режимы производства, больший тираж — больше `time_hours`;
   - невалидный вход — ошибка с русским текстом.

   Если калькулятор переносится из `js_legacy` и подключён в `scripts/run_js_calc.mjs`, эталоны берутся оттуда, с комментарием-датой, как в `test_plaque.py`. В Windows PowerShell 5.1 кавычки внутри JSON экранируются `\"`, иначе скрипт ответит `params не JSON`:

   ```powershell
   node scripts/run_js_calc.mjs calcPlaque --data current --params '{\"quantity\":2,\"plaque_id\":\"Plaque1520\",\"material_id\":\"PVC3\",\"application\":\"isUVPrint\",\"mode\":1}'
   ```

   Ожидается: одна строка JSON с `cost`, `price`, `unit_price`, `time_hours`, `time_ready`, `weight_kg`. Не подключён — эталон из расчёта старой формы на сайте с теми же входами, тоже с датой.

9. Быстрый прогон:

   ```powershell
   python -m pytest calc_service/tests/test_calculators/test_<slug>.py -q
   ```

   Ожидается: `N passed`, `failed` нет.

10. Тест ловит поломку. Временно сменить одно число эталона `price` и прогнать шаг 9.

    Ожидается: `1 failed` с текстом про `price`. Число вернуть, шаг 9 снова зелёный. Временную правку не коммитить.

## Локальный API

11. Поднять API и посчитать:

    ```powershell
    python scripts/dev.py start calc
    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/v1/calc/<slug> -ContentType 'application/json' -Body '<json из эталона>' | ConvertTo-Json -Depth 5
    Invoke-RestMethod http://127.0.0.1:8001/api/v1/tool_schema/<slug> | ConvertTo-Json -Depth 8
    python scripts/dev.py stop calc
    ```

    Ожидается: JSON с `price`, равным эталону шага 8, и `share_url`; в `materials` есть `title`. Схема перечисляет все параметры, которые читает `calculate`.

## Сдача

12. Полная проверка:

    ```powershell
    python scripts/dev.py check
    ```

    Ожидается: код выхода 0, обе сюиты pytest `passed`, `failed` нет. Упало — чинить, не сдавать.

13. Diff только по задаче:

    ```powershell
    git status --short; git diff --stat main
    ```

    Ожидается: `calc_service/calculators/<slug>.py`, `calc_service/calculators/__init__.py`, `calc_service/tests/test_calculators/test_<slug>.py`, при необходимости JSON в `calc_service/data/` и файл задачи. Других файлов нет, отладочных `print` нет.

14. Self-review — чеклист «Перед сдачей» в `AGENTS.md`, коммит в ветку задачи по просьбе человека. Выкатка API после merge в `main` — `bash infra/deploy.sh` (раздел «Деплой API» в `AGENTS.md`). Подключение калькулятора к форме сайта — skill `ezfc-form-to-api`, отдельной задачей.
