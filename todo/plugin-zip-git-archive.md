# plugin-zip-git-archive

Статус: ревью
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: текст станет правилом для агентов (`AGENTS.md`, rule прода, skill деплоя плагина).
Чат: человек открывает новый чат с моделью из поля Implementer, не с той, что уже открыта «под рукой».
Старт: после merge `task/skills-recipes` в `main` — skill `deploy-wp-plugin` есть только в той ветке.

## Цель

Zip плагина `insain-calc-bridge` собирается одной командой `git archive --format=zip -o $env:TEMP\insain-calc-bridge.zip HEAD:wp-plugin` из закоммиченного `main`. `Compress-Archive` в правилах и доках деплоя плагина не остаётся: на Windows PowerShell 5.1 (модуль `Microsoft.PowerShell.Archive` 1.0.1.0) он пишет в zip пути с `\`, и WordPress на Linux распаковывает их как файлы с `\` в имени. `wp-plugin/AGENTS.md` в архив не попадает без ручного удаления.

Решение принято человеком: `git archive` — основной способ, не запасной.

## Контекст и ссылки

- `.cursor/skills/deploy-wp-plugin/SKILL.md` — шаги 4–5 (сборка и просмотр архива) и 13 (откат). Остальные шаги не менять.
- `AGENTS.md` — раздел «Деплой плагина и WordPress», строка «Плагин: …».
- `.cursor/rules/insain-site-autonomous.mdc` — строка «Деплой плагина: Compress-Archive → …».
- `docs/agent-autonomous-environment.md` — часть C.2 и строка «Деплой плагина: Compress-Archive → …» в блоке «Окружение VDS» (около строки 556).
- Остальное не открывать.

Проверено до задачи во временном репозитории:

- `git archive … HEAD:wp-plugin` берёт атрибуты из дерева `wp-plugin/`: корневой `.gitattributes` с `wp-plugin/AGENTS.md export-ignore` **не** действует, `AGENTS.md` остаётся в zip.
- `wp-plugin/.gitattributes` со строками `AGENTS.md export-ignore` и `.gitattributes export-ignore` действует: в zip нет ни `AGENTS.md`, ни самого `.gitattributes`, пути через `/`.

## Scope

- Новый файл `wp-plugin/.gitattributes`, ровно две строки:
  ```text
  AGENTS.md export-ignore
  .gitattributes export-ignore
  ```
- `.cursor/skills/deploy-wp-plugin/SKILL.md`:
  - шаг 4 — команда `git archive --format=zip -o $env:TEMP\insain-calc-bridge.zip HEAD:wp-plugin`; архив собирается из закоммиченного, незакоммиченные правки в zip не попадают (поэтому шаг 1 — чистое дерево на `main`). Команда удаления `AGENTS.md` из zip из основного пути уходит, вместо неё — одна фраза про `wp-plugin/.gitattributes`;
  - шаг 5 — просмотр содержимого остаётся: в корне `insain-calc-bridge.php`, `js/insain-calc-bridge.js`, `forms/<slug>.js` если есть; нет `AGENTS.md`, `.gitattributes`, путей с `\` и префикса `wp-plugin/`. Абзац про обратные слэши `Compress-Archive` и запасной путь убрать;
  - шаг 13 (откат) — та же команда с `<прежний коммит>:wp-plugin`, затем шаг 5. Коммит до появления `wp-plugin/.gitattributes` даст `AGENTS.md` в zip: тогда — команда удаления `AGENTS.md` (нынешняя из шага 4) и повторный шаг 5. Это единственное место, где команда удаления остаётся;
  - `description`, шаги 6–12, строки `API этой командой не деплоить.` и про роль — без изменений.
- `docs/agent-autonomous-environment.md`, C.2: в блоке PowerShell `Compress-Archive …` заменить на `git archive --format=zip -o $env:TEMP\insain-calc-bridge.zip HEAD:wp-plugin`, строку `scp` оставить. Примечание под блоком — `insain-calc-bridge.php` в корне zip, архив из закоммиченного, `AGENTS.md` исключён `wp-plugin/.gitattributes`. Строку в блоке «Окружение VDS» — `git archive → scp /tmp → …`.
- `AGENTS.md` и `.cursor/rules/insain-site-autonomous.mdc`: в строке про деплой плагина `Compress-Archive` → `git archive HEAD:wp-plugin`. Остальной текст строк не менять. Лимит `AGENTS.md` — 150 строк, новых строк не добавлять.

## Не-scope

- Выкладка плагина на прод, версия плагина, `wp-plugin/*.php` и `*.js`.
- `infra/deploy.sh`, деплой API.
- Остальные skills, роли, `docs/refactoring-plan.md`, `docs/archive/`.
- Корневой `.gitattributes` — не создавать и не править: для `HEAD:wp-plugin` он не действует.

## Критерии приёмки

Каждый пункт — команда из корня репозитория. Ожидается stdout `ok` и код выхода 0. Иначе stdout — список промахов. Если в stdout кириллица `???`, перед командой — `$OutputEncoding = [System.Text.UTF8Encoding]::new($false)`.

- [x] Тексты. Stdout `ok`.

```powershell
@'
from pathlib import Path
cmd = r"git archive --format=zip -o $env:TEMP\insain-calc-bridge.zip HEAD:wp-plugin"
files = {
    "AGENTS.md": ["git archive"],
    ".cursor/rules/insain-site-autonomous.mdc": ["git archive"],
    "docs/agent-autonomous-environment.md": [cmd, "scp $env:TEMP\\insain-calc-bridge.zip insain-prod:/tmp/insain-calc-bridge.zip", "insain-calc-bridge.php"],
    ".cursor/skills/deploy-wp-plugin/SKILL.md": [cmd, "wp-plugin/.gitattributes", "insain-calc-bridge.php", "API этой командой не деплоить.",
        "scp $env:TEMP\\insain-calc-bridge.zip insain-prod:/tmp/insain-calc-bridge.zip",
        "sudo -u www-data wp plugin install /tmp/insain-calc-bridge.zip --force --activate --path=/var/www/insain.ru",
        "Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель."],
}
bad = []
for f, need in files.items():
    t = Path(f).read_text(encoding="utf-8")
    if "Compress-Archive" in t:
        bad.append(f + ":Compress-Archive")
    bad += [f + ":" + s for s in need if s not in t]
if len(Path("AGENTS.md").read_text(encoding="utf-8").splitlines()) > 150:
    bad.append("AGENTS.md:long")
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

- [x] `wp-plugin/.gitattributes` — ровно две строки. Stdout `ok`.

```powershell
@'
from pathlib import Path
p = Path("wp-plugin/.gitattributes")
lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else ["missing"]
print("ok" if lines == ["AGENTS.md export-ignore", ".gitattributes export-ignore"] else "\n".join(lines))
'@ | python -
```

- [x] Состав zip из закоммиченного `HEAD` (гонять после коммита в ветку задачи). Stdout `ok`.

```powershell
@'
import io, subprocess, zipfile
data = subprocess.run(["git", "archive", "--format=zip", "HEAD:wp-plugin"], capture_output=True, check=True).stdout
names = set(zipfile.ZipFile(io.BytesIO(data)).namelist())
tracked = subprocess.run(["git", "ls-files", "wp-plugin"], capture_output=True, text=True, check=True).stdout.split()
want = {f[len("wp-plugin/"):] for f in tracked} - {"AGENTS.md", ".gitattributes"}
bad = ["missing:" + w for w in sorted(want - names)]
bad += ["extra:" + n for n in ("AGENTS.md", ".gitattributes") if n in names]
bad += ["backslash:" + n for n in names if "\\" in n]
bad += ["nested:" + n for n in names if n.startswith("wp-plugin/")]
if "insain-calc-bridge.php" not in names:
    bad.append("no insain-calc-bridge.php in root")
print("ok" if not bad else "\n".join(bad))
'@ | python -
```

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод. Если в diff нет Python — можно не гонять, написать это в «Результате».
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)

## Риски

- Прод: нет, сервер и WordPress не меняются. Следующая выкладка плагина пойдёт новым шагом 4; первый прогон — в задаче, где плагин реально выкатывается (`todo/pilot-plaque-form.md`).
- Откат на коммит до `wp-plugin/.gitattributes` даёт `AGENTS.md` в zip — покрыто шагом 13 skill.
- `git archive` не видит незакоммиченных правок: выкладка с грязным деревом даст старый код. Шаг 1 skill (чистое дерево на `main`) это закрывает — не ослаблять.
- Цены: нет.
- Формы: нет.

## Режим

обычный

## Результат

- Ветка, PR или коммит: `task/plugin-zip-git-archive` от `main`, merge fast-forward. PR не обязателен. `git push` — спросить.
- Сделано: коммит `10e5ed6` в `task/plugin-zip-git-archive`. Новый `wp-plugin/.gitattributes` (две строки `export-ignore`). Skill `deploy-wp-plugin`: шаг 4 — `git archive … HEAD:wp-plugin` и фраза про `wp-plugin/.gitattributes`; шаг 5 — просмотр с новым списком «чего нет», абзац про обратные слэши и запасной путь убран; шаг 13 — та же команда с `<прежний коммит>:wp-plugin`, команда удаления `AGENTS.md` — только для коммитов до `.gitattributes`. `AGENTS.md`, rule прода, `docs/agent-autonomous-environment.md` (C.2 и «Окружение VDS») — `Compress-Archive` заменён на `git archive`.
- Чем проверено: три критерия приёмки — stdout `ok` каждый; состав zip из `HEAD`: `insain-calc-bridge.php`, `js/`, `js/insain-calc-bridge.js`. `python scripts/dev.py check` — `441 passed`, `81 passed`, код выхода 0.
- Не сделано и почему: прод не трогали, плагин не выкатывали — не-scope.
- Требуется решение: шаг 10 skill (вне scope, не менялся) по-прежнему говорит про файл с `\` и «пересобрать по шагу 5» — при `git archive` неактуально, можно упростить отдельной правкой.
