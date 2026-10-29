---
name: deploy-wp-plugin
description: Выкладка плагина insain-calc-bridge из wp-plugin/ на прод insain.ru через zip и wp plugin install. Применять, когда изменились файлы wp-plugin/ (bridge JS, PHP, forms/<slug>.js переведённых форм) и их нужно выкатить на сайт. Не для деплоя API и не для правок форм ezFC в админке.
---

# Деплой плагина insain-calc-bridge

Кто выполняет шаг — роль из docs/agents/roles/. Skill описывает действия, не подменяет роль и не выбирает модель.

Деплой плагина входит в «Делай самостоятельно» в `.cursor/rules/insain-site-autonomous.mdc`. Плагин на прод попадает только архивом через `wp plugin install` от `www-data`: `rsync` и `cp` от root недоступны, отдельные файлы в `wp-content` не подкладывать.

API этой командой не деплоить. Выкатка `calc_service` — `bash infra/deploy.sh` с `main` (skill `json-price-rollout`, раздел «Деплой API» в `AGENTS.md`).

Правки форм ezFC в админке (дубль, `read_file`, снимки) в этот skill не входят — это skill `ezfc-form-to-api`.

## Перед выкладкой

1. Ветка и дерево. Из корня репозитория:

   ```powershell
   git branch --show-current; git status --short
   ```

   Ожидается: `main`, пустой список изменений. Выкладывается только смёрженный в `main` код.

2. Зелёная проверка:

   ```powershell
   python scripts/dev.py check
   ```

   Ожидается: код выхода 0, в выводе две строки pytest с `passed` и без `failed`.

3. Версия плагина. Если изменился `wp-plugin/js/insain-calc-bridge.js`, версия поднята в двух местах `wp-plugin/insain-calc-bridge.php`: в шапке `Version:` и в аргументе версии `wp_enqueue_script` (по ней браузер сбрасывает кэш JS). Проверка:

   ```powershell
   Select-String -Path wp-plugin\insain-calc-bridge.php -Pattern "Version:|'\d+\.\d+\.\d+'"
   ```

   Ожидается: обе строки с одной и той же новой версией.

## Сборка архива

4. Архив собирается из содержимого каталога, не из самого каталога:

   ```powershell
   Compress-Archive -Path wp-plugin\* -DestinationPath $env:TEMP\insain-calc-bridge.zip -Force
   ```

   Ожидается: пустой вывод, файл `$env:TEMP\insain-calc-bridge.zip` создан.

   `wp-plugin/AGENTS.md` — правила для агентов, на сайт не попадает. Убрать его из архива:

   ```powershell
   Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem; $z = [IO.Compression.ZipFile]::Open("$env:TEMP\insain-calc-bridge.zip", 'Update'); @($z.Entries | Where-Object FullName -eq 'AGENTS.md') | ForEach-Object { $_.Delete() }; $z.Dispose()
   ```

   Ожидается: пустой вывод.

5. Содержимое архива:

   ```powershell
   Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::OpenRead("$env:TEMP\insain-calc-bridge.zip").Entries | ForEach-Object FullName
   ```

   Ожидается: в корне zip лежит `insain-calc-bridge.php`, рядом `js/insain-calc-bridge.js`. Каталог `forms/`, если он есть в `wp-plugin/`, попадает в архив рядом с php: `forms/<slug>.js`. `AGENTS.md` в списке нет — есть, значит, пропущено удаление из шага 4. Строк вида `wp-plugin/insain-calc-bridge.php` быть не должно — значит, заархивирован каталог, а не содержимое; повторить шаг 4 с `-Path wp-plugin\*`.

   Пути с обратным слэшем (`js\insain-calc-bridge.js`) — признак Windows PowerShell 5.1 с модулем `Microsoft.PowerShell.Archive` 1.0.1.0. WordPress на Linux распакует такую запись как файл с `\` в имени в корне плагина, без каталога `js/`. Тогда архив собирается из закоммиченного `wp-plugin/`, `AGENTS.md` удаляется командой из шага 4, шаг 5 повторяется:

   ```powershell
   git archive --format=zip -o $env:TEMP\insain-calc-bridge.zip HEAD:wp-plugin
   ```

   Ожидается: пути через `/`, состав тот же, без `AGENTS.md`.

## Выкладка

6. Копирование на сервер:

   ```powershell
   scp $env:TEMP\insain-calc-bridge.zip insain-prod:/tmp/insain-calc-bridge.zip
   ```

   Ожидается: строка прогресса `insain-calc-bridge.zip 100%`. Отвалилось по таймауту — повторить ту же команду.

7. Установка поверх текущей версии:

   ```powershell
   ssh insain-prod "chmod 644 /tmp/insain-calc-bridge.zip && sudo -u www-data wp plugin install /tmp/insain-calc-bridge.zip --force --activate --path=/var/www/insain.ru"
   ```

   Команда на сервере целиком: `sudo -u www-data wp plugin install /tmp/insain-calc-bridge.zip --force --activate --path=/var/www/insain.ru`.

   Ожидается: `Plugin updated successfully.` (или `Plugin installed successfully.`) и `Success: Plugin 'insain-calc-bridge' activated.` Warning `Wt::__wakeup()` — шум. Если плагин встал в каталог с другим именем (`insain-calc-bridge-1` и т. п.) — архив собран неверно, вернуться к шагу 5.

8. Сброс кэша страниц:

   ```powershell
   ssh insain-prod "sudo -u www-data wp litespeed-purge all --path=/var/www/insain.ru"
   ```

   Ожидается: строка `Success`.

## Проверка

9. Версия и статус на проде:

   ```powershell
   ssh insain-prod "sudo -u www-data wp plugin get insain-calc-bridge --field=version --path=/var/www/insain.ru; sudo -u www-data wp plugin is-active insain-calc-bridge --path=/var/www/insain.ru && echo ACTIVE"
   ```

   Ожидается: версия из шага 3 и `ACTIVE`.

10. Раскладка файлов на сервере:

    ```powershell
    ssh insain-prod "ls -R /var/www/insain.ru/wp-content/plugins/insain-calc-bridge"
    ```

    Ожидается: в корне `insain-calc-bridge.php` и каталог `js/` с `insain-calc-bridge.js`; если в архиве был `forms/` — каталог `forms/` с теми же `<slug>.js`, что в `wp-plugin/forms/`. `AGENTS.md` нет. Имя файла с `\` в корне — архив с обратными слэшами: пересобрать по шагу 5 и выложить заново.

11. API на месте (плагин его не трогает, проверка, что сайт жив):

    ```powershell
    curl.exe -fsS https://insain.ru/api/v1/calculators -o NUL -w "%{http_code}"
    ```

    Ожидается: `200`.

12. Страница калькулятора, который использует изменённый код (Browser MCP): в Network есть `POST /api/v1/calc/{slug}` со статусом 200, цена и срок выводятся, в консоли нет ошибок `insaincalc`. Скрипт плагина подключён с новой версией: `insain-calc-bridge.js?ver=<версия из шага 3>`.

## Откат

13. Собрать архив из прежнего коммита, рабочее дерево не трогая:

    ```powershell
    git archive --format=zip -o $env:TEMP\insain-calc-bridge.zip <прежний коммит>:wp-plugin
    ```

    Ожидается: пустой вывод. Дальше удаление `AGENTS.md` из шага 4 и шаги 5–9 без изменений. Удалять файлы на сервере для отката не нужно: `--force` заменяет плагин целиком.

## Отчёт

Что выкачено (версия, коммит), вывод шагов 7 и 9, результат шага 12, как откатить (шаг 13).
