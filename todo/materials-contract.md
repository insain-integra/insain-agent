# materials-contract

Статус: ревью
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
3. Единицы по-русски во всех калькуляторах (решено 31.10.2026): `sheet` → `лист`, `mm` → `мм`, `pcs`/`m`/`m2` — тоже по-русски (`шт`, `м`, `м²`). Количество не округлять до целого там, где в JS оно дробное.
4. Bridge: `item.name || item.title`, `code` в подпись не попадает никогда. Версия плагина `0.2.3` → `0.2.4` в обоих местах `insain-calc-bridge.php`.
5. Доки и правила, по строке (решено 31.10.2026, корневой `AGENTS.md` править): `calc_service/AGENTS.md` — на сайт и в бот уходит `name`; корневой `AGENTS.md` — пользователю только `name`/`title`; `docs/data-formats.md` — раздел «Элемент `materials` в ответе»: `code` (ключ, клиенту не показывается), `name` (полное имя, показывается клиенту), `title` (короткое), `unit` (по-русски), `quantity` (число, может быть дробным), `size_mm` (необязательно). Строки 43–44 не должны противоречить: в файлах данных старое `name` — это `description`, в ответе `name` = `description` материала.
6. Прод, после merge в `main`: сначала API (`bash infra/deploy.sh`), затем плагин по skill `deploy-wp-plugin`. После выкатки — форма 79: строки материалов показывают `name`, а не `title`.

## Не-scope

- Цены, наценки, `calc_service/data/`.
- `size_mm` у материалов печати — задача `todo/print-sheet-routing.md`.
- `bot_service/` (консервация): если тесты бота опираются на `title` — строка в отчёт, не правка.
- Формы ezFC и их custom JS, кроме проверки формы 79 глазами.

## Критерии приёмки

- [x] `python -m pytest calc_service/tests -q -k materials_contract` — `passed`, не меньше 4 тестов (пустой `name`, `name` равен `code`, пустой `title`, `quantity` строкой — каждый даёт `ValueError` из `execute()`), без `failed`.
- [x] `rg -n "\"unit\":\s*\"(sheet|mm|pcs|m|m2)\"|_unit = \"(sheet|mm)\"" calc_service/calculators` — пустой вывод, код 1.
- [x] Bridge, версия, правила, доки. Stdout `ok`:

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
assert "name`/`title" in root or "name/title" in root
df = Path("docs/data-formats.md").read_text(encoding="utf-8")
assert "Элемент `materials` в ответе" in df
print("ok")
'@ | python -
```

- [x] (после деплоя) Прод-API после деплоя. Stdout `ok`:

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

- [x] (после деплоя) `ssh insain-prod "sudo -u www-data wp plugin get insain-calc-bridge --field=version --path=/var/www/insain.ru"` — `0.2.4`.
- [x] (после деплоя) `ssh insain-prod "grep -c 'item.name || item.title' /var/www/insain.ru/wp-content/plugins/insain-calc-bridge/js/insain-calc-bridge.js"` — `1`.

## Проверки

- [x] `make check` (или `python scripts/dev.py check`) — зелёный вывод
- [x] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md)
- [x] (после деплоя) Форма 79 (Browser MCP, https://insain.ru/catalog/kalkulyator-pazlov/), вход `REF_PARAMS` пазлов: цена прежняя (как до выкатки), таблица материалов показывает `name` из ответа API, внутренних `code` нет. В «Чем проверено» — цена и строки материалов до и после.

## Риски

- Прод: `execute()` начнёт бросать `ValueError` на калькуляторе, который сейчас отдаёт пустое или равное `code` имя. На сайте через API считают `puzzle` (форма 79) и `plaque` (пилот формы 69); прогнать оба на проде сразу после деплоя API. Откат API — автоматический в `infra/deploy.sh` или образ `insain-agent-calc-api:rollback`; плагин — повторная установка zip предыдущего коммита плагина.
- Цены: нет, JSON не меняются. Цена формы 79 до и после выкатки одна.
- Формы: 79 — меняются подписи материалов с `title` на `name`. Структура формы не меняется.

## Режим

прод

## Результат

- Ветка, PR или коммит: прод с `main` `a8e1f2a` (человек снял условие «main = 80697b4» и разрешил выкатить вместе с print-sheet-routing). Push этого коммита с записью шага 6 — не делался.
- Сделано: шаги 1–5 — как в предыдущей записи (`validate_materials()`, русские единицы, bridge `item.name || item.title`, плагин 0.2.4, доки). Шаг 6: API через `bash infra/deploy.sh` (`663864d` → `a8e1f2a`, smoke пройден, образ `insain-agent-calc-api:rollback` = `f93f0c109e5a`); плагин 0.2.4 архивом `git archive a8e1f2a:wp-plugin`, `wp plugin install --force --activate`.
- Чем проверено:
  - До API. `POST /api/v1/calc/puzzle` `{"quantity":1,"puzzle_id":"Puzzle300420","mode":1}` — `price` 1171. Бумага в ответе: `unit` `sheet`.
  - Форма 79 до плагина (тот же вход, `POST` 200, тело ответа `price` 1171). Экран: 1200 руб., 1200 руб./шт, со скидкой 939 руб. и 939 руб./шт, вес 0.2 кг. Таблица (подписи `title`): «Пазл картонный 300×420 мм», размер 300,420, кол-во 1; «Бумага сублимационная 128г/м²», размер null, кол-во 2.
  - После API. Тот же POST пазла — `price` 1171. Скрипт критерия (name ≠ code, в `unit` нет латиницы) — `ok`. Бумага: `unit` `лист`, `size_mm` 297×420 (это print-sheet-routing в том же `main`). `POST /api/v1/calc/plaque` `quantity` 2, `plaque_id` Plaque2330, `material_id` PVC3, `application` isUVPrint, `mode` 1 — `price` 6205.71. `GET /api/v1/calculators` — 200.
  - Плагин: `wp plugin get` — `0.2.4`, `is-active` — `ACTIVE`. `grep -c 'item.name || item.title'` — `1`. В каталоге плагина `insain-calc-bridge.php`, `js/insain-calc-bridge.js`, `forms/plaque.js`.
  - Форма 79 после плагина. Скрипт `insain-calc-bridge.js?ver=0.2.4`. `POST /api/v1/calc/puzzle` 200, `price` 1171. Экран тот же: 1200 руб. / 1200 руб./шт, скидка 939 / 939, вес 0.2 кг. Таблица (`name`, кодов Puzzle300420 и PaperSublimation128 нет): «Пазл для сублимации, картонный, в рамке, прямоугольный 300×420 мм (300 элементов)», 300,420, 1; «Бумага сублимационная А3 (Китай BS), 128гр/м2», 297,420, 2. Ошибок `insaincalc` в консоли нет.
- Не сделано и почему: `wp litespeed-purge all` дважды ответил `Error: Something went wrong! Got 400` (при установке плагина была строка «Успешная очистка всех кэшей»). Страница калькулятора сброшена отдельно: `wp litespeed-purge url https://insain.ru/catalog/kalkulyator-pazlov/` — `Success: Purged the URL!`. Повторный локальный `python scripts/dev.py check` не запускался: CI Run 17 на этот же `a8e1f2a` зелёный, дерево было чистым. Push не делался.
- Требуется решение: push коммита с этой записью. `bot_service/agent.py:1462` сравнивает `unit` с `"sheet"` (ветка не сработает), `:1363`/`:1400` берут сначала `title` — бот в консервации, не правился. В каталогах 14 позиций без имени (`presswall` Joker…/Tritix…, `calendar` DoubleSide…/OneSide…) — в `materials` не попадают, данные не трогались.
- Как откатить: API — в `/opt/insain-agent` тег `insain-agent-calc-api:rollback` (`f93f0c109e5a`, код до выкатки `663864d`): `git reset --hard 663864d`, `docker tag insain-agent-calc-api:rollback insain-agent-calc-api:latest`, `docker compose -f docker-compose.calc-only.yml up -d --no-build --force-recreate`. Плагин — zip `git archive 663864d:wp-plugin` (на сервере до этой выкладки была 0.2.3) и тот же `wp plugin install --force --activate`. `9639b5e~` уже содержит плагин 0.2.4, им откатывать нельзя.
