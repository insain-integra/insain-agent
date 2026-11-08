# Оглавление docs

Колонка «Статус»: **живой** — текущий регламент или справочник; **архив** — исторический текст, заметка о несделанном или схема, которая расходится с продом. Каталоги `site/` и `archive/` не переносились.

Деплой API описан в skill `.cursor/skills/deploy-api/` и `infra/deploy.sh`. Отдельного runbook деплоя в `docs/` нет.

| Файл | Назначение | Статус |
| --- | --- | --- |
| [agent-autonomous-environment.md](agent-autonomous-environment.md) | Runbook: Cursor, SSH, браузер, деплой плагина на insain.ru | живой |
| [vision.md](vision.md) | Видение и цели G1–G7 до 31.05.2027: метрики, сроки, что не делаем | живой |
| [agents/workflow.md](agents/workflow.md) | Маршруты между ролями: статусы задач, блокеры, ревью, находки вне scope, параллельные ветки | живой |
| [architecture.md](architecture.md) | Черновик схемы контейнеров, потоков и списка API. Схема контейнеров (порт 8001, PostgreSQL, бот в compose) расходится с продом | архив |
| [common-json-reference.md](common-json-reference.md) | Справочник полей `common.json`: наценки, курсы, сроки | живой |
| [data-formats.md](data-formats.md) | Справочник форматов JSON и маппинг JS → Python | живой |
| [ezfc-api-migration.md](ezfc-api-migration.md) | Runbook перевода формы ezFC на Python API | живой |
| [gemini-prompt-caching.md](gemini-prompt-caching.md) | Заметка про кэш промптов Gemini; явный кэш в боте не внедрён | архив |
| [js-runner-cases.md](js-runner-cases.md) | Команды JS-раннера и `price` для сверки форм с API | живой |
| [migration-guide.md](migration-guide.md) | Runbook миграции калькулятора JS → Python | живой |
| [project_summary.md](project_summary.md) | Обзор репозитория с примерами для внешней LLM; не регламент | архив |
| [README.md](README.md) | Это оглавление | живой |
| [dashboard.md](dashboard.md) | Сводка целей, очереди и метрик; собирает `python scripts/dev.py dashboard` | живой |
| [wordpress-integration.md](wordpress-integration.md) | Связка WordPress, bridge и share-ссылок с API | живой |
| [history/README.md](history/README.md) | История проекта: правила ведения и формат записи | живой |
| [history/passport.md](history/passport.md) | Дата старта, цель, исходное состояние | живой |
| [history/log.md](history/log.md) | Журнал крупных задач: срок, затраты, было / стало | живой |
| [history/snapshots.md](history/snapshots.md) | Срезы состояния с одинаковыми метриками | живой |
| [archive/README.md](archive/README.md) | Индекс документов в `docs/archive/` | архив |
| [archive/production-cutover-plan.md](archive/production-cutover-plan.md) | План уже выполненного переключения DNS insain.ru | архив |
| [archive/site-performance-optimization.md](archive/site-performance-optimization.md) | Журнал замеров PageSpeed на test.insain.ru | архив |
| [archive/refactoring-plan.md](archive/refactoring-plan.md) | План фаз 0–6 до перехода на vision/todo | архив |
| [archive/vds-wordpress-docker-setup.md](archive/vds-wordpress-docker-setup.md) | Историческая инструкция первичной установки VDS | архив |
| [site/access-tools.md](site/access-tools.md) | Runbook: чем читать и писать объекты WordPress | живой |
| [site/content-inventory.md](site/content-inventory.md) | Карта контента сайта: объект, где лежит, чем правится | живой |
| [site/forms.md](site/forms.md) | Реестр форм ezFC: страница, id, slug API, статус | живой |
