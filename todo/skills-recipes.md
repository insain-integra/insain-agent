# skills-recipes

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: текст skills станет правилом для агентов.
Чат: человек открывает новый чат с моделью из поля Implementer, не с той, что уже открыта «под рукой».

## Цель

В `.cursor/skills/` четыре рецепта с фиксированными именами каталогов. По ним агент повторяет деплой плагина, заведение калькулятора, смену цены в JSON с выкаткой и перевод формы ezFC на API. Роль по-прежнему говорит, кто смотрит; skill говорит, как делать руками.

## Контекст и ссылки

- `docs/refactoring-plan.md` — только «Протокол выполнения» и пункт 5.5.
- `docs/agents/roles/` — кто выполняет шаг. В skill роли не пересказывать.
- `docs/agent-autonomous-environment.md` — только часть C.2 (zip и `wp plugin install`).
- `.cursor/rules/insain-site-autonomous.mdc` — что на проде делается само, что после вопроса человеку.
- `docs/site/access-tools.md` — «Принятый режим»: `read_file`, снимок `site/forms/<id>.json`, обратный импорт ломает id.
- `docs/ezfc-api-migration.md` — шаблон custom JS (`calcApi`, `showResult`). Порядка «дубль → боевой API → боевая форма» в этом файле нет: его пишет skill.
- `docs/migration-guide.md`, `calc_service/calculators/_template.py`, `calc_service/calculators/laser.py` — шаги нового калькулятора, в skill не копировать целиком.
- `infra/deploy.sh` — имя скрипта выкатки API после смены JSON. Файл скрипта не переписывать.
- `scripts/run_js_calc.mjs`, каталог `calc_service/tests/test_calculators/` — сверка до перевода формы.
- Остальное не открывать.

## Scope

Четыре каталога, в каждом только `SKILL.md`. Имена не менять:

- `.cursor/skills/deploy-wp-plugin/SKILL.md`
- `.cursor/skills/new-calculator/SKILL.md`
- `.cursor/skills/json-price-rollout/SKILL.md`
- `.cursor/skills/ezfc-form-to-api/SKILL.md`

Общее для всех четырёх:

- YAML-frontmatter: `name` равен имени каталога, непустой `description` (когда skill применять). Строки `disable-model-invocation: true` нет.
- Текст по-русски, не длиннее 500 строк.
- Нумерованные шаги: команда и ожидаемый вывод. Ссылка на док не заменяет шаг.
- Дословная строка: `Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.`

`deploy-wp-plugin` — руки при выкладке `wp-plugin/`. Дословно команды из части C.2:

- `Compress-Archive -Path wp-plugin\* -DestinationPath $env:TEMP\insain-calc-bridge.zip -Force`
- `scp $env:TEMP\insain-calc-bridge.zip insain-prod:/tmp/insain-calc-bridge.zip`
- `sudo -u www-data wp plugin install /tmp/insain-calc-bridge.zip --force --activate --path=/var/www/insain.ru`

В корне zip лежит `insain-calc-bridge.php`, не папка `wp-plugin/`. Каталог `forms/`, если он есть в `wp-plugin/`, попадает в архив рядом с php. Дословная строка: `API этой командой не деплоить.` Правки ezFC в этот skill не входят. В `description` есть слово «плагин».

`new-calculator` — руки, когда калькулятор уже решено завести. Шаги ссылаются на копирование `calc_service/calculators/_template.py`, эталон `calc_service/calculators/laser.py`, регистрацию в `calc_service/calculators/__init__.py`, тесты в `calc_service/tests/test_calculators/`, ориентир `docs/migration-guide.md`, проверку `python scripts/dev.py check`. Skill сам калькулятор не создаёт. В `description` есть слово «калькулятор».

`json-price-rollout` — правка только JSON в `calc_service/data/`, тест затронутого калькулятора, зелёный `python scripts/dev.py check`, выкатка с `main` командой `bash infra/deploy.sh`. Дословные строки: `Цены на сервере руками не править.` и `В Python цену не записывать.` В `description` есть слово «выкат».

`ezfc-form-to-api` — перевод одной формы. Заголовки ровно в таком порядке, без вставок между ними:

1. `## Сверка до перевода` — дословная строка: `Сверка скриптом scripts/run_js_calc.mjs и эталонами в calc_service/tests/test_calculators/ делается до перевода и не заменяет дубль, отладку на боевом API и переключение боевой формы.`
2. `## Дубль формы` — форма дублируется в админке ezFC; копия вешается на черновик или приватный товар; видит только админ. Дословные куски в этом разделе: `черновик или приватный товар`, `видит только админ`, `У копии свои id элементов.`
3. `## Отладка на боевом API` — копия ходит в боевой API `https://insain.ru/api/v1`. Дословная строка: `Тестовый контейнер API не поднимать.`
4. `## Боевая форма` — дословный кусок `то же на боевой форме`. Там же: `id элементов боевой формы не менять`, включение `read_file`, путь `forms/<slug>.js`, снимок в `site/forms/`. Дословная строка: `Боевую форму из снимка не импортировать.`

Где угодно в этом skill, дословно: `Дубль формы и переключение боевой формы — вне списка «Делай самостоятельно» в .cursor/rules/insain-site-autonomous.mdc: перед ними спросить человека.`

Custom JS в skill собирается по `docs/ezfc-api-migration.md`: `insaincalc.calcApi`, затем `insaincalc.showResult`. В `description` есть `ezFC`.

## Не-scope

- Прогон рецептов на живой задаче. Перевод формы 69 и деплой плагина для неё — `todo/pilot-plaque-form.md`.
- Новый калькулятор и правка цен «чтобы прогнать skill».
- Остальные формы, дубль сайта, тестовый контейнер API.
- Правки ролей, `AGENTS.md`, `docs/ezfc-api-migration.md`, `docs/migration-guide.md`, `docs/agent-autonomous-environment.md`, `docs/refactoring-plan.md`. Чекбокс 5.5 не ставить.
- Код калькуляторов, JSON цен, WordPress, прод.

## Критерии приёмки

Каждый пункт — команда из корня репозитория. Ожидается stdout `ok` и код выхода 0. Иначе stdout — список промахов.

- [ ] Frontmatter, длина, язык, ключевое слово в `description`. Stdout `ok`.

```powershell
@'
from pathlib import Path
import re
root = Path(".cursor/skills")
names = ["deploy-wp-plugin", "new-calculator", "json-price-rollout", "ezfc-form-to-api"]
keys = {"deploy-wp-plugin": "плагин", "new-calculator": "калькулятор", "json-price-rollout": "выкат", "ezfc-form-to-api": "ezFC"}
bad = []
for n in names:
    p = root / n / "SKILL.md"
    if not p.is_file():
        bad.append(n + ":missing")
        continue
    t = p.read_text(encoding="utf-8")
    if len(t.splitlines()) > 500:
        bad.append(n + ":long")
    if not t.startswith("---"):
        bad.append(n + ":fm")
        continue
    fm = t.split("---", 2)[1]
    m = re.search(r"(?m)^name:\s*(\S+)\s*$", fm)
    if not m or m.group(1) != n:
        bad.append(n + ":name")
    if "description:" not in fm:
        bad.append(n + ":desc")
    if "disable-model-invocation: true" in fm:
        bad.append(n + ":disabled")
    if keys[n] not in fm:
        bad.append(n + ":keyword")
    if not re.search(r"[а-яА-ЯёЁ]", t):
        bad.append(n + ":lang")
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [ ] Строка про роль во всех четырёх файлах. Stdout `ok`.

```powershell
@'
from pathlib import Path
line = "Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель."
names = ["deploy-wp-plugin", "new-calculator", "json-price-rollout", "ezfc-form-to-api"]
bad = [n for n in names if line not in Path(".cursor/skills", n, "SKILL.md").read_text(encoding="utf-8")]
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [ ] Цепочка деплоя плагина. Stdout `ok`.

```powershell
@'
from pathlib import Path
t = Path(".cursor/skills/deploy-wp-plugin/SKILL.md").read_text(encoding="utf-8")
need = [
    r"Compress-Archive -Path wp-plugin\* -DestinationPath $env:TEMP\insain-calc-bridge.zip -Force",
    "scp $env:TEMP\\insain-calc-bridge.zip insain-prod:/tmp/insain-calc-bridge.zip",
    "sudo -u www-data wp plugin install /tmp/insain-calc-bridge.zip --force --activate --path=/var/www/insain.ru",
    "insain-calc-bridge.php",
    "API этой командой не деплоить.",
]
bad = [s for s in need if s not in t]
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [ ] Шаги нового калькулятора. Stdout `ok`.

```powershell
@'
from pathlib import Path
t = Path(".cursor/skills/new-calculator/SKILL.md").read_text(encoding="utf-8")
need = [
    "calc_service/calculators/_template.py",
    "calc_service/calculators/laser.py",
    "calc_service/calculators/__init__.py",
    "calc_service/tests/test_calculators/",
    "docs/migration-guide.md",
    "python scripts/dev.py check",
]
bad = [s for s in need if s not in t]
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [ ] Смена цены и выкатка. Stdout `ok`.

```powershell
@'
from pathlib import Path
t = Path(".cursor/skills/json-price-rollout/SKILL.md").read_text(encoding="utf-8")
need = [
    "calc_service/data/",
    "infra/deploy.sh",
    "bash infra/deploy.sh",
    "main",
    "Цены на сервере руками не править.",
    "В Python цену не записывать.",
]
bad = [s for s in need if s not in t]
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [ ] Порядок перевода формы. Stdout `ok`.

```powershell
@'
from pathlib import Path
t = Path(".cursor/skills/ezfc-form-to-api/SKILL.md").read_text(encoding="utf-8")
marks = ["## Сверка до перевода", "## Дубль формы", "## Отладка на боевом API", "## Боевая форма"]
idx = [t.find(m) for m in marks]
if any(i < 0 for i in idx) or idx != sorted(idx):
    raise SystemExit("order " + str(list(zip(marks, idx))))
parts = [t[idx[i]:idx[i + 1]] for i in range(3)] + [t[idx[3]:]]
need = [
    ["Сверка скриптом scripts/run_js_calc.mjs и эталонами в calc_service/tests/test_calculators/ делается до перевода и не заменяет дубль, отладку на боевом API и переключение боевой формы."],
    ["черновик или приватный товар", "видит только админ", "У копии свои id элементов."],
    ["https://insain.ru/api/v1", "Тестовый контейнер API не поднимать."],
    ["то же на боевой форме", "id элементов боевой формы не менять", "read_file", "forms/<slug>.js", "site/forms/", "Боевую форму из снимка не импортировать."],
]
bad = [f"{i}:{ph}" for i, phrases in enumerate(need) for ph in phrases if ph not in parts[i]]
ask = "Дубль формы и переключение боевой формы — вне списка «Делай самостоятельно» в .cursor/rules/insain-site-autonomous.mdc: перед ними спросить человека."
if ask not in t:
    bad.append(ask)
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

## Проверки

- [ ] `python scripts/dev.py check` — код выхода 0 (pytest `calc_service/tests`, затем `bot_service/tests`)
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: в этой задаче сервер и WordPress не меняются. Skill деплоя и skill формы описывают прод так, чтобы следующий агент не перепутал zip плагина с деплоем API и не правил боевую форму без вопроса человеку.
- Цены: числа в skills не появляются. Рецепт цены ведёт в JSON и `infra/deploy.sh`.
- Формы: ни одна форма ezFC в этой задаче не дублируется и не переключается. Рецепт только фиксирует порядок.

## Режим

обычный

## Результат

- Ветка, PR или коммит: `task/skills-recipes` от `main`, merge fast-forward. PR не обязателен. `git push` — спросить.
- Сделано: четыре `SKILL.md` в `.cursor/skills/` (`deploy-wp-plugin` 146 строк, `new-calculator` 130, `json-price-rollout` 136, `ezfc-form-to-api` 241).
- После ревью: запасной `git archive` в `deploy-wp-plugin` — удаление `AGENTS.md` и повторный просмотр после него; `json-price-rollout` — `run_js_calc.mjs` только со своей функцией, CI по SHA из `git rev-parse` (с `gh` и без); `ezfc-form-to-api` — SQL id копии через файл, «Итог» реестра пересчитывается скриптом по таблице. Команды под Windows PowerShell 5.1: JSON для `node` с `\"`, POST через `Invoke-RestMethod`, SQL к ezFC файлом через `scp`, снимок формы через `/tmp` и `scp`.
- Чем проверено: шесть критериев приёмки — `ok`, код 0 (прогон с `$OutputEncoding = [System.Text.UTF8Encoding]::new($false)`); `python scripts/dev.py check` — 441 passed, 81 passed. Локально: `node scripts/run_js_calc.mjs calcPlaque … --params '{\"quantity\":2,…}'` → `price` 3871.268 (эталон `test_plaque.py` 3871.27); нормализатор снимка из шага 22 — на искусственном снимке; состав zip от `Compress-Archive` и `git archive`. Прод: только `ls -laR` каталога плагина.
- Не сделано и почему: команды к серверу (SQL-снимок, `wp post meta`, `wp litespeed-purge`) не прогонялись — прод вне scope, прогон в `todo/pilot-plaque-form.md`.
- Требуется решение: `Compress-Archive` на этой машине (модуль 1.0.1.0) пишет в zip `js\insain-calc-bridge.js` с обратным слэшем. В skill добавлена проверка и запасной `git archive … HEAD:wp-plugin`. Сделать ли `git archive` основным путём в C.2 и `AGENTS.md` — решение человека.
