# CLAUDE.md - langfuse/

## Zweck

Self-hosted Langfuse-Stack fuer LLM-Observability ueber Dennis' lokale
KI-Tools. Liefert Traces, Generationen, Kosten und Eval-Scores fuer alles, was
durch Ollama, vLLM oder den LiteLLM-Proxy ([REI-266](/REI/issues/REI-266))
laeuft. Konsumenten sind aktuell `ollama-commit` und `local-rag` (externe
GitHub-Repos), spaeter auch der LiteLLM-Proxy als Auto-Logger.

## Dateien

| Datei                 | Was drin steht                                              |
|-----------------------|-------------------------------------------------------------|
| `docker-compose.yml`  | v3 Stack: langfuse-web, langfuse-worker, postgres, clickhouse, redis, minio |
| `.env.example`        | Alle Pflicht-Secrets + optionale Bootstrap-Variablen        |
| `.gitignore`          | Schuetzt `.env`, `data/`, Logs -- nur `.env.example` ist getrackt |
| `README.md`           | Quickstart + Integrations-Snippets fuer ollama-commit, local-rag |
| `CLAUDE.md`           | Du bist hier.                                               |

## Architektur

```
+-----------+        +----------------+        +-------------+
| Client    | HTTP   | langfuse-web   | enqueue| redis       |
| (SDK)     +------->|  Next.js + API +------->| (BullMQ)    |
+-----------+        +----------------+        +------+------+
                                                       |
                                                       v
                                              +----------------+      writes traces
                                              | langfuse-worker+------------------+
                                              +----------------+                  |
                                                       |                          v
                                                       | metadata          +---------------+
                                                       v                   |  clickhouse    |
                                              +----------------+           |  (OLAP store)  |
                                              |  postgres      |           +---------------+
                                              +----------------+
                                                       |
                                                       | blob refs
                                                       v
                                              +----------------+
                                              |  minio (S3)    |  events/, media/
                                              +----------------+
```

- **Postgres** -- relationale Metadaten (Users, Orgs, Projekte, API-Keys, Datasets, Prompts).
- **ClickHouse** -- analytisches Trace-Storage (Observations, Generations, Scores). Hier liegen die teuren Daten.
- **Redis** -- BullMQ-Queue zwischen Web und Worker; auch Rate-Limits.
- **MinIO** -- S3-kompatibler Blob-Store fuer rohe Ingestion-Events + Media-Attachments.

Die Trennung Web/Worker erlaubt horizontales Skalieren des Workers, ist hier
fuer lokal aber rein konzeptionell -- beide laufen als je 1 Container.

## Port-Mapping (host -> container)

| Host    | Container | Service           |
|---------|-----------|-------------------|
| 3030    | 3000      | langfuse-web (UI + API) |
| 9090    | 9000      | MinIO S3 API      |
| 9091    | 9001      | MinIO Web-Console |

`3030` wurde gewaehlt, weil `3000` und `3001` im Repo schon belegt sind
(Astro Dev-Server, metrics-api).

## Secrets

Drei Sorten Geheimnisse, alle ueber `.env`:

1. **Infra-Passwoerter** -- Postgres, ClickHouse, Redis, MinIO Root.
2. **Langfuse-Krypto** -- `LANGFUSE_NEXTAUTH_SECRET` (Session-Signing),
   `LANGFUSE_SALT` (API-Key-Hashing), `LANGFUSE_ENCRYPTION_KEY` (Column-Level
   Encryption, **64 hex chars Pflicht**).
3. **Projekt-API-Keys** -- erst nach erstem Login in der UI sichtbar
   (`pk-lf-...` / `sk-lf-...`). Diese landen in den `.env` der Client-Tools,
   nicht im Stack selbst.

Die `.env` selbst ist via `.gitignore` ausgeschlossen -- nur `.env.example`
wird ge-committed.

## Erweiterungen / wahrscheinliche Folge-Aufgaben

- **LiteLLM-Anbindung ([REI-266](/REI/issues/REI-266)):** LiteLLM hat einen
  nativen `langfuse`-Callback. Wenn der Proxy steht, kann er ALLE LLM-Calls
  automatisch loggen -- dann brauchen Clients gar kein eigenes SDK mehr.
- **Cloudflare-Tunnel:** analog zur `metrics-api` (siehe REI-180-Pattern) kann
  Langfuse hinter `cloudflared` aus dem Heimnetz erreichbar gemacht werden,
  falls Dennis Traces remote sehen will. Dann **muss** `NEXTAUTH_URL` auf den
  Public-Hostname zeigen, sonst bricht OAuth.
- **Backups:** aktuell manuell (siehe README Abschnitt 7). Wenn das Setup
  laenger laeuft, lohnt ein Cron-Container der `pg_dump` + ClickHouse-Backup
  in MinIO ablegt.

## Was hier NICHT reinwandern sollte

- Keine LLM-Calls / Tooling-Logik -- die lebt in den Client-Repos (`ollama-commit`,
  `local-rag`) oder im LiteLLM-Proxy-Verzeichnis.
- Keine portfoliospezifische Astro-Konfiguration -- dieses Verzeichnis ist
  reine Infrastruktur-Komponente innerhalb des Mono-Repos.
- Keine echten Secrets, auch nicht in Beispielen.

## Verwandte Tickets

- [REI-256](/REI/issues/REI-256) -- Brainstorming neue Tools (Parent)
- [REI-265](/REI/issues/REI-265) -- Setup dieses Tools
- [REI-266](/REI/issues/REI-266) -- LiteLLM Proxy (Logging-Producer)
- [REI-267](/REI/issues/REI-267) -- Profil-Repo Update (DevOps)
