#!/usr/bin/env bash
# Деплой insain-agent на VDS: git pull и перезапуск calc-api.
# Единственное определение прода — docker-compose.calc-only.yml:
# 127.0.0.1:8002 → 8001, SITE_URL=https://insain.ru, наружу — nginx.
#
# Требования: git, docker compose v2.
#
# Использование на сервере:
#   bash infra/deploy.sh
#
# Firewall (пример ufw): SSH, Nginx Full; порт 8002 снаружи не открывать.
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

echo ">>> docker compose up -d --build (VDS: calc-api на 127.0.0.1:8002)"
docker compose -f docker-compose.calc-only.yml up -d --build

echo ">>> Состояние контейнеров"
docker compose -f docker-compose.calc-only.yml ps

echo ">>> Готово. Проверка:"
echo "    curl -fsS https://insain.ru/api/v1/calculators | head -c 200; echo"
