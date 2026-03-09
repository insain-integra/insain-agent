#!/usr/bin/env bash

# Проверка схем параметров для основных калькуляторов.
# Требует запущенный calc_service на http://localhost:8001
# и установленный jq.

set -euo pipefail

SLUGS=(
  laser
  print_sheet
  print_laser
  lamination
  milling
  cut_plotter
  cut_guillotine
  cut_roller
)

for slug in "${SLUGS[@]}"; do
  echo "=== ${slug} ==="
  curl -s "http://localhost:8001/api/v1/param_schema/${slug}" | jq '.slug, (.params | length), .param_groups'
  echo
done

