# LiteLLM Proxy

Ein API-Endpunkt fuer alle lokalen Modelle.

Statt jedes Tool einzeln auf Ollama oder vLLM zu zeigen, spricht alles gegen
**einen** Proxy unter `http://localhost:4000` -- OpenAI-kompatibel, mit
einheitlichem API-Key, Logging und einfachem Routing.

```
ollama-commit   ─┐
local-rag       ─┼──► LiteLLM Proxy :4000 ──► Ollama :11434
andere Tools    ─┘                        └──► vLLM   :8000
```

## 1. Voraussetzungen

- Docker Desktop (Windows/macOS) oder Docker Engine >= 24 + Compose v2
- Ollama laeuft auf dem Host (Port 11434) und/oder vLLM (Port 8000)
- Port `4000` frei

## 2. Setup

```bash
cd litellm-proxy
cp .env.example .env

# Starken Master-Key generieren und in .env eintragen:
openssl rand -base64 32   # -> sk-<wert>
# .env: LITELLM_MASTER_KEY=sk-<wert>

docker compose up -d
```

Health-Check:

```bash
curl http://localhost:4000/health/liveliness
# -> {"status":"healthy"}
```

Verfuegbare Modelle anzeigen:

```bash
curl -H "Authorization: Bearer sk-<dein-key>" http://localhost:4000/v1/models
```

## 3. Routing-Uebersicht

| Modell-Name        | Backend  | Host-Port |
|--------------------|----------|-----------|
| `ollama/*`         | Ollama   | 11434     |
| `qwen2.5-coder`    | Ollama   | 11434     |
| `llama3`           | Ollama   | 11434     |
| `mistral`          | Ollama   | 11434     |
| `vllm/*`           | vLLM     | 8000      |
| `vllm-default`     | vLLM     | 8000      |

Weitere Modelle einfach in `litellm_config.yaml` unter `model_list` eintragen.

## 4. Client-Integration

### Python (openai SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-<dein-master-key>",
)

response = client.chat.completions.create(
    model="qwen2.5-coder",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Node/TypeScript (openai SDK)

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:4000/v1",
  apiKey: process.env.LITELLM_API_KEY,
});

const response = await client.chat.completions.create({
  model: "qwen2.5-coder",
  messages: [{ role: "user", content: "Hello!" }],
});
```

### curl

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-<dein-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 5. Langfuse-Integration (REI-265)

Sobald der Langfuse-Stack laeuft (`langfuse/`-Verzeichnis im Mono-Repo), kann
der Proxy alle LLM-Calls automatisch tracen -- ohne Aenderung an den Clients.

1. `.env` ergaenzen:
   ```
   LANGFUSE_HOST=http://host.docker.internal:3030
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   ```

2. In `litellm_config.yaml` die Callback-Zeilen auskommentieren:
   ```yaml
   litellm_settings:
     success_callback: ["langfuse"]
     failure_callback: ["langfuse"]
   ```

3. `docker compose restart litellm` -- ab sofort landen alle Traces in Langfuse.

## 6. Logs

```bash
docker compose logs -f litellm
```

## 7. Stoppen / Entfernen

```bash
docker compose down        # Container stoppen
docker compose down -v     # inkl. Volumes (keine bei diesem Stack noetig)
```
