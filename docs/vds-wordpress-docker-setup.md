# Новый VDS: создание, настройка, перенос WordPress и Docker (insain-agent)

Инструкция для сценария: **отдельный сервер** с **Debian 12** (или Ubuntu LTS), на нём **сайт на WordPress** и **Docker** с сервисами калькуляторов и Telegram-бота из этого репозитория.

**Предположения:**

- Домен сайта, например `insain.ru`, DNS можно менять.
- Для API калькуляторов планируется субдомен `calc.insain.ru` (как в [ROADMAP.md](../ROADMAP.md)).
- Старый сервер доступен по SSH для снятия бэкапов.

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

Для проверки нового сервера можно:

- временно добавить запись `**test.insain.ru`** → новый IP, или  
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

Клиент командной строки называется `**mysql**` (при сервере MariaDB или MySQL):

```bash
sudo mysql -u root
```

В консоли **mysql** (интерактивный клиент к твоему серверу БД):

```sql
CREATE DATABASE wordpress CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY 'СИЛЬНЫЙ_ПАРОЛЬ';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
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
  - если видишь `**php8.2-fpm.sock**` — оставь как в примере ниже с `php8.2`.

То есть **заменить** нужно только **номер версии и имя файла** в пути после `unix:/run/php/` так, чтобы они **совпадали** с тем, что показал `ls`. Если каталог `/run/php/` пустой — служба **php-fpm** не запущена или пакет не установлен: `sudo systemctl status php8.2-fpm` (подставь свою версию из `dpkg -l | grep php-fpm`).

#### Текст конфига

Создай файл `**/etc/nginx/sites-available/insain.ru`** с таким содержимым (в `**fastcgi_pass**` подставь **свой** `.sock` из `ls /run/php/`):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name insain.ru www.insain.ru;
    root /var/www/insain.ru;
    index index.php;

    client_max_body_size 64m;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

Пример: при файле `**php8.3-fpm.sock**` строка должна быть `**fastcgi_pass unix:/run/php/php8.3-fpm.sock;**`.

Включи сайт и перезагрузи nginx:

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

Обычно что-то вроде `/var/www/...`.

### 4.2. Архив файлов

```bash
cd /var/www
sudo tar czvf /root/wp-files-backup.tar.gz ИМЯ_КАТАЛОГА_САЙТА
```

Скопируй архив на новый сервер (`scp`, SFTP, панель файлов):

```bash
# с твоего ПК или со старого сервера на новый
scp root@СТАРЫЙ_IP:/root/wp-files-backup.tar.gz .
scp wp-files-backup.tar.gz root@НОВЫЙ_IP:/root/
```

### 4.3. Дамп базы MySQL

На старом сервере узнай из `wp-config.php`: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`.

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

### 5.1. Распаковка файлов

```bash
cd /var/www
sudo tar xzvf /root/wp-files-backup.tar.gz
# при необходимости перенеси содержимое в /var/www/insain.ru
sudo chown -R www-data:www-data /var/www/insain.ru
find /var/www/insain.ru -type d -exec chmod 755 {} \;
find /var/www/insain.ru -type f -exec chmod 644 {} \;
```

### 5.2. Импорт дампа MySQL

Импорт в пустую базу на новом сервере (имя БД и пользователь — как в шаге 3.2):

```bash
sudo mysql -u wpuser -p wordpress < /root/wp-db.sql
```

Либо от root MySQL: `sudo mysql -u root` и затем `SOURCE /root/wp-db.sql` после `USE wordpress;` — по ситуации.

(Подставь своего пользователя и имя БД из шага 3.2.)

### 5.3. wp-config.php

Отредактируй `/var/www/insain.ru/wp-config.php`:

- `**DB_NAME**`, `**DB_USER**`, `**DB_PASSWORD**`, `**DB_HOST**` — данные **новой** MySQL-базы на VDS (обычно `DB_HOST` = `localhost` или `127.0.0.1`, если MySQL/MariaDB на том же сервере, что и WordPress).
- При смене домена иногда добавляют строки для принудительного HTTPS — делай по необходимости после выпуска сертификата.

### 5.4. URL сайта в базе MySQL

Если **домен тот же** (`https://insain.ru`), в таблице `**wp_options`** поля `**siteurl**` и `**home**` часто уже верные после импорта.

Если тестировал по IP или временному хосту — перед переключением DNS приведи URL к боевым (осторожно, с бэкапом БД):

- через админку WordPress (если открывается), или  
- `wp-cli search-replace` (если установишь wp-cli), или  
- одноразовый SQL — только если понимаешь, что делаешь.

### 5.5. Долго не обновлялись: ядро WordPress и плагины **до** переключения DNS

Если копия сайта давно без обновлений, **не переноси основной домен сразу**. Сначала доведи установку до актуального состояния **на новом VDS**, пока трафик идёт на старый сервер.

**Условие:** сайт открывается по тестовому доступу (п. 5.4: `hosts`, поддомен `test.…` или временное имя) — без переключения A-записи боевого домена.

Рекомендуемый порядок:

1. **Снимок перед правками** на новом сервере: свежий дамп БД и при необходимости копия каталога WordPress — чтобы откатиться, если обновление что-то сломает.
2. **Версия PHP** на новом VDS не ниже требований текущей и целевой версии WordPress (`php -v`, при необходимости обнови пакеты PHP-FPM и перезапусти nginx).
3. **Обновление по слоям** (из админки «Консоль → Обновления» или через `wp-cli`, если настроишь):
   - сначала **ядро WordPress**;
   - затем **плагины** (по одному или пакетом — как привычнее; после крупного отставания иногда безопаснее по очереди с проверкой);
   - при необходимости **тема** (если не кастомная сборка с ручными правками).
4. **Проверка:** главная и типовые страницы, `/wp-admin`, критичные формы, оплата/заявки, интеграции (в т.ч. калькуляторы/виджеты, если есть). Исправь конфликты до переноса DNS.
5. Только после стабильной работы на тестовом доступе переходи к **части 6–7** (HTTPS по боевому имени после указания DNS, переключение A-записи).

Старый сервер до переключения DNS остаётся **боевым**; новый — песочница для миграции и обновлений.

### 5.6. Финальная проверка до переключения DNS

- Через `hosts` на своём ПК или через `test.insain.ru` открой сайт по HTTP/HTTPS (как настроено для теста).
- Войди в `/wp-admin`, проверь главную, формы, загрузку медиа.
- Если выполнял п. 5.5 — убедись, что после обновлений всё ещё ок.

---

## Часть 6. HTTPS для основного сайта (Let’s Encrypt)

Выпускай сертификат, когда A-запись **основного домена** уже указывает на **новый** IP (или отдельно для тестового поддомена). Обычно это **после** проверок из п. 5.5–5.6:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d insain.ru -d www.insain.ru
```

Certbot настроит SSL и при желании редирект HTTP→HTTPS.

**Порядок с переносом:** финальная проверка на новом IP (п. 5.6; при устаревшем сайте — сначала обновления по п. 5.5), затем переключение DNS (часть 7), затем `certbot` для боевого имени.

---

## Часть 7. Переключение DNS

Переключай **основной** домен на новый IP, когда сайт на новом VDS уже проверен (п. 5.6), а при долгом простое обновлений — после п. 5.5.

1. За сутки (если возможно) уменьши **TTL** у A-записей.
2. В панели DNS: **A** для `insain.ru` и при необходимости для `www` → **новый IP**.
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
sudo git clone https://github.com/ВАШ_ОРГ/insain-agent.git insain-agent
sudo chown -R $USER:$USER insain-agent
cd insain-agent
```

Подставь реальный URL репозитория. В `deploy.sh` используй:

```bash
export INSAIN_REPO_DIR=/opt/insain-agent
```

### 8.3. Файл `.env`

```bash
cp .env.example .env
nano .env
```

Заполни как на локальной машине: `TELEGRAM_TOKEN`, ключи LLM и остальное (см. [.env.example](../.env.example)). Файл `.env` в git не коммитится.

### 8.4. Первый запуск контейнеров (продакшен-привязка порта)

На VDS API должен слушать только **localhost:8001**, наружу — nginx. Используется override [infra/compose.vds.yml](../infra/compose.vds.yml) и скрипт [infra/deploy.sh](../infra/deploy.sh):

```bash
chmod +x infra/deploy.sh
export INSAIN_REPO_DIR=/opt/insain-agent
bash infra/deploy.sh
```

Проверка **на сервере**:

```bash
curl -sS http://127.0.0.1:8001/api/v1/calculators | head -c 300
```

### 8.5. Субдомен calc.insain.ru

1. В DNS: **A**-запись `calc` → тот же IP сервера (или отдельный — по твоей схеме).
2. Скопируй шаблон nginx: [infra/nginx.conf](../infra/nginx.conf) в `/etc/nginx/sites-available/calc.insain.ru`, включи сайт, `nginx -t`, reload.
3. Выпусти сертификат:

```bash
sudo certbot --nginx -d calc.insain.ru
```

1. Проверка: `https://calc.insain.ru/api/v1/calculators`.

CORS для сайта настроен в [calc_service/main.py](../calc_service/main.py) (домены insain.ru и www).

### 8.6. Логи бота на диске хоста

В compose том `./logs` монтируется в контейнер бота; каталог `logs` в корне репозитория создаётся при необходимости. Следи за размером диска.

---

## Часть 9. Контрольный список после всего


| Проверка       | Действие                                                            |
| -------------- | ------------------------------------------------------------------- |
| Сайт           | `https://insain.ru` открывается, админка работает                   |
| API            | `https://calc.insain.ru/api/v1/calculators` возвращает JSON         |
| Бот            | В Telegram ответ на `/start`                                        |
| Firewall       | `sudo ufw status` — открыты 22, 80, 443; 8001 не в списке публичных |
| Место на диске | `df -h` — запас под обновления и Docker                             |
| Бэкапы         | Настроить бэкап БД и файлов WP на новом сервере                     |


---

## Часть 10. Если что-то пошло не так

- **502 Bad Gateway** у nginx: проверь `sudo systemctl status php*-fpm`, сокет в конфиге nginx, права на файлы WP.
- **Ошибка подключения к БД (MySQL)**: проверь `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` в `wp-config.php`; что служба `**mariadb`** или `**mysql**` запущена; вход: `mysql -u wpuser -p wordpress` с того же сервера.
- **Docker не стартует**: `docker compose -f docker-compose.yml -f infra/compose.vds.yml logs`.
- **Белый экран WP**: включи отладку временно в `wp-config.php` (`WP_DEBUG`), смотри логи php-fpm/nginx.

---

## Связанные файлы в репозитории

- [docker-compose.yml](../docker-compose.yml) — сервисы calc-api и tg-bot  
- [infra/compose.vds.yml](../infra/compose.vds.yml) — привязка `127.0.0.1:8001`  
- [infra/deploy.sh](../infra/deploy.sh) — деплой на сервере (`INSAIN_REPO_DIR=/opt/insain-agent`)  
- [infra/nginx.conf](../infra/nginx.conf) — reverse proxy для `calc.insain.ru`  
- [ROADMAP.md](../ROADMAP.md) — фазы D2, D3 и дальше

Дата черновика инструкции: 2026-04-04.