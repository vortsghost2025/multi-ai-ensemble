#!/bin/bash
# ============================================================================
# ULTRA-SIMPLE ONE-COMMAND DEPLOYMENT
# For users with accessibility needs - requires only: az login
# ============================================================================
# Instructions:
# 1. Open terminal in this folder
# 2. Type: az login (follow browser prompt)
# 3. Type: ./deploy.sh
# 4. Wait 10-15 minutes
# 5. Script will output your live API URL
# ============================================================================

set -e

echo "Multi-AI Ensemble Deployment"
echo "This will take 10-15 minutes. Press Enter to start or Ctrl+C to cancel"
read

echo "Starting deployment..."

# Create everything
az group create -n rg-ensemble -l eastus --tags project=ensemble --output none
ACR_NAME="ensembleacr$(date +%s | tail -c 4)"
az acr create -g rg-ensemble -n $ACR_NAME --sku Basic --admin-enabled true --output none
az containerapp env create -n env-ensemble -g rg-ensemble -l eastus --output none

echo "Building images (this takes the longest)..."
az acr build -r $ACR_NAME -t api:latest -f api/Dockerfile api --output none &
az acr build -r $ACR_NAME -t orchestrator:latest -f orchestrator/Dockerfile orchestrator --output none &
az acr build -r $ACR_NAME -t model1:latest -f model_service_1/Dockerfile model_service_1 --output none &
az acr build -r $ACR_NAME -t model2:latest -f model_service_2/Dockerfile model_service_2 --output none &
wait
echo "Images built"

echo "Deploying services..."
# Deploy in dependency order
az containerapp create -n model1 -g rg-ensemble --environment env-ensemble -i ${ACR_NAME}.azurecr.io/model1:latest --target-port 8002 --ingress internal --min-replicas 1 --cpu 1 --memory 2Gi --env-vars MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english" DEVICE="cpu" --output none
M1_URL=$(az containerapp show -n model1 -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create -n model2 -g rg-ensemble --environment env-ensemble -i ${ACR_NAME}.azurecr.io/model2:latest --target-port 8003 --ingress internal --min-replicas 0 --cpu 2 --memory 4Gi --env-vars MODEL_NAME="gpt2-medium" DEVICE="cpu" --output none
M2_URL=$(az containerapp show -n model2 -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create -n orchestrator -g rg-ensemble --environment env-ensemble -i ${ACR_NAME}.azurecr.io/orchestrator:latest --target-port 8001 --ingress internal --min-replicas 1 --cpu 0.5 --memory 1Gi --env-vars MODEL_1_URL="https://${M1_URL}/predict" MODEL_2_URL="https://${M2_URL}/predict" --output none
ORCH_URL=$(az containerapp show -n orchestrator -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create -n api -g rg-ensemble --environment env-ensemble -i ${ACR_NAME}.azurecr.io/api:latest --target-port 8000 --ingress external --min-replicas 1 --cpu 0.5 --memory 1Gi --env-vars ORCH_URL="https://${ORCH_URL}" --output none
API_URL=$(az containerapp show -n api -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo "============================================"
echo "SUCCESS! Your API is live at:"
echo "https://${API_URL}"
echo "============================================"
echo ""
echo "Test commands:"
echo "  curl https://${API_URL}/health"
echo "  curl -X POST https://${API_URL}/predict -H 'Content-Type: application/json' -d '{\"text\":\"Hello\"}'"
echo ""
echo "To delete everything: az group delete -n rg-ensemble --yes"
echo ""
read -p "Press Enter to exit"
