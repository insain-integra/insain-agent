# materials-contract

Статус: черновик
Сложность: высокая
Implementer: Opus 5.5
Reviewer: Grok 4.7
Почему: деплой API и плагина на прод, правка правил для агентов (`AGENTS.md`, `calc_service/AGENTS.md`), два контура — расчётное ядро и сайт.

## Цель

Каждый элемент `materials` в ответе калькулятора несёт непустые `name` и `title`, не равные `code`; единицы — по-русски, количество — число (может быть дробным). Это проверяет `BaseCalculator.execute()`. Клиент на сайте видит `name` — полное имя материала, как в старом JS (`material.set(id, [material.name, size, n])`); `code` на сайт не уходит никогда. Эпик `todo/EPIC-calc-port-structure.md`, шаг 1, параллельно с `todo/js-port-gaps.md`.

## Контекст и ссылки

- `calc_service/calculators/base.py` — `execute()` (около строки 145), сейчас только дописывает `share_url`.
- Единицы сейчас вразнобой: `laser.py` (около строки 486) ставит `unit` `mm` или `sheet`, `print_sheet.py` (около строки 677) — `sheet`, остальные — `шт`, `м`, `м²`, `мм`.
- `wp-plugin/js/insain-calc-bridge.js`, `adaptLegacyResult` (строки 53–82): сейчас `item.title || item.name || code`.
- `wp-plugin/insain-calc-bridge.php` — версия `0.2.3` в двух местах: заголовок `Version:` (строка 5) и аргумент версии скрипта (строка 20).
- `calc_service/AGENTS.md`, раздел «Контракт ответа»: строка «На сайт и в бот уходит `title`» — устарела.
- Корневой `AGENTS.md`, «Инварианты»: «Внутренние `code` материалов не показывать … только `title`/`description`» — устарела.
- `docs/data-formats.md` — строки 43–44 про `name` в файлах данных; раздела про элемент `materials` в ответе нет.
- `.cursor/skills/deploy-wp-plugin/SKILL.md` — выкатка плагина. Раздел «Деплой API» в `AGENTS.md` — выкатка API.
- `.cursor/rules/insain-site-autonomous.mdc` — целиком, до первого действия на сервере.
- Форма 79 (пазлы) на API: https://insain.ru/catalog/kalkulyator-pazlov/, эталон `calc_service/tests/test_calculators/test_puzzle.py` (`REF_PARAMS`: `quantity` 1, `puzzle_id` `Puzzle300420`, `mode` 1).
- Остальное не открывать.

## Scope

1. `BaseCalculator.execute()`: после `calculate()` проверить каждый элемент `materials`. `name` и `title` — строки, непустые после `strip()`, не равны `code`; `quantity` — `int` или `float` (не `bool`, не строка); `unit` — строка. Нарушение — `ValueError` с русским текстом.
2. Калькуляторы, у которых проверка падает, исправить: `name` — полное имя из каталога (`description`, как `material.name` в JS), `title` — короткое.
3. Единицы по-русски во всех калькуляторах: `sheet` → `лист`, `mm` → `мм` и т.п. Количество не округлять до целого там, где в JS оно дробное.
4. Bridge: `item.name || item.title`, `code` в подпись не попадает никогда. Версия плагина `0.2.3` → `0.2.4` в обоих местах `insain-calc-bridge.php`.
5. Доки и правила, по строке: `calc_service/AGENTS.md` — на сайт и в бот уходит `name`; корневой `AGENTS.md` — пользователю только `name`/`title`; `docs/data-formats.md` — раздел «Элемент `materials` в ответе»: `code` (ключ, клиенту не показывается), `name` (полное имя, показывается клиенту), `title` (короткое), `unit` (по-русски), `quantity` (число, может быть дробным), `size_mm` (необязательно). Строки 43–44 не должны противоречить: в файлах данных старое `name` — это `description`, в ответе `name` = `description` материала.
6. Прод, после merge в `main`: сначала API (`bash infra/deploy.sh`), затем плагин по skill `deploy-wp-plugin`. После выкатки — форма 79: строки материалов показывают `name`, а не `title`.

## Не-scope

- Цены, наценки, `calc_service/data/`.
- `size_mm` у материалов печати — задача `todo/print-sheet-routing.md`.
- `bot_service/` (консервация): если тесты бота опираются на `title` — строка в отчёт, не правка.
- Формы ezFC и их custom JS, кроме проверки формы 79 глазами.

## Критерии приёмки

- [ ] `python -m pytest calc_service/tests -q -k materials_contract` — `passed`, не меньше 4 тестов (пустой `name`, `name` равен `code`, пустой `title`, `quantity` строкой — каждый даёт `ValueError` из `execute()`), без `failed`.
- [ ] `rg -n "\"unit\":\s*\"(sheet|mm|pcs|m|m2)\"|_unit = \"(sheet|mm)\"" calc_service/calculators` — пустой вывод, код 1.
- [ ] Bridge, версия, правила, доки. Stdout `ok`:

```powershell
@'
import re
from pathlib import Path
js = Path("wp-plugin/js/insain-calc-bridge.js").read_text(encoding="utf-8")
fn = js.split("function adaptLegacyResult", 1)[1].split("function postCalc", 1)[0]
assert "item.name || item.title" in fn and "|| code" not in fn
php = Path("wp-plugin/insain-calc-bridge.php").read_text(encoding="utf-8")
assert php.count("0.2.4") == 2 and "0.2.3" not in php
calc = Path("calc_service/AGENTS.md").read_text(encoding="utf-8")
assert "уходит `title`" not in calc and "уходит `name`" in calc
root = Path("AGENTS.md").read_text(encoding="utf-8")
assert "только `title`/`description`" not in root
df = Path("docs/data-formats.md").read_text(encoding="utf-8")
assert "Элемент `materials` в ответе" in df
print("ok")
'@ | python -
```

- [ ] Прод-API после деплоя. Stdout `ok`:

```powershell
@'
import json, urllib.request
req = urllib.request.Request("https://insain.ru/api/v1/calc/puzzle", data=b'{"quantity":1,"puzzle_id":"Puzzle300420","mode":1}', headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as r:
    mats = json.load(r)["materials"]
assert mats
for m in mats:
    assert m["name"].strip() and m["title"].strip() and m["name"] != m["code"], m["code"]
    assert not any(ch.isascii() and ch.isalpha() for ch in m["unit"]), m["unit"]
print("ok")
'@ | python -
```

- [ ] `ssh insain-prod "sudo -u www-data wp plugin get insain-calc-bridge --field=version --path=/var/www/insain.ru"` — `0.2.4`.
- [ ] `ssh insain-prod "grep -c 'item.name || item.title' /var/www/insain.ru/wp-content/plugins/insain-calc-bridge/js/insain-calc-bridge.js"` — `1`.

## Проверки

- [ ] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
- [ ] Форма 79 (Browser MCP, https://insain.ru/catalog/kalkulyator-pazlov/), вход `REF_PARAMS` пазлов: цена прежняя (как до выкатки), таблица материалов показывает `name` из ответа API, внутренних `code` нет. В «Чем проверено» — цена и строки материалов до и после.

## Риски

- Прод: `execute()` начнёт бросать `ValueError` на калькуляторе, который сейчас отдаёт пустое или равное `code` имя. На сайте через API считают `puzzle` (форма 79) и `plaque` (пилот формы 69); прогнать оба на проде сразу после деплоя API. Откат API — автоматический в `infra/deploy.sh` или образ `insain-agent-calc-api:rollback`; плагин — повторная установка zip предыдущего коммита плагина.
- Цены: нет, JSON не меняются. Цена формы 79 до и после выкатки одна.
- Формы: 79 — меняются подписи материалов с `title` на `name`. Структура формы не меняется.

## Режим

прод

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Как откатить:
