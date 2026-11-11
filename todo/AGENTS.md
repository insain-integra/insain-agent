# todo/ — задачи как спецификации

Правила репозитория, инварианты и сдача — [AGENTS.md](../AGENTS.md). Этот файл — только про файлы в `todo/`.
Кому передаётся задача после каждой сессии — [docs/agents/workflow.md](../docs/agents/workflow.md).

## Файл

- Задачу пишет Analyst: `todo/<короткое-имя>.md` по [_template.md](_template.md).
- Файл задачи коммитится в `main` до начала работы. У задачи с веткой он дальше правится только в её worktree ([workflow.md](../docs/agents/workflow.md), «Ветки и папки»).
- Эпик, если не влезает в один PR: `todo/EPIC-<имя>.md` по [_template-epic.md](_template-epic.md). Работа идёт по файлам задач, не по эпику.

## Шапка

- `Статус:` одна строка из списка в [workflow.md](../docs/agents/workflow.md), «Статусы»; проверяет `make check`.
- `Сложность`, `Implementer`, `Reviewer`, `Site ops`, `Почему` заполняет Analyst по [правилу роли](../docs/agents/roles/analyst.md).
- Модель берётся из полей шапки. Человек открывает чат с указанной моделью.

## После закрытия

Человек говорит «закрой задачу» (или сам запускает команду). Дальше одно:

`python scripts/dev.py close <имя>`

Команда пишет запись в [docs/history/log.md](../docs/history/log.md), ставит `черновик` задачам
с `ждёт todo/<имя>.md`, переносит «Найдено вне scope» в `BACKLOG.md`, пересобирает
[docs/dashboard.md](../docs/dashboard.md), при необходимости дописывает срез в `snapshots.md`
и удаляет файл задачи. Коммит — отдельно, когда человек попросил. В `todo/` не остаются решения и регламенты.

Роли: [Analyst](../docs/agents/roles/analyst.md), [Implementer](../docs/agents/roles/implementer.md), [Reviewer](../docs/agents/roles/reviewer.md), [Site ops](../docs/agents/roles/site-ops.md).
