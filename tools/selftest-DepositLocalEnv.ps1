<#
.SYNOPSIS
    Selbsttest fuer Deposit-LocalEnv.ps1: setzt einen DUMMY-User-Env-Var, prueft den
    gelesenen Wert via [Environment]::GetEnvironmentVariable und raeumt wieder auf.
    Zusaetzlich Negativtests fuer Test-LocalEnvVarName.

.EXAMPLE
    .\selftest-DepositLocalEnv.ps1
#>
[CmdletBinding()]
param(
    [string] $VarName = 'PAPERCLIP_SELFTEST_TMP',
    [string] $DummyValue = 'hallo-1234'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# WICHTIG: Dot-Sourcing von Deposit-LocalEnv.ps1 fuehrt dessen param()-Block im aktuellen
# Scope aus und ueberschreibt $VarName mit 'placeholder'. Daher Test-Eingaben vorher in
# eine Hashtable sichern und danach nur diese verwenden.
$t = @{
    VarName    = $VarName
    DummyValue = $DummyValue
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Funktionen laden (interaktiver Einstieg wird durch Dot-Sourcing uebersprungen).
. (Join-Path $scriptDir 'Deposit-LocalEnv.ps1') -VarName 'placeholder'

$pass = $true

Write-Host "== Selbsttest Deposit-LocalEnv ==" -ForegroundColor Cyan

# Happy path: SecureString programmatisch erzeugen und setzen.
$secure = ConvertTo-SecureString -String $t.DummyValue -AsPlainText -Force
try {
    $r = Set-LocalEnvFromSecureString -VarName $t.VarName -SecureValue $secure
    Write-Host "Set: VarName=$($r.VarName) Length=$($r.Length)"
    if ($r.VarName -ne $t.VarName)            { $pass = $false; Write-Host "FAIL: VarName-Mismatch" -ForegroundColor Red }
    if ($r.Length  -ne $t.DummyValue.Length)  { $pass = $false; Write-Host "FAIL: Length-Mismatch" -ForegroundColor Red }

    $read = [Environment]::GetEnvironmentVariable($t.VarName, 'User')
    if ($read -ne $t.DummyValue) {
        $pass = $false
        Write-Host "FAIL: Gelesener Wert weicht ab (Laenge gelesen: $($read.Length))" -ForegroundColor Red
    } else {
        Write-Host "OK: Wert via GetEnvironmentVariable(User) korrekt zurueckgelesen."
    }
}
catch {
    $pass = $false
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    $secure.Dispose()
    # Aufraeumen: Dummy-Var wieder entfernen. PowerShell coerced $null zu '', daher
    # explizit [NullString]::Value, das die Variable wirklich aus dem User-Scope loescht.
    [Environment]::SetEnvironmentVariable($t.VarName, [NullString]::Value, 'User')
    Write-Host "Cleanup: $($t.VarName) entfernt."
}

# Negativtests: ungueltige Namen muessen abgelehnt werden.
foreach ($bad in @('..', '1FOO', 'a-b', 'a b', 'a;b', 'a$b', 'a/b', 'a.b')) {
    $rejected = $false
    try { Test-LocalEnvVarName -Name $bad } catch { $rejected = $true }
    if (-not $rejected) { $pass = $false; Write-Host "FAIL: '$bad' nicht abgelehnt" -ForegroundColor Red }
    else { Write-Host "OK (abgelehnt): '$bad'" }
}

# Positivtests: gueltige Namen werden akzeptiert.
foreach ($good in @('BINANCE_API_KEY', '_FOO', 'a', 'A1', 'X_2_Y')) {
    $accepted = $true
    try { Test-LocalEnvVarName -Name $good } catch { $accepted = $false }
    if (-not $accepted) { $pass = $false; Write-Host "FAIL: '$good' nicht akzeptiert" -ForegroundColor Red }
    else { Write-Host "OK (akzeptiert): '$good'" }
}

if ($pass) { Write-Host "`nSELFTEST PASS" -ForegroundColor Green; exit 0 }
else       { Write-Host "`nSELFTEST FAIL" -ForegroundColor Red;  exit 1 }
