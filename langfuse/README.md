# Langfuse (self-hosted)

LLM-Observability fuer Dennis Reichenbergs lokale KI-Infrastruktur.
Traces, Evals, Kosten und Prompts fuer alle Tools die mit Ollama, vLLM oder
einem LiteLLM-Proxy sprechen (z.B. [ollama-commit](https://github.com/dennisreichenberg/ollama-commit),
[local-rag](https://github.com/dennisreichenberg/local-rag)).

Quelle: https://langfuse.com/self-hosting -- Langfuse v3 Stack (web + worker +
Postgres + ClickHouse + Redis + MinIO).

## 1. Voraussetzungen

- Docker Desktop (Windows/macOS) oder Docker Engine >= 24 + Compose v2
- ~4 GB RAM frei (ClickHouse + Postgres + MinIO laufen lokal)
- Ports frei: `3030` (UI), `9090`/`9091` (MinIO console)

## 2. Setup

```bash
cd langfuse
cp .env.example .env

# Pflicht: starke Secrets generieren
openssl rand -base64 32   # -> LANGFUSE_NEXTAUTH_SECRET, LANGFUSE_SALT
openssl rand -hex 32      # -> LANGFUSE_ENCRYPTION_KEY (64 hex chars)
openssl rand -base64 24   # -> POSTGRES_PASSWORD, CLICKHOUSE_PASSWORD,
                          #     REDIS_AUTH, MINIO_ROOT_PASSWORD

# .env editieren und alle changeme-* Werte ersetzen
docker compose --env-file .env up -d
```

Erststart dauert ~30s (DB-Migrationen). Logs verfolgen:

```bash
docker compose logs -f langfuse-web
```

UI oeffnen: http://localhost:3030 -- beim ersten Login Account anlegen,
Organisation + Projekt erstellen, dann unter **Project Settings -> API Keys**
ein Schluesselpaar generieren (`pk-lf-...` + `sk-lf-...`).

Diese Schluessel landen in der `.env` der Client-Tools (siehe unten).

## 3. Stack auf einen Blick

| Service           | Container           | Port | Zweck                                  |
|-------------------|---------------------|------|----------------------------------------|
| `langfuse-web`    | `langfuse/langfuse:3`        | 3030 | Next.js UI + REST/Ingest-API |
| `langfuse-worker` | `langfuse/langfuse-worker:3` | -    | Async Trace-Processing       |
| `postgres`        | `postgres:15`       | -    | Auth, Projekte, Datasets               |
| `clickhouse`      | `clickhouse:24.3`   | -    | Traces, Observations, Scores           |
| `redis`           | `redis:7`           | -    | Ingest-Queue, Rate-Limits              |
| `minio`           | `minio/minio`       | 9090/9091 | S3-kompatibler Blob-Store fuer Events + Media |

Persistente Volumes: `langfuse_postgres_data`, `langfuse_clickhouse_data`,
`langfuse_clickhouse_logs`, `langfuse_minio_data`. `docker compose down` laesst
die Daten stehen, `docker compose down -v` loescht sie.

## 4. Integration: ollama-commit (Node/TypeScript)

`ollama-commit` ruft Ollama lokal an. Mit dem Langfuse JS-SDK lassen sich die
Calls als Traces wegschreiben.

```bash
npm install langfuse
```

```ts
// in ollama-commit, z.B. src/llm.ts
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST ?? "http://localhost:3030",
});

export async function suggestCommitMessage(diff: string) {
  const trace = langfuse.trace({ name: "ollama-commit", input: { diff } });
  const generation = trace.generation({
    name: "ollama.chat",
    model: process.env.OLLAMA_MODEL ?? "qwen2.5-coder:7b",
    input: diff,
  });

  const message = await callOllama(diff); // bestehender Call

  generation.end({ output: message });
  await langfuse.flushAsync(); // wichtig in CLIs, sonst gehen Traces verloren
  return message;
}
```

`.env` im `ollama-commit`-Repo:

```
LANGFUSE_HOST=http://localhost:3030
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

CLI-Hinweis: vor `process.exit` immer `await langfuse.flushAsync()` aufrufen,
sonst wird die Ingest-Queue nicht geleert.

## 5. Integration: local-rag (Python)

`local-rag` ist Python-basiert. Es gibt zwei Wege:

### 5a. Dekorator-Style (einfach)

```bash
pip install langfuse
```

```python
# local-rag/rag/pipeline.py
import os
from langfuse import observe
from langfuse.openai import openai  # drop-in wrapper, traced automatisch

os.environ.setdefault("LANGFUSE_HOST", "http://localhost:3030")
# LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY aus .env

@observe(name="rag.answer")
def answer(question: str, docs: list[str]) -> str:
    context = "\n\n".join(docs)
    response = openai.chat.completions.create(
        model="llama3.1:8b",
        base_url="http://localhost:11434/v1",  # Ollama OpenAI-kompatibel
        api_key="ollama",
        messages=[
            {"role": "system", "content": "Beantworte auf Basis des Kontexts."},
            {"role": "user", "content": f"Kontext:\n{context}\n\nFrage: {question}"},
        ],
    )
    return response.choices[0].message.content
```

`@observe` legt automatisch einen Trace an, der OpenAI-Wrapper haengt
Generationen mit Token-Counts + Latenz an.

### 5b. Manuelle Spans (volle Kontrolle)

```python
from langfuse import Langfuse

lf = Langfuse()  # liest LANGFUSE_* aus env
trace = lf.trace(name="rag.answer", user_id=user_id, input={"question": question})

retrieval = trace.span(name="retrieve", input={"k": 5})
docs = vectorstore.similarity_search(question, k=5)
retrieval.end(output={"doc_ids": [d.id for d in docs]})

gen = trace.generation(name="ollama.chat", model="llama3.1:8b", input=docs)
answer_text = call_llm(question, docs)
gen.end(output=answer_text)

trace.update(output=answer_text)
lf.flush()  # in Scripts/Notebooks; in Web-Apps reicht der Background-Flush
```

`.env` im `local-rag`-Repo (identisch zu oben):

```
LANGFUSE_HOST=http://localhost:3030
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

## 6. Optional: Headless-Bootstrap

Beim ersten Start kann Langfuse Org/Projekt/User automatisch anlegen, statt
der UI-Klickstrecke. Setze in `.env`:

```
LANGFUSE_INIT_ORG_NAME=reichenberg
LANGFUSE_INIT_PROJECT_NAME=local-llm-tools
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-localdev
LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-localdev
LANGFUSE_INIT_USER_EMAIL=dennis@example.org
LANGFUSE_INIT_USER_NAME=Dennis
LANGFUSE_INIT_USER_PASSWORD=changeme-init
```

Danach ist das `pk-lf-localdev` / `sk-lf-localdev` Paar sofort fuer die Clients
nutzbar -- keine UI-Anmeldung noetig fuer CI/Smoke-Tests.

## 7. Backup / Restore

```bash
# Postgres
docker compose exec postgres pg_dump -U langfuse langfuse | gzip > langfuse-pg-$(date +%F).sql.gz

# ClickHouse (Traces)
docker compose exec clickhouse clickhouse-client --user clickhouse --password "$CLICKHOUSE_PASSWORD" \
  --query "BACKUP DATABASE default TO Disk('default','backup-$(date +%F)')"
```

MinIO-Daten liegen im Volume `langfuse_minio_data`; ein `docker run --rm
-v langfuse_minio_data:/data alpine tar czf - /data` reicht fuer Snapshots.

## 8. Update auf neue Version

```bash
docker compose pull
docker compose up -d
```

Langfuse fuehrt Migrationen beim Start des `langfuse-web` Containers aus.

## 9. Troubleshooting

- **`web` startet nicht, ClickHouse healthcheck fails:** ClickHouse braucht
  auf langsamen Disks > 30s zum Hochfahren. `docker compose up -d` nochmal,
  oder im `healthcheck` `retries` hochsetzen.
- **`ENCRYPTION_KEY must be 64 hex characters`:** `openssl rand -hex 32`
  benutzen, nicht `base64`.
- **Traces erscheinen nicht in der UI:** in CLI-Clients `flush()` /
  `flushAsync()` vor Prozessende. Im Worker-Log nach `ingestion` greppen.

## 10. Verwandte Issues

- [REI-256](/REI/issues/REI-256) -- Parent: neue Tools fuer Dennis evaluieren
- [REI-265](/REI/issues/REI-265) -- dieses Setup
- [REI-266](/REI/issues/REI-266) -- LiteLLM Proxy (sendet Calls ebenfalls an Langfuse)
- [REI-267](/REI/issues/REI-267) -- Profil-Repo Update
