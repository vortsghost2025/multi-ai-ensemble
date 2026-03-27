#!/bin/bash
# ============================================================================
# ONE-CLICK AZURE DEPLOYMENT SCRIPT
# For users who need minimal terminal interaction
# ============================================================================
# This script deploys the Multi-AI Ensemble directly to Azure without GitHub
# Requires: Azure CLI installed and logged in (run: az login)
# ============================================================================

set -e  # Exit on error

echo "============================================"
echo "Multi-AI Ensemble - Azure Deployment"
echo "============================================"
echo ""

# Configuration
RG_NAME="rg-ensemble"
LOCATION="eastus"
ACR_NAME="ensembleacr$(date +%s | tail -c 4)"  # Unique name
ENV_NAME="env-ensemble"
API_APP="api-ensemble"
ORCH_APP="orchestrator-ensemble"
MODEL1_APP="model1-ensemble"
MODEL2_APP="model2-ensemble"

echo "Step 1: Creating Resource Group..."
az group create \
    --name $RG_NAME \
    --location $LOCATION \
    --tags environment=production project=multi-ai-ensemble \
    --output none
echo "✓ Resource Group created: $RG_NAME"
echo ""

echo "Step 2: Creating Container Registry..."
az acr create \
    --resource-group $RG_NAME \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --output none
echo "✓ Container Registry created: $ACR_NAME"
echo ""

echo "Step 3: Creating Container App Environment..."
az containerapp env create \
    --name $ENV_NAME \
    --resource-group $RG_NAME \
    --location $LOCATION \
    --output none
echo "✓ Container App Environment created: $ENV_NAME"
echo ""

echo "Step 4: Building and Pushing Images..."
echo "  (This may take 5-10 minutes on first run)"
echo ""

# Build images locally and push to ACR
services=("api" "orchestrator" "model_service_1" "model_service_2")
for svc in "${services[@]}"; do
    echo "  Building $svc..."
    az acr build \
        --registry $ACR_NAME \
        --image $svc:latest \
        --file ./$svc/Dockerfile \
        ./$svc \
        --output none
    echo "  ✓ $svc built and pushed"
done
echo ""
echo "✓ All images built and pushed to ACR"
echo ""

echo "Step 5: Deploying Model Service 1 (CPU - Sentiment)..."
az containerapp create \
    --name $MODEL1_APP \
    --resource-group $RG_NAME \
    --environment $ENV_NAME \
    --image $ACR_NAME.azurecr.io/model_service_1:latest \
    --target-port 8002 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 1.0 \
    --memory 2Gi \
    --env-vars MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english" DEVICE="cpu" \
    --registry-server $ACR_NAME.azurecr.io \
    --output none
echo "✓ Model Service 1 deployed"
echo ""

echo "Step 6: Deploying Model Service 2 (Text Generation)..."
az containerapp create \
    --name $MODEL2_APP \
    --resource-group $RG_NAME \
    --environment $ENV_NAME \
    --image $ACR_NAME.azurecr.io/model_service_2:latest \
    --target-port 8003 \
    --ingress internal \
    --min-replicas 0 \
    --max-replicas 2 \
    --cpu 2.0 \
    --memory 4Gi \
    --env-vars MODEL_NAME="gpt2-medium" DEVICE="cpu" \
    --registry-server $ACR_NAME.azurecr.io \
    --output none
echo "✓ Model Service 2 deployed"
echo ""

echo "Step 7: Getting internal URLs..."
MODEL1_URL=$(az containerapp show --name $MODEL1_APP --resource-group $RG_NAME --query properties.configuration.ingress.fqdn -o tsv)
MODEL2_URL=$(az containerapp show --name $MODEL2_APP --resource-group $RG_NAME --query properties.configuration.ingress.fqdn -o tsv)
echo "  Model 1: https://$MODEL1_URL/predict"
echo "  Model 2: https://$MODEL2_URL/predict"
echo ""

echo "Step 8: Deploying Orchestrator..."
az containerapp create \
    --name $ORCH_APP \
    --resource-group $RG_NAME \
    --environment $ENV_NAME \
    --image $ACR_NAME.azurecr.io/orchestrator:latest \
    --target-port 8001 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars \
        MODEL_1_URL="https://$MODEL1_URL/predict" \
        MODEL_2_URL="https://$MODEL2_URL/predict" \
    --registry-server $ACR_NAME.azurecr.io \
    --output none
echo "✓ Orchestrator deployed"
echo ""

echo "Step 9: Getting Orchestrator URL..."
ORCH_URL=$(az containerapp show --name $ORCH_APP --resource-group $RG_NAME --query properties.configuration.ingress.fqdn -o tsv)
echo "  Orchestrator: https://$ORCH_URL"
echo ""

echo "Step 10: Deploying Public API..."
az containerapp create \
    --name $API_APP \
    --resource-group $RG_NAME \
    --environment $ENV_NAME \
    --image $ACR_NAME.azurecr.io/api:latest \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars ORCH_URL="https://$ORCH_URL" \
    --registry-server $ACR_NAME.azurecr.io \
    --output none
echo "✓ Public API deployed"
echo ""

echo "============================================"
echo "DEPLOYMENT COMPLETE!"
echo "============================================"
echo ""

# Get the public API URL
API_FQDN=$(az containerapp show --name $API_APP --resource-group $RG_NAME --query properties.configuration.ingress.fqdn -o tsv)
API_URL="https://$API_FQDN"

echo "Your API is live at:"
echo "  $API_URL"
echo ""
echo "Test it with:"
echo "  curl $API_URL/health"
echo "  curl -X POST $API_URL/predict -H 'Content-Type: application/json' -d '{\"text\": \"Hello world\"}'"
echo ""
echo "Resource Group: $RG_NAME"
echo "Container Registry: $ACR_NAME"
echo "Container App Environment: $ENV_NAME"
echo ""
echo "To clean up (delete everything):"
echo "  az group delete --name $RG_NAME --yes"
echo ""
echo "============================================"
