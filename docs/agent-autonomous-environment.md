# Среда для автономной работы ИИ-агентов с сайтом insain.ru

Пошаговый план настройки: Cursor (терминал, браузер, MCP), SSH на VDS, деплой `wp-plugin`, проверки на боевом домене и правила безопасности.

Если нужно только **переключение режимов** (автономный ↔ с подтверждением) — сразу к [разделу 2](#2-два-режима-работы-и-как-переключаться).

**Целевая среда:** основной сайт `https://insain.ru` (после переноса с `test.insain.ru`).  
**Связанные документы:** [production-cutover-plan.md](production-cutover-plan.md), [vds-wordpress-docker-setup.md](vds-wordpress-docker-setup.md) (п. 8.7), [wordpress-integration.md](wordpress-integration.md).

---

## 1. Что получится в итоге

После выполнения плана агент в Cursor сможет **без подтверждения на каждый шаг** (в пределах выбранного режима Auto-Run):

| Действие | Где |
|----------|-----|
| Править код в репозитории (`wp-plugin/`, `calc_service/`, `infra/`) | Локально, workspace `insain-agent` |
| Запускать тесты и локальный API | `make calc-up`, `pytest` |
| Подключаться к VDS по SSH | Пользователь `agent` |
| Деплоить bridge-плагин, смотреть логи nginx/php/docker | `/var/www/insain.ru`, `/opt/insain-agent` |
| Открывать сайт, админку, страницы калькуляторов и проверять UI | Browser MCP в вашем Chrome |

Агент **не заменяет** администратора: на проде нужны бэкапы, ограниченные права SSH и осознанный выбор режима Auto-Run.

---

## 2. Два режима работы и как переключаться

Это главный переключатель. Им управляет **один** параметр Cursor — **Auto-Run** (`Cursor Settings → Agents`), плюс подключение Browser MCP и правила проекта.

| | Сценарий 1. Автономный | Сценарий 2. С подтверждением |
|---|---|---|
| **Что делает агент** | Сам пишет код, гоняет тесты, деплоит на VDS, отлаживает, открывает сайт в браузере, заходит в админку и меняет настройки | Предлагает правки и команды; **вы жмёте «Run» / «Accept»** на каждый шаг |
| **Auto-Run** | **Run Everything** (вкл.) | **Off** (выкл.) |
| **Терминал (ssh, wp, docker)** | Выполняется сразу | Кнопка **Run** на каждую команду |
| **Правки файлов** | Применяются сразу | Показываются диффом, нужен **Accept** |
| **Browser / админка** | Browser MCP подключён (с вашей Chrome-сессией) | Можно держать выключенным |
| **Правило `insain-site-autonomous`** | Прикреплено к чату | Не обязательно |
| **Когда использовать** | Рутина, доверенная задача, вы рядом и следите | Прод-изменения с риском, незнакомая задача, нет бэкапа |

### Как переключиться за 30 секунд

**→ В автономный (Сценарий 1):**
1. `Cursor Settings → Agents → Auto-Run` = **Run Everything**.
2. Убедиться, что Browser MCP подключён (зелёный) и Chrome залогинен в `https://insain.ru/wp-admin` — см. п. **A.5** ниже.
3. В чате режим **Agent**, прикрепить правило `@insain-site-autonomous` (или написать «работаем по docs/agent-autonomous-environment.md, автономно»).

**→ В режим подтверждений (Сценарий 2):**
1. `Cursor Settings → Agents → Auto-Run` = **Off**.
2. Дальше работаете как обычно: агент предлагает — вы подтверждаете каждую команду и каждый дифф.

> **Важно про Sandbox.** Промежуточный режим **Auto-Run in Sandbox** ограничивает сеть и запись вне workspace, поэтому **SSH-деплой на прод и `curl` к insain.ru в нём могут не работать**. Для автономной работы с сайтом нужен именно **Run Everything** (при ограниченных правах пользователя `agent`, см. [Часть B](#часть-b-ssh-доступ-агента-к-vds)). Sandbox оставьте для чисто локальных правок без выхода на сервер.

> **Граница автономии.** Даже в Сценарии 1 правило `insain-site-autonomous` требует у агента **спросить подтверждение** перед опасными действиями (`git push`, смена DNS, `wp search-replace` по всей БД, удаление томов). То есть «автономно» — это «без кликов на рутину», но не «без тормозов на необратимое».

---

## 3. Схема доступа

```text
┌─────────────────────────────────────────────────────────────────┐
│  ПК разработчика (Windows) — Cursor IDE                          │
│  • Репозиторий D:\Projects\insain-agent                        │
│  • Agent + Auto-Run + Node.js/npm/npx + Browser MCP            │
│  • ssh insain-prod → VDS                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SSH (22)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  VDS (insain.ru) — 5.181.252.133 (см. production-cutover-plan) │
│                                                                  │
│  /var/www/insain.ru          WordPress + wp-plugin               │
│  /etc/nginx/sites-enabled/   insain.ru + location /api/          │
│  127.0.0.1:8002              calc-api (Docker)                   │
│  /opt/insain-agent           git, docker-compose, .env           │
└─────────────────────────────────────────────────────────────────┘
                            │
         Chrome через MCP ───┼──► https://insain.ru/...
                            └──► https://insain.ru/api/v1/...
```

**Важно:** bridge использует относительный URL `/api/v1` — запросы идут на тот же origin, что и сайт. Отдельный домен `calc.insain.ru` для агента не обязателен (см. [ROADMAP.md](../ROADMAP.md)).

---

## 4. Предварительные условия

Перед настройкой автономии убедитесь, что прод уже живёт на новом сервере:

1. DNS: `insain.ru` и `www.insain.ru` → IP нового VDS.
2. HTTPS: сертификат Let's Encrypt для `insain.ru` / `www.insain.ru`.
3. В nginx для `insain.ru` есть прокси API (порт **8002** на хосте):

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

4. WordPress: `home` и `siteurl` = `https://insain.ru` (без `test.insain.ru` в опциях и контенте).
5. Проверки с любой машины:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://insain.ru/
curl -sS https://insain.ru/api/v1/calculators | head -c 200
```

Ожидается: `200` на главной и JSON со списком калькуляторов.

Подробный cutover: [production-cutover-plan.md](production-cutover-plan.md).

---

## Часть A. Cursor IDE (локально)

### A.1. Режим агента

1. Откройте проект `insain-agent` в Cursor.
2. В чате выберите режим **Agent** (не Ask — в Ask нет правок файлов и полного терминала).
3. Для задач по сайту в первом сообщении укажите: «работаем с prod `https://insain.ru`, см. docs/agent-autonomous-environment.md».

### A.2. Auto-Run — переключатель сценариев

**Путь:** `Cursor Settings` → **Agents** → **Terminal / Auto-Run** (названия чуть отличаются по версии).

| Режим | Сценарий | Поведение |
|-------|----------|-----------|
| **Off** | **2. Подтверждение** | Каждая команда и каждый дифф — вручную |
| **Run Everything** | **1. Автономный** | Команды (`ssh`, `wp`, `docker`, `curl`) и правки идут сразу |
| Auto-Run in Sandbox | (только локально) | Сеть/запись вне workspace ограничены → **SSH на прод не годится** |

Подробное сравнение и шаги переключения — в [разделе 2](#2-два-режима-работы-и-как-переключаться).

**Безопасность Run Everything:** автономия безопасна ровно настолько, насколько ограничен пользователь `agent` на сервере ([Часть B.4](#b4-ограниченный-sudo-рекомендуется)) и насколько дисциплинированы бэкапы ([Часть G](#часть-g-безопасность-и-откат)). Cursor сам по себе деструктивные команды не блокирует.

**Альтернатива Run Everything — allowlist.** Если не хотите полностью открытый режим, оставьте Auto-Run **Off** и добавьте в **Command allowlist** доверенные команды:

```text
git, pytest, python, pip, make, curl, ssh, scp,
docker, docker compose, wp, nginx, sudo nginx, sudo systemctl
```

Чтобы allowlist надёжно работал, в `Cursor Settings → Agents` включите **Legacy Terminal Tool** (в sandbox-режиме allowlist часто игнорируется).

### A.3. Node.js для MCP-серверов

Browser MCP запускается через `npx`, поэтому на Windows нужен полноценный Node.js с `npm`/`npx`. Встроенный `node.exe` из Cursor для этого не подходит: он есть в PATH, но без `npm` и `npx`.

Установка:

```powershell
winget install OpenJS.NodeJS.LTS
```

После установки **полностью закройте Cursor** (в том числе процессы `Cursor.exe` в диспетчере задач) и запустите заново. Проверка в терминале Cursor:

```powershell
node --version
npm --version
npx --version
```

Ожидаемый результат: все три команды отвечают версиями. Если `npm`/`npx` не видны, Cursor не подхватил новый PATH — перезапустите Cursor ещё раз или укажите в `.cursor/mcp.json` абсолютный путь к `npx.cmd`.

### A.4. Встроенный Browser — вспомогательная проверка

Подходит для быстрых проверок публичных URL и API без логина.

1. `Cursor Settings` → **Agents** / **MCP** → включить **Browser**.
2. Для Enterprise: в allowlist origin добавить `https://insain.ru`, `https://www.insain.ru`.
3. **Полностью перезапустить Cursor** после включения MCP.

Что агент проверяет здесь:

- внешний вид страниц калькуляторов и каталога;
- загрузку `insain-calc-bridge.js`;
- запросы `GET /api/v1/product/...`, `POST /api/v1/calc/...` во вкладке Network;
- ошибки в консоли.

**Ограничение:** это чистая сессия без cookies — в **админку WordPress** через встроенный браузер агент не войдёт. Для `insain.ru` основной инструмент проверки сайта — Browser MCP в вашем Chrome (см. A.5), потому что он работает в той же сессии, где открыт WordPress admin bar.

### A.5. Browser MCP — админка WP и проверка вида сайта

Нужен для **Сценария 1**, где агент заходит в `wp-admin` и меняет настройки под **вашей** залогиненной сессией.

1. Убедиться, что выполнен A.3: `npm` и `npx` видны из терминала Cursor.
2. Установить расширение [Browser MCP](https://browsermcp.io/) в тот Chrome/Edge, где вы **уже залогинены** в `https://insain.ru/wp-admin`.
3. В репозитории должен быть `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "browsermcp": {
      "command": "npx",
      "args": ["-y", "@browsermcp/mcp@latest"]
    }
  }
}
```

4. В расширении нажать **Connect**, перезапустить Cursor, дождаться зелёного статуса MCP.
5. Проверка агентом: открыть `https://insain.ru/` через Browser MCP. Рабочий признак — в snapshot/скриншоте видна верхняя панель WordPress (`Привет, admin`, `Редактировать страницу`, `WPBakery`).
6. В задаче писать: «для сайта и wp-admin используй Browser MCP в подключённом Chrome».

> Так как сессия — ваша, агент действует **с вашими правами администратора**. Для Сценария 1 это и нужно, но именно поэтому правки в админке держите в списке «спроси подтверждение» для рискованных настроек (оплата, SEO, темы).

### A.6. Правило проекта (переключатель поведения)

Файл `.cursor/rules/insain-site-autonomous.mdc` **уже есть в репозитории** (`alwaysApply: false`). Он задаёт границы автономии (что делать самому, что — с подтверждением).

- **Сценарий 1:** прикрепите правило к чату через `@insain-site-autonomous` или упоминанием.
- **Сценарий 2:** правило не обязательно — за подтверждение отвечает Auto-Run = Off.

Полный текст — в [Приложении A](#приложение-a-правило-cursor-insain-site-autonomousmdc).

### A.7. Локальный calc_service (для правок API)

Из корня репозитория — поднять **только** API (без Telegram-бота):

```powershell
make calc-up
# либо без make:
python scripts/dev.py start calc
```

Проверка:

```powershell
curl http://127.0.0.1:8001/api/v1/calculators
pytest calc_service/tests/ -q
```

На VDS API снаружи идёт через nginx на **8002**; локально по умолчанию **8001** — не путать порты при чтении логов.

---

## Часть B. SSH-доступ агента к VDS

### B.1. Создать пользователя `agent` (на сервере, один раз)

Выполнить под `root` на VDS:

```bash
sudo adduser --disabled-password --gecos "" agent
sudo usermod -aG www-data,docker agent
sudo mkdir -p /home/agent/.ssh
sudo chmod 700 /home/agent/.ssh
```

### B.2. SSH-ключ (на ПК Windows)

В PowerShell:

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\insain_agent_ed25519" -C "cursor-agent-insain"
```

Публичный ключ скопировать на сервер:

```powershell
type $env:USERPROFILE\.ssh\insain_agent_ed25519.pub
```

На сервере:

```bash
sudo nano /home/agent/.ssh/authorized_keys
# вставить одну строку pub key
sudo chown -R agent:agent /home/agent/.ssh
sudo chmod 600 /home/agent/.ssh/authorized_keys
```

Проверка:

```powershell
ssh -i $env:USERPROFILE\.ssh\insain_agent_ed25519 agent@5.181.252.133 "whoami && hostname"
```

(Подставьте актуальный IP или `insain.ru`, если SSH слушает на 22 по домену.)

### B.3. Файл SSH config на Windows

Файл: `%USERPROFILE%\.ssh\config`

```ssh-config
Host insain-prod
    HostName 5.181.252.133
    User agent
    IdentityFile ~/.ssh/insain_agent_ed25519
    IdentitiesOnly yes
```

Проверка:

```powershell
ssh insain-prod "ls -la /var/www/insain.ru/wp-config.php"
```

### B.4. Ограниченный sudo (рекомендуется)

Не давайте `agent` полный NOPASSWD:ALL. Пример `/etc/sudoers.d/agent`:

```bash
sudo visudo -f /etc/sudoers.d/agent
```

```sudoers
# nginx: только проверка и reload
agent ALL=(root) NOPASSWD: /usr/sbin/nginx -t, /bin/systemctl reload nginx

# wp-cli от www-data (WordPress)
agent ALL=(www-data) NOPASSWD: /usr/local/bin/wp, /usr/bin/wp
```

Пути к `wp` и `nginx` уточните на сервере: `which wp`, `which nginx`.

> **Docker без sudo.** В [B.1](#b1-создать-пользователя-agent-на-сервере-один-раз) `agent` добавлен в группу `docker`, поэтому `docker compose` запускается **без** `sudo` — отдельная sudo-строка для docker не нужна. Помните: членство в группе `docker` (как и `sudo`) фактически даёт root-уровень, поэтому не открывайте сервер `agent` наружу и используйте только ключи.

### B.5. Права на каталоги

| Путь | Назначение | Кто пишет |
|------|------------|-----------|
| `/var/www/insain.ru` | WordPress | `www-data`; деплой плагина — через zip + `wp plugin install` от `www-data` |
| `/opt/insain-agent` | Репозиторий, Docker | `agent` + `git pull`; перезапуск контейнеров — `docker compose` |
| `/etc/nginx/sites-enabled/insain.ru` | Конфиг сайта | копия из `infra/`, правка через `sudo` |

Плагин bridge копировать в:

```text
/var/www/insain.ru/wp-content/plugins/insain-calc-bridge/
```

### B.6. wp-cli и PHP 8.2 (обязательно на этом VDS)

На VDS NetAngels действует **пер-юзерный селектор PHP**: `/usr/bin/php` — это скрипт, который выбирает версию по `~/etc/php/version` или глобальному `/etc/default/php`. Панель хостинга задаёт PHP-FPM для сайта, но `wp-cli` использует **CLI PHP**, поэтому это проверяется отдельно.

Фактическое состояние после настройки:

```bash
ssh insain-prod "sudo -u www-data wp --info --path=/var/www/insain.ru | grep -i 'php version'"
# PHP version: 8.2.x
```

Если после переноса/обновления сервера `wp option get siteurl` падает с ошибкой `mysqli`, значит CLI снова ушёл на PHP 8.0. Фикс (один раз, под root):

```bash
# как root на VDS
install -d -o www-data -g www-data /var/www/etc/php
ln -sfn 8.2 /var/www/etc/php/version
chown -h www-data:www-data /var/www/etc/php/version
# проверка тут же (должно стать 8.2 и вернуть https://insain.ru):
sudo -u www-data wp --info --path=/var/www/insain.ru | grep -i 'php version'
sudo -u www-data wp option get siteurl --path=/var/www/insain.ru
```

Почему сюда: при `sudo -u www-data` (env_reset) `HOME=/var/www`, и скрипт-селектор `/usr/bin/php` читает `$HOME/etc/php/version`. Поэтому селектор в `/home/agent/...` **не** действует — нужен именно `/var/www/etc/php/version`. После фикса существующий sudoers (`agent ALL=(www-data) NOPASSWD: .../wp`) работает без изменений: команда — это `wp`, версию PHP подбирает селектор.

> **Если после селектора всё ещё 8.0** (другой механизм панели) — глобальный фолбэк под root:
> ```bash
> sed -i 's/^DEFAULT=.*/DEFAULT=8.2/' /etc/default/php
> sudo -u www-data wp --info --path=/var/www/insain.ru | grep -i 'php version'
> ```
> Это меняет дефолт PHP CLI для всех пользователей сервера (на этом VDS обслуживается только insain.ru, php8.2-fpm уже основной — приемлемо).

---

## Часть C. Установка и деплой wp-plugin

### C.1. Структура на сервере

```text
wp-content/plugins/insain-calc-bridge/
├── insain-calc-bridge.php
└── js/
    └── insain-calc-bridge.js
```

Источник в репозитории: [wp-plugin/](../wp-plugin/).

### C.2. Деплой через `wp plugin install` (рекомендуется)

Каталог `wp-content/plugins` принадлежит `www-data` и **не** доступен на запись группе, а sudoers `agent` разрешает только `wp`/`nginx` (не `rsync`/`cp` от root). Поэтому надёжный путь — установка из zip силами самого `www-data`.

С ПК (PowerShell в корне репозитория):

```powershell
Compress-Archive -Path wp-plugin\* -DestinationPath $env:TEMP\insain-calc-bridge.zip -Force
scp $env:TEMP\insain-calc-bridge.zip insain-prod:/tmp/insain-calc-bridge.zip
```

> zip должен содержать `insain-calc-bridge.php` в корне (не вложенную папку `wp-plugin/`). Если структура не та — заархивируйте содержимое каталога, а не сам каталог.

На сервере (через ssh, без root):

```bash
ssh insain-prod "chmod 644 /tmp/insain-calc-bridge.zip && sudo -u www-data wp plugin install /tmp/insain-calc-bridge.zip --force --activate --path=/var/www/insain.ru"
```

### C.3. Проверка установки

```bash
ssh insain-prod "sudo -u www-data wp plugin list --path=/var/www/insain.ru | grep insain"
ssh insain-prod "sudo -u www-data wp plugin is-active insain-calc-bridge --path=/var/www/insain.ru && echo ACTIVE"
```

Или: **Плагины** в админке → **Insain Calc Bridge**.

### C.4. Проверка API base

В `insain-calc-bridge.php` должно оставаться:

```php
'apiBase' => '/api/v1',
```

Менять на абсолютный `https://calc.insain.ru` **не нужно**, пока nginx проксирует `/api/` на том же хосте.

---

## Часть D. Деплой и перезапуск calc_service на VDS

### D.1. Обновление кода

```bash
ssh insain-prod "cd /opt/insain-agent && git fetch origin && git pull --ff-only"
```

Ветку укажите ту, с которой реально работает прод (например `main` или `feature/agent-logic` — как зафиксировано на сервере).

### D.2. Пересборка и перезапуск

Имя compose-файла на VDS смотрите в [vds-wordpress-docker-setup.md](vds-wordpress-docker-setup.md) (часто `docker-compose.calc-only.yml`):

```bash
ssh insain-prod "cd /opt/insain-agent && docker compose -f docker-compose.calc-only.yml build calc-api && docker compose -f docker-compose.calc-only.yml up -d calc-api"
```

### D.3. Проверка

```bash
ssh insain-prod "curl -sS http://127.0.0.1:8002/api/v1/calculators | head -c 200"
curl -sS https://insain.ru/api/v1/calculators | head -c 200
```

---

## Часть E. Сценарий работы агента (типовой цикл)

1. **Задача** в Agent-чате: slug калькулятора, URL страницы, что проверить.
2. **Локально:** правки в `wp-plugin/` или `calc_service/` → `pytest`.
3. **Деплой bridge:** zip из `wp-plugin/` → `scp` в `/tmp` → `wp plugin install --force --activate`.
4. **Деплой API:** `git pull` + `docker compose` на VDS.
5. **Сброс кэша** (при необходимости):
   ```bash
   ssh insain-prod "sudo -u www-data wp cache flush --path=/var/www/insain.ru"
   ```
6. **Браузер:** открыть `https://insain.ru/...` через Browser MCP (Chrome-сессия), проверить `POST /api/v1/calc/{slug}` и вид страницы.
7. **Отчёт:** цена, срок, материалы, ошибки в консоли.

Для миграции очередной формы ez Form — чеклист полей: [wordpress-integration.md](wordpress-integration.md).

---

## Часть F. Чеклист проверки среды (один раз после настройки)

| # | Проверка | Команда / действие | Ожидание |
|---|----------|-------------------|----------|
| 1 | DNS | `dig +short insain.ru` | IP нового VDS |
| 2 | HTTPS | Browser MCP → `https://insain.ru` | без ошибок сертификата, виден WordPress admin bar |
| 3 | API снаружи | `curl https://insain.ru/api/v1/calculators` | JSON |
| 4 | API локально на VDS | `curl http://127.0.0.1:8002/api/v1/calculators` | JSON |
| 5 | SSH | `ssh insain-prod whoami` | `agent` |
| 6 | wp-cli | `ssh insain-prod "sudo -u www-data wp option get siteurl --path=/var/www/insain.ru"` | `https://insain.ru` |
| 7 | Browser MCP | открыть `https://insain.ru/` | видна страница и WordPress admin bar |
| 8 | Плагин | `wp plugin is-active insain-calc-bridge` | active |
| 9 | Bridge JS | Browser MCP → страница калькулятора → Sources/Network | `insain-calc-bridge.js` |
| 10 | Расчёт | изменить поля формы | запрос `POST /api/v1/calc/...` 200 |
| 11 | Локальные тесты | `pytest calc_service/tests/` | green |

---

## Часть G. Безопасность и откат

### G.1. Риски Auto-Run на проде

- массовый `wp search-replace` с ошибкой в URL;
- `docker compose down` / удаление томов;
- правка nginx без `nginx -t`;
- утечка секретов из `.env` в чат.

**Меры:**

- бэкап БД перед автономной сессией (через wp-cli, без отдельных MySQL-кредов и без записи в `/root`):
  ```bash
  ssh insain-prod "cd /var/www/insain.ru && sudo -u www-data wp db export wp-backup-$(date +%F-%H%M).sql"
  ```
- не хранить пароли в репозитории; `.env` только на сервере и локально в `.gitignore`;
- в правиле агента: **не** `git push` и **не** менять DNS без явной просьбы;
- для отката DNS — [production-cutover-plan.md](production-cutover-plan.md).

### G.2. Быстрый откат nginx

```bash
sudo cp /root/nginx-insain-before-prod.conf /etc/nginx/sites-enabled/insain.ru
sudo nginx -t && sudo systemctl reload nginx
```

### G.3. test.insain.ru

После перехода на prod: редирект `test.insain.ru` → `insain.ru` или `noindex`, чтобы не дублировать сайт в поиске.

---

## Часть H. Устранение неполадок

| Симптом | Что проверить |
|---------|----------------|
| `POST /api/v1/calc/...` 404 | nginx `location /api/`, контейнер на 8002, `docker compose ps` |
| CORS в консоли | При `/api/v1` на том же домене CORS не нужен; если API на другом домене — добавить origin в `calc_service/main.py` |
| Bridge не грузится | плагин активен, нет ошибок в `wp-content/debug.log` |
| 502 на сайте | `php-fpm`, логи `/var/log/nginx/insain.ru.error.log` |
| Browser MCP не запускается | `npm --version` и `npx --version` в терминале Cursor; расширение Browser MCP в Chrome нажато **Connect**; MCP зелёный после перезапуска Cursor |
| SSH Permission denied | `authorized_keys`, права 600/700, верный `IdentityFile` |

---

## Приложение A. Правило Cursor `insain-site-autonomous.mdc`

Файл уже лежит в репозитории: `.cursor/rules/insain-site-autonomous.mdc`. Текущее содержимое (правьте при необходимости):

```markdown
---
description: Автономная работа с prod insain.ru (WP, bridge, API, VDS)
alwaysApply: false
---

# Сайт insain.ru — режим автономной работы

## Контекст
- Прод: https://insain.ru
- WordPress: /var/www/insain.ru
- API: относительный /api/v1 (nginx → 127.0.0.1:8002)
- Репозиторий на сервере: /opt/insain-agent
- SSH: Host insain-prod (см. docs/agent-autonomous-environment.md)

## Окружение VDS (важно)
- wp-команды: sudo -u www-data wp ... --path=/var/www/insain.ru
  (www-data переключён на php8.2; mysqli есть только в 8.2)
- Деплой плагина: Compress-Archive → scp /tmp → sudo -u www-data wp plugin install zip --force --activate
  (rsync/cp от root недоступны: sudoers только wp+nginx)
- sudo доступен только для: nginx -t, systemctl reload nginx, wp (как www-data)
- docker compose — без sudo (agent в группе docker)
- Browser MCP работает через реальный Chrome с залогиненной админ-сессией WordPress

## Делай самостоятельно
- Правки wp-plugin/, calc_service/, infra/; pytest перед деплоем
- Деплой плагина через wp plugin install (см. выше)
- git pull и docker compose на VDS для API (cd /opt/insain-agent)
- Проверка страниц через Browser MCP; Network: /api/v1/
- wp cache flush, wp plugin list/activate (через sudo -u www-data)

## Спроси подтверждение у пользователя
- git push, смена DNS, wp search-replace по всей БД
- удаление файлов/БД, docker compose down -v
- отключение плагинов оплаты/SEO без явной задачи

## Не делай
- не коммить .env и секреты
- не использовать test.insain.ru как целевой URL (только prod)
- не выводить внутренние code материалов в ответы пользователям сайта

## После изменений
1. curl -sS https://insain.ru/api/v1/calculators | head -c 200
2. Открыть страницу калькулятора, проверить POST /api/v1/calc/{slug}
3. Краткий отчёт: что изменено, что проверено, ошибки консоли
```

---

## Связанные файлы

| Файл | Назначение |
|------|------------|
| [production-cutover-plan.md](production-cutover-plan.md) | DNS, SSL, search-replace на prod |
| [wordpress-integration.md](wordpress-integration.md) | ez Form, bridge, миграция калькуляторов |
| [vds-wordpress-docker-setup.md](vds-wordpress-docker-setup.md) | Полная установка VDS, Docker, nginx |
| [site-performance-optimization.md](site-performance-optimization.md) | Производительность и bridge на страницах |
| [wp-plugin/](../wp-plugin/) | Insain Calc Bridge |
| [infra/nginx-wp.conf](../infra/nginx-wp.conf) | Эталон nginx для WordPress |

---

*Документ создан: 2026-05-30. Обновлён: 2026-06-05. Целевой домен: insain.ru (после переноса с test.insain.ru).*
