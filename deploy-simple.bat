@echo off
REM ============================================================================
REM ULTRA-SIMPLE ONE-COMMAND DEPLOYMENT FOR WINDOWS
REM ============================================================================
REM Instructions:
REM 1. Open PowerShell or CMD in this folder
REM 2. Type: az login (follow browser prompt)
REM 3. Type: .\deploy-simple.bat
REM 4. Wait 10-15 minutes
REM 5. Script will show your live API URL
REM ============================================================================

echo Multi-AI Ensemble Deployment
echo This will take 10-15 minutes.
pause

echo Starting deployment...

REM Create resource group
az group create -n rg-ensemble -l eastus --tags project=ensemble --output none

REM Create unique registry name
for /f "tokens=*" %%a in ('powershell -Command Get-Random -Maximum 9999') do set RAND=%%a
set ACR_NAME=ensembleacr%RAND%

REM Create ACR
az acr create -g rg-ensemble -n %ACR_NAME% --sku Basic --admin-enabled true --output none

REM Create environment
az containerapp env create -n env-ensemble -g rg-ensemble -l eastus --output none

echo Building images (this takes the longest, 10-15 minutes)...
echo Building API...
az acr build -r %ACR_NAME% -t api:latest -f api/Dockerfile api --output none

echo Building Orchestrator...
az acr build -r %ACR_NAME% -t orchestrator:latest -f orchestrator/Dockerfile orchestrator --output none

echo Building Model 1...
az acr build -r %ACR_NAME% -t model1:latest -f model_service_1/Dockerfile model_service_1 --output none

echo Building Model 2...
az acr build -r %ACR_NAME% -t model2:latest -f model_service_2/Dockerfile model_service_2 --output none

echo Deploying services...

REM Deploy Model 1
az containerapp create -n model1 -g rg-ensemble --environment env-ensemble -i %ACR_NAME%.azurecr.io/model1:latest --target-port 8002 --ingress internal --min-replicas 1 --cpu 1 --memory 2Gi --env-vars MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english" DEVICE="cpu" --output none
for /f "tokens=*" %%a in ('az containerapp show -n model1 -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv') do set M1_URL=%%a

REM Deploy Model 2
az containerapp create -n model2 -g rg-ensemble --environment env-ensemble -i %ACR_NAME%.azurecr.io/model2:latest --target-port 8003 --ingress internal --min-replicas 0 --cpu 2 --memory 4Gi --env-vars MODEL_NAME="gpt2-medium" DEVICE="cpu" --output none
for /f "tokens=*" %%a in ('az containerapp show -n model2 -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv') do set M2_URL=%%a

REM Deploy Orchestrator
az containerapp create -n orchestrator -g rg-ensemble --environment env-ensemble -i %ACR_NAME%.azurecr.io/orchestrator:latest --target-port 8001 --ingress internal --min-replicas 1 --cpu 0.5 --memory 1Gi --env-vars MODEL_1_URL="https://%M1_URL%/predict" MODEL_2_URL="https://%M2_URL%/predict" --output none
for /f "tokens=*" %%a in ('az containerapp show -n orchestrator -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv') do set ORCH_URL=%%a

REM Deploy API
az containerapp create -n api -g rg-ensemble --environment env-ensemble -i %ACR_NAME%.azurecr.io/api:latest --target-port 8000 --ingress external --min-replicas 1 --cpu 0.5 --memory 1Gi --env-vars ORCH_URL="https://%ORCH_URL%" --output none
for /f "tokens=*" %%a in ('az containerapp show -n api -g rg-ensemble --query properties.configuration.ingress.fqdn -o tsv') do set API_URL=%%a

echo.
echo ============================================
echo SUCCESS! Your API is live at:
echo https://%API_URL%
echo ============================================
echo.
echo Test with:
echo   curl https://%API_URL%/health
echo   curl -X POST https://%API_URL%/predict -H "Content-Type: application/json" -d "{\"text\":\"Hello\"}"
echo.
echo To delete everything: az group delete -n rg-ensemble --yes
echo.
pause
