# KILO QUICK START GUIDE (Audio/Screen Reader Friendly)
## Multi-AI Ensemble Deployment

### What You Have
- Complete multi-AI platform with 4 microservices
- Runs locally with: docker compose up
- Deploys to Azure with: python kilo.py deploy

### Prerequisites (One-time setup)

1. **Azure CLI** - Install from: aka.ms/installazurecliwindows
2. **Login to Azure** - Open terminal, type:
   ```
   az login
   ```
   Follow browser prompts to authenticate

3. **Python 3** - Should be pre-installed on Windows

### Deploy to Azure (3 steps)

**Step 1: Open terminal in project folder**
- Press Windows key
- Type: terminal
- Press Enter
- Type: cd c:\workspace\fresh-agent-project
- Press Enter

**Step 2: Run Kilo**
```
python kilo.py deploy
```

**Step 3: Wait 10-15 minutes**
Kilo will:
- Create Azure resources
- Build Docker images
- Deploy 4 services
- Output your live API URL

### What Kilo Does

1. Creates resource group: rg-ensemble
2. Creates container registry: ensembleacrXXXX
3. Creates container app environment
4. Builds 4 Docker images (5-10 min each)
5. Deploys Model Service 1 (sentiment analysis)
6. Deploys Model Service 2 (text generation)
7. Deploys Orchestrator (routes requests)
8. Deploys Public API (your entry point)

### After Deployment

Kilo saves deployment info to: deployment.json

Your API URL will be shown at the end, like:
```
https://api.something.eastus.azurecontainerapps.io
```

Test it:
```
curl https://YOUR-URL/health
```

### Commands

```bash
# Check status
python kilo.py status

# Full deployment (GitHub + Azure)
python kilo.py full-deploy

# Delete everything
python kilo.py cleanup
```

### Troubleshooting

**"Azure CLI not authenticated"**
- Run: az login
- Complete browser authentication
- Try again

**"Timeout building images"**
- This is normal on first run
- Images are 2-4GB each
- Wait time: 10-15 minutes total

**"Resource group already exists"**
- Delete it first: python kilo.py cleanup
- Or use a different location

### Local Development (No Azure needed)

```bash
# Start everything locally
docker compose up --build

# Test
curl http://localhost:8000/health
```

Press Ctrl+C to stop

### Need Help?

- Check deployment.json for your URLs
- Run: python kilo.py status
- View logs in Azure Portal: portal.azure.com

### Costs

- Azure Container Apps: ~$50-150/month
- Container Registry: ~$5/month
- Total: ~$55-155/month while running

Scale to zero: Set min-replicas=0 to pay only when used
