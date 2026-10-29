---
name: json-price-rollout
description: Смена цены, наценки, курса или срока в JSON calc_service/data/ и выкатка API на прод с main через bash infra/deploy.sh. Применять, когда поставщик поменял цену, нужно поправить наценку margin… или срок, и новое значение должно попасть в расчёт на insain.ru. Только данные, без правки кода калькуляторов.
---

# Смена цены в JSON и выкатка API

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.

Цены, наценки, курсы и сроки живут только в json5-файлах `calc_service/data/` (`common.json`, `materials/*.json`, `equipment/*.json`). Цены на сервере руками не править. В Python цену не записывать.

Одна позиция в одном файле — быстрый режим `AGENTS.md`, правка сразу в `main`. Несколько файлов или смена логики наценок — обычный режим, ветка `task/<имя>` от `main` и ревью до merge.

## Правка

1. Свежий `main`, чистое дерево:

   ```powershell
   git switch main; git pull --ff-only; git status --short
   ```

   Ожидается: `Already up to date.` или fast-forward, пустой список изменений.

2. Найти позицию по коду или ключу:

   ```powershell
   Select-String -Path calc_service\data\common.json,calc_service\data\materials\*.json,calc_service\data\equipment\*.json -Pattern '"<код или ключ>"'
   ```

   Ожидается: ровно один файл и строка. Две записи с одним кодом — стоп, вопрос человеку, какая верная.

3. Поменять только число. Рядом обновить `cost_date` (`ГГГГ-ММ-ДД`) и `cost_source`, если эти поля есть у записи, иначе — комментарий с датой и источником, как у соседних строк. Комментарии json5 не удалять: их читает загрузчик.

4. Diff — только эта позиция:

   ```powershell
   git diff --stat; git diff
   ```

   Ожидается: один файл в `calc_service/data/`, изменены число и дата/источник. Других строк нет, `.py` не тронуты.

## Тесты

5. Какие калькуляторы задеты:

   ```powershell
   Select-String -Path calc_service\calculators\*.py,calc_service\tests\test_calculators\*.py -Pattern '<код или ключ>' | ForEach-Object Filename | Sort-Object -Unique
   ```

   Ожидается: список файлов. Для ключей `common.json` (`marginMaterial`, `costOperator`, `USD` и т. п.) задеты почти все калькуляторы — тогда сразу шаг 7.

6. Тест затронутого калькулятора:

   ```powershell
   python -m pytest calc_service/tests/test_calculators/test_<slug>.py -q
   ```

   Ожидается: `passed`. Упал эталон с числом, в который входит эта позиция, — это ожидаемо: пересчитать эталон на новом прайсе и записать с датой в комментарии. Эталоны `JS_CASES` пересчитываются скриптом `scripts/run_js_calc.mjs` с `--data current`: имя JS-функции затронутого калькулятора и вход из его `JS_CASES`. Сейчас в скрипт подключена только `calcPlaque`; для другого калькулятора её не вызывать — чужая функция даст чужую цену. Пример для плакеток, он же образец кавычек PowerShell 5.1 (JSON экранируется `\"`):

   ```powershell
   node scripts/run_js_calc.mjs calcPlaque --data current --params '{\"quantity\":2,\"plaque_id\":\"Plaque1520\",\"material_id\":\"PVC3\",\"application\":\"isUVPrint\",\"mode\":1}'
   ```

   Ожидается: JSON с `price`. Ответ `Калькулятор не подключён: calc…` и код 1 — калькулятор в скрипт не подключён: сверка этой командой пропускается, это строка в отчёт, скрипт не править.

   Допуск сравнения в тесте не расширять. Упало что-то кроме эталона (ошибка загрузки JSON, `KeyError`) — правка сломала формат, вернуться к шагу 3.

7. Полная проверка:

   ```powershell
   python scripts/dev.py check
   ```

   Ожидается: код выхода 0, обе сюиты `passed`, `failed` нет.

8. Локальный расчёт на новом прайсе:

   ```powershell
   python scripts/dev.py start calc
   Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/v1/calc/<slug> -ContentType 'application/json' -Body '<json входа>' | Select-Object cost, price, unit_price
   python scripts/dev.py stop calc
   ```

   Ожидается: `price` изменилась в ожидаемую сторону и совпадает с новым эталоном шага 6. Записать вход и `price` для шага 13.

## В main

9. Коммит — по просьбе человека, одна правка — один коммит. Push в `main` — только с подтверждения человека.

10. CI на этом коммите зелёный: GitHub Actions, workflow `check` (`make check`), `conclusion` = `success` у коммита из `git rev-parse HEAD`. Сверка по SHA, не по последнему запуску ветки:

    ```powershell
    $sha = git rev-parse HEAD; $sha; if (Get-Command gh -ErrorAction SilentlyContinue) { gh run list --commit $sha --json headSha,workflowName,status,conclusion | ConvertFrom-Json | Format-Table } else { "gh не установлен: https://github.com/insain-integra/insain-agent/actions, запуск check для $sha" }
    ```

    Ожидается: полный SHA, затем строка с тем же `headSha`, `check`, `completed`, `success`. Без `gh` — строка со ссылкой: на странице Actions у запуска `check` с этим коммитом зелёная галочка. Пустая таблица, `in_progress`, `failure` — не выкатывать.

## Выкатка

Деплой API с `main` входит в «Делай самостоятельно» в `.cursor/rules/insain-site-autonomous.mdc`. Ручной `git pull` и `docker compose` для выкатки не использовать.

11. На сервере:

    ```powershell
    ssh insain-prod "cd /opt/insain-agent && bash infra/deploy.sh"
    ```

    Ожидается: `>>> Коммит: <старый> → <новый>`, `GET /api/v1/calculators → 200`, `POST /api/v1/calc/puzzle → 200`, `>>> Готово: <новый> выкачен, smoke пройден.` SSH отвалился по таймауту — повторить. Отказ `ветка '…', деплой только с main` или `рабочее дерево грязное` — стоп, на сервере руками не чинить, вывод в отчёт.

    Smoke не прошёл — скрипт сам откатывает код и образ на `insain-agent-calc-api:rollback` и выходит с ненулевым кодом. Повторно не запускать, вывод — в отчёт.

12. Код на проде:

    ```powershell
    ssh insain-prod "git -c safe.directory=/opt/insain-agent -C /opt/insain-agent log --oneline -1"
    ```

    Ожидается: коммит из шага 10.

13. Новая цена на боевом API:

    ```powershell
    Invoke-RestMethod -Method Post -Uri https://insain.ru/api/v1/calc/<slug> -ContentType 'application/json' -Body '<json входа из шага 8>' | Select-Object price, unit_price
    ```

    Ожидается: та же `price`, что в шаге 8.

14. Страница калькулятора, переведённого на API (Browser MCP): `POST /api/v1/calc/<slug>` — 200, на странице новая цена. Формы, ещё не переведённые на API (реестр — `docs/site/forms.md`), считают старым JS с прайсом из `/icalc/` — новая цена в них не появится; это строка в отчёт, не правка.

## Откат

15. Неверная цена, которую smoke пропустил: `git revert <коммит>` в `main`, `python scripts/dev.py check`, push с подтверждения человека, зелёный CI, затем шаги 11–13. Правка JSON на сервере откатом не считается.

## Отчёт

Позиция, старое и новое значение, коммит, вывод `deploy.sh` (последние строки), `price` до и после на боевом API, как откатить.
