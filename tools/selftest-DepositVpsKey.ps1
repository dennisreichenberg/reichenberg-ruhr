<#
.SYNOPSIS
    Selbsttest fuer Deposit-VpsKey.ps1: legt einen DUMMY-Key auf dem VPS ab,
    verifiziert Perms/Size und raeumt wieder auf. Kein echtes Secret.

.DESCRIPTION
    Dot-sourct Deposit-VpsKey.ps1 (Funktionen ohne interaktiven Einstieg) und ruft
    Invoke-VpsKeyDeposit mit einer programmatisch erzeugten SecureString (Dummy) auf.
    Erwartung: Datei mit Perms 600 und Size = Laenge des Dummy-Werts.
    Zusaetzlich Negativtests fuer Test-VpsKeyName (Injection-/Pfad-Schutz).

.EXAMPLE
    .\selftest-DepositVpsKey.ps1 -IdentityFile $HOME\.ssh\test_key
#>
[CmdletBinding()]
param(
    [string] $IdentityFile = (Join-Path $HOME '.ssh\ionos_admin_ed25519'),
    [string] $VpsHost = '217.160.192.248',
    [string] $VpsUser = 'admin',
    [int]    $Port = 22,
    [string] $RemoteDir = 'secrets',
    [string] $KeyName = 'selftest_dummy'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# WICHTIG: Dot-Sourcing von Deposit-VpsKey.ps1 fuehrt dessen param()-Block im aktuellen
# Scope aus und ueberschreibt gleichnamige Variablen (VpsHost, Port, ...). Daher die
# Test-Eingaben vorher in eine Hashtable sichern und danach nur diese verwenden.
$t = @{
    IdentityFile = $IdentityFile
    VpsHost      = $VpsHost
    VpsUser      = $VpsUser
    Port         = $Port
    RemoteDir    = $RemoteDir
    KeyName      = $KeyName
    SshExe       = (Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe')
}
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Funktionen laden (interaktiver Einstieg wird durch Dot-Sourcing uebersprungen).
. (Join-Path $scriptDir 'Deposit-VpsKey.ps1') -KeyName 'placeholder'

$dummy = 'dummy-secret-value-1234'   # 23 Zeichen
$expectedSize = [System.Text.Encoding]::UTF8.GetByteCount($dummy)
$secure = ConvertTo-SecureString -String $dummy -AsPlainText -Force

Write-Host "== Selbsttest Deposit-VpsKey ==" -ForegroundColor Cyan
Write-Host "Erwartet: Perms 600, Size $expectedSize"

$pass = $true
try {
    $r = Invoke-VpsKeyDeposit -KeyName $t.KeyName -SecureValue $secure `
        -VpsHost $t.VpsHost -VpsUser $t.VpsUser -Port $t.Port -IdentityFile $t.IdentityFile `
        -RemoteDir $t.RemoteDir -SshExe $t.SshExe -NonInteractive

    Write-Host "Ergebnis: Path=$($r.Path) Perms=$($r.Perms) Size=$($r.Size)"
    if ($r.Perms -ne '600')        { $pass = $false; Write-Host "FAIL: Perms != 600" -ForegroundColor Red }
    if ($r.Size  -ne $expectedSize){ $pass = $false; Write-Host "FAIL: Size != $expectedSize" -ForegroundColor Red }
}
catch {
    $pass = $false
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "AT: $($_.InvocationInfo.PositionMessage)" -ForegroundColor Red
}
finally {
    $secure.Dispose()
    # Aufraeumen: Dummy wieder entfernen.
    & $t.SshExe -i $t.IdentityFile -p $t.Port -o StrictHostKeyChecking=accept-new -o BatchMode=yes `
        "$($t.VpsUser)@$($t.VpsHost)" "rm -f ~/'$($t.RemoteDir)'/'$($t.KeyName)'" 2>&1 | Out-Null
    Write-Host "Cleanup: ~/$($t.RemoteDir)/$($t.KeyName) entfernt."
}

# Negativtests: ungueltige Namen muessen abgelehnt werden.
foreach ($bad in @('..', 'a/b', 'a;b', 'a b', 'a$b', 'a`b')) {
    $rejected = $false
    try { Test-VpsKeyName -Name $bad } catch { $rejected = $true }
    if (-not $rejected) { $pass = $false; Write-Host "FAIL: '$bad' nicht abgelehnt" -ForegroundColor Red }
    else { Write-Host "OK (abgelehnt): '$bad'" }
}

if ($pass) { Write-Host "`nSELFTEST PASS" -ForegroundColor Green; exit 0 }
else       { Write-Host "`nSELFTEST FAIL" -ForegroundColor Red;  exit 1 }
