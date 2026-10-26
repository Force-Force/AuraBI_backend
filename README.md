# AuraBI Backend

Visual ETL backend for banking data pipelines. Provides REST + WebSocket APIs for a ReactFlow frontend and a Master Agent chat orchestrator.

**Installation sans Docker** : PostgreSQL et l’API tournent sur votre machine. Vous exposez l’API à vos collègues sur le réseau local (LAN).

## Stack

- Python 3.11+
- PostgreSQL 16+ (installation système)
- FastAPI, SQLAlchemy 2 (async), Alembic
- FastMCP (optionnel, IDE)

## Quick start (local)

### 1. PostgreSQL

**Ubuntu / Debian**

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql
sudo -u postgres psql -f scripts/setup_postgres.sql
```

**macOS** : voir [docs/EXPOSITION_RESEAU.md](docs/EXPOSITION_RESEAU.md).

### 2. Environnement Python

```bash
cp .env.example .env
# Éditez .env : les paramètres Nemotron/Zetaris et CORS si besoin

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The `requirements.txt` file includes the complete runtime and test dependency
set. Use `python -m pytest` to run tests and
`python scripts/evaluate_scout_intent.py` for the reproducible Scout Intent
evaluation.

Generic Zetaris-shaped offline flow test:

```bash
python -m pytest -q tests/test_generic_data_flow.py
```

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For the complete cross-platform setup and troubleshooting guide, see
[docs/DEVOPS_DOCKER.md](docs/DEVOPS_DOCKER.md).

### 3. Migrations

```bash
alembic upgrade head
```

### 4. Lancer l’API (accessible sur le LAN)

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

L’API écoute sur `0.0.0.0:8000` par défaut.

| URL | Usage |
|-----|--------|
| http://127.0.0.1:8000/docs | Swagger (vous) |
| http://\<votre-ip\>:8000/docs | Swagger (collègues) |
| http://\<votre-ip\>:8000/health | Santé |
Référence détaillée des routes (usage, utilité, exemples) : [docs/API_ROUTES.md](docs/API_ROUTES.md)

Guide Docker/DevOps : [docs/DEVOPS_DOCKER.md](docs/DEVOPS_DOCKER.md)
Guide d'intégration frontend : [docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md)
Explication des technologies sponsors : [docs/SPONSOR_TECHNOLOGY.md](docs/SPONSOR_TECHNOLOGY.md)

Evaluation reproductible Scout Intent : `python scripts/evaluate_scout_intent.py`

Meterless H-MEM writes auditable memory evidence to
`logs/meterless_memory.jsonl` and reinjects relevant memories into analysis
requests. See [docs/SPONSOR_TECHNOLOGY.md](docs/SPONSOR_TECHNOLOGY.md) for the
mounted engine and its boundaries. No separate Meterless installation or API
key is required; the manual setup is documented in
[docs/DEVOPS_DOCKER.md](docs/DEVOPS_DOCKER.md).

### Docker (API + DB)

Guide détaillé partage réseau : **[docs/EXPOSITION_RESEAU.md](docs/EXPOSITION_RESEAU.md)**

Référence des routes : **[docs/API_ROUTES.md](docs/API_ROUTES.md)**
Guide Docker/DevOps : **[docs/DEVOPS_DOCKER.md](docs/DEVOPS_DOCKER.md)**
Guide d'intégration frontend : **[docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md)**
Explication des technologies sponsors : **[docs/SPONSOR_TECHNOLOGY.md](docs/SPONSOR_TECHNOLOGY.md)**
Workflow `curl` : **[docs/WORKFLOW_CURL.md](docs/WORKFLOW_CURL.md)** — démo rapide `./scripts/demo_workflow.sh`, **usage normal** `./scripts/workflow_normal.sh`

## Variables d’environnement

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Connexion PostgreSQL locale |
| `API_HOST` | `0.0.0.0` pour exposer au LAN (défaut) |
| `API_PORT` | Port HTTP (défaut `8000`) |
| `CORS_ORIGINS` | URLs frontend autorisées (virgules) |
| `CORS_ALLOW_ALL` | `true` = tout autoriser en dev LAN |
| `MODEL_PROVIDER` | Route active (`nvidia` or `nightshift`) |
| `NVIDIA_BASE_URL` | Endpoint OpenAI-compatible NVIDIA (default `https://integrate.api.nvidia.com/v1`) |
| `NVIDIA_API_KEY` | Clé NVIDIA API Catalog |
| `NVIDIA_MODEL` | Identifiant du modèle Nemotron (tested: `nvidia/nemotron-3.5-lightning-30b-a3b`) |
| `NIGHTSHIFT_BASE_URL` / `NIGHTSHIFT_API_KEY` / `NIGHTSHIFT_MODEL` | Route Nightshift séparée |
| `ZETARIS_API_URL` / `ZETARIS_REST_URL` | Endpoint analytique Zetaris |
| `ZETARIS_API_KEY` / `ZETARIS_ORG_ID` | Authentification et organisation Zetaris |

Vérification : `GET /health` → `provider`, `model`, `llm_configured`.

## Exemples concrets d’input/output

Les exemples ci-dessous sont directement inspirés des flux de validation automatisés du backend. Ils montrent le comportement attendu du système sans prétendre à une intégration live de Zetaris ou de modèle sponsor en production.

### Exemple 1 — demande standard de revenus par région

Input:

```text
Show revenue by region
```

Output (réponse finale du flux agent):

```text
North generated 1200 and South generated 800.
```

Trace attendue:

```json
{
  "question": "Show revenue by region",
  "intent": { "approval_required": false },
  "sql_executions": [
    {
      "sql": "SELECT region, revenue FROM sales",
      "row_count": 2,
      "preview": [
        { "region": "North", "revenue": 1200 },
        { "region": "South", "revenue": 800 }
      ]
    }
  ]
}
```

### Exemple 2 — demande d’action bloquée avant exécution

Input:

```text
Drop the sales table
```

Output:

```text
Cette demande est orientée action et nécessite une approbation Guardian avant toute exécution.
```

Trace attendue:

```json
{
  "intent": { "approval_required": true },
  "sql_executions": []
}
```

### Exemple 3 — mémoire H-MEM réutilisée sur une seconde demande

Input:

```text
Show revenue by region
```

Second run output (sur le même historique de mémoire):

```json
{
  "trace": {
    "memory": {
      "retrieved": true,
      "written": true
    }
  }
}
```

Cette séquence de 2 exécutions est le comportement validé par les tests `tests/test_generic_data_flow.py` : la donnée issue de Zetaris est injectée dans la mémoire, puis réutilisée lors d’une requête ultérieure.

## Preuves de traces et journaux

AuraBI enregistre un journal JSONL de mémoire pour le moteur H-MEM. Le fichier est configuré par `METERLESS_MEMORY_LOG` et est créé automatiquement si nécessaire.

Exemple de trace écrite :

```json
{"event":"memory.remembered","id":"mem_...","content":"Zetaris returned 2 rows for SQL: SELECT region, revenue FROM sales","memory_type":"factual","layer":"working","source":"zetaris.tool_result","confidence":0.7,"agent_id":"nvidia","run_id":"generic-run","task_id":null,"created_at":"2026-10-26T...Z","access_count":0}
```

Le comportement associé est testable via :

```bash
python -m pytest -q tests/test_generic_data_flow.py
```

## Pre-existing components

No pre-existing components built before the hackathon build window are claimed in this repository beyond standard open-source Python libraries and the project scaffolding itself.

The work included in this submission consists of the AuraBI backend, the agent orchestration layer, the read-only Zetaris integration pattern, the H-MEM memory engine, and the test validation flows implemented during the hackathon period. Nothing secret or sponsor-managed was committed to the repository.

## REST API (`/api/v1`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pipelines` | Create project |
| GET | `/pipelines` | List projects |
| GET | `/pipelines/{id}` | Full graph (ReactFlow-ready) |
| PATCH | `/pipelines/{id}` | Update name, status, architecture_design |
| DELETE | `/pipelines/{id}` | Delete project |
| POST | `/pipelines/{id}/nodes` | Create node |
| PATCH | `/pipelines/{id}/nodes/{node_id}` | Update node |
| DELETE | `/pipelines/{id}/nodes/{node_id}` | Delete node + linked edges |
| POST | `/pipelines/{id}/edges` | Create edge |
| DELETE | `/pipelines/{id}/edges/{edge_id}` | Delete edge |
| GET | `/pipelines/{id}/chat` | Chat history |
| POST | `/pipelines/{id}/chat` | Send message → Master Agent reply |

### ReactFlow payload

`GET /pipelines/{id}` returns:

```json
{
  "nodes": [{ "id": "uuid", "position": { "x": 0, "y": 0 }, "type": "SOURCE", ... }],
  "edges": [{ "id": "uuid", "source": "node-uuid", "target": "node-uuid" }]
}
```

## WebSocket

Connect to: `ws://<host>:8000/api/v1/ws/pipelines/{pipeline_id}`

| type | When |
|------|------|
| `pipeline.updated` | Pipeline metadata changed |
| `node.created` / `node.updated` / `node.deleted` | Node mutations |
| `edge.created` / `edge.deleted` | Edge mutations |
| `chat.message` | New chat message |
| `agent_task.updated` | Master delegated a task |

## MCP server

The current project does not define an `mcp` optional dependency or include an
`app/mcp/server.py` entry point. Do not run the old `pip install -e ".[mcp]"`
command; use the REST and WebSocket APIs documented above.

## Manual MVP test

```bash
curl http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/api/v1/pipelines \
  -H 'Content-Type: application/json' -d '{"name":"Bank ETL Demo"}' | jq .
```

## Security (MVP)

No authentication. Use only on a trusted LAN/VPN. Do not expose to the public Internet without HTTPS and auth (phase 2).

## Tests

```bash
pytest
```
