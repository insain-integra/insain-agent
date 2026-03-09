$slugs = @(
  "laser",
  "print_sheet",
  "print_laser",
  "lamination",
  "milling",
  "cut_plotter",
  "cut_guillotine",
  "cut_roller"
)

foreach ($slug in $slugs) {
    Write-Host "=== $slug ==="
    curl -s "http://localhost:8001/api/v1/param_schema/$slug" | jq '.slug, (.params | length), .param_groups'
    Write-Host ""
}

