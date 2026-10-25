# STATUS — снимок прода insain.ru

Календарная дата снимка: **25.10.2026**. Команды ниже выполнены по SSH на хосте `insain-prod` (пользователь `agent`) и ничего на сервере не меняли. Точные метки времени — UTC, как их вернул `date -u` в начале соответствующей команды. Окно снимка: **2026-10-25T07:10:26Z – 2026-10-25T07:18:48Z**. Значения секретов в этот файл не записывались.

## Хост и адреса

Проверено `hostname`, `hostname -I` в **2026-10-25T07:17:22Z**.

| Факт | Значение |
| --- | --- |
| Имя хоста | `vm-52541a6a` |
| Публичный IPv4 | `5.181.252.133` |
| Репозиторий на VDS | `/opt/insain-agent` |
| Корень WordPress | `/var/www/insain.ru` |
| `siteurl` и `home` | `https://insain.ru` |

`siteurl` и `home`: `sudo -u www-data wp option get siteurl --path=/var/www/insain.ru` и та же команда с `home`, **2026-10-25T07:17:22Z**. Оба ответа: `https://insain.ru`.

Публичная проверка, `curl -sS -o /dev/null -w "%{http_code}"`, **2026-10-25T07:17:22Z**:

| URL | Код |
| --- | --- |
| `https://insain.ru/` | 200 |
| `https://insain.ru/api/v1/calculators` | 200 |
| `http://127.0.0.1:8002/api/v1/calculators` | 200 |

`SITE_URL` работающего контейнера `insain-calc-api` (из `Config.Env` взято только это поле): `https://insain.ru`. Команда — `docker inspect insain-calc-api` с печатью одного имени, сразу после снимка **2026-10-25T07:18:48Z**, та же календарная дата.

Nginx, активный файл `/etc/nginx/sites-enabled/insain.ru` (`ls -l`: обычный файл, не симлинк, `root:root`, дата файла May 27). Разбор `grep -n` по `server_name`, `listen`, `root`, `proxy_pass`, `ssl_certificate` — **2026-10-25T07:17:22Z**; строки `location` — сразу после **2026-10-25T07:18:48Z**.

- `server_name insain.ru www.insain.ru`, `root /var/www/insain.ru`.
- `location ^~ /api/` → `proxy_pass http://127.0.0.1:8002`.
- `listen 5.181.252.133:443 ssl http2`, сертификат `/etc/letsencrypt/live/insain.ru/fullchain.pem`.
- В том же файле отдельный server для `test.insain.ru` с тем же `location ^~ /api/` и `proxy_pass http://127.0.0.1:8002`.
- `listen 5.181.252.133:80`, `server_name insain.ru www.insain.ru test.insain.ru`.

Канонический адрес сайта по WordPress — `https://insain.ru`. Отдельный `curl` на `www.insain.ru` и `test.insain.ru` не делался.

Файл `/etc/nginx/sites-available/vm-52541a6a.na4u.ru.conf` при обходе `/etc/nginx` не прочитан (`PermissionError`).

## Git

Репозиторий `/opt/insain-agent`. Префикс команд: `git -c safe.directory=/opt/insain-agent -C /opt/insain-agent`. Время **2026-10-25T07:17:22Z** (тот же HEAD уже был в **2026-10-25T07:10:26Z**).

| Факт | Значение | Команда |
| --- | --- | --- |
| Ветка | `main` | `rev-parse --abbrev-ref HEAD` |
| HEAD | `3b2ae44b65ca4bc52102ee568557902b842170c5` | `rev-parse HEAD` |
| `origin/main` | тот же хеш | `rev-parse origin/main` |
| Дата коммита | 2026-10-25 14:18:07 +0800 | `log -1 --format=%ci` |
| Тема | Mark task 0.4 done: production deploys from main. | `log -1 --format=%s` |
| Рабочее дерево | чистое, нет ahead/behind | `status -sb` → `## main...origin/main` |
| origin | `https://github.com/insain-integra/insain-agent.git` | `remote get-url origin` (в URL нет учётных данных) |

## Контейнеры и порты

Рабочий контейнер создан файлом `/opt/insain-agent/docker-compose.calc-only.yml`.

`docker inspect insain-calc-api`, **2026-10-25T07:17:22Z**:

| Поле | Значение |
| --- | --- |
| Имя | `insain-calc-api` |
| Сервис compose | `calc-api` |
| `com.docker.compose.project.working_dir` | `/opt/insain-agent` |
| `com.docker.compose.project.config_files` | `/opt/insain-agent/docker-compose.calc-only.yml` |
| Образ | `insain-agent-calc-api` |
| Image ID | `sha256:e8efca23463a3746b68179279e3550c44e3d9b63b5e3123de94efd303dc5035e` |
| Состояние | `running`, health `healthy` |
| Создан | 2026-10-25T06:50:31Z |
| Restart | `always` |
| Команда | `uvicorn main:app --host 0.0.0.0 --port 8001` |
| WorkingDir | `/app/calc_service` |
| Публикация порта | `127.0.0.1:8002` → `8001/tcp` |
| Bind | `/opt/insain-agent/calc_service/data` → `/app/calc_service/data:rw` |

`docker compose -f /opt/insain-agent/docker-compose.calc-only.yml ps -a`, **2026-10-25T07:18:48Z**: один сервис `calc-api`, контейнер `insain-calc-api`, статус `Up … (healthy)`, порты `127.0.0.1:8002->8001/tcp`.

`docker ps -a`, **2026-10-25T07:12:02Z** и снова **2026-10-25T07:17:22Z**: на хосте один контейнер, `insain-calc-api`.

Объявление порта в самом `docker-compose.calc-only.yml` (разбор ключей файла, **2026-10-25T07:18:48Z**): `"127.0.0.1:8002:8001"`. Комментарий в строке 1 этого файла: «VDS: только calc-api. Рабочий контейнер insain-calc-api создан этим файлом».

`/opt/insain-agent/docker-compose.yml` описывает локальный запуск `calc-api` и `tg-bot` (комментарий строки 1, **2026-10-25T07:18:48Z**). У `calc-api` в этом файле порт объявлен как `"8001:8001"`. Label работающего контейнера указывает на `docker-compose.calc-only.yml`.

Слушающие сокеты хоста, `ss -tln`, **2026-10-25T07:17:22Z**:

| Адрес | Порт | К снимку проекта |
| --- | --- | --- |
| `5.181.252.133` | 80, 443 | HTTP/HTTPS nginx |
| `127.0.0.1` | 8002 | API калькуляторов |
| `127.0.0.1` | 3306 | локальный MySQL (имена доступа — в `wp-config.php`) |
| `127.0.0.1` | 25, 9090 | прочие локальные сокеты, процесс по `ss -tln` не виден |
| `0.0.0.0` и `[::]` | 21, 22 | FTP и SSH |
| `*` | 9191 | прочий сокет, процесс не виден |
| `127.0.0.53`, `127.0.0.54` | 53 | локальный DNS |

Внутри контейнера процесс слушает `8001` (`ps -eo pid,cmd`, **2026-10-25T07:17:22Z**): `uvicorn main:app --host 0.0.0.0 --port 8001`.

## Образы

`docker images` **2026-10-25T07:12:02Z** и `docker image inspect` **2026-10-25T07:17:22Z**. Других образов на хосте нет.

| Тег | ID | Создан | Кто использует |
| --- | --- | --- | --- |
| `insain-agent-calc-api:latest` | `e8efca23463a` | 2026-10-25 09:49:02 +0300 | работающий `insain-calc-api` |
| `insain-agent-calc-api:deploy-2026-10-25` | `e8efca23463a` | 2026-10-25 09:49:02 +0300 | тот же образ, что `latest` |
| `insain-agent-calc-api:rollback` | `c71450a10e57` | 2026-05-01 22:21:25 +0300 | контейнер с этим ID не запущен |

Полный ID rollback: `sha256:c71450a10e57c484ababf7609fca10bc287ffc6cdcf813d85ce5b58149d0b712`.

Образ `latest` создан 2026-10-25 09:49:02 +0300, коммит HEAD — 2026-10-25 14:18:07 +0800 (06:18Z). Образ новее этого коммита (06:49Z), контейнер создан в 06:50Z.

## WordPress

| Факт | Значение | Команда | Время |
| --- | --- | --- | --- |
| Версия ядра | 6.9.5 | `sudo -u www-data wp core version --path=/var/www/insain.ru` | 2026-10-25T07:12:02Z и 2026-10-25T07:17:22Z |
| PHP, которым выполняется wp-cli | 8.2.30 | `sudo -u www-data wp eval 'echo PHP_VERSION;' --path=/var/www/insain.ru` | 2026-10-25T07:17:22Z |

### insain-calc-bridge

`sudo -u www-data wp plugin get insain-calc-bridge --field=version --path=/var/www/insain.ru` — **0.2.3** (**2026-10-25T07:12:02Z** и **2026-10-25T07:17:22Z**).

`sudo -u www-data wp plugin status insain-calc-bridge --path=/var/www/insain.ru`, **2026-10-25T07:12:02Z**: имя Insain Calc Bridge, статус Active, версия 0.2.3, автор Insain. Описание: мост ez Form Calculator и Python calc_service (методы `insaincalc.calcApi`, `showResult`, `showError`, `syncUrl`).

### Активные плагины

`sudo -u www-data wp plugin list --path=/var/www/insain.ru --status=active --fields=name,status,version,update`, **2026-10-25T07:12:02Z**. 29 активных. Колонка `update` — как её вернул wp-cli.

| name | version | update |
| --- | --- | --- |
| advanced-custom-fields | 6.8.0 | available |
| akismet | 5.7 | available |
| cookie-notice | 3.0.2 | available |
| contact-form-7 | 6.1.5 | unavailable |
| cyr2lat | 6.7.0 | available |
| easy-woocommerce-auto-sku-generator | 1.3.1 | available |
| ez-form-calculator-premium | 2.14.0.2 | none |
| imagerecycle-pdf-image-compression | 3.1.18 | none |
| insain-calc-bridge | 0.2.3 | none |
| insainParse | (пусто) | none |
| jetpack | 15.7.1 | unavailable |
| litespeed-cache | 7.8.1 | available |
| mihdan-disable-aggressive-updates-master | 1.0 | none |
| porto-functionality | 3.8.5 | none |
| simple-google-recaptcha | 3.9 | none |
| user-role-editor | 4.64.6 | available |
| woocommerce | 10.7.0 | unavailable |
| wc-dynamic-pricing-and-discounts | 2.5 | none |
| js_composer | 8.7.2 | available |
| wp-media-folder | 6.2.2 | available |
| wp-media-folder-addon | 4.1.5 | available |
| wp-media-folder-gallery-addon | 2.6.13 | available |
| wt_geotargeting_pro | 1.7.6 | none |
| counter-yandex-metrica | 1.4.3 | none |
| yith-woocommerce-ajax-navigation | 5.19.0 | available |
| yith-woocommerce-ajax-search | 2.23.0 | available |
| duplicate-post | 4.6 | unavailable |
| wordpress-seo | 27.5 | available |
| tinkoff-woocommerce | 2.2.0 | none |

Та же команда печатает PHP warning: `Wt::__wakeup()` в `/var/www/insain.ru/wp-content/plugins/wt_geotargeting_pro/includes/WtKit.php`, строка 36.

## Бот

Бот на VDS не запущен. Это и есть текущая консервация: на проде поднят только calc-api.

Проверено **2026-10-25T07:17:22Z**:

| Команда | Результат |
| --- | --- |
| `docker ps -a` | контейнера бота нет, есть только `insain-calc-api` |
| `docker ps -a --filter name=insain-tg-bot` | пусто |
| `ps -eo pid,cmd` (фильтр `bot.py`, `aiogram`, `insain-tg`, `uvicorn`, `telegram`) | единственное совпадение — uvicorn калькулятора |
| `systemctl list-units --all --type=service` (фильтр `insain`, `telegram`, `tg-bot`) | совпадений нет |
| `docker images` | образа бота нет |

`docker-compose.calc-only.yml` содержит один сервис, `calc-api` (разбор файла, **2026-10-25T07:18:48Z**). Комментарий строки 1: «VDS: только calc-api».

`docker-compose.yml` описывает сервис `tg-bot`: `container_name insain-tg-bot`, сборка `./bot_service`, `env_file: .env`, переменная `CALC_API_URL` задана в файле литералом (значение не копировалось), volume `./logs`, `restart always`. Этот compose работающий контейнер не создавал.

Слова «консервация» в комментариях обоих compose-файлов нет (`grep -n '^#'`, **2026-10-25**, сразу после 07:18:48Z).

## Секреты

Только расположение и имена. Значения не снимались и сюда не входят.

### WordPress

Файл `/var/www/insain.ru/wp-config.php`, `ls -l`: `-rw-r--r-- www-data www-data`, дата файла May 1 18:31. Имена констант, `grep -oE "define\(\s*'[A-Z0-9_]+'"`, **2026-10-25T07:17:22Z**:

`WP_CACHE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_CHARSET`, `DB_COLLATE`, `AUTH_KEY`, `SECURE_AUTH_KEY`, `LOGGED_IN_KEY`, `NONCE_KEY`, `AUTH_SALT`, `SECURE_AUTH_SALT`, `LOGGED_IN_SALT`, `NONCE_SALT`, `WP_DEBUG`, `WP_DEBUG_LOG`, `WP_DEBUG_DISPLAY`, `FS_METHOD`, `WP_MEMORY_LIMIT`, `ABSPATH`.

Вариант с двойными кавычками в `define` не найден (тот же `grep`, код возврата 1).

### TLS

Пути из `/etc/nginx/sites-enabled/insain.ru`, **2026-10-25T07:17:22Z**:

| Что | Путь |
| --- | --- |
| Сертификат insain.ru | `/etc/letsencrypt/live/insain.ru/fullchain.pem` |
| Ключ insain.ru | `/etc/letsencrypt/live/insain.ru/privkey.pem` |
| Сертификат test.insain.ru | `/etc/letsencrypt/live/test.insain.ru/fullchain.pem` |
| Ключ test.insain.ru | `/etc/letsencrypt/live/test.insain.ru/privkey.pem` |

### Бот и `.env`

`ls -l /opt/insain-agent/.env`, **2026-10-25T07:11:50Z**: файла нет. Каталог `/opt/insain-agent` в **2026-10-25T07:17:22Z** содержит `.env.example` и не содержит `.env`.

Обход `/opt/insain-agent` и `/home/agent` (глубина до 3, имена `.env`, `.env.*`, `*.env`, `credentials.json`, `wp-config.php`), **2026-10-25T07:17:22Z**: найден только `/opt/insain-agent/.env.example`.

Имена переменных в примере, `grep -oE '^[A-Za-z_][A-Za-z0-9_]*' /opt/insain-agent/.env.example`, **2026-10-25T07:18:48Z**: одно имя, `TELEGRAM_TOKEN`.

В `docker-compose.yml` у сервиса `tg-bot` указан `env_file: .env` (разбор ключей, **2026-10-25T07:17:22Z**). Комментарий этого файла: для бота нужен `.env` в корне репозитория.

### Окружение контейнера API

`docker inspect insain-calc-api`, из `Config.Env` записаны только имена, **2026-10-25T07:17:22Z**.

Имя проекта: `SITE_URL`. В `docker-compose.calc-only.yml` оно задано литералом у сервиса `calc-api` (значение в файл не копировалось; отдельно проверенное значение в контейнере — публичный адрес `https://insain.ru`, см. раздел адресов).

Остальные имена пришли из базового образа Python и в `docker image inspect insain-agent-calc-api:latest` совпадают (**2026-10-25T07:18:48Z**): `PATH`, `LANG`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`. `SITE_URL` в env образа нет, оно задаётся при запуске.

## Известный хвост: `stash@{0}`

`git -c safe.directory=/opt/insain-agent -C /opt/insain-agent stash list`, **2026-10-25T07:17:22Z**:

`stash@{0}: On feature/agent-logic: task-0.5-prod-tree-before-main`

| Факт | Значение | Команда |
| --- | --- | --- |
| Хеш | `fdbe29f4ee6e775b5bc17fd55b13fb31b7f9b7dd` | `rev-parse stash@{0}` |
| Дата | 2026-10-25 09:48:25 +0300 | `log -1 --format=%ci stash@{0}` |

`stash show --stat stash@{0}`, то же время:

```
 calc_service/data/materials/puzzle.json | 14 ++++++-------
 docker-compose.calc-only.yml            | 36 +++++++++++++++++++++++++++++++++
 infra/compose.vds.yml                   | 13 ++++++------
 infra/deploy.sh                         | 20 +++++++++---------
 4 files changed, 59 insertions(+), 24 deletions(-)
```

Stash не применялся. `status -sb` в тот же момент показывает чистый `main`, совпадающий с `origin/main`.
