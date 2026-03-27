# Azure Deployment Plan - Multi-AI Ensemble Platform
## Based on Blueprint 4: Complete Starter Kit

**Status:** PENDING APPROVAL  
**Created:** 2026-03-27  
**Architecture:** AKS-based Microservices with GPU Support  
**Scope:** Full Infrastructure + Application Skeleton  
**Cost:** ~$1,800-2,900/month

---

## Executive Summary

This plan provisions a **production-grade multi-AI ensemble platform** on Azure using AKS (Azure Kubernetes Service) with GPU node pools, comprehensive observability, and enterprise security.

**Key Differentiators:**
- ✅ **AKS with GPU nodes** - for heavy ML models
- ✅ **API Management** - enterprise gateway with rate limiting  
- ✅ **Application Gateway + Front Door** - WAF + global load balancing
- ✅ **Azure ML Workspace** - model registry and MLOps
- ✅ **Cognitive Search/Milvus** - vector database for RAG
- ✅ **Celery + Service Bus** - async task processing
- ✅ **Prometheus + Grafana** - advanced monitoring
- ✅ **Helm charts** - full Kubernetes deployment
- ✅ **Docker Compose** - complete local development

---

## 1. Architecture Overview

**32 Azure Services | 6 Week Timeline | AKS with GPU Support**

### Core Components:
- **AKS Cluster**: System pool (3x D4s_v5) + GPU pool (1-3x NC6s_v3)
- **Microservices**: API, Orchestrator, 2 Model Services, Celery Workers
- **Data**: PostgreSQL, Redis, Blob Storage, Cognitive Search
- **Networking**: Front Door → APIM → App Gateway → AKS
- **Monitoring**: Prometheus, Grafana, App Insights, Log Analytics
- **Security**: Azure AD, Key Vault, Private Endpoints, NSGs

### Local Development:
- Docker Compose with PostgreSQL, Redis, Milvus, Prometheus, Grafana
- Hot-reload for all services
- Integration tests included

## 3. Azure Services Required

### Core Infrastructure
- [ ] Resource Group: `rg-master-cockpit-prod`
- [ ] Container Registry: `acrmastercockpit`
- [ ] Key Vault: `kv-master-cockpit`
- [ ] Virtual Network: `vnet-master-cockpit`
- [ ] Managed Identity: `mi-master-cockpit`

### Compute
- [ ] Container App Environment: `cae-master-cockpit`
- [ ] Container App: `ca-master-cockpit` (Dashboard)
- [ ] Container App: `ca-agent-kilo` (Master)
- [ ] Container App: `ca-agent-lingma` (Research)
- [ ] Container App: `ca-agent-claude` (Coding)
- [ ] Container App: `ca-agent-glm` (Analysis)
- [ ] Container App: `ca-agent-copilot` (Review)
- [ ] Container App: `ca-swarm-worker` (Dynamic nodes)

### Data
- [ ] Cosmos DB Account: `cosmos-master-cockpit`
  - [ ] Container: `memory-layers`
  - [ ] Container: `agent-state`
  - [ ] Container: `pipeline-results`
  - [ ] Container: `test-results`
  - [ ] Container: `healing-events`
  - [ ] Container: `constraint-lattice`
- [ ] Redis Cache: `redis-48layer-memory` (6GB, C3 tier)
- [ ] Service Bus: `sb-master-cockpit` (Standard)
- [ ] Storage Account: `stmastercockpit` (Cool tier)

### AI/ML
- [ ] Azure OpenAI: `openai-coding-agent`
  - [ ] Deployment: `gpt-4-coding`
  - [ ] Deployment: `gpt-35-turbo-chat`
  - [ ] Deployment: `text-embedding-ada`
- [ ] Cognitive Services: `cognitiveservices-research`
- [ ] AI Search: `search-knowledge-index`

### Observability
- [ ] Application Insights: `appinsights-master-cockpit`
- [ ] Log Analytics: `log-master-cockpit`

### Networking
- [ ] Azure Front Door: `afd-master-cockpit` (Dual-federation)
- [ ] Private Endpoints for data services
- [ ] NSG: `nsg-master-cockpit`

## 4. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create resource group
- [ ] Provision ACR and push base images
- [ ] Configure Key Vault with secrets
- [ ] Set up VNet and subnets
- [ ] Create managed identity with RBAC

### Phase 2: Data Layer (Week 1-2)
- [ ] Deploy Cosmos DB with all containers
- [ ] Configure Redis Cache
- [ ] Set up Service Bus namespace
- [ ] Create Storage Account
- [ ] Verify connectivity

### Phase 3: Compute Layer (Week 2)
- [ ] Create Container App Environment
- [ ] Deploy all 7 container apps
- [ ] Configure auto-scaling rules
- [ ] Set up health probes

### Phase 4: Networking (Week 2-3)
- [ ] Configure private endpoints
- [ ] Deploy Azure Front Door
- [ ] Set up NSG rules
- [ ] Test cross-region connectivity

### Phase 5: Observability (Week 3)
- [ ] Deploy Application Insights
- [ ] Configure Log Analytics
- [ ] Set up custom metrics
- [ ] Create monitoring dashboard

### Phase 6: AI/ML (Week 3-4)
- [ ] Deploy Azure OpenAI
- [ ] Configure content filtering
- [ ] Deploy Cognitive Services
- [ ] Set up AI Search

### Phase 7: Validation (Week 4)
- [ ] End-to-end testing
- [ ] Load testing (50+ nodes)
- [ ] DR testing
- [ ] Security audit

## 5. Configuration

### azure.yaml
```yaml
name: master-cockpit
resourceGroup: rg-master-cockpit-prod
location: eastus

services:
  master-cockpit:
    project: ./src/master-cockpit
    language: js
    host: containerapp
    
  agent-kilo:
    project: ./src/agents/kilo
    language: js
    host: containerapp
    
  agent-lingma:
    project: ./src/agents/lingma
    language: js
    host: containerapp
    
  agent-claude:
    project: ./src/agents/claude
    language: js
    host: containerapp
    
  agent-glm:
    project: ./src/agents/glm
    language: js
    host: containerapp
    
  agent-copilot:
    project: ./src/agents/copilot
    language: js
    host: containerapp

infra:
  provider: bicep
  path: ./infra
```

### Required Secrets (Key Vault)
- `redis-connection-string`
- `cosmos-primary-key`
- `cosmos-secondary-key`
- `service-bus-connection`
- `openai-api-key`
- `app-insights-connection`
- `jwt-signing-key`
- `websocket-auth-secret`

## 6. Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| Container Apps | $150-300 |
| Cosmos DB | $200-400 |
| Redis Cache | $100 |
| Service Bus | $20 |
| Storage | $15 |
| App Insights | $50 |
| Key Vault | $3 |
| Azure OpenAI | $100-500 |
| AI Search | $75 |
| Front Door | $50 |
| **TOTAL** | **$763-1513/month** |

## 7. Validation Checklist

Before proceeding to deployment:
- [ ] All 24 Azure services identified
- [ ] Cost estimate approved
- [ ] Region selection confirmed (East US + West Europe)
- [ ] Scaling rules defined
- [ ] Security architecture reviewed
- [ ] 7-week timeline accepted

## 8. Approval

**Status:** ⏳ PENDING USER APPROVAL

**Next Steps After Approval:**
1. Generate Bicep infrastructure templates
2. Create azure.yaml configuration
3. Set up GitHub Actions workflow
4. Invoke azure-validate
5. Deploy to Azure

---

**DO NOT PROCEED WITH INFRASTRUCTURE CREATION UNTIL THIS PLAN IS APPROVED.**

Approve? (yes/no/modify)
