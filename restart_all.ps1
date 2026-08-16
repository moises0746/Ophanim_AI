Write-Host "Restarting Ophanim AI Services..."
.\stop_all.ps1
Start-Sleep -Seconds 2
.\start_all.ps1
