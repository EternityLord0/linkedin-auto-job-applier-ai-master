$log = "$env:TEMP\fix_teclado.log"
"Starting fix at $(Get-Date)" | Out-File $log

# 1. Kill malware processes
$targets = @('UpdateSystem', 'UpdateRede', 'CUH')
foreach ($name in $targets) {
    $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        try {
            $path = $p.Path
            if (-not $path) { $path = $p.MainModule.FileName }
            "Found $name at $path (PID $($p.Id))" | Out-File $log -Append
            Stop-Process -Id $p.Id -Force
            if ($path -and (Test-Path $path)) {
                Remove-Item $path -Force
                "Deleted $path" | Out-File $log -Append
            }
        } catch {
            "Error on $name : $_" | Out-File $log -Append
        }
    }
}

# Also try taskkill
cmd /c "taskkill /F /IM UpdateSystem.exe /IM UpdateRede.exe /T 2>&1" | Out-File $log -Append

# 2. Clean Run keys from registry
Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'System32','DriverNetwork' -ErrorAction SilentlyContinue

# 3. Restart Windows text/keyboard input host to reset dead keys buffer
Get-Process TextInputHost, ctfmon -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Process ctfmon.exe

"Finished fix at $(Get-Date)" | Out-File $log -Append
