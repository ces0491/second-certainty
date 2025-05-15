# fetch_all_tax_years.ps1

$START_YEAR = 2018
$END_YEAR = 2023

for ($year = $START_YEAR; $year -le $END_YEAR; $year++) {
  $next_year = $year + 1
  $tax_year = "$year-$next_year"
  
  Write-Host "Fetching tax data for $tax_year..."
  python fetch_tax_data.py --year $tax_year --force
  
  # Add a small delay
  Start-Sleep -Seconds 2
}

Write-Host "All tax years processed!"