<#
.SYNOPSIS
    Legt einen geheimen Schluessel/Wert sicher auf dem IONOS-VPS ab (Self-Service).

.DESCRIPTION
    Laeuft lokal auf der Windows-Maschine und nutzt das eingebaute OpenSSH (ssh.exe).
    Der geheime Wert wird verdeckt (Read-Host -AsSecureString) eingegeben, nur
    transient im RAM als Klartext gehalten und ueber SSH-stdin an den VPS gepiped --
    NIE als Kommandozeilen-Argument, NIE in eine lokale Klartext-Datei, NIE ins Log.

    Ablage auf dem VPS: ~/<RemoteDir>/<KeyName> (Datei 600, Verzeichnis 700).
    Standard-RemoteDir: "secrets".

    Sicherheitsmodell:
      - SecureString-Eingabe; Klartext nur via Marshal-BSTR und sofortiges ZeroFreeBSTR.
      - Wert kommt remote ausschliesslich ueber stdin an (in remote "ps" nicht sichtbar).
      - Verifikation per "stat" (Perms+Size) -- niemals "cat" des Werts.
      - Bei Erfolg wird nur KeyName + Zielpfad + OK gemeldet, nie der Wert.

.PARAMETER KeyName
    Name des Schluessels (= Dateiname auf dem VPS). Erlaubt: A-Z a-z 0-9 _ . -
    Reservierte Namen "." und ".." werden abgelehnt (Pfad-Schutz).

.PARAMETER VpsHost
    Hostname/IPv4 des VPS. Default: 217.160.192.248

.PARAMETER VpsUser
    SSH-Benutzer. Default: admin

.PARAMETER Port
    SSH-Port. Default: 22

.PARAMETER IdentityFile
    Pfad zum privaten SSH-Key. Default: $HOME\.ssh\ionos_admin_ed25519

.PARAMETER RemoteDir
    Zielverzeichnis relativ zum Home auf dem VPS. Default: secrets

.PARAMETER SshExe
    Pfad zu ssh.exe. Default: das in Windows eingebaute OpenSSH.

.PARAMETER ConfigFile
    Optionale JSON-Config mit NICHT-geheimen Defaults (VpsHost, VpsUser, Port,
    IdentityFile, RemoteDir). Explizite Parameter ueberschreiben die Config.
    Die Config enthaelt KEINE Secrets.

.PARAMETER NonInteractive
    Setzt ssh BatchMode=yes (kein Passwort-/Passphrase-Prompt). Fuer automatisierte
    Selbsttests mit passphrase-losem Key. Im Normalfall NICHT setzen, damit ssh
    bei Bedarf nach der Key-Passphrase fragen kann.

.EXAMPLE
    .\Deposit-VpsKey.ps1 -KeyName binance_api_secret
    Fragt den Wert verdeckt ab und legt ihn unter ~/secrets/binance_api_secret (600) ab.

.EXAMPLE
    .\Deposit-VpsKey.ps1 -KeyName my_token -RemoteDir secrets -VpsUser admin
    Wie oben, mit explizitem Benutzer und Zielverzeichnis.

.NOTES
    Beim ersten Connect wird der Host-Key per TOFU akzeptiert (StrictHostKeyChecking=accept-new)
    und in known_hosts gespeichert. Danach wird er gegen den gespeicherten Key geprueft.

    Testbarkeit: Die Datei kann dot-gesourct werden (. .\Deposit-VpsKey.ps1 -KeyName x),
    dann wird der interaktive Teil uebersprungen und nur die Funktionen geladen
    (Invoke-VpsKeyDeposit, Test-VpsKeyName). Siehe tools\selftest-DepositVpsKey.ps1.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $KeyName,

    [string] $VpsHost,
    [string] $VpsUser,
    [int]    $Port,
    [string] $IdentityFile,
    [string] $RemoteDir,
    [string] $SshExe,
    [string] $ConfigFile,
    [switch] $NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Validierung KeyName (Schutz gegen Command-/Path-Injection) ---
function Test-VpsKeyName {
    param([Parameter(Mandatory)][string] $Name)
    if ($Name -notmatch '^[A-Za-z0-9_.-]+$') {
        throw "Ungueltiger KeyName '$Name'. Erlaubt nur: A-Z a-z 0-9 _ . -"
    }
    if ($Name -eq '.' -or $Name -eq '..') {
        throw "Ungueltiger KeyName '$Name' (reserviert)."
    }
}

# --- Validierung RemoteDir (Unterverzeichnisse ok, kein ..) ---
function Test-VpsRemoteDir {
    param([Parameter(Mandatory)][string] $Dir)
    if ($Dir -notmatch '^[A-Za-z0-9_./-]+$') {
        throw "Ungueltiges RemoteDir '$Dir'. Erlaubt nur: A-Z a-z 0-9 _ . / -"
    }
    if ($Dir -match '(^|/)\.\.(/|$)') {
        throw "Ungueltiges RemoteDir '$Dir' (.. nicht erlaubt)."
    }
}

# --- ssh-Argumentliste aufbauen (ArgumentList -> kein Quoting-Risiko) ---
function New-VpsSshArgs {
    param(
        [Parameter(Mandatory)][string] $IdentityFile,
        [Parameter(Mandatory)][int]    $Port,
        [Parameter(Mandatory)][string] $VpsUser,
        [Parameter(Mandatory)][string] $VpsHost,
        [Parameter(Mandatory)][string] $RemoteCommand,
        [switch] $NonInteractive
    )
    $a = [System.Collections.Generic.List[string]]::new()
    $a.Add('-i');  $a.Add($IdentityFile)
    $a.Add('-p');  $a.Add([string]$Port)
    $a.Add('-o');  $a.Add('StrictHostKeyChecking=accept-new')
    if ($NonInteractive) { $a.Add('-o'); $a.Add('BatchMode=yes') }
    $a.Add("$VpsUser@$VpsHost")
    $a.Add($RemoteCommand)
    return [string[]]$a.ToArray()
}

<#
    Kern: nimmt eine SecureString und legt sie sicher auf dem VPS ab.
    Plaintext entsteht nur transient (BSTR -> Bytes), wird via ssh-stdin uebertragen
    und danach (auch im Fehlerfall) genullt/freigegeben. Gibt PSCustomObject mit
    Perms/Size zurueck. Wirft bei Fehler (ohne den Wert preiszugeben).
#>
function Invoke-VpsKeyDeposit {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]                       $KeyName,
        [Parameter(Mandatory)][System.Security.SecureString] $SecureValue,
        [Parameter(Mandatory)][string] $VpsHost,
        [Parameter(Mandatory)][string] $VpsUser,
        [Parameter(Mandatory)][int]    $Port,
        [Parameter(Mandatory)][string] $IdentityFile,
        [Parameter(Mandatory)][string] $RemoteDir,
        [Parameter(Mandatory)][string] $SshExe,
        [switch] $NonInteractive
    )

    Test-VpsKeyName  -Name $KeyName
    Test-VpsRemoteDir -Dir $RemoteDir
    $RemoteDir = $RemoteDir.Trim('/')

    if (-not (Test-Path -LiteralPath $SshExe))       { throw "ssh.exe nicht gefunden: $SshExe" }
    if (-not (Test-Path -LiteralPath $IdentityFile)) { throw "SSH-Key nicht gefunden: $IdentityFile" }
    if ($SecureValue.Length -eq 0)                   { throw "Leerer Wert -- Abbruch (nichts uebertragen)." }

    # Wert kommt remote via stdin (cat > ...). KeyName/RemoteDir sind validiert (safe charset).
    $remoteUpload = "umask 077; mkdir -p ~/'$RemoteDir'; chmod 700 ~/'$RemoteDir'; cat > ~/'$RemoteDir'/'$KeyName'; chmod 600 ~/'$RemoteDir'/'$KeyName'"

    $bstr = [IntPtr]::Zero
    $plainBytes = $null
    try {
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        $plainBytes = [System.Text.Encoding]::UTF8.GetBytes($plain)
        $plain = $null

        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $SshExe
        $sshArgs = New-VpsSshArgs -IdentityFile $IdentityFile -Port $Port -VpsUser $VpsUser `
            -VpsHost $VpsHost -RemoteCommand $remoteUpload -NonInteractive:$NonInteractive
        foreach ($arg in $sshArgs) { $psi.ArgumentList.Add($arg) }
        $psi.UseShellExecute        = $false
        $psi.RedirectStandardInput  = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true

        $proc = [System.Diagnostics.Process]::Start($psi)
        # Bytes ohne Newline/BOM auf stdin schreiben, dann stdin schliessen.
        $proc.StandardInput.BaseStream.Write($plainBytes, 0, $plainBytes.Length)
        $proc.StandardInput.BaseStream.Flush()
        $proc.StandardInput.Close()

        $stderr = $proc.StandardError.ReadToEnd()
        [void]$proc.StandardOutput.ReadToEnd()
        $proc.WaitForExit()

        if ($proc.ExitCode -ne 0) {
            # stderr ist ssh-Diagnose; der Wert ging nur ueber stdin und ist hier nie enthalten.
            throw "Upload fehlgeschlagen (ssh ExitCode $($proc.ExitCode)). $stderr".Trim()
        }
    }
    finally {
        if ($null -ne $plainBytes) { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
        if ($bstr -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }

    # --- Verify ohne Wert-Leak: nur Perms + Size ---
    $remoteVerify = "stat -c '%a %s' ~/'$RemoteDir'/'$KeyName'"
    $verifyArgs = New-VpsSshArgs -IdentityFile $IdentityFile -Port $Port -VpsUser $VpsUser `
        -VpsHost $VpsHost -RemoteCommand $remoteVerify -NonInteractive:$NonInteractive
    $verify = & $SshExe $verifyArgs 2>&1
    $verifyExit = $LASTEXITCODE
    if ($verifyExit -ne 0) {
        throw "Verify fehlgeschlagen (ssh ExitCode $verifyExit): $verify"
    }

    $parts = ("$verify".Trim() -split '\s+')
    $perms = $parts[0]
    $size  = if ($parts.Count -gt 1) { [int]$parts[1] } else { 0 }
    if ($perms -ne '600') { throw "Verify-Warnung: Perms '$perms', erwartet '600'." }
    if ($size  -le 0)     { throw "Verify-Warnung: Datei leer (Size $size)." }

    return [PSCustomObject]@{
        KeyName = $KeyName
        Path    = "~/$RemoteDir/$KeyName"
        Perms   = $perms
        Size    = $size
    }
}

# ----------------------------------------------------------------------------
# Interaktiver Einstieg. Wird uebersprungen, wenn die Datei dot-gesourct wird
# (z.B. aus dem Selbsttest), damit nur die Funktionen geladen werden.
# ----------------------------------------------------------------------------
if ($MyInvocation.InvocationName -ne '.') {

    $defaults = @{
        VpsHost      = '217.160.192.248'
        VpsUser      = 'admin'
        Port         = 22
        IdentityFile = (Join-Path $HOME '.ssh\ionos_admin_ed25519')
        RemoteDir    = 'secrets'
        SshExe       = (Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe')
    }

    if ($ConfigFile) {
        if (-not (Test-Path -LiteralPath $ConfigFile)) { throw "ConfigFile nicht gefunden: $ConfigFile" }
        $cfg = Get-Content -LiteralPath $ConfigFile -Raw | ConvertFrom-Json
        foreach ($k in @('VpsHost','VpsUser','Port','IdentityFile','RemoteDir','SshExe')) {
            if ($cfg.PSObject.Properties.Name -contains $k -and $null -ne $cfg.$k -and "$($cfg.$k)" -ne '') {
                $defaults[$k] = $cfg.$k
            }
        }
    }

    if (-not $VpsHost)      { $VpsHost      = $defaults.VpsHost }
    if (-not $VpsUser)      { $VpsUser      = $defaults.VpsUser }
    if (-not $Port)         { $Port         = [int]$defaults.Port }
    if (-not $IdentityFile) { $IdentityFile = $defaults.IdentityFile }
    if (-not $RemoteDir)    { $RemoteDir    = $defaults.RemoteDir }
    if (-not $SshExe)       { $SshExe       = $defaults.SshExe }

    Test-VpsKeyName -Name $KeyName

    Write-Host "Ziel: $VpsUser@${VpsHost}:$Port  ->  ~/$($RemoteDir.Trim('/'))/$KeyName" -ForegroundColor Cyan

    $secure = Read-Host -AsSecureString "Wert fuer '$KeyName' (Eingabe wird verdeckt)"
    if ($null -eq $secure -or $secure.Length -eq 0) {
        throw "Leerer Wert -- Abbruch (es wurde nichts uebertragen)."
    }

    try {
        $result = Invoke-VpsKeyDeposit -KeyName $KeyName -SecureValue $secure `
            -VpsHost $VpsHost -VpsUser $VpsUser -Port $Port -IdentityFile $IdentityFile `
            -RemoteDir $RemoteDir -SshExe $SshExe -NonInteractive:$NonInteractive
    }
    finally {
        $secure.Dispose()
    }

    Write-Host ""
    Write-Host "OK: '$($result.KeyName)' abgelegt." -ForegroundColor Green
    Write-Host "    Pfad : $($result.Path)" -ForegroundColor Green
    Write-Host "    Perms: $($result.Perms) (owner-only)" -ForegroundColor Green
    Write-Host "    Size : $($result.Size) Byte" -ForegroundColor Green
}
