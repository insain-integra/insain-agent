# dashboard-harness

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Site ops: не нужен
Почему: текст станет правилом для агентов (`AGENTS.md`, close, дашборд).
Чат: эта сессия Implementer.

## Цель

Закрытие задачи — одна команда: журнал, дашборд, снятие «ждёт», удаление файла. Часы — по чатам Cursor. `make check` падает, если дашборд устарел или эпик ссылается на несуществующие `todo/*.md`.

## Контекст и ссылки

- `docs/vision.md`, `docs/history/README.md`, `docs/agents/workflow.md`
- `todo/AGENTS.md`, «После закрытия»
- Остальное не открывать.

## Scope

- `scripts/dashboard.py`, `scripts/close_task.py`; вызов из `scripts/dev.py`
- `docs/dashboard.md` собирается скриптом, руками не править
- Тесты в `calc_service/tests/test_todo_files.py` и `test_dashboard.py`
- Правила: `todo/AGENTS.md`, `docs/history/README.md`, команда в `AGENTS.md`

## Файлы

- `scripts/dashboard.py`, `scripts/close_task.py`, `scripts/dev.py`
- `docs/dashboard.md`, `docs/history/README.md`, `todo/AGENTS.md`, `AGENTS.md`
- `calc_service/tests/test_todo_files.py`, `calc_service/tests/test_dashboard.py`

## Не-scope

- `--live` метрики прода, Метрика, amoCRM
- Автокоммит после close
- Пересчёт старых записей `log.md`

## Критерии приёмки

- [ ] `python scripts/dev.py dashboard` — код 0, `docs/dashboard.md` содержит `G1` и имена открытых эпиков
- [ ] Повторный `python scripts/dashboard.py --check` — код 0
- [ ] `python -m pytest calc_service/tests/test_todo_files.py calc_service/tests/test_dashboard.py -q` — `passed`
- [ ] В `AGENTS.md` есть строка `python scripts/dev.py close`

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет
- Цены: нет
- Формы: нет

## Режим

обычный

## Журнал передач

- 07.11.2026 — Implementer, Opus 5.5 — реализация close/dashboard — дальше Reviewer

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит: `task/vision-align`
- Было / стало: журнал и план руками / close + дашборд из todo и vision
- Было / стало: журнал и план руками / `python scripts/dev.py close` и дашборд из vision+todo
- Сделано: close, dashboard, проверки эпиков и дашборда в pytest
- Чем проверено: `python -m pytest calc_service/tests/test_todo_files.py calc_service/tests/test_dashboard.py -q`
- Не сделано и почему: `--live` метрики — не-scope
- Требуется решение: —
