# Deposit-VpsKey.ps1 -- Schluessel sicher auf den VPS legen

Legt einen geheimen Wert (z.B. API-Key/Secret) sicher auf dem IONOS-VPS ab.
Laeuft lokal in PowerShell und nutzt das in Windows eingebaute OpenSSH. Der Wert
wird verdeckt eingegeben, nur kurz im RAM gehalten und ueber SSH direkt auf den
Server gepiped -- nie in eine Datei geschrieben, nie geloggt, nie als
Kommandozeilen-Argument uebergeben.

## Bedienanleitung fuer Dennis (kurz)

1. PowerShell oeffnen, in den `tools`-Ordner wechseln.
2. Befehl ausfuehren (Name frei waehlbar, nur Buchstaben/Ziffern/`_ . -`):

   ```powershell
   .\Deposit-VpsKey.ps1 -KeyName binance_api_secret
   ```

3. Wenn gefragt wird, den geheimen Wert eintippen (Eingabe ist unsichtbar) und Enter.

Fertig. Das Skript meldet am Ende nur Key-Name, Zielpfad, Datei-Rechte (600) und
Groesse -- niemals den Wert selbst. Abgelegt wird unter `~/secrets/<KeyName>` auf
dem VPS (Datei nur fuer den Besitzer lesbar).

## Optionen

| Parameter        | Default                          | Zweck                                  |
|------------------|----------------------------------|----------------------------------------|
| `-KeyName`       | (Pflicht)                        | Dateiname auf dem VPS                   |
| `-VpsHost`       | `217.160.192.248`                | Host/IPv4                               |
| `-VpsUser`       | `admin`                          | SSH-Benutzer                            |
| `-Port`          | `22`                             | SSH-Port                                |
| `-IdentityFile`  | `$HOME\.ssh\ionos_admin_ed25519` | Privater SSH-Key                        |
| `-RemoteDir`     | `secrets`                        | Zielverzeichnis (relativ zum Home)      |
| `-ConfigFile`    | (keine)                          | JSON mit Nicht-Secret-Defaults          |
| `-NonInteractive`| aus                              | ssh BatchMode (nur fuer Selbsttests)    |

Hilfe anzeigen:

```powershell
Get-Help .\Deposit-VpsKey.ps1 -Detailed
```

## Sicherheit (wie der Wert geschuetzt wird)

- Eingabe verdeckt via `Read-Host -AsSecureString`.
- Klartext entsteht nur transient im RAM (BSTR) und wird sofort genullt/freigegeben.
- Uebertragung ausschliesslich ueber SSH-stdin -- in der remote Prozessliste ist
  der Wert nie sichtbar, lokal wird keine Klartext-Datei angelegt.
- Verifikation per `stat` (Rechte + Groesse), nie per `cat` -- der Wert wird beim
  Pruefen nicht ausgelesen.
- Key-Name wird gegen `^[A-Za-z0-9_.-]+$` geprueft (Schutz gegen Injection).

Beim ersten Connect wird der Host-Schluessel des VPS einmalig akzeptiert (TOFU) und
in `known_hosts` gespeichert; danach wird er automatisch geprueft.

## Selbsttest

`selftest-DepositVpsKey.ps1` legt einen Dummy-Wert ab, prueft Rechte (600) und
Groesse, raeumt wieder auf und testet die Namens-Validierung. Kein echtes Secret.

```powershell
.\selftest-DepositVpsKey.ps1 -IdentityFile <pfad-zum-test-key>
```
