# EPIC-antispam-recaptcha

Статус: черновик

## Цель

На https://insain.ru Google reCAPTCHA не используется. На login, register и остальных точках, где сейчас Simple Google reCAPTCHA, стоит Yandex SmartCaptcha (или согласованный аналог из РФ). Публичная регистрация магазина сохранена; поток спам-регистраций заметно снижен за счёт капчи и ужесточения настроек, без отключения защиты «на время». Логин `/my-account/` из РФ без VPN проходит.

Чистка уже накопившихся спам-аккаунтов — не здесь: `todo/EPIC-spam-users-cleanup.md`.

## Задачи

- `todo/smartcaptcha-replace.md` — инвентарь точек Google reCAPTCHA → SmartCaptcha на те же точки → снятие Google только после smoke
- `todo/registration-harden.md` — открытая регистрация магазина + согласование Akismet/Woo/ролей после живой капчи на register

## Порядок

Последовательно: обе задачи правят `/my-account/`, `STATUS.md` и `docs/site/`. Вторая стоит в `заблокировано: ждёт todo/smartcaptcha-replace.md` ([docs/agents/workflow.md](../docs/agents/workflow.md)).

1. `todo/smartcaptcha-replace.md` — ключи Yandex Cloud даёт человек до или в начале работы (вне git)
2. `todo/registration-harden.md` — после предыдущей: капча на регистрации уже проверяет submit
