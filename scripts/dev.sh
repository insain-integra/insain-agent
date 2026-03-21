#!/usr/bin/env bash
# То же, что «make up/down/…» — если в Git Bash нет команды make.
# Примеры:  bash scripts/dev.sh start all
#           bash scripts/dev.sh status
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python "$ROOT/scripts/dev.py" "$@"
