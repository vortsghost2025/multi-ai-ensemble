# Multi-AI Ensemble Platform

A multi-agent AI ensemble system with 4 microservices:
- **API Gateway** (port 8000) - Public API
- **Orchestrator** (port 8001) - Routes requests to models
- **Model Service 1** (port 8002) - Sentiment analysis
- **Model Service 2** (port 8003) - Text generation

## Local Development

```bash
docker-compose up --build
```

Test:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing!"}'
```

## Azure Deployment

The GitHub Actions workflow automatically deploys to Azure Container Apps on push to main.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   API       │─────▶│ Orchestrator │─────▶│   Model 1   │
│  Gateway    │      │              │      │ (Sentiment) │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   Model 2   │
                     │ (Generation)│
                     └─────────────┘
```
