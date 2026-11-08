# form-button-pins

Статус: черновик
Сложность: средняя
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Grok 4.7
Почему: калькулятор-обёртка над готовой `calc_button_pins` по skill `new-calculator`; прод — выкатка по `deploy-api` и копия формы по `ezfc-form-to-api`.
Чат: сначала Implementer (калькулятор), затем копия формы — Site ops по skill `ezfc-form-to-api`.

## Цель

Форма 12 CalcButtonPins считает `POST /api/v1/calc/button_pins`. В реестре API есть slug `button_pins`. Копия на черновике товара: GET = имя элемента, цена по ссылке та же. Боевая страница https://insain.ru/catalog/znachki-zakatnye-kruglye/ на старом JS, пока форму не возьмёт пакет переключения.

## Контекст и ссылки

- Эпик `todo/EPIC-forms-to-api.md`, пачка 5
- `.cursor/skills/new-calculator/SKILL.md` и `.cursor/skills/ezfc-form-to-api/SKILL.md`
- Логика уже есть: `calc_service/common/process_tools.py` `calc_button_pins`, JS `insaincalc.calcButtonPins`
- `docs/site/forms.md` — строка формы 12, только читать до переключения
- Остальное не открывать

## Scope

В git (Implementer):

1. Калькулятор по шаблону `_template.py`: обёртка над `calc_button_pins`, без копирования формул. Регистрация в `__init__.py`. Тесты: эталон со старого JS, обязательные поля ответа.
2. После зелёного `make check` и слияния — выкатка API (человек / Site ops по `infra/deploy.sh`).

На проде (Site ops), после API на проде:

3. Перевод формы 12 через копию по skill `ezfc-form-to-api`. Боевую не переключать.

## Файлы

- `calc_service/calculators/button_pins.py`, `calc_service/calculators/__init__.py`
- `calc_service/tests/test_calculators/test_button_pins.py`
- `wp-plugin/forms/button_pins.js` — на шаге копии
- WordPress: только копия формы и черновик товара

## Не-scope

- Боевая форма 12, `forms-batch-switch`, цены в JSON (наценка `marginButtonPins` уже есть)
- Другие значки (`metal_pins`, `badge`)

## Критерии приёмки

- [ ] `python bot_service/check_calc_registry.py` на локальном API — в списке есть `button_pins` (нужен `make calc-up`)
- [ ] `python -m pytest calc_service/tests/test_calculators/test_button_pins.py -q` — `passed`
- [ ] Раннер JS и API: rel ≤ 0.001 на эталоне (команда раннера — из skill / `docs/js-runner-cases.md` после добавления кейса)
- [ ] Копия не на витрине: `draft` или `private`, гость `404`
- [ ] На копии POST `/api/v1/calc/button_pins` → 200, цена на странице = API с округлением `showResult`

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: дубль формы только с подтверждения; боевая страница не меняется в этой задаче
- Цены: JSON не менять; `marginButtonPins` уже в `common.json`
- Формы: id боевой 12 не менять

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`.

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
