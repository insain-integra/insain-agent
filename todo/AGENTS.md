# todo/ — задачи как спецификации

Правила репозитория, инварианты и сдача — [AGENTS.md](../AGENTS.md). Этот файл — только про файлы в `todo/`.
Кому передаётся задача после каждой сессии — [docs/agents/workflow.md](../docs/agents/workflow.md).

## Файл

- Задачу пишет Analyst: `todo/<короткое-имя>.md` по [_template.md](_template.md).
- Эпик, если не влезает в один PR: `todo/EPIC-<имя>.md` по [_template-epic.md](_template-epic.md). Работа идёт по файлам задач, не по эпику.

## Шапка

- `Статус:` одна строка из списка в [workflow.md](../docs/agents/workflow.md), «Статусы»; проверяет `make check`.
- `Сложность`, `Implementer`, `Reviewer`, `Site ops`, `Почему` заполняет Analyst по [правилу роли](../docs/agents/roles/analyst.md).
- Модель берётся из полей шапки. Человек открывает чат с указанной моделью.

## После закрытия

Задача закрыта: обычная — после merge, смешанная и прод — после выкатки Site ops. Тогда файл удаляется.
Перед удалением человек разбирает «Найдено вне scope» (строка в `BACKLOG.md`, задача через Analyst или отказ),
устойчивое знание переносится в `docs/`, запись о задаче или эпике — в [docs/history/log.md](../docs/history/log.md)
по формату из её README. В `todo/` не остаются решения и регламенты.

Роли: [Analyst](../docs/agents/roles/analyst.md), [Implementer](../docs/agents/roles/implementer.md), [Reviewer](../docs/agents/roles/reviewer.md), [Site ops](../docs/agents/roles/site-ops.md).
