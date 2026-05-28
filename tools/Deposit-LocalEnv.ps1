<#
.SYNOPSIS
    Setzt eine lokale Windows-Umgebungsvariable (User-Scope) sicher per verdeckter Eingabe.

.DESCRIPTION
    Liest den Wert verdeckt via Read-Host -AsSecureString ein, haelt ihn nur transient im
    RAM (BSTR -> String) und schreibt ihn per [Environment]::SetEnvironmentVariable in den
    User-Scope. Der Wert wird NIE in eine Datei, ein Log oder die PowerShell-History
    geschrieben und niemals in der Ausgabe angezeigt -- gemeldet wird nur Name + Laenge.

    Use-Case: Der CFO-Agent benoetigt BINANCE_API_KEY / BINANCE_API_SECRET als Umgebungs-
    variablen. Dennis setzt sie hiermit selbst -- keine Datei auf der Platte, kein Agent
    sieht oder loggt den Wert.

    Sicherheitsmodell:
      - SecureString-Eingabe; Klartext nur via Marshal-BSTR und sofortiges ZeroFreeBSTR.
      - Setzen erfolgt direkt im User-Scope (HKCU\Environment via SetEnvironmentVariable).
      - Validierung: VarName muss dem Env-Var-Namensschema entsprechen
        (^[A-Za-z_][A-Za-z0-9_]*$), keine "..", keine Pfadtrenner.
      - Ausgabe: nur "<VarName> gesetzt (Laenge: N Zeichen). ..." -- nie der Wert.

.PARAMETER VarName
    Name der zu setzenden Umgebungsvariable. Muss ^[A-Za-z_][A-Za-z0-9_]*$ erfuellen.

.EXAMPLE
    .\Deposit-LocalEnv.ps1 -VarName BINANCE_API_KEY
    Fragt den Wert verdeckt ab und setzt BINANCE_API_KEY im User-Scope.

.EXAMPLE
    .\Deposit-LocalEnv.ps1 -VarName BINANCE_API_SECRET
    Wie oben, fuer das Secret. Neue PowerShell-Session starten, damit Kinder den Wert erben.

.NOTES
    Testbarkeit: Dot-Sourcing (. .\Deposit-LocalEnv.ps1 -VarName placeholder) ueberspringt
    den interaktiven Einstieg und laedt nur die Funktionen (Test-LocalEnvVarName,
    Set-LocalEnvFromSecureString). Siehe tools\selftest-DepositLocalEnv.ps1.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $VarName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Validierung VarName (Schutz gegen Injection/Pfad-Tricks) ---
function Test-LocalEnvVarName {
    param([Parameter(Mandatory)][string] $Name)
    if ($Name -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
        throw "Ungueltiger VarName '$Name'. Erlaubt: Buchstaben, Ziffern, '_' -- muss mit Buchstabe/'_' beginnen."
    }
    if ($Name -eq '.' -or $Name -eq '..') {
        throw "Ungueltiger VarName '$Name' (reserviert)."
    }
}

<#
    Kern: nimmt eine SecureString und setzt sie als User-Scope-Env-Var.
    Plaintext entsteht nur transient (BSTR), wird sofort genullt/freigegeben.
    Rueckgabe: PSCustomObject mit VarName und Length (in Zeichen). Wirft bei Fehler
    ohne den Wert preiszugeben.
#>
function Set-LocalEnvFromSecureString {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]                       $VarName,
        [Parameter(Mandatory)][System.Security.SecureString] $SecureValue
    )

    Test-LocalEnvVarName -Name $VarName
    if ($SecureValue.Length -eq 0) {
        throw "Leerer Wert -- Abbruch (Variable wurde nicht gesetzt)."
    }

    $bstr  = [IntPtr]::Zero
    $plain = $null
    try {
        $bstr  = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        $len   = $plain.Length

        [Environment]::SetEnvironmentVariable($VarName, $plain, 'User')
    }
    finally {
        # Plaintext-String aus dem RAM raeumen (best effort -- .NET-Strings sind immutable,
        # darum wird die Referenz genullt und GC angestossen; BSTR wird hart genullt).
        $plain = $null
        if ($bstr -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
    }

    return [PSCustomObject]@{
        VarName = $VarName
        Length  = $len
    }
}

# ----------------------------------------------------------------------------
# Interaktiver Einstieg. Wird uebersprungen, wenn die Datei dot-gesourct wird
# (z.B. aus dem Selbsttest), damit nur die Funktionen geladen werden.
# ----------------------------------------------------------------------------
if ($MyInvocation.InvocationName -ne '.') {

    Test-LocalEnvVarName -Name $VarName

    $secure = Read-Host -AsSecureString "Wert fuer '$VarName' (Eingabe wird verdeckt)"
    if ($null -eq $secure -or $secure.Length -eq 0) {
        throw "Leerer Wert -- Abbruch (Variable wurde nicht gesetzt)."
    }

    try {
        $result = Set-LocalEnvFromSecureString -VarName $VarName -SecureValue $secure
    }
    finally {
        $secure.Dispose()
    }

    Write-Host ""
    Write-Host "$($result.VarName) gesetzt (Laenge: $($result.Length) Zeichen). Neue PowerShell-Session starten damit Agenten den Wert erben." -ForegroundColor Green
}
