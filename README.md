# Multi-AI Ensemble Platform

A production-ready, multi-AI ensemble system built with FastAPI, Azure Container Apps, and modern ML infrastructure.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Client     │────►│  Azure API  │────►│  Container  │
│             │     │  Management │     │  Apps       │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────┐
                    │                          │          │
               ┌────▼────┐              ┌──────▼─────┐   │
               │   API   │              │Orchestrator│   │
               │ Service │              │  Service   │   │
               └────┬────┘              └──────┬─────┘   │
                    │                          │          │
                    └──────────────────────────┘          │
                               │                          │
                    ┌──────────┼──────────┐               │
                    │          │          │               │
               ┌────▼───┐ ┌────▼───┐ ┌────▼───┐          │
               │Model 1 │ │Model 2 │ │ Celery │          │
               │(CPU)   │ │(GPU)   │ │ Workers│          │
               └────────┘ └────────┘ └────────┘          │
                               │                          │
               ┌───────────────┼───────────────┐         │
               │               │               │          │
          ┌────▼────┐    ┌────▼────┐    ┌────▼────┐     │
          │PostgreSQL│    │  Redis  │    │  Blob   │     │
          │         │    │         │    │ Storage │     │
          └─────────┘    └─────────┘    └─────────┘     │
```

## Quick Start - Local Development

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/multi-ai-ensemble.git
cd multi-ai-ensemble

# Run locally with Docker Compose
docker compose up --build

# Test the API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message"}'
```

## Services

| Service | Port | Purpose | Scaling |
|---------|------|---------|---------|
| API | 8000 | Public-facing API | 2-10 replicas |
| Orchestrator | 8001 | Request routing & ensemble logic | 2-5 replicas |
| Model Service 1 | 8002 | CPU-based model (DistilBERT) | 1-3 replicas |
| Model Service 2 | 8003 | GPU-based model (GPT-2) | 1-2 replicas |
| Celery Workers | - | Background task processing | 0-20 replicas |

## Azure Deployment

### Prerequisites

- Azure CLI installed
- GitHub account
- Azure subscription

### One-Time Setup

```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-ensemble --location eastus

# Create container registry
az acr create --resource-group rg-ensemble --name ensembleacr --sku Basic --admin-enabled true

# Create container app environment
az containerapp env create --name env-ensemble --resource-group rg-ensemble --location eastus
```

### GitHub Actions Deployment

1. Add `AZURE_CREDENTIALS` secret to GitHub:
```bash
az ad sp create-for-rbac \
  --name "github-ci" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-ensemble \
  --sdk-auth
```

2. Push to `main` branch - GitHub Actions automatically builds and deploys.

## Project Structure

```
.
├── api/                    # Public API service
│   ├── src/
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── orchestrator/           # Ensemble orchestrator
│   ├── src/
│   │   └── orchestrator.py
│   ├── Dockerfile
│   └── requirements.txt
├── model_service_1/        # CPU model service
│   ├── src/
│   │   └── model.py
│   ├── Dockerfile
│   └── requirements.txt
├── model_service_2/        # GPU model service
│   ├── src/
│   │   └── model.py
│   ├── Dockerfile
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline
├── docker-compose.yml      # Local development
├── .gitignore
└── README.md
```

## Monitoring

- **Azure Application Insights** - Distributed tracing
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards (local: http://localhost:3000)
- **Azure Monitor** - Alerts and logging

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ORCH_URL` | Orchestrator service URL | http://orchestrator:8001 |
| `MODEL_1_URL` | Model 1 endpoint | http://model_service_1:8002/predict |
| `MODEL_2_URL` | Model 2 endpoint | http://model_service_2:8003/predict |
| `REDIS_URL` | Redis connection | redis://redis:6379 |
| `POSTGRES_URL` | PostgreSQL connection | postgresql://ensemble_user:ensemble_pass@postgres:5432/ensemble_db |

## License

MIT License - See LICENSE file
