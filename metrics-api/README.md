# Reichenberg Metrics API

Local backend service exposing GitHub engagement metrics for Dennis Reichenberg's 14 Local-LLM tools.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tools/metrics` | All 14 tools aggregated |
| GET | `/api/tools/:slug/metrics` | Single tool detail |
| GET | `/health` | Health check |

### Example response (`/api/tools/metrics`)

```json
{
  "owner": "dennisreichenberg",
  "count": 14,
  "tools": [
    {
      "slug": "ollama-commit",
      "description": "AI-powered Git commit message generator...",
      "stars": 42,
      "forks": 7,
      "openIssues": 2,
      "watchers": 42,
      "lastCommitAt": "2026-05-10T14:23:00Z",
      "defaultBranch": "main",
      "readmeLength": 3842,
      "traffic": {
        "views": { "count": 120, "uniques": 45 },
        "clones": { "count": 18, "uniques": 12 }
      },
      "fetchedAt": "2026-05-17T10:00:00Z"
    }
  ]
}
```

## Setup

```bash
cd metrics-api
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
npm install
npm run dev        # development (ts-node)
npm run build && npm start   # production
```

## Configuration

Copy `.env.example` to `.env` and fill in:

- `GITHUB_TOKEN` -- GitHub PAT with `public_repo` scope (add `repo` for traffic data)
- `PORT` -- defaults to `3001`

## Caching

Metrics are cached in memory with a 1-hour TTL per tool. GitHub rate limits:
- Without token: 60 requests/hour
- With token: 5,000 requests/hour

Each full refresh of all 14 tools costs up to ~56 GitHub API requests (repo + readme + traffic x2 per tool).

## Deployment

Intended to run behind a Cloudflare Tunnel (see [REI-180](/REI/issues/REI-180)). No authentication layer needed -- the tunnel provides access control.

```bash
# Example: expose via cloudflared tunnel
cloudflared tunnel --url http://localhost:3001
```
