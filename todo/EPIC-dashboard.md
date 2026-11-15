# EPIC-dashboard

Статус: в работе
Цель: G6

## Цель

К 31.12.2026 дашборд, журнал и срезы обновляются командой закрытия задачи, без ручного переписывания сводок. `make check` ловит рассинхрон дашборда и пустые эпики.

## Задачи

- `dashboard-harness` (закрыто 2026-11-15, `docs/history/log.md`) — `scripts/dev.py close` и `dashboard`, `docs/dashboard.md`, проверки в `make check`, часы по чатам Cursor.
- Срез `--live` (версия плагина на VDS, LCP, заявки) — отдельная задача после доступов G3/G4; в этом файле не заводить.

## Порядок

1. `dashboard-harness` (закрыто 2026-11-15, `docs/history/log.md`)
2. live-метрики — после `todo/metrics-baseline.md`
