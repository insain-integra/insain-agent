# Копия формы и отладка (шаги 6–16)

Часть skill `ezfc-form-to-api`: общие правила, «SQL через файл» и роли — в `SKILL.md`.

## Дубль формы

Спросить человека: дубль формы `<id>` и черновик товара для него. Без ответа «да» дальше не идти.

Доступ к админке (Browser MCP): открыть `https://insain.ru/wp-admin/admin.php?page=ezfc` (не `page=ezfc-forms`). Открылась `wp-login.php` или ошибка доступа — стоп, попросить человека войти в этом браузере. Логин и пароль не вводить, автозаполнение браузера не использовать. wp-cli дубль формы ezFC не делает — не искать.

6. В админке ezFC у формы `<id>` — «Duplicate», один клик, без повтора. Id копии, SQL через файл:

   ```sql
   SELECT id, name FROM wp_insain_ezfc_forms ORDER BY id DESC LIMIT 3;
   ```

   Ожидается: одна новая строка с именем формы-источника — это `<copy>`. Две новые (на форме 78 так появились 90 и 91) — `<copy>` старшая по id, обе в отчёт; лишнюю удалять только с «да» человека.

7. Товар для копии: черновик или приватный товар, который видит только админ. В админке WooCommerce у товара с боевой формой — «Копировать» (создаётся черновик), затем форма копии на него:

   ```powershell
   ssh insain-prod "sudo -u www-data wp post meta update <product> ezfc_form_id <copy> --path=/var/www/insain.ru"
   ssh insain-prod "sudo -u www-data wp post get <product> --field=post_status --path=/var/www/insain.ru"
   ```

   Ожидается: `Success: Updated custom field 'ezfc_form_id'.` и `draft` (или `private`). Статус `publish` — сразу вернуть в черновик, копия не должна быть видна покупателям.

8. Гость копию не видит:

   ```powershell
   curl.exe -s -o NUL -w "%{http_code}" "https://insain.ru/?post_type=product&p=<product>"
   ```

   Ожидается: `404`. `200` — товар открыт гостям, стоп, вернуть статус шага 7.

9. Id копии — одной таблицей с боевой, SQL через файл:

   ```sql
   SELECT JSON_UNQUOTE(JSON_EXTRACT(b.data, '$.name')) AS name, b.id AS id_live, c.id AS id_copy FROM wp_insain_ezfc_forms_elements b LEFT JOIN wp_insain_ezfc_forms_elements c ON c.f_id = <copy> AND JSON_UNQUOTE(JSON_EXTRACT(c.data, '$.name')) = JSON_UNQUOTE(JSON_EXTRACT(b.data, '$.name')) WHERE b.f_id = <id> ORDER BY b.position;
   ```

   Третья команда «SQL через файл» здесь пишет вывод в файл: `... 2>/dev/null" | Set-Content -Encoding utf8 $env:TEMP\ezfc-map.tsv`.

   Ожидается: у каждой строки `id_copy` заполнен и отличается от `id_live`. `JSON_UNQUOTE` с обеих сторон обязателен: без него на форме 91 сравнение имён дало пустые `id_copy`. Пустой `id_copy` или `id_copy = id_live` — в запросе не тот `<copy>` или дубль не создался: повторить шаг 6, не подставлять id боевой формы. Эта таблица — источник id для JS копии в шаге 10.

   Ссылки `get_value_from(N)` в старом JS копии указывают на элементы боевой формы — этот JS в копии не отлаживать.

10. JS формы по шаблону `cjsCalc` из `docs/ezfc-api-migration.md`: чтение полей (`{{numN}}`, `ezfc_functions.get_value_from`), `insaincalc.syncUrl`, затем `insaincalc.calcApi('<slug>', {…})`, в `.then` — `insaincalc.showResult(calcCost, qty, __form_id__)`, в `.catch` — `insaincalc.showError`. Формул цены, чтения через DOM и своего вывода цены в JS нет.

    Исключение — повторяемая вложенная форма (repeatable form: слои формы 78 из формы 77). `get_value_from` не обходит её ряды, поэтому ряды читаются DOM по классам, как в боевом `cjsCalc`; остальные поля — как обычно. Исключение — комментарием в начале `forms/<slug>.js` и строкой «для Reviewer» в «Результат».

    Источник правды — `wp-plugin/forms/<slug>.js` в ветке задачи, с id **боевой** формы. В копию его пишет скрипт: id из таблицы шага 9 подставляет `scripts/ezfc_copy.py`, записывает `scripts/ezfc_copy_apply.php` вместе с GET (шаг 14). `--get` — каждое поле из `syncUrl`; dropdown с кодом — `:index`, `rdoModeProduction` — `:value`, числа — без суффикса:

    ```powershell
    python scripts/ezfc_copy.py wp-plugin/forms/<slug>.js --live <id> --copy <copy> --map $env:TEMP\ezfc-map.tsv --get numN --get rdoModeProduction:value --get <dpdX>:index --out $env:TEMP\ezfc-copy.json
    scp scripts/ezfc_copy_apply.php $env:TEMP\ezfc-copy.json insain-prod:/tmp/
    ssh insain-prod "sudo -u www-data wp eval-file /tmp/ezfc_copy_apply.php /tmp/ezfc-copy.json --path=/var/www/insain.ru"
    ```

    Ожидается: `стоп` нет; по строке на ключ, `→` у меняемых значений, у элемента расчёта `calcApi=1`. `стоп: … опубликованных товарах` — `<copy>` боевая форма, ничего не записано, вернуться к шагу 6. Затем та же команда `ssh` с `apply` после пути к пакету: `бэкап: /tmp/ezfc-copy-…json` и `записано` у каждого элемента. Откат — строки из бэкапа. Скрипт пишет только `custom_calculation`, `custom_calculation_function_read_file`, `GET`, `GET_check_option_value` в элементы копии; боевую форму, опубликованную форму и структуру формы он не меняет.

    ```powershell
    Select-String -Path wp-plugin\forms\<slug>.js -Pattern "insaincalc.calcApi\('<slug>'|insaincalc.showResult|get_value_from\(\d+"
    ```

    Ожидается: вызов `calcApi('<slug>'`, `showResult` и только id боевой формы из шага 5.

## Отладка на боевом API

Копия ходит в боевой API `https://insain.ru/api/v1`: `apiBase` плагина — `/api/v1` на том же домене. Тестовый контейнер API не поднимать.

11. Открыть черновик под админом (Browser MCP): `https://insain.ru/?post_type=product&p=<product>&preview=true`.

12. Network и консоль. Ожидается: `POST https://insain.ru/api/v1/calc/<slug>` — 200; в теле запроса коды материалов из `data-value`, а не `0`; в консоли нет ошибок `insaincalc` и `ezfc`.

13. Ввести вход эталона из шага 1. Ожидается: цена на странице равна `price` эталона (с учётом округления вывода). Блок результата на копии — как у формы 79, раздел «Блок результата» в `docs/ezfc-api-migration.md`: менеджерская цена и «со скидкой» в одной строке, режим внутри группы срока под текстом «Срок …», вес, таблица материалов без внутренних `code`. Старая вёрстка (себестоимость отдельным блоком, клиентские `sbtPrice` / `sbtPriceTotal`, пустой `htmTime`) правится в админке копии до этой проверки. Id полей ввода не менять.

14. Сначала сброс кэшей — без него страница отдаёт старые значения radio и GET:

    ```powershell
    ssh insain-prod "sudo -u www-data wp litespeed-purge all --path=/var/www/insain.ru; sudo -u www-data wp cache flush --path=/var/www/insain.ru"
    ```

    Поведение формы по чеклисту `docs/ezfc-api-migration.md`: смена каждого dropdown меняет цену и материалы; URL обновляется GET-именами формы; перезагрузка страницы не меняет режим и срок. Срок на копии равен сроку боевой формы на тех же значениях, не только цена. У `rdoModeProduction` на копии и перед переключением боевой формы `GET_check=value` (в том числе для значения `0`). У dropdown с кодом в `data-value` остаётся `index`.

15. Нашлась ошибка — правка в `wp-plugin/forms/<slug>.js` (id боевой формы), затем команды шага 10 заново, шаги 12–14 заново. Правка, сделанная только в админке копии, в git не попадает и считается потерянной. Копия и боевая форма расходятся на одинаковых значениях — сначала кейс дефолта раннером и боевым API (шаг 3): совпали — ошибка в JS или полях копии, Implementer; не совпали — порт, `заблокировано: аналитик`.

16. Записать в отчёт: `<copy>`, `<product>`, `post_status`, код шага 8, `price` из шага 13.
