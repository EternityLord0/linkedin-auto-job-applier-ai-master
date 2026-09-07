# diagnostico_completo.ps1
$outputFile = "$env:TEMP\diagnostico_processos.txt"
"=== DIAGNOSTICO COMPLETO DE PROCESSOS ===" | Out-File $outputFile

# Todos os processos com seus caminhos e nomes
Get-Process | Where-Object { $_.Path } | Select-Object Id, ProcessName, Path, Company, Description | Sort-Object ProcessName | Format-Table -AutoSize | Out-String -Width 300 | Out-File $outputFile -Append

# Checar processos que nao sao da Microsoft ou nao estao em C:\Windows
"=== PROCESSOS FORA DE C:\WINDOWS E FORA DE PROGRAM FILES ===" | Out-File $outputFile -Append
Get-Process | Where-Object { 
    $_.Path -and 
    $_.Path -notmatch "^C:\\Windows" -and 
    $_.Path -notmatch "^C:\\Program Files"
} | Select-Object Id, ProcessName, Path | Format-Table -AutoSize | Out-String -Width 300 | Out-File $outputFile -Append

# Checar conexoes de rede ativas (ESTABLISHED) por processos
"=== CONEXOES DE REDE ATIVAS ===" | Out-File $outputFile -Append
Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess | Format-Table -AutoSize | Out-String -Width 300 | Out-File $outputFile -Append

Write-Output "Diagnostico salvo em $outputFile"
