# Master Cockpit - Infrastructure Architecture Plan
## Autonomous ES Evolution Agent - WE4FREE Framework

**Version:** 1.0  
**Date:** 2026-03-27  
**Status:** PRE-BUILD PLANNING PHASE  
**Approach:** Infrastructure-First Design

---

## Executive Summary

This document defines the complete Azure infrastructure architecture required BEFORE any application code is written. The system implements a dual-federation swarm architecture with 5 AI agents, 48-layer memory, and self-healing capabilities.

**Key Decisions:**
- **ZERO Framework** approach (vanilla JS + Express) for maximum portability
- Container-based deployment for agent isolation
- Azure Container Apps for serverless orchestration
- Azure Service Bus for agent messaging
- Azure Redis for 48-layer memory cache
- Cosmos DB for persistent memory state

---

## 1. Azure Resource Topology

### 1.1 Resource Group Structure

```
rg-master-cockpit-prod (Production)
├── Compute Layer
│   ├── ca-master-cockpit (Container App - Main Dashboard)
│   ├── ca-agent-kilo (Container App - Master Agent)
│   ├── ca-agent-lingma (Container App - Research Agent)
│   ├── ca-agent-claude (Container App - Coding Agent)
│   ├── ca-agent-glm (Container App - Analysis Agent)
│   ├── ca-agent-copilot (Container App - Review Agent)
│   └── cae-swarm-nodes (Container App Environment - Dynamic Swarm)
│
├── Data Layer
│   ├── cosmos-master-cockpit (Cosmos DB - Persistent Memory)
│   ├── redis-48layer-memory (Azure Cache for Redis - Hot Memory)
│   ├── sb-agent-messaging (Service Bus - Agent Communication)
│   └── storage-checkpoints (Storage Account - Backups & Manifests)
│
├── AI/ML Layer
│   ├── openai-coding-agent (Azure OpenAI Service)
│   ├── cognitiveservices-research (Cognitive Services)
│   └── search-knowledge-index (Azure AI Search)
│
├── Networking
│   ├── vnet-master-cockpit (Virtual Network)
│   ├── lb-swarm-ingress (Load Balancer)
│   └── pe-private-endpoints (Private Endpoints)
│
├── Observability
│   ├── log-master-cockpit (Log Analytics Workspace)
│   ├── appinsights-agents (Application Insights)
│   └── dashboard-monitoring (Azure Dashboard)
│
└── Security
    ├── kv-secrets (Key Vault)
    ├── managed-identity-agents (User-Assigned Managed Identity)
    └── acr-images (Container Registry)
```

### 1.2 Regional Deployment (Dual-Federation)

**Primary Region:** East US (Global Work Tier + Lane L)  
**Secondary Region:** West Europe (Lane R + Consensus)

```
┌─ Global Work Tier (East US) ─┐    ┌─ Verification Lane R (West Europe) ─┐
│                              │    │                                      │
│  ca-agent-kilo (Primary)     │◄──►│  ca-agent-kilo-replica               │
│  ca-agent-lingma             │    │  (Verification & Consensus)          │
│  ca-agent-claude             │    │                                      │
│  ca-agent-glm                │    │  Consensus Engine                    │
│  ca-agent-copilot            │    │  (Cross-region validation)           │
│                              │    │                                      │
└──────────┬───────────────────┘    └──────────────┬─────────────────────┘
           │                                        │
           └────────────┬───────────────────────────┘
                        │
              ┌─────────▼──────────┐
              │  Global Load Balancer │
              │  (Azure Front Door)   │
              └───────────────────────┘
```

---

## 2. Container & Orchestration Strategy

### 2.1 Container Architecture

| Container | Purpose | Base Image | Ports | Scaling |
|-----------|---------|------------|-------|---------|
| `master-cockpit` | Dashboard UI + WebSocket hub | `node:20-alpine` | 3001 | 2-10 replicas |
| `agent-kilo` | Master orchestration agent | `node:20-alpine` | 3002 | 1-3 replicas |
| `agent-lingma` | Research & knowledge agent | `node:20-alpine` | 3003 | 1-5 replicas |
| `agent-claude` | Code generation agent | `node:20-alpine` | 3004 | 1-5 replicas |
| `agent-glm` | Analysis & synthesis agent | `node:20-alpine` | 3005 | 1-5 replicas |
| `agent-copilot` | Review & validation agent | `node:20-alpine` | 3006 | 1-3 replicas |
| `swarm-worker` | Dynamic task processing | `node:20-alpine` | 3007 | 0-50 replicas |

### 2.2 Azure Container Apps Environment

```yaml
# Container App Environment Configuration
environment:
  name: cae-master-cockpit
  type: Managed
  
  # Virtual Network Integration
  vnet:
    enabled: true
    infrastructureSubnetId: /subscriptions/.../vnet-master-cockpit/subnets/aca-infra
    internal: false  # Allow public ingress
  
  # Observability
  appInsightsConfiguration:
    connectionString: ${APP_INSIGHTS_CONNECTION_STRING}
  
  # Zone Redundancy (for HA)
  zoneRedundant: true

# Container App Definitions
apps:
  - name: master-cockpit
    image: acr-master-cockpit.azurecr.io/master-cockpit:latest
    targetPort: 3001
    ingress:
      external: true
      transport: auto
      allowInsecure: false
    scaling:
      minReplicas: 2
      maxReplicas: 10
      rules:
        - type: http
          metadata:
            concurrentRequests: 100
    resources:
      cpu: 1.0
      memory: 2.0Gi
    env:
      - name: REDIS_URL
        secretRef: redis-connection
      - name: COSMOS_ENDPOINT
        secretRef: cosmos-endpoint
      - name: SERVICE_BUS_CONNECTION
        secretRef: service-bus-connection

  - name: agent-kilo
    image: acr-master-cockpit.azurecr.io/agent-kilo:latest
    targetPort: 3002
    ingress:
      external: false  # Internal only
    scaling:
      minReplicas: 1
      maxReplicas: 3
    resources:
      cpu: 0.5
      memory: 1.0Gi

  - name: swarm-worker
    image: acr-master-cockpit.azurecr.io/swarm-worker:latest
    targetPort: 3007
    ingress:
      external: false
    scaling:
      minReplicas: 0  # Scale to zero when idle
      maxReplicas: 50
      rules:
        - type: azure-queue
          metadata:
            queueName: swarm-tasks
            queueLength: 10
    resources:
      cpu: 0.25
      memory: 0.5Gi
```

---

## 3. Data Architecture (48-Layer Memory)

### 3.1 Memory Tier Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    48-LAYER MEMORY ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HOT TIER (Azure Redis Cache) - Layers 41-48                    │
│  ├── Performance Cache (41-44): Hot path optimization           │
│  └── Meta-Learning (45-48): Cross-cluster patterns              │
│  Size: 6 GB | Eviction: LRU | Persistence: AOF                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WARM TIER (Cosmos DB) - Layers 1-40                            │
│  ├── Constitutional (1-4): Core invariants                     │
│  ├── Constraint Lattice (5-8): Architecture rules              │
│  ├── Phenotype Selection (9-12): CPS tests                     │
│  ├── Drift Detection (13-16): Basin monitoring                   │
│  ├── Recovery Protocol (17-20): Checkpoint verification        │
│  ├── Agent Coordination (21-24): Messaging state               │
│  ├── Swarm Intelligence (25-28): Federation state              │
│  ├── Pipeline Engine (29-32): Processing state                 │
│  ├── Self-Healing (33-36): Recovery logs                       │
│  └── Integrity System (37-40): SHA-256 manifests               │
│  API: SQL | Consistency: Strong | Partition: /agentId          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  COLD TIER (Storage Account) - Checkpoints & Archives            │
│  ├── Daily snapshots of full 48-layer state                    │
│  ├── Immutable manifests for integrity verification            │
│  └── 90-day retention with lifecycle management                │
│  Tier: Cool → Archive after 30 days                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Cosmos DB Schema

```json
{
  "database": "master-cockpit-db",
  "containers": [
    {
      "name": "memory-layers",
      "partitionKey": "/layerRange",
      "indexingPolicy": {
        "includedPaths": [
          { "path": "/layerRange" },
          { "path": "/timestamp" },
          { "path": "/agentId" }
        ]
      },
      "defaultTTL": null
    },
    {
      "name": "agent-state",
      "partitionKey": "/agentId",
      "defaultTTL": null
    },
    {
      "name": "pipeline-results",
      "partitionKey": "/pipelineType",
      "defaultTTL": 2592000  // 30 days
    },
    {
      "name": "test-results",
      "partitionKey": "/testSuite",
      "defaultTTL": 604800  // 7 days
    },
    {
      "name": "healing-events",
      "partitionKey": "/eventType",
      "defaultTTL": 1209600  // 14 days
    },
    {
      "name": "constraint-lattice",
      "partitionKey": "/layerId",
      "defaultTTL": null
    }
  ]
}
```

### 3.3 Redis Data Structure

```
# Redis Key Patterns for 48-Layer Memory

# Hot Path Cache (Layers 41-44)
HSET mc:cache:hotpath:{agentId} field value
EXPIRE mc:cache:hotpath:{agentId} 3600  # 1 hour TTL

# Pattern Cache
ZADD mc:cache:patterns  score  "pattern:{hash}"

# Meta-Learning (Layers 45-48)
HSET mc:meta:learning:{agentId} 
  crossClusterPatterns "{json}"
  federationWeights "{json}"
  evolutionScore 0.95

# Session State
SET mc:session:{sessionId} "{json}" EX 7200  # 2 hours

# Pub/Sub Channels
SUBSCRIBE mc:agents:broadcast
SUBSCRIBE mc:swarm:{swarmId}
SUBSCRIBE mc:agent:{agentId}
```

---

## 4. Messaging & Communication

### 4.1 Service Bus Topology

```
┌─────────────────────────────────────────────────────────────┐
│              AZURE SERVICE BUS NAMESPACE                     │
│                   sb-master-cockpit                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  QUEUES (Point-to-Point)                                    │
│  ├── q.tasks.critical        (MaxSize: 5GB, Partitioned)     │
│  ├── q.tasks.standard        (MaxSize: 2GB)                │
│  ├── q.healing.events        (MaxSize: 1GB, TTL: 1h)       │
│  └── q.pipeline.results      (MaxSize: 2GB, TTL: 24h)       │
│                                                             │
│  TOPICS (Pub-Sub)                                           │
│  ├── t.agents.broadcast                                     │
│  │   ├── s.agent-kilo                                       │
│  │   ├── s.agent-lingma                                     │
│  │   ├── s.agent-claude                                     │
│  │   ├── s.agent-glm                                        │
│  │   └── s.agent-copilot                                    │
│  │                                                           │
│  ├── t.swarm.updates                                        │
│  │   ├── s.swarm-nodes-all                                  │
│  │   └── s.swarm-master                                     │
│  │                                                           │
│  └── t.system.events                                        │
│      ├── s.healing-system                                   │
│      ├── s.monitoring                                       │
│      └── s.logging                                          │
│                                                             │
│  RULES & FILTERS                                            │
│  ├── agent-filter: agentId = 'kilo' OR 'all'               │
│  ├── priority-filter: priority > 5                          │
│  └── type-filter: messageType IN ['command', 'event']        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 WebSocket Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           WEBSOCKET COMMUNICATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Master Cockpit (WebSocket Server)                          │
│  ├── Port: 3001                                            │
│  ├── Protocol: ws:// (dev) / wss:// (prod)                 │
│  ├── Heartbeat: 30s ping/pong                              │
│  └── Reconnection: Exponential backoff (max 30s)          │
│                                                             │
│  Connection Types:                                          │
│  1. Dashboard Clients (Browser UI)                          │
│     └── Subscribe to: state updates, logs, metrics          │
│                                                             │
│  2. Agent Connections                                       │
│     └── Subscribe to: commands, swarm updates             │
│                                                             │
│  3. Swarm Node Workers                                      │
│     └── Subscribe to: task assignments, node health         │
│                                                             │
│  Message Protocol:                                          │
│  {                                                          │
│    type: "state" | "command" | "event" | "log",            │
│    timestamp: 1711564800000,                               │
│    source: "agent-kilo" | "master-cockpit" | "swarm-node", │
│    payload: { ... },                                       │
│    priority: 1-10,                                          │
│    ttl: 30000  // optional milliseconds                     │
│  }                                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. AI/ML Infrastructure

### 5.1 Azure OpenAI Configuration

```yaml
# OpenAI Service for Coding Agent
service:
  name: openai-coding-agent
  location: East US
  sku: S0
  
  deployments:
    - name: gpt-4-coding
      model: gpt-4
      version: "0613"
      capacity: 20  # TPM (Tokens Per Minute)
      
    - name: gpt-35-turbo-chat
      model: gpt-35-turbo
      version: "0613"
      capacity: 60
      
    - name: text-embedding-ada
      model: text-embedding-ada-002
      version: "2"
      capacity: 120

  # Content filtering
  contentFilters:
    - type: hate
      severity: high
      action: block
    - type: violence
      severity: high
      action: block
```

### 5.2 Cognitive Services

```yaml
# Cognitive Services for Research Agent
services:
  - name: cognitiveservices-research
    kind: TextAnalytics
    location: East US
    sku: S
    
  - name: search-knowledge-index
    kind: Search
    location: East US
    sku: standard
    
    indexes:
      - name: research-papers
        fields:
          - name: id
            type: Edm.String
            key: true
          - name: title
            type: Edm.String
            searchable: true
          - name: content
            type: Edm.String
            searchable: true
            analyzer: standard.lucene
          - name: embedding
            type: Collection(Edm.Single)
            dimensions: 1536
            vectorSearchConfiguration: default-vector-config
```

---

## 6. Security Architecture

### 6.1 Managed Identities

```
┌─────────────────────────────────────────────────────────────┐
│                  SECURITY ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User-Assigned Managed Identity: mi-master-cockpit          │
│                                                             │
│  RBAC Assignments:                                          │
│  ├── Key Vault:                                             │
│  │   └── Secrets: Get, List                                 │
│  │                                                          │
│  ├── Cosmos DB:                                             │
│  │   └── Role: "Cosmos DB Built-in Data Contributor"       │
│  │                                                          │
│  ├── Service Bus:                                           │
│  │   └── Role: "Azure Service Bus Data Owner"              │
│  │                                                          │
│  ├── Container Registry:                                    │
│  │   └── Role: "AcrPull"                                   │
│  │                                                          │
│  └── Storage Account:                                       │
│      └── Role: "Storage Blob Data Contributor"             │
│                                                             │
│  Network Security:                                          │
│  ├── Private Endpoints for all data services               │
│  ├── NSG rules: Allow 3001 (dashboard), deny direct DB    │
│  └── DDoS Protection Standard on VNet                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Key Vault Secrets

```yaml
# Required Secrets in kv-master-cockpit
secrets:
  - name: redis-connection-string
    description: Azure Redis Cache connection
    
  - name: cosmos-primary-key
    description: Cosmos DB read-write key
    
  - name: cosmos-secondary-key
    description: Cosmos DB secondary key
    
  - name: service-bus-connection
    description: Service Bus namespace connection string
    
  - name: openai-api-key
    description: Azure OpenAI service key
    
  - name: app-insights-connection
    description: Application Insights connection string
    
  - name: jwt-signing-key
    description: JWT token signing secret
    
  - name: websocket-auth-secret
    description: WebSocket connection auth token
```

---

## 7. Observability & Monitoring

### 7.1 Log Analytics Queries

```kusto
// Agent Health Dashboard Query
AgentHeartbeat_CL
| where TimeGenerated > ago(1h)
| summarize 
    LastHeartbeat = max(TimeGenerated),
    AvgCPU = avg(CPU_d),
    AvgMemory = avg(Memory_d),
    ErrorCount = countif(Status_s == "error")
  by AgentId_s
| extend Status = case(
    ErrorCount > 0, "error",
    datetime_diff('minute', now(), LastHeartbeat) > 5, "offline",
    "healthy"
  )
| project AgentId_s, Status, LastHeartbeat, AvgCPU, AvgMemory, ErrorCount

// Pipeline Performance Query
PipelineResults_CL
| where TimeGenerated > ago(24h)
| summarize 
    AvgDuration = avg(DurationMs_d),
    P95Duration = percentile(DurationMs_d, 95),
    SuccessRate = countif(Status_s == "complete") * 100.0 / count()
  by PipelineType_s, bin(TimeGenerated, 1h)
| render timechart

// Swarm Node Utilization
SwarmNodes_CL
| where TimeGenerated > ago(1h)
| summarize 
    AvgTasks = avg(Tasks_d),
    MaxTasks = max(Tasks_d),
    NodeCount = dcount(NodeId_s)
  by bin(TimeGenerated, 5m)
| render timechart
```

### 7.2 Application Insights Configuration

```yaml
# Application Insights for Distributed Tracing
applicationInsights:
  name: appinsights-master-cockpit
  location: East US
  
  # Custom Metrics
  customMetrics:
    - name: agent.tasks.completed
      namespace: master-cockpit
      
    - name: swarm.nodes.active
      namespace: master-cockpit
      
    - name: memory.layer.access.latency
      namespace: master-cockpit
      
    - name: websocket.connections.active
      namespace: master-cockpit
  
  # Availability Tests
  webTests:
    - name: dashboard-health
      url: https://master-cockpit.azurecontainerapps.io/health
      frequency: 300  # 5 minutes
      
    - name: websocket-connectivity
      url: wss://master-cockpit.azurecontainerapps.io
      frequency: 300
```

---

## 8. CI/CD Pipeline

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy Master Cockpit

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AZURE_CONTAINER_REGISTRY: acrmastercockpit.azurecr.io
  RESOURCE_GROUP: rg-master-cockpit-prod
  CONTAINER_APP_ENV: cae-master-cockpit

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Master Cockpit
        run: |
          docker build -t $AZURE_CONTAINER_REGISTRY/master-cockpit:${{ github.sha }} .
          docker push $AZURE_CONTAINER_REGISTRY/master-cockpit:${{ github.sha }}
      
      - name: Build Agents
        run: |
          for agent in kilo lingma claude glm copilot; do
            docker build -t $AZURE_CONTAINER_REGISTRY/agent-$agent:${{ github.sha }} ./agents/$agent
            docker push $AZURE_CONTAINER_REGISTRY/agent-$agent:${{ github.sha }}
          done
      
      - name: Run Tests
        run: |
          npm ci
          npm test
          npm run test:integration

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy Master Cockpit
        run: |
          az containerapp update \
            --name ca-master-cockpit \
            --resource-group $RESOURCE_GROUP \
            --image $AZURE_CONTAINER_REGISTRY/master-cockpit:${{ github.sha }}
      
      - name: Deploy Agents
        run: |
          for agent in kilo lingma claude glm copilot; do
            az containerapp update \
              --name ca-agent-$agent \
              --resource-group $RESOURCE_GROUP \
              --image $AZURE_CONTAINER_REGISTRY/agent-$agent:${{ github.sha }}
          done
      
      - name: Run Smoke Tests
        run: |
          curl -f https://master-cockpit.azurecontainerapps.io/health
          npm run test:smoke
```

---

## 9. Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create Azure resource groups
- [ ] Set up Container Registry (ACR)
- [ ] Configure Key Vault with all secrets
- [ ] Create Virtual Network and subnets
- [ ] Set up Managed Identity with RBAC

### Phase 2: Data Layer (Week 1-2)
- [ ] Deploy Cosmos DB with all containers
- [ ] Deploy Azure Redis Cache
- [ ] Configure Service Bus namespace
- [ ] Create Storage Account for checkpoints
- [ ] Test data layer connectivity

### Phase 3: Compute Layer (Week 2)
- [ ] Create Container App Environment
- [ ] Deploy Master Cockpit container
- [ ] Deploy all 5 agent containers
- [ ] Configure auto-scaling rules
- [ ] Set up health probes

### Phase 4: Networking (Week 2-3)
- [ ] Configure Private Endpoints
- [ ] Set up Azure Front Door (dual-federation)
- [ ] Configure NSG rules
- [ ] Test cross-region connectivity
- [ ] SSL/TLS certificate setup

### Phase 5: Observability (Week 3)
- [ ] Deploy Application Insights
- [ ] Set up Log Analytics Workspace
- [ ] Configure custom metrics
- [ ] Create Azure Dashboard
- [ ] Set up alerting rules

### Phase 6: AI/ML (Week 3-4)
- [ ] Deploy Azure OpenAI service
- [ ] Deploy Cognitive Services
- [ ] Configure content filtering
- [ ] Set up AI Search index
- [ ] Test AI service connectivity

### Phase 7: Validation (Week 4)
- [ ] End-to-end integration testing
- [ ] Load testing with 50+ swarm nodes
- [ ] Disaster recovery testing
- [ ] Security audit
- [ ] Performance benchmarking

---

## 10. Cost Estimation (Monthly)

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Container Apps | 10 apps, 2-10 replicas | ~$150-300 |
| Cosmos DB | Standard, 10K RU/s | ~$200-400 |
| Redis Cache | C3 (6GB) | ~$100 |
| Service Bus | Standard | ~$20 |
| Storage Account | Cool tier, 500GB | ~$15 |
| Application Insights | Pay-as-you-go | ~$50 |
| Key Vault | Standard | ~$3 |
| Azure OpenAI | S0, 20 TPM | ~$100-500 |
| Cognitive Search | Standard | ~$75 |
| Virtual Network | Basic | ~$10 |
| **TOTAL** | | **~$723-1473/month** |

---

## Next Steps

1. **Review this architecture plan** with stakeholders
2. **Provision Azure resources** using Azure CLI or Terraform
3. **Set up CI/CD pipeline** in GitHub
4. **Begin application development** only after infrastructure is ready
5. **Implement incremental deployment** starting with single region

**DO NOT PROCEED TO APPLICATION CODE UNTIL:**
- All Phase 1-3 infrastructure is provisioned
- Data layer connectivity is verified
- Container environment is tested
- Security policies are enforced

---

*Document generated for fresh-agent-project*  
*Architecture Version: 1.0*  
*Plan Before Build: ENABLED*
