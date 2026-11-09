# ezfc-options-source-reset

Статус: черновик
Сложность: высокая
Implementer: Grok 4.7
Reviewer: Auto
Site ops: Opus 5.5
Почему: массовая запись в элементы 42 форм ezFC на проде, skill нет и операция впервые; скрипт — один контур по образцу `scripts/ezfc_copy_apply.php`.

## Цель

Ни у одного элемента ezFC на проде нет `options_source` с внешним URL `http://vm-57d1b2fc.na4u.ru/calc/js/paper_test.json`: у всех таких элементов `options_source` = `{"source": "options", "value": ""}`. Списки dropdown и radio на страницах калькуляторов те же, что до правки, цены те же. Есть бэкап и проверенный откат.

## Контекст и ссылки

Факты на 10.11.2026 (чтение wp-cli и кода ezFC на VDS):

- 78 элементов в 42 формах (`wp_insain_ezfc_forms_elements.data`, поиск `na4u`): почти все боевые калькуляторы и копии 86–89, 92, 93. У всех `options_source.source` = `json`, `value` — этот URL.
- ezFC при `source` = `json` или `json_merge` на каждую отрисовку формы делает `wp_remote_get` по URL (`get_options_source()` в `wp-content/plugins/ez-form-calculator-premium/class.ezfc_frontend.php`). Ответ с `options` полностью заменяет сохранённые опции элемента; ошибка — остаются сохранённые.
- Сейчас у хоста нет DNS: `cURL error 6: Could not resolve host` за 0.002–0.011 с, страницы показывают сохранённые опции. Риск — если имя хостинга NetAngels достанется чужой VM, она подменит списки (и значения, от которых зависит цена) в 42 калькуляторах; если хост начнёт резолвиться и не отвечать — таймаут `wp_remote_get` (5 с) на каждый такой элемент.
- `scripts/ezfc_copy_apply.php` — образец: `wp eval-file`, показ без `apply`, бэкап строк в `/tmp`, запись только разрешённых ключей в `data`, кодирование `data` как в нём.
- `docs/site/access-tools.md` — каналы доступа к WP. `AGENTS.md`, «Запреты» — прямая запись в таблицы WordPress только с подтверждения человека.
- Остальное не открывать.

## Scope

- В git (Implementer): `scripts/ezfc_options_source_reset.php` для `sudo -u www-data wp eval-file … --path=/var/www/insain.ru`:
  - без аргумента — показ: id элемента, id и имя формы, текущий `options_source`, итоговые числа элементов и форм; ничего не пишет;
  - `apply` — бэкап затронутых строк (`id`, `data`) в `/tmp/ezfc-options-source-<время>.json`, затем в `data` каждого элемента с `options_source.value`, содержащим `na4u.ru`, ставит `options_source` = `{"source":"options","value":""}`; остальные ключи `data`, `options`, структура формы — без изменений; построчный вывод `записано <id>`;
  - `restore <файл бэкапа>` — возвращает `data` из бэкапа по `id`;
  - элемент с `options_source` на другой внешний URL или `source` `php`/`php_merge` — не трогать, вывести строкой `пропуск <id>: <source> <value>`.
- На проде (Site ops): показ → числа в отчёт → «да» человека → `apply` → проверка → сброс кэша. Расхождение опций на странице — `restore` и блокер Implementer.

## Файлы

- `scripts/ezfc_options_source_reset.php`
- WordPress: только ключ `options_source` в `data` элементов ezFC с URL `na4u.ru` — все формы, в т.ч. боевые из `todo/forms-batch-switch.md` и копии задач эпика `EPIC-forms-to-api`. С ними пересечение по объекту, не по ключам; сессии Site ops — последовательно, не одновременно с другой записью в формы.

## Не-scope

- Другие ключи элементов (`options`, `GET`, `custom_calculation`, `calculate`), структура и id элементов, перевод форм на API.
- Снимки `site/forms/*.json`, `docs/site/forms.md`.
- Плагин ezFC, его код и настройки. Удаление форм и копий (лишняя копия 90 — отдельно).
- `insainParse` — `todo/insainparse-admin-scripts.md`.

## Критерии приёмки

Каждый пункт — команда и ожидаемый результат. `BACKUP` — путь бэкапа из вывода `apply`. Скрипт кладётся на VDS в `/tmp/ezfc_options_source_reset.php` (как `ezfc_copy_apply.php` в skill `ezfc-form-to-api`).

- [ ] Синтаксис. Stdout: `No syntax errors detected`.

```powershell
ssh insain-prod "php -l /tmp/ezfc_options_source_reset.php"
```

- [ ] Показ до записи: 78 элементов в 42 формах (или числа на день запуска — в отчёт), строк `записано` нет, `пропуск` — каждая в отчёте.

```powershell
ssh insain-prod "sudo -u www-data wp eval-file /tmp/ezfc_options_source_reset.php --path=/var/www/insain.ru"
```

- [ ] После «да» человека — `apply`: путь бэкапа, по строке `записано <id>` на каждый элемент из показа.

```powershell
ssh insain-prod "sudo -u www-data wp eval-file /tmp/ezfc_options_source_reset.php apply --path=/var/www/insain.ru"
```

- [ ] В базе не осталось URL. Stdout: `0`.

```powershell
"SELECT COUNT(*) FROM wp_insain_ezfc_forms_elements WHERE data LIKE '%na4u%';" | ssh insain-prod 'sudo -u www-data wp db query --skip-column-names --path=/var/www/insain.ru 2>/dev/null'
```

- [ ] Опции не сдвинулись: у элементов 2024 (форма 49) и 103 значения `options` до и после совпадают (сверка с `BACKUP`). Повторный показ — 0 элементов.
- [ ] Страницы калькуляторов отвечают 200 после `wp cache flush` и сброса LiteSpeed: https://insain.ru/catalog/kalkulyator-rollapov/, https://insain.ru/catalog/kalkulyator-pressvolov/ и ещё три боевые страницы из показа; на странице роллапов селект типа — `econom` / `standart` / `premium`, цена по умолчанию та же, что до правки (записать до `apply`).
- [ ] Откат проверен на одном элементе: `restore` на копии 93 возвращает её `options_source` к URL, затем повторный `apply` для неё снова чистит. Боевые формы откатом не трогать.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: запись в `data` элементов 42 форм, в т.ч. боевых. Только после показа и «да» человека, с бэкапом; откат — `restore BACKUP`.
- Цены: JSON не трогается. Опции dropdown не меняются — значения, от которых зависит цена, те же.
- Формы: кодирование `data` должно совпасть с ezFC (unicode и `\/` как в сохранённых строках) — иначе админка ezFC может не открыть элемент. Проверить открытие одного изменённого элемента в редакторе ezFC.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату
[docs/agents/workflow.md](../docs/agents/workflow.md). Замечания ревью — ниже, в «Ревью N».

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Период:
- Часы человека: не учтено
- Работа агентов:
- Было / стало:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
