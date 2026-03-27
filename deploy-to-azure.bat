@echo off
REM ============================================================================
REM ONE-CLICK AZURE DEPLOYMENT SCRIPT FOR WINDOWS
REM For users who need minimal terminal interaction
REM ============================================================================
REM This script deploys the Multi-AI Ensemble directly to Azure without GitHub
REM Requires: Azure CLI installed and logged in (run: az login)
REM ============================================================================

echo ============================================
echo Multi-AI Ensemble - Azure Deployment
echo ============================================
echo.

REM Configuration
set RG_NAME=rg-ensemble
set LOCATION=eastus
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format yyyyMMddHHmm"') do set TIMESTAMP=%%a
set ACR_NAME=ensembleacr%TIMESTAMP:~-4%
set ENV_NAME=env-ensemble
set API_APP=api-ensemble
set ORCH_APP=orchestrator-ensemble
set MODEL1_APP=model1-ensemble
set MODEL2_APP=model2-ensemble

echo Step 1: Creating Resource Group...
az group create --name %RG_NAME% --location %LOCATION% --tags environment=production project=multi-ai-ensemble --output none
if errorlevel 1 (
    echo Error creating resource group
    exit /b 1
)
echo [OK] Resource Group created: %RG_NAME%
echo.

echo Step 2: Creating Container Registry...
az acr create --resource-group %RG_NAME% --name %ACR_NAME% --sku Basic --admin-enabled true --output none
if errorlevel 1 (
    echo Error creating container registry
    exit /b 1
)
echo [OK] Container Registry created: %ACR_NAME%
echo.

echo Step 3: Creating Container App Environment...
az containerapp env create --name %ENV_NAME% --resource-group %RG_NAME% --location %LOCATION% --output none
if errorlevel 1 (
    echo Error creating container app environment
    exit /b 1
)
echo [OK] Container App Environment created: %ENV_NAME%
echo.

echo Step 4: Building and Pushing Images...
echo   (This may take 10-15 minutes on first run)
echo.

echo   Building api...
az acr build --registry %ACR_NAME% --image api:latest --file ./api/Dockerfile ./api --output none
echo   [OK] api built
echo.

echo   Building orchestrator...
az acr build --registry %ACR_NAME% --image orchestrator:latest --file ./orchestrator/Dockerfile ./orchestrator --output none
echo   [OK] orchestrator built
echo.

echo   Building model_service_1...
az acr build --registry %ACR_NAME% --image model_service_1:latest --file ./model_service_1/Dockerfile ./model_service_1 --output none
echo   [OK] model_service_1 built
echo.

echo   Building model_service_2...
az acr build --registry %ACR_NAME% --image model_service_2:latest --file ./model_service_2/Dockerfile ./model_service_2 --output none
echo   [OK] model_service_2 built
echo.

echo [OK] All images built and pushed to ACR
echo.

echo Step 5: Deploying Model Service 1 (CPU - Sentiment)...
az containerapp create --name %MODEL1_APP% --resource-group %RG_NAME% --environment %ENV_NAME% --image %ACR_NAME%.azurecr.io/model_service_1:latest --target-port 8002 --ingress internal --min-replicas 1 --max-replicas 3 --cpu 1.0 --memory 2Gi --env-vars MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english" DEVICE="cpu" --registry-server %ACR_NAME%.azurecr.io --output none
echo [OK] Model Service 1 deployed
echo.

echo Step 6: Deploying Model Service 2 (Text Generation)...
az containerapp create --name %MODEL2_APP% --resource-group %RG_NAME% --environment %ENV_NAME% --image %ACR_NAME%.azurecr.io/model_service_2:latest --target-port 8003 --ingress internal --min-replicas 0 --max-replicas 2 --cpu 2.0 --memory 4Gi --env-vars MODEL_NAME="gpt2-medium" DEVICE="cpu" --registry-server %ACR_NAME%.azurecr.io --output none
echo [OK] Model Service 2 deployed
echo.

echo Step 7: Getting internal URLs...
for /f "tokens=*" %%a in ('az containerapp show --name %MODEL1_APP% --resource-group %RG_NAME% --query properties.configuration.ingress.fqdn -o tsv') do set MODEL1_URL=%%a
for /f "tokens=*" %%a in ('az containerapp show --name %MODEL2_APP% --resource-group %RG_NAME% --query properties.configuration.ingress.fqdn -o tsv') do set MODEL2_URL=%%a
echo   Model 1: https://%MODEL1_URL%/predict
echo   Model 2: https://%MODEL2_URL%/predict
echo.

echo Step 8: Deploying Orchestrator...
az containerapp create --name %ORCH_APP% --resource-group %RG_NAME% --environment %ENV_NAME% --image %ACR_NAME%.azurecr.io/orchestrator:latest --target-port 8001 --ingress internal --min-replicas 1 --max-replicas 3 --cpu 0.5 --memory 1Gi --env-vars MODEL_1_URL="https://%MODEL1_URL%/predict" MODEL_2_URL="https://%MODEL2_URL%/predict" --registry-server %ACR_NAME%.azurecr.io --output none
echo [OK] Orchestrator deployed
echo.

echo Step 9: Getting Orchestrator URL...
for /f "tokens=*" %%a in ('az containerapp show --name %ORCH_APP% --resource-group %RG_NAME% --query properties.configuration.ingress.fqdn -o tsv') do set ORCH_URL=%%a
echo   Orchestrator: https://%ORCH_URL%
echo.

echo Step 10: Deploying Public API...
az containerapp create --name %API_APP% --resource-group %RG_NAME% --environment %ENV_NAME% --image %ACR_NAME%.azurecr.io/api:latest --target-port 8000 --ingress external --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1Gi --env-vars ORCH_URL="https://%ORCH_URL%" --registry-server %ACR_NAME%.azurecr.io --output none
echo [OK] Public API deployed
echo.

echo ============================================
echo DEPLOYMENT COMPLETE!
echo ============================================
echo.

for /f "tokens=*" %%a in ('az containerapp show --name %API_APP% --resource-group %RG_NAME% --query properties.configuration.ingress.fqdn -o tsv') do set API_FQDN=%%a

echo Your API is live at:
echo   https://%API_FQDN%
echo.
echo Test it with:
echo   curl https://%API_FQDN%/health
echo   curl -X POST https://%API_FQDN%/predict -H "Content-Type: application/json" -d "{\"text\": \"Hello world\"}"
echo.
echo Resource Group: %RG_NAME%
echo Container Registry: %ACR_NAME%
echo Container App Environment: %ENV_NAME%
echo.
echo To clean up (delete everything):
echo   az group delete --name %RG_NAME% --yes
echo.
echo ============================================
pause
