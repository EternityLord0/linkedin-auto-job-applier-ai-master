# consertar_layout_e_sessao.ps1
$log = @()
$log += "Iniciando ajuste de sessao e teclado: $(Get-Date)"

# 1. Ajustar lista de idiomas do usuario para APENAS Portugues (Brasil) ABNT2
try {
    $langList = New-WinUserLanguageList "pt-BR"
    # Adicionar layout ABNT2 (0416:00010416)
    $langList[0].InputMethodTips.Clear()
    $langList[0].InputMethodTips.Add("0416:00010416")
    Set-WinUserLanguageList $langList -Force
    $log += "Layout de teclado redefinido exclusivamente para Portugues (Brasil) - ABNT2."
} catch {
    $log += "Erro ao definir layout: $_"
}

# 2. Ajustar Preload no Registro para ABNT2 puro (00000416 / 00010416)
try {
    Set-ItemProperty -Path "HKCU:\Keyboard Layout\Preload" -Name "1" -Value "00010416"
    Remove-ItemProperty -Path "HKCU:\Keyboard Layout\Preload" -Name "2" -ErrorAction SilentlyContinue
    $log += "Preload do registro configurado para ABNT2."
} catch {
    $log += "Erro no registro de teclado: $_"
}

# 3. Reiniciar Windows Explorer e ctfmon para recarregar todos os hooks de janelas
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

$log += "Concluido em $(Get-Date)"
$log | Out-String | Write-Output
