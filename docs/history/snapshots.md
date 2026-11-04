# Срезы состояния

Одинаковый набор метрик в каждом срезе, чтобы видеть динамику. Новый срез — сверху.
Как снять метрику — колонка «Чем» в первом срезе; «—» значит метрики на дату не было.

## Срез 04.11.2026

| Метрика | 28.09.2026 (аудит) | 04.11.2026 | Чем |
| --- | --- | --- | --- |
| Калькуляторов в API | 38 публичных (на 25.10) | 39 модулей | `GET /api/v1/calculators`; модули в `calc_service/calculators/` |
| Тестов | 5 падали | 581, зелёные | `python -m pytest calc_service/tests bot_service/tests --collect-only -q`; `make check` |
| CI | нет | GitHub Actions, `make check` | `.github/workflows/` |
| Деплой API | вручную, с рабочей ветки | `infra/deploy.sh` с `main`, smoke, автооткат | `AGENTS.md`, «Деплой API» |
| Форм ezFC всего | 49 | 49 | `docs/site/forms.md`, «Итог» |
| Боевых форм на API | 1 (пазлы) | 1 (пазлы) | `docs/site/forms.md` |
| Форм готово к переключению | 0 | 1 (плакетки, на копии) | `todo/forms-batch-switch.md`, «Состав пакета» |
| Плагин insain-calc-bridge | 0.2.3 | 0.2.6 | `wp plugin get insain-calc-bridge --field=version` |
| Skills (рецепты агентов) | 0 | 4 | `.cursor/skills/` |
| Коммитов всего | 26 | 127 | `git rev-list --count HEAD` |
| Часы человека, нарастающим итогом | оценка 26 ч | оценка 127 ч | 1 ч на коммит, `docs/history/log.md` |
| Скорость главной, LCP моб. | 10,4 с (до оптимизации, май) | не замерялась | PageSpeed Insights |

Открыто: пакетное переключение форм (`todo/forms-batch-switch.md`), антиспам и чистка
спам-пользователей (`todo/EPIC-antispam-recaptcha.md`, `todo/EPIC-spam-users-cleanup.md`),
фаза 6 плана — управление контентом сайта. Бот — на консервации.
