# ai-calc-authoring-skill

Статус: черновик
Сложность: высокая
Implementer: Gemini 4 Hydrogen High
Reviewer: Grok 4.7
Site ops: не нужен
Почему: проектирует правила работы агентов (новый сквозной skill интервью, аудита базы и сборки «API + форма»).

## Цель

У агентов есть единый воспроизводимый сценарий `.cursor/skills/create-calc-with-form/`: по текстовому описанию нового калькулятора от владельца агент задаёт структурированные уточняющие вопросы (через `AskQuestion`), проверяет существующие калькуляторы, материалы и оборудование, переиспользует их или дописывает новые, генерирует код API, `wp-plugin/forms/<slug>.js` и JSON-спеку для `scripts/ezfc_build_form.py`, после чего доводит форму до черновика товара на сайте и приёмки.

## Контекст и ссылки

- `.cursor/skills/new-calculator/SKILL.md` — текущий skill для Python-части калькулятора (перенос/шаблон).
- `.cursor/skills/ezfc-form-to-api/SKILL.md`, `.cursor/skills/deploy-api/SKILL.md`, `.cursor/skills/deploy-wp-plugin/SKILL.md` — эталоны деплоя и проверки форм.
- `.cursor/rules/interactive-choices.mdc` — правила оформления `AskQuestion`.
- `scripts/ezfc_build_form.py` (из `ezfc-form-builder` (закрыто 2026-11-20, `docs/history/log.md`)) — интерфейс конструктора форм и формат JSON-спеки.
- `calc_service/calculators/_template.py`, `calc_service/calculators/laser.py`, `calc_service/AGENTS.md` — единый стиль кода и контракты калькуляторов.
- `docs/ezfc-api-migration.md` — единый стиль форм ezFC и блока результата.
- `docs/README.md` — оглавление документации (добавить ссылку при необходимости).
- Остальное не открывать.

## Scope

- Создать `.cursor/skills/create-calc-with-form/SKILL.md` и модульные файлы этапов (`interview.md`, `backend.md`, `form.md`) со сквозным маршрутом:
  1. **Интервью (`Analyst`):**
     - обязательный предварительный скан базы (команда быстрого обзора `CALCULATORS`, `materials/*.json`, `equipment/*.json`, `common.json`, чтобы не читать десятки файлов целиком);
     - чеклист уточняющих вопросов владельцу через `AskQuestion` (назначение и диапазон размеров/тиражей, тип исполнения: своё производство / подрядчик / логистика — и логика режимов `mode=0, 1, 2` по стандарту из `docs/migration-guide.md`, переиспользование базовых калькуляторов/операций, выбор существующих или ввод новых материалов/оборудования с источником цены, состав и условия полей формы, наценка `margin…` и срок готовности, целевой товар/страница или новый черновик);
     - формат спецификации задачи `todo/<slug>.md` (включая таблицу маппинга «поле формы → параметр API → источник опций в JSON»).
  2. **Бэкенд и данные (`Implementer`):**
     - переиспользование существующих калькуляторов/утилит (`common/layout.py`, `common/process_tools.py`, вызов существующих калькуляторов как подрасчётов) вместо дублирования формул;
     - порядок добавления новых материалов/оборудования/наценок в `calc_service/data/` (`cost_date`, `cost_source`, комментарии json5);
     - реализация калькулятора (ссылка на шаги `.cursor/skills/new-calculator/SKILL.md`), тестов и `wp-plugin/forms/<slug>.js` + JSON-спеки формы для `scripts/ezfc_build_form.py`.
  3. **Сборка на сайте и приёмка (`Site ops`):**
     - деплой API (`deploy-api`) и плагина (`deploy-wp-plugin`);
     - создание/привязка черновика товара WooCommerce (`draft`, 404 для гостей);
     - сборка новой формы через `scripts/ezfc_build_form.py` + `scripts/ezfc_build_apply.php`;
     - проверка в браузере (Network `POST /api/v1/calc/<slug>` = 200, консоль без ошибок, блок результата по эталону 79, GET-параметры URL, смена всех dropdown/условий) → передача на приёмку владельцу через `AskQuestion` (включая вариант публикации товара после приёмки).
- Добавить компактную CLI-команду/скрипт обзора каталогов (например, в `scripts/dev.py` или `scripts/calc_catalog_index.py`), выводящую список `slug` калькуляторов, файлов `materials/*.json` и `equipment/*.json` с кодами/описаниями и ключами `margin*` из `common.json` — чтобы `Analyst` и `Implementer` мгновенно находили готовую базу для переиспользования.
- Уточнить в `.cursor/skills/new-calculator/SKILL.md` его роль как подэтапа реализации Python-модуля (ссылка на `create-calc-with-form` для полного цикла с интервью и формой), при необходимости обновить `docs/README.md`.

## Файлы

- `.cursor/skills/create-calc-with-form/SKILL.md`
- `.cursor/skills/create-calc-with-form/interview.md`
- `.cursor/skills/create-calc-with-form/backend.md`
- `.cursor/skills/create-calc-with-form/form.md`
- `.cursor/skills/new-calculator/SKILL.md`
- `scripts/calc_catalog_index.py` (или `scripts/dev.py` — если добавляется подкоманда)
- `calc_service/tests/test_calc_catalog_index.py`
- `docs/README.md`

## Не-scope

- Правка `scripts/ezfc_build_form.py` и `scripts/ezfc_build_apply.php` (сделано в `ezfc-form-builder` (закрыто 2026-11-20, `docs/history/log.md`)).
- Реализация конкретного калькулятора C2 (это `todo/pilot-acrylic-medals-calc.md`).
- Правка `AGENTS.md` и `docs/site/forms.md`.

## Критерии приёмки

- [ ] `python scripts/calc_catalog_index.py` (или подкоманда `scripts/dev.py`) выводит в stdout актуальный сводный список всех `slug` из `CALCULATORS`, категорий `materials/*.json`, `equipment/*.json` и ключей `margin*` из `common.json` без ошибок.
- [ ] `python -m pytest calc_service/tests/test_calc_catalog_index.py -q` — `passed`, `failed` нет.
- [ ] В `.cursor/skills/create-calc-with-form/` присутствуют `SKILL.md`, `interview.md`, `backend.md`, `form.md`; все ссылки внутри них на существующие скрипты (`scripts/ezfc_build_form.py`, `scripts/ezfc_build_apply.php`, `scripts/calc_catalog_index.py`) и skills (`new-calculator`, `deploy-api`, `deploy-wp-plugin`) валидны и проверены.
- [ ] В `SKILL.md` и `interview.md` явно закреплены: обязательные уточняющие вопросы через `AskQuestion`, правило переиспользования текущих калькуляторов/материалов/оборудования, единый стиль форм (эталон 79) и запрет публикации без приёмки владельца.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет (изменения только в git: skills, индексный скрипт и тесты).
- Цены: нет.
- Формы: риск рассинхронизации описанных в skill команд с реальным CLI `ezfc_build_form.py`; снимается тем, что задача стартует строго после закрытия `ezfc-form-builder` (закрыто 2026-11-20, `docs/history/log.md`).

## Режим

обычный

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека:
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
