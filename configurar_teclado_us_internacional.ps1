# configurar_teclado_us_internacional.ps1
$log = @()
$log += "Configurando teclado Estados Unidos (Internacional): $(Get-Date)"

try {
    $langList = New-WinUserLanguageList "pt-BR"
    $langList[0].InputMethodTips.Clear()
    # Adiciona apenas Estados Unidos (Internacional)
    $langList[0].InputMethodTips.Add("0416:00020409")
    Set-WinUserLanguageList $langList -Force
    $log += "Lista de idiomas configurada: Portugues (Brasil) com layout Estados Unidos (Internacional)."
} catch {
    $log += "Erro ao definir idioma: $_"
}

try {
    # No registro, 00020409 e o codigo do teclado US-International
    Set-ItemProperty -Path "HKCU:\Keyboard Layout\Preload" -Name "1" -Value "00020409"
    # Remove layouts extras
    Remove-ItemProperty -Path "HKCU:\Keyboard Layout\Preload" -Name "2" -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path "HKCU:\Keyboard Layout\Preload" -Name "3" -ErrorAction SilentlyContinue
    $log += "Preload do registro configurado exclusivamente para US-International (00020409)."
} catch {
    $log += "Erro no registro: $_"
}

# Reiniciar ctfmon e Explorer para aplicar imediatamente na sessao
try {
    Stop-Process -Name ctfmon, TextInputHost -Force -ErrorAction SilentlyContinue
    Start-Process ctfmon.exe
    $log += "ctfmon reiniciado."
} catch {}

try {
    Stop-Process -Name explorer -Force
    $log += "Windows Explorer reiniciado com sucesso."
} catch {
    $log += "Erro ao reiniciar Explorer: $_"
}

$log += "Finalizado em $(Get-Date)"
$log | Out-String | Write-Output
