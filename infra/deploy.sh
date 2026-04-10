#!/usr/bin/env bash
# Деплой insain-agent на VDS: git pull и перезапуск контейнеров.
# calc-api слушает только 127.0.0.1:8001 (см. infra/compose.vds.yml), наружу — nginx.
#
# Требования: git, docker compose v2, в корне репозитория есть .env для tg-bot.
#
# Использование на сервере:
#   export INSAIN_REPO_DIR=/var/www/insain-agent
#   bash infra/deploy.sh
#
# Firewall (пример ufw): SSH, Nginx Full; порт 8001 снаружи не открывать.
#   sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable

set -euo pipefail

INSAIN_REPO_DIR="${INSAIN_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cd "$INSAIN_REPO_DIR"

echo ">>> Репозиторий: $INSAIN_REPO_DIR"

if [[ -d .git ]]; then
  echo ">>> git pull"
  git pull --ff-only
else
  echo ">>> Предупреждение: каталог не похож на git-клон (.git нет), пропускаю pull"
fi

echo ">>> docker compose up -d --build (VDS: calc-api на 127.0.0.1:8001)"
docker compose -f docker-compose.yml -f infra/compose.vds.yml up -d --build

echo ">>> Состояние контейнеров"
docker compose -f docker-compose.yml -f infra/compose.vds.yml ps

echo ">>> Готово. Проверка (после DNS и certbot):"
echo "    curl -fsS https://calc.insain.ru/api/v1/calculators | head -c 200; echo"
