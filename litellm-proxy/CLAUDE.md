# CLAUDE.md - litellm-proxy/

## Zweck

LiteLLM Proxy als einheitliches API-Gateway fuer Dennis' lokale KI-Infrastruktur.
Alle Tools (ollama-commit, local-rag, spaetere Clients) sprechen gegen einen
einzigen OpenAI-kompatiblen Endpunkt auf Port 4000. Der Proxy routet intern zu
Ollama (Port 11434) oder vLLM (Port 8000).

Schwester-Tool: `langfuse/` ([REI-265](/REI/issues/REI-265)) -- Observability-
Stack der optionale Logging-Ziel fuer alle Proxy-Calls ist.

## Dateien

| Datei                  | Was drin steht                                            |
|------------------------|-----------------------------------------------------------|
| `litellm_config.yaml`  | Modell-Routing (Ollama/vLLM) + Proxy-Einstellungen        |
| `docker-compose.yml`   | Einzelner LiteLLM-Container, Port 4000                    |
| `.env.example`         | LITELLM_MASTER_KEY + optionale Langfuse-Keys              |
| `.gitignore`           | Schuetzt `.env` -- nur `.env.example` wird getrackt       |
| `README.md`            | Quickstart + Client-Snippets (Python, Node, curl)         |
| `CLAUDE.md`            | Du bist hier.                                             |

## Architektur

```
+------------------+   OpenAI-API   +-------------------+
| Client           +--------------->| LiteLLM Proxy     |
| (ollama-commit,  |  :4000/v1      | ghcr.io/berriai/  |
|  local-rag, ...)  |                | litellm:stable    |
+------------------+                +--------+----------+
                                             |
                          +------------------+------------------+
                          |                                     |
                          v                                     v
               +----------+----------+              +----------+----------+
               | Ollama              |              | vLLM                |
               | host:11434          |              | host:8000/v1        |
               | (native Ollama API) |              | (OpenAI-kompatibel) |
               +---------------------+              +---------------------+
```

Der Proxy laeuft als Docker-Container. Zugriff auf Host-Dienste
(Ollama/vLLM) erfolgt ueber `host.docker.internal` (automatisch auf
Docker Desktop; unter Linux per `extra_hosts: host-gateway`).

## Port-Mapping

| Host | Container | Service              |
|------|-----------|----------------------|
| 4000 | 4000      | LiteLLM Proxy API    |

Port 4000 wurde gewaehlt weil 3000 (Astro), 3001 (metrics-api) und 3030
(Langfuse UI) bereits vergeben sind.

## Routing-Logik

`litellm_config.yaml` definiert `model_list`. Jeder Eintrag hat:
- `model_name` -- was der Client sendet (z.B. `"qwen2.5-coder"`)
- `litellm_params.model` -- interner LiteLLM-Provider-String
- `litellm_params.api_base` -- Ziel-Endpunkt

Wildcard-Routing (`ollama/*`, `vllm/*`) macht explizite Aliase optional --
ein Client kann direkt `model="ollama/phi3:mini"` senden ohne Config-Aenderung.

## Secrets

Nur ein Pflicht-Secret: `LITELLM_MASTER_KEY` (Format: `sk-...`). Alle Clients
senden diesen Key als Bearer-Token. Der Key wird per `os.environ/` in der
Config referenziert und nie geloggt.

Optionale Langfuse-Keys (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY) aktivieren
das Callback-Logging -- erst nach Langfuse-Setup eintragen.

## Erweiterungen / wahrscheinliche Folge-Aufgaben

- **Langfuse-Callback aktivieren:** Callback-Zeilen in `litellm_config.yaml`
  auskommentieren + Langfuse-Keys in `.env` eintragen. Dann loggt der Proxy
  **alle** Client-Calls automatisch ohne SDK-Aenderungen an den Clients.
- **Virtuelle Keys:** Mit `DATABASE_URL` (Postgres) kann LiteLLM pro-Client
  API-Keys mit eigenem Budget + Rate-Limit ausstellen. Sinnvoll sobald mehr
  als ein Tool den Proxy nutzt.
- **Neue Modelle:** Einfach neuen Eintrag in `model_list` hinzufuegen, kein
  Container-Neustart noetig (nur `docker compose restart litellm`).
- **Cloudflare-Tunnel:** Analog `metrics-api` kann der Proxy von ausserhalb
  des Heimnetzes erreichbar sein -- dann `LITELLM_MASTER_KEY` besonders stark
  waehlen.

## Was hier NICHT reinwandern sollte

- Keine Astro/Frontend-Konfiguration.
- Keine echten Secrets, auch nicht in Beispielen.
- Keine Tool-spezifische Logik -- die lebt in den Client-Repos.

## Verwandte Tickets

- [REI-256](/REI/issues/REI-256) -- Brainstorming neue Tools (Parent)
- [REI-265](/REI/issues/REI-265) -- Langfuse Observability (Logging-Ziel)
- [REI-266](/REI/issues/REI-266) -- Setup dieses Tools
- [REI-267](/REI/issues/REI-267) -- Profil-Repo Update (DevOps)
