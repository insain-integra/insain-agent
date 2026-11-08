---
name: deploy-api
description: Выкатка calc_service (API) на прод insain.ru с main через bash infra/deploy.sh — ворота, smoke, автооткат, проверка. Применять после слияния в main правки calc_service/ или infra/, когда CI на коммите зелёный. Не для плагина (skill deploy-wp-plugin) и не для смены цен (skill json-price-rollout — он ссылается сюда на выкатку).
---

# Деплой API

Деплой API с `main` входит в «Делай самостоятельно» в `.cursor/rules/insain-site-autonomous.mdc`. Ручной `git pull` и `docker compose` для выкатки не использовать.

Деплоить только коммит с зелёным CI (GitHub Actions, `make check`).

```bash
ssh insain-prod            # с первого раза может отвалиться по таймауту — повторить
cd /opt/insain-agent
bash infra/deploy.sh       # main + чистое дерево → tag rollback → pull → build → smoke → автооткат
curl -fsS https://insain.ru/api/v1/calculators | head -c 200
```

Smoke в скрипте: `GET /api/v1/calculators` и `POST /api/v1/calc/puzzle`. Упал — скрипт сам откатывает код
и образ на `insain-agent-calc-api:rollback` и выходит с ненулевым кодом. Проверка отката без поломки прода:
`SMOKE_EXTRA_PATH=/api/v1/nonexistent bash infra/deploy.sh`. Затем smoke на странице калькулятора.
Git на VDS: `git -c safe.directory=/opt/insain-agent -C /opt/insain-agent …`.
