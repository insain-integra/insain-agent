# Проверить все калькуляторы
for slug in laser print_sheet print_laser lamination milling cut_plotter cut_guillotine cut_roller: 
do
  echo "=== $slug ==="
  curl -s http://localhost:8001/api/v1/param_schema/$slug | jq '.slug, (.params | length), .param_groups'
done

# Должны все вернуть валидные схемы