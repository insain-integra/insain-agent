# Протокол параллельных задач

Единый регламент для человека и агентов (`Analyst`, `Orchestrator`, `Implementer`, `Reviewer`, `Site ops`).
Базовая схема: **1 чат = 1 задача = 1 внешний worktree `..\insain-agent-<имя>` (`task/<имя>`)**.
Основная папка `insain-agent` всегда остаётся на `main` (не переключается на `task/*`).

## 1. Старт задачи

1. На `main` `Analyst` создаёт и коммитит `todo/<имя>.md` (проверив пересечение `## Файлы`).
2. `Orchestrator` запускается новым чатом (в первом сообщении обязательно указать `todo/<имя>.md`, иначе `close_task.py` не учтёт часы). Можно открывать из основного окна на `main` или из отдельного окна на worktree.
3. Если worktree ещё не создан, `Orchestrator` сам вызывает `python scripts/dev.py wt-add <имя>` (человек может сделать это заранее, опционально). Команда откажет, если `todo/<имя>.md` не закоммичен в `main` или `## Файлы` пересекаются с активной задачей (у которой есть worktree или статус `в работе` / `ревью` / `доработка` / `выкатка` / `закрытие`).

## 2. Изоляция worktree и контроль субагентов

- `Orchestrator` передаёт каждому субагенту абсолютный путь worktree задачи (и требует передавать его в `working_directory` для `Shell`, а пути файлов — от корня worktree).
- После завершения **каждого** субагента `Orchestrator` запускает:
  ```powershell
  python scripts/dev.py wt-check <имя>
  ```
  Команда проверяет, что основная папка чистая на `main`, а worktree задачи стоит на `task/<имя>`. При ошибке — стоп до выяснения.
- Локальный API (`make calc-up`): в соседнем worktree задавать свой порт (`$env:CALC_PORT=8011`).

## 3. Общие ресурсы и блокировки (`lock`)

Состояние блокировок хранится в общем `.git/insain-locks/` и видно из всех worktree.

| Что | Режим | Команда контроля |
| --- | --- | --- |
| Код, тесты, `make check`, `Reviewer` | Параллельно в своих worktree | `wt-add` (проверка `## Файлы`) + `wt-check` |
| Прод, Browser MCP, админка WP/ezFC, деплой | **Строго по 1 задаче** (`Site ops`) | `lock acquire prod <имя>` / `release prod <имя>` |
| Слияние, `close`, `push` (`finish-task` на `main`) | **Строго по 1 задаче** | `lock acquire merge <имя>` / `release merge <имя>` |

Если ресурс занят другой задачей — не обходить молча: остановиться и спросить человека через `AskQuestion` (подождать завершения соседней задачи или снять зависший lock через `--force`).

## 4. Общие файлы и конфликты при `rebase`

- Общие файлы (`STATUS.md`, `BACKLOG.md`, `docs/site/forms.md`, `docs/history/log.md`, `docs/js-runner-cases.md`, `todo/EPIC-*.md`, `todo/forms-batch-switch.md`, `calc_service/calculators/__init__.py`, `calc_service/data/common.json`, версия `wp-plugin/insain-calc-bridge.php`) в параллельной ветке **не правят**: нужную дописку пишут в раздел «Результат» задачи и вносят в `main` при слиянии (под `lock merge`).
- Если `main` ушёл вперёд, в worktree делают `git rebase main`. При конфликте в `docs/dashboard.md` пересобирают его и продолжают rebase:
  ```powershell
  python scripts/dev.py dashboard; git add docs/dashboard.md; git rebase --continue
  ```

## 5. Диагностика

- Проверить активные worktree и блокировки: `python scripts/dev.py status` (или `python scripts/dev.py lock status`).
- Снять зависший lock (только с согласия человека): `python scripts/dev.py lock release <prod|merge> <имя> --force`.
