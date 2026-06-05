# Новый VDS: создание, настройка, перенос WordPress и Docker (insain-agent)

Инструкция для сценария: **отдельный сервер** с **Debian 12** (или Ubuntu LTS), на нём **сайт на WordPress** и **Docker** с сервисами калькуляторов и Telegram-бота из этого репозитория.

**Архитектура (вариант B — полностью ручной nginx):**

```text
Интернет → nginx (наши конфиги)
               ├─ test.insain.ru / insain.ru → PHP-FPM → WordPress
               └─ /api/                      → proxy_pass → Docker calc-api 127.0.0.1:8002
           Docker tg-bot → outbound → Telegram
```

- **nginx → PHP-FPM** напрямую (без Apache). Apache отключён.
- Автоконфиг панели NetAngels (`vm-*.na4u.ru.conf`) **отключён** — nginx-конфигами управляем вручную.
- Панель [NetAngels](https://panel.netangels.ru) используется **только для DNS** и управления VDS (старт/стоп/бэкапы).
- Эталонные конфиги nginx хранятся в `**infra/`** репозитория ([nginx-wp.conf](../infra/nginx-wp.conf), [nginx.conf](../infra/nginx.conf)) для воспроизводимости и управления ИИ-агентом.
- `.htaccess` **не работает** с nginx — все правила (ЧПУ, редиректы) задаются в конфиге nginx.

**Предположения:**

- Хостинг — VDS на **[NetAngels](https://panel.netangels.ru)** (Debian 12 с предустановленным nginx/Apache/PHP; Apache отключаем в п. 3.0).
- Домен сайта, например `insain.ru`, DNS можно менять.
- Для тестового API калькуляторов используется путь `test.insain.ru/api/`; отдельный субдомен `calc.insain.ru` можно добавить позже (как в [ROADMAP.md](../ROADMAP.md)).
- Старый сервер доступен по SSH для снятия бэкапов.
- В перспективе ИИ-агент получит SSH-доступ к серверу для управления сайтом, nginx, Docker и wp-cli (п. 8.7).

**База данных WordPress и MySQL**

Сайт на WordPress использует **реляционную базу MySQL**: в `wp-config.php` задаются `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`; драйвер в PHP — **mysqli** / расширение `php-mysql`.

На **новом сервере** нужен **сервер БД, совместимый с MySQL** (тот же протокол и SQL для типовых запросов WP):

- В **Debian/Ubuntu** из официальных репозиториев обычно ставят **MariaDB** (`mariadb-server`) — для WordPress, для `mysql` / `mysqldump` и для импорта дампа с хостинга с «классическим» MySQL это **нормальная и распространённая схема**.
- Если принципиально нужен **Oracle MySQL Server**, его ставят из [официального репозитория MySQL](https://dev.mysql.com/doc/mysql-apt-repo-quick-guide/en/) (команды в шагах 3.1–3.2, 4.3, 5.2 те же: клиент называется `mysql`, дамп — `mysqldump`). Служба тогда часто `mysql`, а не `mariadb`.

Дамп базы со старого сервера (**mysqldump** или экспорт из панели в формате `.sql`) переносится в новую БД без смены движка WordPress — меняются только учётные данные и хост в `wp-config.php`.

---

## Часть 1. Заказ и первый вход

### 1.1. Выбор тарифа и образа (NetAngels и аналоги)

1. Возьми тариф с **запасом по диску и RAM** (WordPress + MySQL + Docker + образы и логи). Ориентир: **от 8 ГБ RAM**, **от 30 ГБ NVMe** — см. обсуждение в ROADMAP.
2. ОС: **Debian 12** с выбором PHP (готовая сборка хостера нормальна).
3. Запомни **публичный IP** нового сервера (панель хостинга или `curl -4 ifconfig.me` после входа).

### 1.2. DNS до миграции (рекомендация)

Пока сайт на старом сервере, **не спеши** переключать A-запись основного домена на новый IP.

Записи DNS для доменов на NetAngels обычно правятся в **[панели NetAngels](https://panel.netangels.ru)** в разделе, связанном с **доменом** и **DNS-зоной** (редактор записей A/CNAME и т.д.). Если домен делегирован на сторонние NS, правки делай там, где сейчас обслуживается зона.

Для проверки нового сервера можно:

- временно добавить запись `**test.ДОМЕН`** → **новый IP** (подробно: п. 5.4), или  
- на своём ПК править файл `hosts` (Windows: `C:\Windows\System32\drivers\etc\hosts`): строка `НОВЫЙ_IP insain.ru www.insain.ru` — только для своего компьютера.

### 1.3. Вход по SSH

С Windows (PowerShell):

```text
ssh root@НОВЫЙ_IP
```

или пользователь, который выдал хостер. При первом подключении подтверди fingerprint (`yes`), введи пароль или используй ключ:

```text
ssh -i путь\к\ключу.pem root@НОВЫЙ_IP
```

Убедись, что видишь приглашение shell на Linux.

### 1.4. Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

Если заходишь как не-root, везде ниже при необходимости добавляй `sudo`.

---

## Часть 2. Базовая безопасность и firewall

### 2.1. Пользователь с sudo (если работаешь только от root — шаг можно отложить)

На небольшом сервере часто оставляют `root` + ключ; для продакшена удобен отдельный пользователь.

### 2.2. UFW (простой firewall)

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

**Важно:** порт **8001** для API калькуляторов **не открывай** наружу: доступ к API будет через **nginx** на 443 (см. [infra/nginx.conf](../infra/nginx.conf)).

---

## Часть 3. Стек под WordPress (nginx + PHP-FPM + сервер MySQL)

Ниже — типичная схема для **Debian 12**. Версии пакетов могут отличаться; главное — **PHP не ниже**, чем на старом сайте (проверь на старом сервере: `php -v` или панель).

### 3.0. Отключение Apache и автоконфига панели NetAngels

На VDS NetAngels по умолчанию работает связка **nginx → Apache → PHP**. Панель автоматически генерирует конфиг `vm-*.na4u.ru.conf`, в котором nginx проксирует запросы в Apache на `127.0.0.1:80`. Для варианта B (nginx → PHP-FPM напрямую) нужно это отключить.

#### 3.0.1. Остановить и отключить Apache

```bash
sudo systemctl stop apache2
sudo systemctl disable apache2
```

Проверка — Apache не должен слушать порт:

```bash
sudo ss -tlnp | grep apache
```

Если вывод пустой — Apache остановлен.

#### 3.0.2. Удалить автосгенерированный конфиг nginx

```bash
sudo rm /etc/nginx/sites-enabled/vm-*.na4u.ru.conf
```

Файл в `sites-available` можно оставить как справку; главное — убрать **симлинк** из `sites-enabled`.

#### 3.0.3. Узнать публичный IP для директивы `listen`

На VDS NetAngels nginx привязан к **конкретному IP** (а не к `0.0.0.0`). IP обычно записан в автоконфиге:

```bash
cat /etc/nginx/listen.conf
```

Пример вывода:

```text
listen 185.41.161.31:80;
```

**Запомни этот IP** — его нужно подставить во **все** наши `server`-блоки nginx. Если `listen.conf` нет или он пустой — используй `curl -4 ifconfig.me` для определения публичного IP.

#### 3.0.4. Перезагрузить nginx

```bash
sudo nginx -t && sudo systemctl reload nginx
```

После этого nginx работает **без** Apache и **без** автоконфига панели. Все `server`-блоки будем писать вручную.

### 3.1. Установка пакетов

Ставим **MariaDB** как сервер БД, совместимый с MySQL (WordPress подключается как к обычной MySQL):

```bash
sudo apt install -y nginx mariadb-server \
  php-fpm php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl
```

Пакет `**php-mysql**` даёт расширения для доступа WordPress к базе по протоколу MySQL.

Проверка версий и служб:

```bash
php -v
sudo systemctl status nginx php*-fpm mariadb
```

Если вместо MariaDB установлен **MySQL Server** от Oracle, в последней команде проверяй службу `**mysql`** (и при необходимости исправь имя в выводе `systemctl`).

Имя сокета FPM может быть вроде `php8.2-fpm` — подставь свою версию в конфиге nginx.

### 3.2. Создание базы и пользователя MySQL для WordPress

Клиент командной строки называется `**mysql`** (при сервере MariaDB или MySQL):

```bash
sudo mysql -u root
```

В консоли **mysql** (интерактивный клиент к твоему серверу БД):

```sql
CREATE DATABASE insain CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY 'PVKPqTXLijsA34w';
GRANT ALL PRIVILEGES ON insain.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Имя БД и пользователя можно другие; пароль сохрани в менеджере паролей.

### 3.3. Каталог сайта

Пример корня сайта:

```bash
sudo mkdir -p /var/www/insain.ru
sudo chown -R www-data:www-data /var/www/insain.ru
```

Сюда позже распакуешь файлы WordPress.

### 3.4. Виртуальный хост nginx

#### Имя файла

Обычно конфиг называют **по домену**, чтобы было понятно, что внутри:

- `**/etc/nginx/sites-available/insain.ru`** — нормальный вариант для сайта `insain.ru`.

Расширение `.conf` тоже допустимо: `insain.ru.conf` — как принято на твоём сервере, лишь бы имя было латиницей без пробелов.

#### Как создать файл

Каталог `/etc/nginx/` доступен **root**. Варианты:

1. **Через редактор** (проще всего):
  ```bash
   sudo nano /etc/nginx/sites-available/insain.ru
  ```
   Вставь текст конфига из блока ниже, сохрани: в nano **Ctrl+O**, Enter, **Ctrl+X**.
2. **Через `tee`** (если копируешь с другого компьютера):
  ```bash
   sudo tee /etc/nginx/sites-available/insain.ru > /dev/null <<'EOF'
   …содержимое…
   EOF
  ```

#### Сокет PHP-FPM: что куда подставлять

Nginx передаёт PHP-запросы в **php-fpm** через **Unix-сокет** — это файл вида `php8.x-fpm.sock` в каталоге `**/run/php/`** (на части систем то же самое видно в `/var/run/php/`).

1. На сервере выполни:
  ```bash
   ls -la /run/php/
  ```
2. В списке найди файл, в имени которого есть `**fpm**` и `**.sock**`, например:
  - `php8.2-fpm.sock`
  - `php8.3-fpm.sock`
3. В конфиге nginx в директиве `**fastcgi_pass**` должна быть **ровно эта строка** (одна строка, без переноса):
  - если в `ls` видишь `**php8.3-fpm.sock`**, пиши:
  - если видишь `**php8.2-fpm.sock`** — оставь как в примере ниже с `php8.2`.

То есть **заменить** нужно только **номер версии и имя файла** в пути после `unix:/run/php/` так, чтобы они **совпадали** с тем, что показал `ls`. Если каталог `/run/php/` пустой — служба **php-fpm** не запущена или пакет не установлен: `sudo systemctl status php8.2-fpm` (подставь свою версию из `dpkg -l | grep php-fpm`).

#### Текст конфига

Создай файл `**/etc/nginx/sites-available/insain.ru`** с таким содержимым. **Подставь:**

- в `**listen`** — публичный IP из п. 3.0.3 (например `185.41.161.31`);
- в `**fastcgi_pass`** — свой `.sock` из `ls /run/php/`.

Эталонный конфиг хранится в репозитории: [infra/nginx-wp.conf](../infra/nginx-wp.conf).

```nginx
server {
    listen ПУБЛИЧНЫЙ_IP:80;
    server_name insain.ru www.insain.ru;
    root /var/www/insain.ru;
    index index.php;

    access_log /var/log/nginx/insain.ru.access.log;
    error_log  /var/log/nginx/insain.ru.error.log;

    client_max_body_size 64m;
    fastcgi_buffer_size 64k;
    fastcgi_buffers 16 64k;
    fastcgi_busy_buffers_size 128k;

    # ЧПУ WordPress (замена .htaccess RewriteRule)
    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
    }

    # Запрет доступа к .htaccess и другим скрытым файлам
    location ~ /\. {
        deny all;
    }
}
```

Пример: при файле `**php8.3-fpm.sock**` строка должна быть `**fastcgi_pass unix:/run/php/php8.3-fpm.sock;**`.

`fastcgi_buffer_*` нужен, если WordPress или плагины отдают крупные HTTP-заголовки. В текущей миграции 502 вызывал большой `Set-Cookie: wt_geo_data=...` от геотаргетинга: плагин сохранял в cookie полный JSON-ответ DaData с адресными полями, поэтому стандартного буфера nginx не хватало.

#### `.htaccess` не работает с nginx

nginx **не обрабатывает** файлы `.htaccess` — это механизм Apache. Правила WordPress для ЧПУ (красивых URL) уже покрыты блоком `try_files` выше. Если в `.htaccess` на старом сервере были **дополнительные** правила (редиректы HTTP→HTTPS, блокировка IP, защита wp-admin и т.п.), их нужно перенести в конфиг nginx вручную. Типичные примеры:

```nginx
# Редирект HTTP → HTTPS (добавится автоматически при запуске certbot)
# Если нужно вручную:
# if ($scheme = http) { return 301 https://$host$request_uri; }

# Защита wp-admin по IP (пример):
# location /wp-admin {
#     allow 1.2.3.4;
#     deny all;
#     try_files $uri $uri/ /index.php?$args;
# }
```

Файл `.htaccess` в каталоге WordPress можно оставить (он просто не читается nginx), но **полагаться на него нельзя**.

#### Включить сайт и перезагрузить nginx

```bash
sudo ln -sf /etc/nginx/sites-available/insain.ru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Пока файлов WP нет — при открытии по IP или тестовому имени может быть 403/404 — это нормально до заливки сайта.

---

## Часть 4. Бэкап на старом сервере

Делай **до** любых разрушительных действий.

### 4.1. Найти корень WordPress

На старом сервере:

```bash
# пример: посмотреть root в конфиге nginx
grep -R root /etc/nginx/sites-enabled/
```

Обычно на классических VDS-панелях это путь вида `/home/web/<домен>/www`.

Для старого сайта `insain.ru`:

```bash
/home/web/vm-2d6b099b.na4u.ru/www
```

Быстрая проверка, что это действительно корень WordPress:

```bash
ls -la /home/web/vm-2d6b099b.na4u.ru/www
# должны быть wp-admin, wp-content, wp-includes, wp-config.php, index.php
```

### 4.2. Архив файлов

```bash
cd /home/web/vm-2d6b099b.na4u.ru
sudo tar czvf /root/wp-files-backup.tar.gz www
```

Скопируй архив на новый сервер (`scp`, SFTP, панель файлов):

```bash
# с твоего ПК или со старого сервера на новый
scp root@СТАРЫЙ_IP:/root/wp-files-backup.tar.gz .
scp wp-files-backup.tar.gz root@НОВЫЙ_IP:/root/
```

### 4.3. Дамп базы MySQL

На старом сервере узнай из `wp-config.php`: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`.

Для текущего сайта:

```php
define( 'DB_NAME', 'insain' );

/** Имя пользователя MySQL */
define( 'DB_USER', 'root' );

/** Пароль к базе данных MySQL */
define( 'DB_PASSWORD', 'PVKPqTXLijsA34w' );

/** Имя сервера MySQL */
define( 'DB_HOST', 'localhost' );
```

Если база на **том же сервере**, что и сайт (`DB_HOST` = `localhost` или `127.0.0.1`), дамп с хоста:

```bash
mysqldump -u DB_USER -p DB_NAME > /root/wp-db.sql
```

Если на хостинге указан **удалённый** `DB_HOST` (отдельный сервер БД), дамп делается **на той машине, где крутится MySQL**, или через панель хостинга («Экспорт», phpMyAdmin и т.п.) — важно получить полный **SQL-дамп** той же базы, что в `wp-config.php`.

Скопируй `wp-db.sql` на новый VDS.

```bash
scp /root/wp-db.sql root@НОВЫЙ_IP:/root/
```

### 4.4. Альтернатива — плагин Duplicator / All-in-One WP Migration

Можно собрать пакет через плагин и развернуть на новом сервере по инструкции плагина; тогда шаги 4.2–4.3 частично заменяются.

---

## Часть 5. Восстановление WordPress на новом сервере

Важно: в части 5 используется путь **нового VDS** (`/var/www/insain.ru`).
Путь **старого сайта** для бэкапа — `/home/web/vm-2d6b099b.na4u.ru/www` (см. часть 4).

### 5.1. Распаковка файлов

```bash
sudo mkdir -p /var/www/insain.ru
cd /var/www
# архив содержит верхний каталог www/
sudo tar xzvf /root/wp-files-backup.tar.gz
# переносим содержимое www/ в целевой корень сайта
sudo rsync -a /var/www/www/ /var/www/insain.ru/
sudo chown -R www-data:www-data /var/www/insain.ru
find /var/www/insain.ru -type d -exec chmod 755 {} \;
find /var/www/insain.ru -type f -exec chmod 644 {} \;
```

### 5.2. Импорт дампа MySQL

Импорт в пустую базу на новом сервере (имя БД и пользователь — как в шаге 3.2):

```bash
sudo mariadb -u wpuser -p insain < /root/wp-db.sql
```

Либо от root MySQL/MariaDB: `sudo mariadb -u root` и затем `SOURCE /root/wp-db.sql` после `USE wordpress;` — по ситуации.

(Подставь своего пользователя и имя БД из шага 3.2.)

### 5.3. wp-config.php

Отредактируй `/var/www/insain.ru/wp-config.php`:

- `**DB_NAME**`, `**DB_USER**`, `**DB_PASSWORD**`, `**DB_HOST**` — данные **новой** MySQL-базы на VDS (обычно `DB_HOST` = `localhost` или `127.0.0.1`, если MySQL/MariaDB на том же сервере, что и WordPress).
- При смене домена иногда добавляют строки для принудительного HTTPS — делай по необходимости после выпуска сертификата.

### 5.4. Тестовый поддомен и URL в базе MySQL

**Зачем это нужно.** После копии файлов и импорта БД WordPress на **новом** VDS всё ещё «думает», что его адрес — **старый** боевой URL (например `https://insain.ru`). Если открыть новый сервер по IP, браузер часто улетает редиректом на старый домен. Поддомен вида `**test.insain.ru`** решает задачу так:


| Что                | Куда смотрит DNS         | Кто видит сайт                                     |
| ------------------ | ------------------------ | -------------------------------------------------- |
| `insain.ru`, `www` | **старый IP** (как было) | посетители, поисковики — **без изменений**         |
| `test.insain.ru`   | **новый IP** VDS         | ты и команда — **копия** для проверки и обновлений |


Ниже — по шагам: DNS → nginx → правка URL в базе. Подставь свой домен вместо `**insain.ru`**, свой поддомен вместо `**test.insain.ru`**, если хочешь другое имя (`staging.…`, `new.…` — логика та же).

---

#### Шаг A. DNS: запись на новый сервер

1. Узнай **публичный IP нового VDS** (карточка VDS в [панели NetAngels](https://panel.netangels.ru) или `curl -4 ifconfig.me` на новом сервере).
2. Зайди в **редактор DNS-зоны** домена. На NetAngels — через [панель](https://panel.netangels.ru), раздел домена / DNS (имя пункта может называться «Зона DNS», «Управление DNS», «Ресурсные записи» и т.п.). Если зона не на NetAngels — панель регистратора или Cloudflare.
3. Добавь запись типа **A**:
  - **Имя / Host / Subdomain:** в большинстве панелей достаточно `**test`** — получится полное имя `**test.insain.ru`**. В некоторых нужно ввести полностью `**test.insain.ru**` или `**test.insain.ru.**` — смотри подсказку панели.
  - **Значение / Points to:** IP **нового** VDS.
  - **TTL:** по возможности поставь **меньше** (300 с, 600 с) на время отладки, чтобы правки DNS быстрее доходили.
4. **Прокси (если используешь Cloudflare «оранжевое облако»):** для первой отладки можно выключить прокси (только DNS), чтобы не путаться с кэшем и сертификатами. Через NetAngels без Cloudflare этот пункт не нужен.
5. Подожди **распространения** (от нескольких минут до часа). Проверка с **своего ПК**:
  ```bash
   dig +short test.insain.ru
  ```
   или `nslookup test.insain.ru` — в ответе должен быть **новый** IP.

Пока эта запись не «видится» с твоего компьютера, браузер не попадёт на новый nginx по имени — сначала доведи DNS, потом проверяй сайт.

---

#### Шаг B. Nginx: добавить тестовое имя

Поскольку Apache и автоконфиг панели отключены (п. 3.0), на сервере работает **один** наш `server`-блок из п. 3.4.

1. Открой конфиг сайта:
  ```bash
   sudo nano /etc/nginx/sites-available/insain.ru
  ```
2. В строке `**server_name**` добавь тестовое имя **через пробел**:
  ```nginx
   server_name insain.ru www.insain.ru test.insain.ru;
  ```
3. Проверь и перезагрузи:
  ```bash
   sudo nginx -t && sudo systemctl reload nginx
  ```
4. Проверка в браузере: `**http://test.insain.ru**` — должна открыться главная (или редирект на старый URL — тогда переходи к шагу C).

---

#### Шаг C. Замена URL во всей базе WordPress (wp-cli)

WordPress хранит URL в **тысячах** мест БД: `siteurl` / `home` в `wp_options`, содержимое страниц (`wp_posts`), настройки темы и виджетов (сериализованные массивы в `wp_options`, `wp_postmeta` и др.). Простой SQL `REPLACE` **ломает сериализованные данные** (длины строк не пересчитываются → «критическая ошибка», пропадают настройки темы). Поэтому используем **wp-cli** — он корректно обрабатывает сериализацию.

##### Установка wp-cli

```bash
cd /tmp
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp
wp --info
```

##### Проверка MySQL-модулей PHP для wp-cli

Если `wp-cli` падает с ошибкой вида `Call to undefined function mysql_connect()`, установи MySQL-модули для PHP CLI и проверь, что они загрузились:

```bash
sudo apt update
sudo apt install -y php8.0-mysql
php -m | grep -E "mysqli|mysqlnd|pdo_mysql"
```

##### Бэкап перед заменой

```bash
sudo mysqldump -u root insain > /root/wp-db-before-replace.sql
```

(подставь имя БД.)

##### Замена URL

Сначала **dry-run** (показывает сколько замен будет, без изменений):

```bash
cd /var/www/insain.ru
sudo -u www-data wp search-replace 'https://insain.ru' 'http://test.insain.ru' --all-tables --skip-plugins --skip-themes --dry-run
```

Если dry-run прошёл без ошибок — запускай без `--dry-run`:

```bash
sudo -u www-data wp search-replace 'https://insain.ru' 'http://test.insain.ru' --all-tables --skip-plugins --skip-themes
```

Флаги `--skip-plugins --skip-themes` обходят загрузку плагинов/темы (на старом сайте бывают несовместимости с wp-cli). Если и так ошибка — см. фоллбэк ниже.

##### Фиксация URL через `wp-config.php` (рекомендуется на время теста)

Добавь в `wp-config.php` **перед** строкой `/* That's all, stop editing! */`:

```php
define('WP_HOME',    'http://test.insain.ru');
define('WP_SITEURL', 'http://test.insain.ru');
```

Эти константы перекрывают БД и гарантируют правильный URL даже если в `wp_options` что-то не так.

##### Проверка

Открой `http://test.insain.ru` в **режиме инкогнито** (Ctrl+Shift+N). Верстка, стили, картинки должны грузиться. Если что-то ещё ссылается на старый домен — проверь в DevTools (F12 → Console / Network) и при необходимости прогони `wp search-replace` ещё раз с другим паттерном (например `http://insain.ru` без `s`).

##### Фоллбэк: SQL-замена (если wp-cli не работает)

**Внимание:** SQL `REPLACE` **не** обрабатывает сериализованные данные. Используй только если wp-cli не запускается.

```bash
sudo mariadb -u root wordpress -e "
UPDATE wp_options SET option_value = REPLACE(option_value, 'https://insain.ru', 'http://test.insain.ru') WHERE option_value LIKE '%insain.ru%';
UPDATE wp_posts SET post_content = REPLACE(post_content, 'https://insain.ru', 'http://test.insain.ru');
UPDATE wp_posts SET guid = REPLACE(guid, 'https://insain.ru', 'http://test.insain.ru');
UPDATE wp_postmeta SET meta_value = REPLACE(meta_value, 'https://insain.ru', 'http://test.insain.ru') WHERE meta_value LIKE '%insain.ru%';
"
```

Подставь свой префикс таблиц (проверь: `grep table_prefix /var/www/insain.ru/wp-config.php`). После SQL-замены зайди в wp-admin и **пересохрани** настройки темы и виджетов, чтобы восстановить сериализацию. Или установи плагин **Better Search Replace** и прогони замену через него.

---

#### Перед переключением основного домена (часть 7)

Когда тесты и обновления (п. 5.5–5.6) закончены:

1. **Бэкап БД** на новом сервере.
2. Обратная замена URL через wp-cli:
  ```bash
   cd /var/www/insain.ru
   sudo -u www-data wp search-replace 'http://test.insain.ru' 'https://insain.ru' --all-tables --skip-plugins --skip-themes
  ```
3. Убери или замени `**WP_HOME` / `WP_SITEURL**` в `wp-config.php`:
  ```php
   define('WP_HOME',    'https://insain.ru');
   define('WP_SITEURL', 'https://insain.ru');
  ```
4. Переключай A-записи основного домена на новый IP (часть 7), затем HTTPS (часть 6).

---

#### Если поддомен не нужен: только `hosts` или IP

Можно не создавать DNS-запись и смотреть сайт только с одного компьютера (п. 1.2): строка в `hosts` вида `НОВЫЙ_IP insain.ru`. Тогда wp-cli search-replace не нужен (URL в БД и так `insain.ru`), но проверяешь только со своего ПК. Перед боевым DNS убери строку из `hosts`.

### 5.5. Долго не обновлялись: ядро WordPress и плагины **до** переключения DNS

Если копия сайта давно без обновлений, **не переноси основной домен сразу**. Сначала доведи установку до актуального состояния **на новом VDS**, пока трафик идёт на старый сервер.

**Условие:** сайт открывается по **тестовому поддомену** из п. 5.4 (рекомендуется) или по `hosts` / IP — **без** переключения A-записи боевого домена на новый IP.

Рекомендуемый порядок:

1. **Снимок перед правками** на новом сервере: свежий дамп БД и при необходимости копия каталога WordPress — чтобы откатиться, если обновление что-то сломает.
2. **Версия PHP** на новом VDS не ниже требований текущей и целевой версии WordPress (`php -v`, при необходимости обнови пакеты PHP-FPM и перезапусти nginx).
3. **Обновление по слоям**:
  - сначала **ядро WordPress** и низкорисковые бесплатные плагины;
  - затем **тема Porto** из актуального `porto.zip`;
  - после обновления Porto — bundled-плагины темы (`Porto Functionality`, `WPBakery Page Builder`, при необходимости `Slider Revolution`) из пакета Porto или через `Appearance → Install Plugins` / механизм Porto;
  - только после этого **WooCommerce**, YITH/WooCommerce-плагины, платёжные и коммерческие расширения;
  - платные плагины, которые не обновляются через репозиторий WordPress, ставь из zip-архивов через `wp plugin install ... --force --activate`;
  - остальные плагины — пакетами с промежуточной проверкой.
4. **Проверка:** главная и типовые страницы, `/wp-admin`, критичные формы, оплата/заявки, интеграции (в т.ч. калькуляторы/виджеты, если есть). Исправь конфликты до переноса DNS.
5. Только после стабильной работы на тестовом доступе переходи к **переключению DNS** (часть 7) и **HTTPS для боевого имени** (часть 6). При необходимости HTTPS на тестовом поддомене — см. абзац про `test.ДОМЕН` в части 6 **до** смены A-записи основного домена.

Старый сервер до переключения DNS остаётся **боевым**; новый — песочница для миграции и обновлений.

### 5.5.1. Текущий baseline перед обновлением (WordPress 5.8.13 + плагины)

Перед массовыми обновлениями зафиксируй исходное состояние копии сайта на новом VDS.

- **Версия WordPress на момент переноса:** `5.8.13`.
- **Целевая среда:** PHP `8.2` (проверка совместимости обязательна до переключения DNS).

Матрица установленных плагинов и действий:


| Плагин                      | Версия   | Статус PHP 8.2        | Действие                                |
| --------------------------- | -------- | --------------------- | --------------------------------------- |
| Advanced Custom Fields      | 5.10.2   | ⚠️ Устарела           | Обновить до 6.x или перейти на ACF Free |
| Akismet                     | 4.1.12   | ⚠️ Устарела           | Обновить до 5.6                         |
| Contact Form 7              | 5.5.6.1  | ⚠️ Устарела           | Обновить                                |
| Cookie Notice               | 2.4.12   | 🔴 Не работает        | Обновить до 2.5.16+                     |
| Cyr-To-Lat                  | 6.6.0    | ✅                     | Оставить                                |
| Easy Auto SKU               | 1.3.1    | ⚠️ Проверить          | Протестировать                          |
| ez Form Calculator          | 2.14.0.2 | ⚠️ Устарела           | Обновить до 2.14.2.1                    |
| ImageRecycle                | 3.1.18   | ⚠️ Проверить          | Протестировать                          |
| InsainParser                | —        | ❓ Кастомный           | Тщательно проверить                     |
| Jetpack                     | 10.9.3   | 🔴 Остановлен         | Обновить                                |
| Jivo                        | 1.3.5.6  | ⚠️ Устарела           | Обновить до 1.3.6.1                     |
| LiteSpeed Cache             | 4.6      | 🔴 Уязвимость         | Обновить до 7.8.x                       |
| Porto Theme - Functionality | 2.2.0    | ⚠️ Требует обновления | Обновить                                |
| Simple Google reCAPTCHA     | 3.9      | ⚠️ Проверить          | Протестировать                          |
| Slider Revolution           | 6.2.1    | ⚠️ Требует обновления | Обновить                                |
| Social Slider Widget        | 1.9.2    | 🔴 Не работает        | Обновить до 2.3.3+                      |
| User Role Editor            | 4.62     | ⚠️ Устарела           | Обновить до 4.64.6                      |
| WooCommerce                 | 5.7.3    | 🔴 Очень устарела     | Обновить (осторожно!)                   |
| WooCommerce Dynamic Pricing | 2.3.9    | ⚠️ Устарела           | Обновить из zip до актуальной версии    |
| WooCommerce PayPal          | 2.0.3    | ⚠️ Неактивен          | Проверить/удалить                       |
| WP Media Folder             | 5.3.21   | ⚠️ Устарела           | Обновить из zip до актуальной версии    |
| WP Media Folder Addon       | 3.4.19   | ⚠️ Устарела           | Обновить из zip до актуальной версии    |
| WP Media Folder Gallery     | 2.3.2    | ⚠️ Устарела           | Обновить из zip до актуальной версии    |
| WPBakery Page Builder       | 6.7.0    | ⚠️ Устарела           | Обновить до 8.7.2                       |
| WT Geotargeting Pro         | 1.7.6    | ⚠️ Проверить          | Протестировать                          |
| YITH Ajax Search            | 1.24.0   | ✅                     | Оставить                                |
| YITH Ajax фильтр            | 4.15.0   | ✅                     | Оставить                                |
| Yoast Duplicate Post        | 4.5      | ⚠️ Проверить          | Протестировать                          |
| Yoast SEO                   | 19.4     | ⚠️ Устарела           | Обновить                                |
| Тинькофф Банк               | 2.2.0    | ⚠️ Проверить          | Обязательно протестировать платежи      |
| Яндекс.Метрика              | 1.4.3    | ⚠️ Проверить          | Протестировать                          |

#### Актуальный статус обновления на `test.insain.ru` (2026-05-01)

Выполнено:

1. Зафиксирован baseline через `wp-cli`:
   - WordPress был `5.8.13`, обновлён до `6.9.4`;
   - `siteurl` и `home`: `http://test.insain.ru`;
   - проверка БД: все таблицы `OK`;
   - PHP CLI/FPM: `8.2`, nginx: `1.22.1`.
2. Обновлено ядро WordPress и база:

```bash
wp core update --locale=ru_RU
wp core update-db
```

3. Обновлены низкорисковые плагины:
   - `akismet`;
   - `litespeed-cache`;
   - `instagram-slider-widget`;
   - `user-role-editor`.
4. После обновления ядра плагины, которые раньше показывали `unavailable`, стали доступны к обновлению: `advanced-custom-fields`, `contact-form-7`, `cyr2lat`, `jetpack`, `woocommerce`, `yith-*`, `duplicate-post`, `wordpress-seo` и др.
5. Попытка обновить `js_composer` отдельно через `wp-cli` не сработала:

```text
Warning: Пакет обновления недоступен.
Error: No plugins updated (1 failed).
js_composer 6.7.0 -> 8.7.2 Error
```

Причина: WPBakery установлен как bundled-плагин темы Porto. Его нужно обновлять **после обновления Porto** из пакета темы или через механизм темы (`Внешний вид → Установить плагины` / `Appearance → Install Plugins`).

6. Сделан промежуточный бэкап перед обновлением Porto/WooCommerce:
   - каталог: `/root/wp-mid-backup-2026-05-01-1525`;
   - дамп БД: `insain-db-2026-05-01-1525.sql` (`244M`);
   - архив файлов WordPress: `insain-files-2026-05-01-1525.tar.gz` (`1.5G`);
   - копии конфигов nginx и PHP-FPM.
7. Обновлена тема Porto из `porto.zip`:

```bash
cd /var/www/insain.ru
php8.2 -d display_errors=0 -d error_reporting=8191 /usr/local/bin/wp --allow-root theme install /root/porto.zip --force
```

   Итог: `porto 7.8.5`.
8. Из zip-архивов полного пакета Porto вручную обновлены bundled-плагины:
   - `porto-functionality 3.8.5`, активен;
   - `js_composer` / WPBakery `8.7.2`, активен;
   - `revslider 6.7.41`, неактивен, как и до обновления.
9. После обновления Porto была нарушена вёрстка WooCommerce-категорий из-за связки новый Porto + старый WooCommerce `5.7.3`; исправлено обновлением WooCommerce-блока:
   - `woocommerce 10.7.0`;
   - `yith-woocommerce-ajax-navigation 5.19.0`;
   - `yith-woocommerce-ajax-search 2.23.0`.
10. Перед обновлением коммерческих zip-плагинов сделан отдельный бэкап:
    - каталог: `/root/wp-paid-plugins-backup-2026-05-01-1953`;
    - дамп БД: `insain-db-2026-05-01-1953.sql`;
    - копии каталогов `wc-dynamic-pricing-and-discounts`, `wp-media-folder`, `wp-media-folder-addon`, `wp-media-folder-gallery-addon`.
11. Из zip-архивов `/root/plugin-updates/` обновлены коммерческие плагины:
    - `wc-dynamic-pricing-and-discounts 2.3.9 -> 2.5` (`2.5.1` всё ещё показывается как доступное обновление);
    - `wp-media-folder 5.3.21 -> 6.2.2`;
    - `wp-media-folder-addon 3.4.19 -> 4.1.5`;
    - `wp-media-folder-gallery-addon 2.3.2 -> 2.6.13` (`2.6.16` всё ещё показывается как доступное обновление).
12. После обновлений появился fatal в шаблоне Porto:

```text
Call to undefined function wc_wp_theme_get_element_class_name()
/wp-content/themes/porto/woocommerce/content-widget-price-filter.php:46
```

   Причина: шаблон фильтра цены Porto вызывал WooCommerce-функцию без проверки доступности. Временно исправлено в parent theme `Porto` через `function_exists()` в файле `wp-content/themes/porto/woocommerce/content-widget-price-filter.php`. Перед правкой сохранена копия:
   `/root/content-widget-price-filter-before-fix-2026-05-01-1739.php`.
   Важно: правка находится в parent theme и может быть перезаписана при следующем обновлении Porto.
13. Выполнена финальная проверка:
    - главная, категория услуг, каталог/товар и `wp-json` отвечали `200 OK`;
    - после правки фильтра цены свежих `Fatal error` не было;
    - визуальная проверка проблемных страниц прошла успешно;
    - `WP_DEBUG`, `WP_DEBUG_LOG`, `WP_DEBUG_DISPLAY` выключены в `wp-config.php`.

Осталось отдельно:

- `wc-dynamic-pricing-and-discounts` активен, обновлён из zip до `2.5`, но WordPress ещё показывает доступное обновление до `2.5.1`; нужен более свежий лицензионный zip-пакет.
- `wp-media-folder-gallery-addon` активен, обновлён из zip до `2.6.13`, но WordPress ещё показывает доступное обновление до `2.6.16`; нужен более свежий zip-пакет.
- `jivochat` неактивен, доступно обновление, можно не трогать до решения о включении.
- В cookie `wt_geo_data` сохраняется ответ DaData `Feature 'SUGGESTIONS' disabled for token`; это не ломает сайт после увеличения FastCGI buffers, но геотаргетинг нужно отдельно проверить по токену/тарифу DaData.
- В логах остаются нефатальные PHP 8.2 deprecated-предупреждения от отдельных плагинов (`wp-media-folder-gallery-addon`, `tinkoff-woocommerce`, `wt_geotargeting_pro`); исправлять отдельным этапом после проверки бизнес-функций.

Проверочные команды после таких обновлений:

```bash
curl -I http://test.insain.ru/
curl -I http://test.insain.ru/category/services/plotternaya-rezka/
curl -I http://test.insain.ru/catalog/plotternaya-rezka/
curl -I http://test.insain.ru/wp-json/
grep -i "fatal\|uncaught\|parse error" /var/www/insain.ru/wp-content/debug.log | tail -n 20
```


#### Минимальные PHP 8.2-правки, найденные при тестовом запуске

Если после переноса отдельные страницы дают `500 Internal Server Error`, внутри HTML появляется `WordPress › Ошибка` или ломается вёрстка, включи временный лог WordPress:

```php
define( 'WP_DEBUG', true );
define( 'WP_DEBUG_LOG', true );
define( 'WP_DEBUG_DISPLAY', false );
```

Проверка fatal-ошибок:

```bash
cd /var/www/insain.ru
grep -i "fatal\|uncaught\|parse error" wp-content/debug.log | tail -n 20
```

Найденные ручные правки для старых плагинов:

1. `porto-functionality/shortcodes/templates/porto_lightbox.php` — PHP 8.2 не поддерживает доступ к символу строки через фигурные скобки:

```php
$rand .= $valid_characters{$which_character};
```

заменить на:

```php
$rand .= $valid_characters[$which_character];
```

2. `ez-form-calculator-premium/class.ezfc_functions.php` — PHP 8 не поддерживает функцию `each()`. В `array_merge_recursive_distinct()` заменить:

```php
while (list($key, $value) = @each($array)) {
```

на:

```php
foreach ($array as $key => $value) {
```

После правок:

```bash
php8.2 -l /var/www/insain.ru/wp-content/plugins/porto-functionality/shortcodes/templates/porto_lightbox.php
php8.2 -l /var/www/insain.ru/wp-content/plugins/ez-form-calculator-premium/class.ezfc_functions.php
curl -I http://test.insain.ru/
curl -I http://test.insain.ru/catalog/plotternaya-rezka/
```

После диагностики верни `WP_DEBUG` в `false`. Эти ручные изменения — временный workaround для первого запуска на PHP 8.2; долгосрочно нужно обновить соответствующие плагины после бэкапа базы и `wp-content`.

Фактическая последовательность обновления для `test.insain.ru` зафиксирована выше в блоке «Актуальный статус обновления». Если обновление повторяется на другой копии, используй общий порядок из п. 5.5: бэкап → ядро WordPress → низкорисковые плагины → Porto → bundled-плагины Porto → WooCommerce/YITH/платёжные → коммерческие zip-плагины → остальные плагины пакетами с промежуточными проверками.

### 5.6. Финальная проверка до переключения DNS

- Открой сайт по **тестовому поддомену** (п. 5.4) или через `hosts` / IP — по HTTP/HTTPS, как настроено.
- Войди в `/wp-admin`, проверь главную, формы, загрузку медиа.
- Если выполнял п. 5.5 — убедись, что после обновлений всё ещё ок.

---

## Часть 6. HTTPS для основного сайта (Let’s Encrypt)

Выпускай сертификат, когда A-запись **основного домена** уже указывает на **новый** IP. Обычно это **после** проверок из п. 5.5–5.6:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d insain.ru -d www.insain.ru
```

**Тестовый поддомен (п. 5.4):** если DNS для `test.ДОМЕН` уже смотрит на новый VDS и в nginx есть этот `server_name`, можно **до** переключения боевого домена выпустить отдельный сертификат:  
`sudo certbot --nginx -d test.ДОМЕН` — затем в WordPress выставь `siteurl` / `home` на `https://test.ДОМЕН`.

Certbot настроит SSL и при желании редирект HTTP→HTTPS.

**Порядок с переносом:** финальная проверка на новом IP (п. 5.6; при устаревшем сайте — сначала обновления по п. 5.5), затем переключение DNS (часть 7), затем `certbot` для боевого имени.

---

## Часть 7. Переключение DNS

Переключай **основной** домен на новый IP, когда сайт на новом VDS уже проверен (п. 5.6), а при долгом простое обновлений — после п. 5.5.

1. За сутки (если возможно) уменьши **TTL** у A-записей.
2. В [панели NetAngels](https://panel.netangels.ru) (или там, где у тебя зона DNS): **A** для `insain.ru` и при необходимости для `www` → **новый IP** нового VDS.
3. Подожди распространения (от минут до пары часов).
4. Проверь с телефона без Wi‑Fi (другая сеть) или через онлайн-проверку DNS.
5. Выпусти/обнови сертификаты, если домен только что указывает на новый сервер.

Старый сервер не выключай сразу: оставь **1–2 недели** как резервную копию на случай отката.

---

## Часть 8. Docker и проект insain-agent на том же VDS

### 8.1. Установка Docker (Debian 12)

Официальная инструкция: [Install Docker Engine on Debian](https://docs.docker.com/engine/install/debian/).

Кратко: добавить репозиторий Docker, установить `docker-ce`, `docker-compose-plugin`, проверить:

```bash
sudo docker run --rm hello-world
docker compose version
```

Опционально, чтобы не использовать `sudo` для docker:

```bash
sudo usermod -aG docker $USER
# перелогинься
```

### 8.2. Клонирование репозитория

Каталог WordPress (`/var/www/insain.ru`) должен оставаться за `**www-data**`; репозиторий агента держи **отдельно**, например в `/opt/insain-agent`:

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/insain-integra/insain-agent.git insain-agent
cd insain-agent
sudo git fetch origin
sudo git checkout feature/agent-logic
sudo git pull --ff-only origin feature/agent-logic
```

Важно: на момент тестового развёртывания `docker-compose.yml` и `infra/compose.vds.yml` лежали в ветке `feature/agent-logic`, поэтому после clone нужно явно переключиться на неё.

### 8.3. Файл `.env`

```bash
cp .env.example .env
nano .env
```

Заполни как на локальной машине: `TELEGRAM_TOKEN`, ключи LLM и остальное (см. [.env.example](../.env.example)). Файл `.env` в git не коммитится.

Для запуска только `calc_service` файл `.env` не обязателен, если задаёшь `SITE_URL` прямо в compose override.

### 8.4. Развёртывание `calc_service` для prod `insain.ru`

На VDS API не должен открывать публичный порт. Для prod используется отдельный compose только для `calc_service`: контейнер слушает `8001` внутри Docker, а на хосте доступен только как `127.0.0.1:8002`. Наружу API отдаёт nginx по `https://insain.ru/api/`.

Создай файл `/opt/insain-agent/docker-compose.calc-only.yml`:

```bash
cd /opt/insain-agent

cat > docker-compose.calc-only.yml <<'EOF'
services:
  calc-api:
    build:
      context: ./calc_service
      dockerfile: Dockerfile
    container_name: insain-calc-api
    ports:
      - "127.0.0.1:8002:8001"
    volumes:
      - ./calc_service/data:/app/calc_service/data
    environment:
      SITE_URL: https://insain.ru
    restart: always
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/api/v1/calculators', timeout=5).read()",
        ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
EOF
```

Запусти сервис:

```bash
cd /opt/insain-agent
docker rm -f insain-calc-api || true
docker compose -f docker-compose.calc-only.yml up -d --build
```

Проверка **на сервере**:

```bash
docker ps -a | grep insain-calc-api
ss -tlnp | grep -E ':8001|:8002' || true
docker logs --tail=80 insain-calc-api
curl -sS http://127.0.0.1:8002/api/v1/calculators | head -c 300
```

Ожидаемо:

- `ss` показывает `127.0.0.1:8002`, но не публичный `0.0.0.0:8001`;
- `curl` возвращает JSON со списком калькуляторов.

### 8.5. Проксирование API через `insain.ru/api/`

После переноса сайта API подключён к основному WordPress-домену:

```text
https://insain.ru/api/v1/calculators → nginx → http://127.0.0.1:8002/api/v1/calculators
```

В nginx-конфиг сайта `/etc/nginx/sites-available/insain.ru` добавь блок **перед** `location /`:

```nginx
location ^~ /api/ {
    proxy_pass http://127.0.0.1:8002;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}
```

Команды на сервере:

```bash
CONF="/etc/nginx/sites-available/insain.ru"
TS=$(date +%F-%H%M)
cp "$CONF" "/root/insain.ru-nginx-before-calc-api-$TS.conf"
nano "$CONF"
nginx -t
systemctl reload nginx
```

Проверка:

```bash
curl -sS https://insain.ru/api/v1/calculators | head -c 300
```

Не используй `curl -I` для проверки FastAPI endpoint: `-I` отправляет `HEAD`, а `/api/v1/calculators` разрешает `GET`, поэтому нормальный ответ на `HEAD` может быть `405 Method Not Allowed`.

Позже, когда будет нужен отдельный API-домен `calc.insain.ru`, можно перенести proxy-блок в отдельный server block из [infra/nginx.conf](../infra/nginx.conf) и выпустить сертификат для `calc.insain.ru`.

CORS для сайта настроен в [calc_service/main.py](../calc_service/main.py) (домены `insain.ru` и `www.insain.ru`). При относительном `/api/v1` запросы идут на тот же origin, поэтому CORS не нужен.

### 8.6. Логи бота на диске хоста

В compose том `./logs` монтируется в контейнер бота; каталог `logs` в корне репозитория создаётся при необходимости. Следи за размером диска.

### 8.7. Подготовка к ИИ-доступу

**Пошаговый план (Cursor, SSH, Browser, деплой bridge, безопасность):** [agent-autonomous-environment.md](agent-autonomous-environment.md).

Кратко — что нужно на сервере для агента:

1. **SSH-ключ для ИИ-агента.** Создай отдельного пользователя `agent` и добавь отдельный SSH-ключ:
  ```bash
   sudo adduser --disabled-password --gecos "" agent
   sudo usermod -aG www-data,docker agent
   sudo install -d -m 700 -o agent -g agent /home/agent/.ssh
   # скопируй публичный ключ ИИ-агента в /home/agent/.ssh/authorized_keys
  ```
2. **Ограниченный sudo, не группа `sudo`.** В `/etc/sudoers.d/agent` разрешить только `nginx -t`, `systemctl reload nginx` и `wp` от `www-data`. Полный пример — в [agent-autonomous-environment.md](agent-autonomous-environment.md).
3. **wp-cli + PHP 8.2 CLI.** `wp` должен запускаться от `www-data` на PHP 8.2 (`sudo -u www-data wp --info --path=/var/www/insain.ru`). Панель хостинга задаёт PHP-FPM сайта, а CLI-версия проверяется отдельно.
4. **Docker CLI** — пользователь в группе `docker`: перезапуск контейнеров, просмотр логов, деплой `calc_service` через `/opt/insain-agent/docker-compose.calc-only.yml`.
5. **Browser MCP в Chrome.** Для админки WordPress агент использует Browser MCP в вашем залогиненном Chrome, а не встроенный Browser.
6. **Конфиги nginx в `infra/`** — эталоны [nginx-wp.conf](../infra/nginx-wp.conf) и [nginx.conf](../infra/nginx.conf) хранятся в репозитории; ИИ-агент может обновить конфиг на сервере через `git pull` + ограниченный reload nginx.
7. **Все действия через CLI и Browser MCP** — нет зависимости от GUI-панелей хостера; всё автоматизируемо.

---

## Часть 9. Контрольный список после всего


| Проверка       | Действие                                                            |
| -------------- | ------------------------------------------------------------------- |
| Сайт           | `https://insain.ru` открывается, админка работает                   |
| API            | `https://insain.ru/api/v1/calculators` возвращает JSON              |
| Бот            | В Telegram ответ на `/start`                                        |
| Firewall       | `sudo ufw status` — открыты 22, 80, 443; 8001/8002 не в списке публичных |
| Apache         | `sudo systemctl status apache2` — должен быть `inactive (dead)`     |
| nginx          | `sudo nginx -T` — только наши конфиги, нет `vm-*.na4u.ru.conf`      |
| Место на диске | `df -h` — запас под обновления и Docker                             |
| wp-cli         | `wp --info` — установлен, работает                                  |
| Бэкапы         | Настроить бэкап БД и файлов WP на новом сервере                     |


---

## Часть 10. Если что-то пошло не так

- **502 Bad Gateway** у nginx: проверь `sudo systemctl status php*-fpm`, сокет в конфиге nginx, права на файлы WP. Если в `/var/log/nginx/insain.ru.error.log` есть `upstream sent too big header while reading response header from upstream`, увеличь `fastcgi_buffer_size`, `fastcgi_buffers`, `fastcgi_busy_buffers_size` в конфиге WordPress (см. п. 3.4). Частая причина — слишком большой `Set-Cookie`, например `wt_geo_data` от геотаргетинга.
- **Ошибка подключения к БД (MySQL)**: проверь `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` в `wp-config.php`; что служба `**mariadb`** или `**mysql`** запущена; вход: `mysql -u wpuser -p wordpress` с того же сервера.
- **Docker не стартует**: `cd /opt/insain-agent && docker compose -f docker-compose.calc-only.yml logs`.
- **Белый экран WP**: включи отладку временно в `wp-config.php` (`WP_DEBUG`), смотри логи php-fpm и nginx (`/var/log/nginx/insain.ru.error.log`).
- `**bind() to 0.0.0.0:80 failed (98: Address already in use)`**: порт 80 уже занят. Проверь:
  ```bash
  sudo ss -tlnp | grep ':80 '
  ```
  Типичные причины: **Apache ещё запущен** (остановить: п. 3.0.1), второй экземпляр nginx, или конфликт `listen 80` (на `0.0.0.0`) с `listen IP:80` (на конкретный IP). Все наши `server`-блоки должны использовать **`listen ПУБЛИЧНЫЙ_IP:80`** (п. 3.0.3).
- **Apache ещё запущен** (забыли отключить): `sudo systemctl status apache2`. Если `active` — остановить и отключить по п. 3.0.1.
- **Критическая ошибка WP / пропала верстка после замены URL**: скорее всего SQL `REPLACE` сломал сериализованные данные в БД. Восстанови из бэкапа (`mysql < /root/wp-db-before-replace.sql`) и используй **wp-cli** `search-replace` вместо SQL — он корректно пересчитывает длины строк в сериализованных массивах (п. 5.4, шаг C).
- **wp-cli падает с ошибкой плагина**: используй флаги `--skip-plugins --skip-themes` (п. 5.4, шаг C).
- **Заглушка NetAngels «Сайт не существует»**: запрос попал в автоконфиг панели (`vm-*.na4u.ru.conf`). Убедись, что он удалён из `sites-enabled` (п. 3.0.2) и nginx перезагружен.

---

## Связанные файлы в репозитории

- [docker-compose.yml](../docker-compose.yml) — общий compose для calc-api и tg-bot  
- `/opt/insain-agent/docker-compose.calc-only.yml` — фактический compose тестового VDS для `calc_service` (`127.0.0.1:8002`)  
- [infra/compose.vds.yml](../infra/compose.vds.yml) — старый/общий override с привязкой `127.0.0.1:8001`; для текущего тестового VDS не используется  
- [infra/nginx.conf](../infra/nginx.conf) — заготовка reverse proxy для будущего `calc.insain.ru`  
- [infra/nginx-wp.conf](../infra/nginx-wp.conf) — эталонный конфиг nginx для WordPress (п. 3.4)  
- [ROADMAP.md](../ROADMAP.md) — фазы D2, D3 и дальше

Дата черновика инструкции: 2026-04-04.  
Обновление (вариант B — ручной nginx, без Apache): 2026-04-12.