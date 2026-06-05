# Переключение insain.ru на новый WordPress

Финальный боевой план замены старого сайта `insain.ru` новым сайтом, который сейчас доступен как `test.insain.ru`.

## Текущее состояние

- Новый сайт: `https://test.insain.ru`.
- Новый сервер: `5.181.252.133`.
- Корень WordPress на новом сервере: `/var/www/insain.ru`.
- API калькуляторов работает локально на `127.0.0.1:8002`.
- Наружу API отдаётся через nginx по пути `/api/`, например `https://test.insain.ru/api/v1/calculators`.
- Порт `8001` не используется.
- HTTPS настроен для `test.insain.ru`.
- Для `insain.ru` и `www.insain.ru` SSL нужно выпустить после переключения DNS.

Цель:

```text
https://insain.ru     -> 5.181.252.133
https://www.insain.ru -> 5.181.252.133
```

## Перед переключением

Сохранить текущий nginx-конфиг на новом сервере:

```bash
sudo cp /etc/nginx/sites-enabled/insain.ru /root/nginx-insain-before-prod.conf
```

Проверить новый сайт и API:

```bash
curl -I https://test.insain.ru/
curl http://127.0.0.1:8002/api/v1/calculators
curl https://test.insain.ru/api/v1/calculators
```

Проверить nginx:

```bash
sudo nginx -t
```

## DNS

В DNS-зоне поменять только две A-записи:

```dns
insain.ru.      300 IN A 5.181.252.133
www.insain.ru.  300 IN A 5.181.252.133
```

Старые значения:

```dns
insain.ru.      3600 IN A 185.93.109.70
www.insain.ru.  3600 IN A 185.93.109.70
```

Не трогать:

```dns
MX mx.yandex.net.
TXT SPF/DKIM/Google verification
CAA letsencrypt.org
test.insain.ru
calc.insain.ru
metallicheskie-znachki.insain.ru
www.old.insain.ru
_acme-challenge.insain.ru
```

После изменения проверить:

```bash
dig +short insain.ru
dig +short www.insain.ru
```

Ожидаемый результат:

```text
5.181.252.133
5.181.252.133
```

Из-за старого TTL `3600` часть пользователей может до часа видеть старый сайт.

## SSL

Когда DNS уже указывает на новый сервер, выпустить сертификат:

```bash
sudo certbot --nginx -d insain.ru -d www.insain.ru
```

Затем проверить и перезагрузить nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Проверить, что в HTTPS-блоке для `insain.ru` есть прокси API:

```bash
sudo nginx -T | grep -n "server_name insain.ru\|server_name www.insain.ru\|api/\|8002\|ssl_certificate"
```

Если `/api/` в HTTPS-блоке для `insain.ru` нет, добавить туда:

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

После правки снова проверить и перезагрузить nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## WordPress-домен

После SSL заменить домен в базе WordPress:

```bash
cd /var/www/insain.ru

wp search-replace 'http://test.insain.ru' 'https://insain.ru' --all-tables
wp search-replace 'https://test.insain.ru' 'https://insain.ru' --all-tables

wp option get home
wp option get siteurl
```

Ожидаемый результат:

```text
https://insain.ru
https://insain.ru
```

Если WP-CLI нет, использовать плагин Better Search Replace. Обычный SQL `REPLACE()` не использовать, потому что WordPress хранит часть данных в сериализованном виде.

## Финальная проверка

Открыть:

```text
https://insain.ru/
https://www.insain.ru/
https://insain.ru/wp-admin/
https://insain.ru/api/v1/calculators
https://insain.ru/catalog/kalkulyator-pazlov/
```

Проверить:

- сайт открывается по HTTPS;
- `www` редиректится как нужно;
- `/api/v1/calculators` отдаёт JSON;
- калькулятор считает;
- формы отправляются;
- картинки грузятся;
- нет запросов на `test.insain.ru`;
- нет mixed content;
- в консоли браузера нет критичных ошибок;
- ЧПУ-страницы открываются;
- `robots.txt` и `sitemap.xml` доступны.

## После запуска

`test.insain.ru` закрыть от индексации или сделать редирект на `insain.ru`.

Старый сервер не выключать несколько дней. Если понадобится откат, вернуть DNS `insain.ru` и `www.insain.ru` на старый IP:

```text
185.93.109.70
```

Если сломается только nginx на новом сервере, быстрый откат конфига:

```bash
sudo cp /root/nginx-insain-before-prod.conf /etc/nginx/sites-enabled/insain.ru
sudo nginx -t
sudo systemctl reload nginx
```

## Дальше: автономная работа агентов

После cutover настройте Cursor, SSH-пользователя `agent`, Browser и деплой `wp-plugin`: [agent-autonomous-environment.md](agent-autonomous-environment.md).
