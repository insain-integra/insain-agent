#!/usr/bin/env bash
# Деплой insain-agent на VDS: git pull и перезапуск calc-api с воротами.
# Единственное определение прода — docker-compose.calc-only.yml:
# 127.0.0.1:8002 → 8001, SITE_URL=https://insain.ru, наружу — nginx.
#
# Требования: git, docker compose v2, curl.
#
# Использование на сервере:
#   bash infra/deploy.sh
#
# Ворота:
#   1. Отказ, если ветка не main или рабочее дерево грязное.
#   2. Перед сборкой текущий образ тегируется как insain-agent-calc-api:rollback.
#   3. После выкатки smoke: GET /api/v1/calculators = 200 и POST /api/v1/calc/puzzle = 200 с price.
#   4. Smoke упал — откат кода (git reset на прежний коммит) и образа на rollback,
#      повторный smoke, выход с ненулевым кодом.
#
# Переменные окружения:
#   INSAIN_REPO_DIR   — каталог клона (по умолчанию корень репозитория рядом со скриптом).
#   SMOKE_BASE_URL    — куда стучится smoke (по умолчанию http://127.0.0.1:8002).
#   SMOKE_EXTRA_PATH  — доп. GET в smoke после выкатки (не при повторном smoke после отката).
#                       Для проверки отката: SMOKE_EXTRA_PATH=/api/v1/nonexistent bash infra/deploy.sh
#
# Firewall (пример ufw): SSH, Nginx Full; порт 8002 снаружи не открывать.
#   sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable

set -euo pipefail

INSAIN_REPO_DIR="${INSAIN_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://127.0.0.1:8002}"
SMOKE_EXTRA_PATH="${SMOKE_EXTRA_PATH:-}"

COMPOSE_FILE="docker-compose.calc-only.yml"
IMAGE="insain-agent-calc-api"
SMOKE_WAIT_SECONDS=60
SMOKE_CALC_BODY='{"quantity": 1, "puzzle_id": "Puzzle300420", "mode": 1}'

cd "$INSAIN_REPO_DIR"

g() { git -c safe.directory="$INSAIN_REPO_DIR" "$@"; }
dc() { docker compose -f "$COMPOSE_FILE" "$@"; }
fail() { echo "!!! $*" >&2; exit 1; }

echo ">>> Репозиторий: $INSAIN_REPO_DIR"

[[ -d .git ]] || fail "каталог не git-клон (.git нет), деплой отменён"

branch="$(g rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "main" ]] || fail "ветка '$branch', деплой только с main"

if [[ -n "$(g status --porcelain)" ]]; then
  g status --short >&2
  fail "рабочее дерево грязное, деплой отменён"
fi

prev_commit="$(g rev-parse HEAD)"

echo ">>> git pull --ff-only"
g pull --ff-only
new_commit="$(g rev-parse HEAD)"
echo ">>> Коммит: ${prev_commit:0:7} → ${new_commit:0:7}"

have_rollback=0
if docker image inspect "$IMAGE:latest" >/dev/null 2>&1; then
  docker tag "$IMAGE:latest" "$IMAGE:rollback"
  have_rollback=1
  echo ">>> Текущий образ сохранён как $IMAGE:rollback ($(docker image inspect -f '{{.Id}}' "$IMAGE:rollback" | cut -c8-19))"
else
  echo ">>> Предупреждение: образа $IMAGE:latest нет, откат будет недоступен"
fi

# smoke [extra_path] — ждёт готовности API, затем проверяет список калькуляторов и расчёт puzzle.
smoke() {
  local extra_path="${1:-}" code body i
  echo ">>> Smoke: $SMOKE_BASE_URL"
  for ((i = 0; i < SMOKE_WAIT_SECONDS; i += 2)); do
    code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$SMOKE_BASE_URL/api/v1/calculators" 2>/dev/null || true)"
    [[ "$code" == "200" ]] && break
    sleep 2
  done
  echo "    GET /api/v1/calculators → $code"
  [[ "$code" == "200" ]] || return 1

  body="$(curl -sS --max-time 15 -H 'Content-Type: application/json' -d "$SMOKE_CALC_BODY" \
    -w '\n%{http_code}' "$SMOKE_BASE_URL/api/v1/calc/puzzle" 2>/dev/null || true)"
  code="${body##*$'\n'}"
  echo "    POST /api/v1/calc/puzzle → $code"
  [[ "$code" == "200" && "$body" == *'"price"'* ]] || return 1

  if [[ -n "$extra_path" ]]; then
    code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$SMOKE_BASE_URL$extra_path" 2>/dev/null || true)"
    echo "    GET $extra_path → $code"
    [[ "$code" == "200" ]] || return 1
  fi
  return 0
}

echo ">>> docker compose up -d --build (VDS: calc-api на 127.0.0.1:8002)"
dc up -d --build

if smoke "$SMOKE_EXTRA_PATH"; then
  echo ">>> Состояние контейнеров"
  dc ps
  echo ">>> Готово: ${new_commit:0:7} выкачен, smoke пройден."
  exit 0
fi

echo "!!! Smoke после выкатки ${new_commit:0:7} не пройден." >&2
[[ "$have_rollback" == "1" ]] || fail "образа rollback нет, откатывать не на что. Прод требует ручного разбора."

echo ">>> Откат: код на ${prev_commit:0:7}, образ $IMAGE:rollback"
g reset --hard "$prev_commit"
docker tag "$IMAGE:rollback" "$IMAGE:latest"
dc up -d --no-build --force-recreate

if smoke; then
  dc ps
  fail "деплой ${new_commit:0:7} откачен на ${prev_commit:0:7}, прод работает на прежнем образе. Разберите причину до повторного деплоя."
fi
dc ps || true
fail "деплой ${new_commit:0:7} откачен, но smoke после отката тоже не пройден. Прод требует ручного разбора."
