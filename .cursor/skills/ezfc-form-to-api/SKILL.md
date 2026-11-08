---
name: ezfc-form-to-api
description: Перевод одной формы ezFC на сайте insain.ru со старого JS (insaincalc.calcXxx) на расчёт через API — insaincalc.calcApi и insaincalc.showResult. Порядок — сверка расчётов, дубль формы на черновик или приватный товар, отладка копии на боевом API, затем то же на боевой форме через read_file и forms/<slug>.js в плагине. Применять, когда калькулятор формы уже есть в calc_service и выкачен на прод.
---

# Перевод формы ezFC на API

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.

Дубль формы и переключение боевой формы — вне списка «Делай самостоятельно» в .cursor/rules/insain-site-autonomous.mdc: перед ними спросить человека.

Одна форма за проход. Обозначения: `<id>` — id боевой формы, `<slug>` — калькулятор API, `<copy>` — id копии формы, `<product>` — id товара с копией. Реестр форм и страниц — `docs/site/forms.md`. Как собирать поля и вызывать API — `docs/ezfc-api-migration.md`.

## Этапы

Шаги разнесены по файлам. Читать этот файл и файл своего этапа, остальные не открывать.

| Шаги | Этап | Кто | Файл |
| --- | --- | --- | --- |
| 0–5б | Сверка до перевода: порт, эталоны, боевой API, поля формы | Implementer | [verify.md](verify.md) |
| 6–16 | Дубль формы, JS копии, отладка на боевом API | Implementer (JS, шаг 10), Site ops | [copy.md](copy.md) |
| 17–24 | Боевая форма, снимок, реестр, откат | Site ops | [live.md](live.md) |

## SQL через файл

Запросы к базе ezFC. В Windows PowerShell 5.1 кавычки внутри аргумента `ssh` теряются, поэтому SQL идёт файлом:

```powershell
Set-Content -Encoding ascii -Path $env:TEMP\ezfc-<шаг>.sql -Value "<SQL>"
scp $env:TEMP\ezfc-<шаг>.sql insain-prod:/tmp/ezfc-<шаг>.sql
ssh insain-prod "sudo -u www-data wp db query --skip-column-names --path=/var/www/insain.ru < /tmp/ezfc-<шаг>.sql 2>/dev/null"
```

Ниже «SQL через файл» — эти три команды с нужным `<SQL>`. Только `SELECT`. У каждого запроса своё имя файла (`ezfc-5.sql`, `ezfc-9.sql`), запросы — по одному, не параллельно: с одним файлом параллельные вызовы перетирают друг друга.

Запись в таблицы `wp_insain_ezfc_*`: в копию формы JS и GET пишет только `scripts/ezfc_copy_apply.php` (шаг 10), структуру формы и блок результата правят в админке ezFC (Browser MCP). Свой PHP, `wp eval-file` или SQL на запись не писать.

## Роли и цепочка

- Implementer, git: шаги 0–5б, текст `wp-plugin/forms/<slug>.js` (шаг 10), эталон в тесте, `make check`. Статус остаётся `в работе`, промпт Site ops.
- Site ops, прод (лучше отдельный чат): шаги 6–16 после «да» человека, затем статус `ревью`. Расхождение на копии — обратно Implementer (шаг 15).
- Человек принимает копию → Reviewer (diff и настройки копии чтением с прода) → человек: skill `finish-task`.
- Каждый отчёт заканчивается готовым промптом следующей сессии (`docs/agents/workflow.md`, «Итоги»).
