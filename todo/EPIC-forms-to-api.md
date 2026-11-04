# EPIC-forms-to-api

Статус: черновик

## Цель

Восемь форм ezFC посчитаны через `insaincalc.calcApi` на принятой человеком копии (черновик товара, GET = имя элемента, та же цена по ссылке). Шесть функций, которых не было в раннере, сначала считает `todo/js-runner-forms.md`. Боевые формы этой пачки ещё на старом JS. Переключение, снимки `site/forms/<id>.json` и реестр `docs/site/forms.md` делает `todo/forms-batch-switch.md`, когда строка формы есть в его «Составе пакета».

## Задачи

- `todo/js-runner-forms.md` — `scripts/run_js_calc.mjs` считает шесть функций, цена сходится с API.
- Форма 26, slug `uv_print`, закрыта 05.11.2026: копия 87 принята, боевая страница ждёт `todo/forms-batch-switch.md`.
- `todo/form-mug.md` — форма 41, slug `mug`. Путь кружки — сублимация. Раннер уже умеет `calcMug`.
- `todo/form-embossing.md` — форма 85, slug `embossing`, цепочка 3.
- `todo/form-acrylic-prizes.md` — форма 78, slug `acrylic_prizes`, цепочка 8.
- `todo/form-rollup.md` — форма 49, slug `rollup`, цепочка 10.
- `todo/form-presswall.md` — форма 46, slug `presswall`, цепочка 11.
- `todo/form-pennant.md` — форма 73, slug `pennant`, цепочка 14.
- `todo/form-flag.md` — форма 55, slug `flag`, цепочка 15.

## Порядок

1. `todo/js-runner-forms.md`
2. Форма 26 закрыта. `todo/form-mug.md` — параллельно раннеру, на форму 26 не завязана
3. `todo/form-embossing.md` — после закрытия раннера
4. `todo/form-acrylic-prizes.md`
5. `todo/form-rollup.md`
6. `todo/form-presswall.md`
7. `todo/form-pennant.md`
8. `todo/form-flag.md`

Модель чата — поле `Implementer` в шапке задачи. Одна задача — одна сессия.
