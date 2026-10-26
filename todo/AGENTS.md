# todo/ — задачи как спецификации

Правила репозитория, инварианты и сдача — [AGENTS.md](../AGENTS.md). Этот файл — только про файлы в `todo/`.

## Файл

- Задачу пишет Analyst: `todo/<короткое-имя>.md` по [_template.md](_template.md).
- Эпик, если не влезает в один PR: `todo/EPIC-<имя>.md` по [_template-epic.md](_template-epic.md). Работа идёт по файлам задач, не по эпику.

## Шапка

- `Статус:` одна строка — `черновик` / `в работе` / `ревью` / `готово`.
- `Сложность`, `Implementer`, `Reviewer`, `Почему` заполняет Analyst по [правилу роли](../docs/agents/roles/analyst.md).
- Модель берётся из полей шапки. Человек открывает чат с указанной моделью.

## После закрытия

После merge файл удаляется. Устойчивое знание переносится в `docs/`. В `todo/` не остаются решения и регламенты.

Роли: [Analyst](../docs/agents/roles/analyst.md), [Implementer](../docs/agents/roles/implementer.md), [Reviewer](../docs/agents/roles/reviewer.md), [Site ops](../docs/agents/roles/site-ops.md).
