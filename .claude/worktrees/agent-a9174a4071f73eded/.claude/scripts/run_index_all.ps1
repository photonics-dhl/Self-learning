# Run batch_index_postdoc.py per professor to avoid model reload issues
$professors = @(
    "baum", "chang", "gedik", "hommelhoff", "huber", "kaertner",
    "keller", "kling", "krausz", "leone", "lhuillier", "miao",
    "murnane", "nisoli", "ropers"
)

$all_start = Get-Date
$results = @()

foreach ($prof in $professors) {
    $prof_start = Get-Date
    Write-Host "============================================================="
    Write-Host "[$prof] $(Get-Date -Format 'HH:mm:ss') Starting..."
    Write-Host "============================================================="

    $output = python "z:/321/DHL/Self_Learning/academic_rag/batch_index_postdoc.py" --professor $prof 2>&1
    $output | ForEach-Object { $_ }

    $prof_elapsed = (Get-Date) - $prof_start
    $total_elapsed = (Get-Date) - $all_start
    $results += "[$prof] $([math]::Round($prof_elapsed.TotalSeconds))s"
    Write-Host "[$prof] Done in $([math]::Round($prof_elapsed.TotalSeconds))s (total: $([math]::Round($total_elapsed.TotalSeconds))s)"
}

Write-Host "`n============================================================="
Write-Host "ALL DONE in $([math]::Round(((Get-Date) - $all_start).TotalSeconds))s"
foreach ($r in $results) {
    Write-Host "  $r"
}
Write-Host "============================================================="
