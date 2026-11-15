---
name: finish-task
description: Завершение принятой задачи из todo/ одной командой человека — запись приёмки в журнал, коммит на ветке task/<имя>, fast-forward в main, make check, python scripts/dev.py close, пуш и удаление ветки, проверка CI. Применять, когда человек пишет «принято, закрывай», «принято, сливай», «закрывай», «завершай задачу», «finish-task» после вердикта Reviewer «принято», сдачи при Reviewer: не нужен или приёмки Site ops. Не для выкатки на прод и не вместо ревью.
---

# Завершение принятой задачи

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель. Выполняет агент по команде человека или выбору в `AskQuestion`.

`<имя>` — имя файла задачи без `.md`. Ветка — `task/<имя>`, её worktree — `..\insain-agent-<имя>` (`git worktree list`).
Если ветка `task/<имя>` и её worktree есть — шаги 1–5 выполняются в worktree `..\insain-agent-<имя>`, а шаги 6–12 — в основной папке на `main` (основная папка не переключается на `task/*`). Ветки нет (быстрый трек, прод без git, закрытие после выкатки) — всё в основной папке на `main`, шаги 4–6 пропустить.
Перед слиянием в `main` (шаг 6) обязательно захватывается `python scripts/dev.py lock acquire merge <имя>`, после окончания или остановки — `lock release merge <имя>`.
Таблица «кто и когда» — `docs/agents/workflow.md`, «Слияние и закрытие». Протокол параллельной работы — `docs/agents/parallel-protocol.md`.

## Можно ли завершать

1. Статус и журнал:

   ```powershell
   Select-String -Path todo\<имя>.md -Pattern "^Статус:|— Reviewer, .* — принято|— человек — принято|^Reviewer:\s*не нужен"
   ```

   Ожидается: статус `ревью` или `закрытие`, и при этом либо есть строка «принято» от Reviewer/человека, либо в шапке `Reviewer: не нужен` (или человек сам вызвал `finish-task` с приёмкой).
   Иначе — стоп: задача не принята, уточнить через `AskQuestion`.

2. Прод после слияния. В смешанной цепочке (`docs/agents/workflow.md`, «Три трека») выкатка идёт после merge: если в «Scope» есть шаги Site ops на боевом сайте, которые ещё не сделаны, задача не закрывается. Выполнить шаги 3–7 (в шаге 3 статус — `выкатка`), закоммитить, шаги 10–12 (пуш, CI, удаление ветки), дать промпт Site ops и остановиться. После отчёта Site ops со статусом `закрытие` — второй запуск: шаги 1, 3, 7–12. Задача на копию формы ezFC боевую форму не трогает — её закрывать можно.

## Приёмка и коммит на ветке

3. В «Журнал передач» строка человека и статус:

   ```text
   - ДД.ММ.ГГГГ — человек — принято — закрытие
   ```

   `Статус: закрытие`. В «Результат» заполнены «Было / стало» и «Ветка, PR или коммит» — без них `close` откажет. Не выдумывать: пусто — спросить через `AskQuestion`.

4. Дерево ветки:

   ```powershell
   git branch --show-current; git status --short
   ```

   Ожидается: `task/<имя>`, в списке только файлы из «Файлы» задачи, `docs/dashboard.md` и `todo/<имя>.md`. Чужие файлы — не коммитить, уточнить через `AskQuestion`.

5. Коммит одной осмысленной правкой (английский, по смыслу, как в `git log`):

   ```powershell
   git add <файлы задачи>; git commit -m "<что сделано>"
   ```

## Слияние

6. Блокировка `merge` и fast-forward в `main` — выполняется в **основной папке** (на `main`). Сначала захватить блокировку слияния (если занята — стоп и `AskQuestion`) и проверить diff ветки:

   ```powershell
   python scripts/dev.py lock acquire merge <имя>
   git branch --show-current; git diff --stat main...task/<имя>
   git pull --ff-only; git merge --ff-only task/<имя>
   ```

   Ожидается: блокировка захвачена, текущая ветка — `main`, merge прошёл как fast-forward. Если основная папка не на `main` — освободить lock (`lock release merge <имя>`) и проверить через `AskQuestion`.

   Если `merge --ff-only` не прошёл (`main` ушёл вперёд из-за параллельной задачи) — перейти в worktree `..\insain-agent-<имя>` и сделать `git rebase main`:
   - Конфликт только в `docs/dashboard.md` — пересобрать и продолжить rebase:
     ```powershell
     python scripts/dev.py dashboard; git add docs/dashboard.md; git rebase --continue
     ```
   - Закрытый в `main` файл `todo/` вернулся после rebase — убрать его из ветки после подтверждения через `AskQuestion`.
   - Иной конфликт — освободить lock (`python scripts/dev.py lock release merge <имя>`), стоп, `заблокировано: исполнитель`, предложить варианты через `AskQuestion`.
   После успешного rebase вернуться в основную папку и повторить `git merge --ff-only task/<имя>`.

7. Проверка на `main`:

   ```powershell
   python scripts/dev.py check
   ```

   Ожидается: код 0, `passed` в обеих сюитах. `check` пересобирает `docs/dashboard.md` — если он изменился, добавить в коммит шага 9.

## Закрытие

8. Закрыть задачу (в основной папке на `main`):

   ```powershell
   python scripts/dev.py close <имя>
   ```

   Ожидается: `закрыто: <имя>.md`, `журнал и дашборд обновлены`. Строки «снят «ждёт»» и «ссылки помечены закрытыми» — перечислить в отчёте. Задача, которая ждёт эту и живёт в своём worktree со статусом `заблокировано: ждёт todo/<имя>.md`, разблокируется в её worktree после `git rebase main` — статус `черновик` и строка в журнал.

9. Проверить запись и закоммитить:

   ```powershell
   Select-String -Path docs\history\log.md -Pattern "— <имя>$" -Context 0,4
   git add -A todo docs BACKLOG.md; git status --short; git commit -m "Close <имя>: <итог одной фразой>."
   ```

   Ожидается в журнале: период и часы правдоподобны. Устаревший текст эпика вокруг помеченной ссылки поправить в том же коммите.

## Пуш и очистка ветки

10. Если человек уже выбрал вариант с `push` (в `AskQuestion` или фразой «принято, закрывай» / «закрывай») — **повторно про `git push` не переспрашивать**. Если запускали без явного решения о `push`, спросить через `AskQuestion`:
    - «Запушить `main` и удалить worktree `..\insain-agent-<имя>` и ветку `task/<имя>` (Рекомендуется)»
    - «Оставить коммиты локально (без push)»
    Если выбран локальный вариант (без `push`), снять блокировку: `python scripts/dev.py lock release merge <имя>`.

11. При подтверждении `push` (в основной папке на `main`):

    ```powershell
    git push origin main; python scripts/dev.py wt-rm <имя>; git push origin --delete task/<имя>; python scripts/dev.py lock release merge <имя>
    ```

    `wt-rm` удаляет `..\insain-agent-<имя>` и ветку `task/<имя>` без `--force` (если в worktree есть незакоммиченные файлы — откажет и покажет ошибку). Ветки и worktree уже нет (второй запуск, задача без ветки) — только `git push origin main` и `lock release merge <имя>`. Ветки на origin нет — ошибку `remote ref does not exist` игнорировать.

12. CI по пушнутому коммиту (`gh` нет, публичный API):

    ```powershell
    Invoke-RestMethod "https://api.github.com/repos/insain-integra/insain-agent/actions/runs?branch=main&per_page=1" | ForEach-Object { $r = $_.workflow_runs[0]; "$($r.head_sha.Substring(0,7)) $($r.status) $($r.conclusion)" }
    ```

    Ожидается: SHA пушнутого коммита, `completed success`. `failure` — предупредить сразу: деплой с `main` запрещён до починки.

## Отчёт

Коммиты (SHA), запись журнала (период, часы), что разблокировано, результат CI. Дальше — `AskQuestion` со следующей задачей эпика или действием на проде (если актуально).
