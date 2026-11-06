# smartcaptcha-replace

Статус: черновик
Сложность: высокая
Implementer: не нужен
Reviewer: Grok 4.7
Site ops: Opus 5.5
Почему: прод WordPress, смена антиспама без окна без защиты.
Чат: человек открывает новый чат Site ops с моделью из поля Site ops; ключи SmartCaptcha — только вне git и без записи секретов в репозиторий.

## Цель

Плагин Simple Google reCAPTCHA на проде не активен. На всех точках, где он защищал submit (как минимум WooCommerce login и register на `/my-account/`, плюс остальные флаги плагина по инвентарю), работает Yandex SmartCaptcha. Логин и регистрация из РФ без VPN проходят без ошибки `Google reCAPTCHA verification failed`. Google-плагин снимают только после успешного smoke новой капчи.

## Контекст и ссылки

- Эпик `todo/EPIC-antispam-recaptcha.md` — порядок и связь с harden.
- Следующая задача эпика: `todo/registration-harden.md` (не смешивать scope).
- Чистка старых аккаунтов — `todo/EPIC-spam-users-cleanup.md`, не эта задача.
- `STATUS.md` — плагин `simple-google-recaptcha` 3.9 active; также `akismet` 5.7 (только читать статус, не настраивать здесь).
- `.cursor/rules/insain-site-autonomous.mdc` — целиком до первого действия на сервере.
- `docs/site/access-tools.md` — wp-cli, Browser MCP; секреты и ключи в git не класть.
- Симптом: https://insain.ru/my-account/ → `Error: Google reCAPTCHA verification failed. Do you have JavaScript enabled?`
- Остальное не открывать.

## Scope

1. Инвентарь (только чтение): опции Simple Google reCAPTCHA — какие экраны включены (login, register, lost password, CF7, comments, checkout и т.д.). Список точек записать в «Результат».
2. Человек создаёт ключи Yandex SmartCaptcha (client key + server key) для домена `insain.ru` (и `www`, если используется) и передаёт Site ops вне репозитория. Без ключей установку на прод не начинать.
3. Установить и активировать официальный/согласованный плагин Yandex SmartCaptcha для WordPress; настроить те же точки, что в инвентаре п.1 (минимум: login + register WooCommerce / WP).
4. Smoke при ещё активном Google-плагине, если оба могут сосуществовать без двойного ломания форм; если конфликт — сначала спросить человека, не отключать Google молча.
5. После успешного smoke: deactivate `simple-google-recaptcha` (удалять файлы плагина не обязательно в этой задаче).
6. Повторный smoke: логин и регистрация без Google-ошибки; в Network на этих страницах нет обязательной загрузки `google.com/recaptcha` / `gstatic.com/recaptcha` для проверки submit.
7. Обновить `STATUS.md` (версия/статус плагинов). Краткая заметка в `docs/site/` — что стоит вместо Google и что ключи только в WP/админке, не в git (без секретов).

Git-правок calc/bot/wp-plugin bridge не требуется, если не понадобится мелкая док-правка в `docs/site/`. Операции на WP — Site ops по правилу прода.

Распределение: прод без git — всё делает Site ops, включая запись в `STATUS.md` и `docs/site/`. Reviewer смотрит отчёт Site ops с выводами команд.

## Файлы

- WordPress: плагины `simple-google-recaptcha` и SmartCaptcha, их настройки; страницы `/my-account/` (login, register) и точки из инвентаря
- `STATUS.md` — строки плагинов антиспама
- `docs/site/` — короткая заметка про капчу, без ключей

## Не-scope

- Отключение капчи «на время» или deactivate Google до рабочего SmartCaptcha.
- Удаление или правка пользователей, массовая чистка спама.
- Смена политики `users_can_register`, роли по умолчанию, гостевой checkout — это `registration-harden`.
- Настройка/ключ Akismet — `registration-harden`.
- ezFC, calc_service, цены, деплой API, `infra/deploy.sh`.
- Contact Form 7 / checkout — только если они были в инвентаре п.1 у Google-плагина; новые точки «на всякий случай» не добавлять без вопроса человеку.
- hCaptcha / Cloudflare Turnstile вместо Яндекса — только если человек явно сменил решение; по умолчанию Yandex SmartCaptcha.

## Критерии приёмки

Команды с VDS через `ssh insain-prod`, если не сказано иначе. Секреты в вывод не печатать.

- [ ] Инвентарь в «Результат»: таблица «экран → было у Google → покрыто SmartCaptcha».
- [ ] `sudo -u www-data wp plugin is-active simple-google-recaptcha --path=/var/www/insain.ru` — пустой вывод / не active (после переключения).
- [ ] Плагин SmartCaptcha active: `sudo -u www-data wp plugin list --path=/var/www/insain.ru --status=active --fields=name,status,version` — в списке есть плагин SmartCaptcha, нет активного `simple-google-recaptcha`.
- [ ] Browser MCP или ручная проверка человеком: открыть https://insain.ru/my-account/, войти тестовой/своей учёткой без VPN — нет текста `Google reCAPTCHA verification failed`.
- [ ] То же для регистрации нового тестового пользователя (потом тестового можно удалить вручную или оставить пометку в «Результат» для эпика cleanup) — submit не отвергается из‑за Google; SmartCaptcha отрабатывает.
- [ ] `STATUS.md` отражает актуальные плагины антиспама; в `docs/site/` есть короткая запись без ключей.

## Проверки

- [ ] `make check` — N/A для чисто WP-операций; если трогали только `STATUS.md` / `docs/site/`, check не обязателен. Если задели код в git — `make check` зелёный.
- [ ] Self-review — чеклист «Перед сдачей» в [AGENTS.md](../AGENTS.md); секреты не в diff.

## Риски

- Прод: установка плагина, deactivate Google, настройки капчи на login/register; ошибка конфигурации снова блокирует вход админа — держать SSH/wp-cli сессию, откат = снова activate `simple-google-recaptcha` только если SmartCaptcha сломан и человек подтвердил аварийный откат.
- Цены: нет.
- Формы: точки из инвентаря Simple Google reCAPTCHA; ezFC не трогать.

## Режим

прод

## Журнал передач

Строка на сессию: `<дата> — <роль>, <модель> — <итог> — дальше <роль>`. Блокер — по формату [docs/agents/workflow.md](../docs/agents/workflow.md).

## Найдено вне scope

- —

## Результат

- Ветка, PR или коммит:
- Сделано:
- Чем проверено:
- Не сделано и почему:
- Требуется решение:
- Откат:
