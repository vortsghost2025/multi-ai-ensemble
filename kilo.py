#!/usr/bin/env python3
"""
KILO - Autonomous Deployment Agent
===================================
Kilo handles GitHub and Azure deployment operations autonomously.
Designed for accessibility - minimal user interaction required.

Usage:
    python kilo.py deploy        # Deploy to Azure
    python kilo.py github-setup  # Create GitHub repo and push
    python kilo.py full-deploy   # Do everything

Requirements:
    - Azure CLI installed and logged in (az login)
    - GitHub CLI installed and authenticated (gh auth login)
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict

class KiloAgent:
    """Autonomous deployment agent"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.rg_name = "rg-ensemble"
        self.location = "eastus"
        self.acr_name = None
        self.env_name = "env-ensemble"
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and audio-friendly formatting"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_cmd(self, cmd: List[str], description: str, timeout: int = 600) -> tuple:
        """Run command with clear output"""
        self.log(f"Starting: {description}")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                self.log(f"✓ Completed: {description}")
                return (True, result.stdout)
            else:
                self.log(f"✗ Failed: {description}", "ERROR")
                self.log(f"Error: {result.stderr}", "ERROR")
                return (False, result.stderr)
        except subprocess.TimeoutExpired:
            self.log(f"✗ Timeout: {description}", "ERROR")
            return (False, "Timeout")
        except Exception as e:
            self.log(f"✗ Exception: {e}", "ERROR")
            return (False, str(e))
    
    def check_prerequisites(self) -> bool:
        """Check if Azure CLI and GitHub CLI are ready"""
        self.log("Checking prerequisites...")
        
        # Check Azure CLI
        success, _ = self.run_cmd(["az", "account", "show"], "Azure CLI auth check", timeout=30)
        if not success:
            self.log("Azure CLI not authenticated. Run: az login", "ERROR")
            return False
            
        self.log("✓ Azure CLI authenticated")
        
        # Check GitHub CLI (optional)
        success, _ = self.run_cmd(["gh", "auth", "status"], "GitHub CLI auth check", timeout=30)
        if success:
            self.log("✓ GitHub CLI authenticated")
        else:
            self.log("GitHub CLI not authenticated (optional)", "WARNING")
            
        return True
    
    def generate_acr_name(self) -> str:
        """Generate unique ACR name"""
        import random
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"ensembleacr{suffix}"
    
    def deploy_azure(self) -> bool:
        """Deploy to Azure Container Apps"""
        self.log("=== AZURE DEPLOYMENT STARTED ===")
        
        # Generate ACR name
        self.acr_name = self.generate_acr_name()
        
        # Step 1: Resource Group
        success, _ = self.run_cmd([
            "az", "group", "create",
            "--name", self.rg_name,
            "--location", self.location,
            "--tags", "project=ensemble", "environment=production"
        ], "Creating Resource Group")
        if not success:
            return False
        
        # Step 2: Container Registry
        success, _ = self.run_cmd([
            "az", "acr", "create",
            "--resource-group", self.rg_name,
            "--name", self.acr_name,
            "--sku", "Basic",
            "--admin-enabled", "true"
        ], "Creating Container Registry")
        if not success:
            return False
        
        # Step 3: Container App Environment
        success, _ = self.run_cmd([
            "az", "containerapp", "env", "create",
            "--name", self.env_name,
            "--resource-group", self.rg_name,
            "--location", self.location
        ], "Creating Container App Environment")
        if not success:
            return False
        
        # Step 4: Build images (this takes longest)
        services = ["api", "orchestrator", "model_service_1", "model_service_2"]
        for svc in services:
            success, _ = self.run_cmd([
                "az", "acr", "build",
                "--registry", self.acr_name,
                "--image", f"{svc}:latest",
                "--file", f"./{svc}/Dockerfile",
                f"./{svc}"
            ], f"Building {svc} image (takes 5-10 minutes)", timeout=900)
            if not success:
                self.log(f"Warning: {svc} build had issues, continuing...", "WARNING")
        
        # Step 5: Deploy Model Service 1
        success, _ = self.run_cmd([
            "az", "containerapp", "create",
            "--name", "model1",
            "--resource-group", self.rg_name,
            "--environment", self.env_name,
            "--image", f"{self.acr_name}.azurecr.io/model_service_1:latest",
            "--target-port", "8002",
            "--ingress", "internal",
            "--min-replicas", "1",
            "--max-replicas", "3",
            "--cpu", "1.0",
            "--memory", "2Gi",
            "--env-vars", "MODEL_NAME=distilbert-base-uncased-finetuned-sst-2-english", "DEVICE=cpu"
        ], "Deploying Model Service 1")
        if not success:
            return False
        
        # Get Model 1 URL
        success, m1_url = self.run_cmd([
            "az", "containerapp", "show",
            "--name", "model1",
            "--resource-group", self.rg_name,
            "--query", "properties.configuration.ingress.fqdn",
            "-o", "tsv"
        ], "Getting Model 1 URL", timeout=30)
        m1_url = m1_url.strip() if success else ""
        
        # Step 6: Deploy Model Service 2
        success, _ = self.run_cmd([
            "az", "containerapp", "create",
            "--name", "model2",
            "--resource-group", self.rg_name,
            "--environment", self.env_name,
            "--image", f"{self.acr_name}.azurecr.io/model_service_2:latest",
            "--target-port", "8003",
            "--ingress", "internal",
            "--min-replicas", "0",
            "--max-replicas", "2",
            "--cpu", "2.0",
            "--memory", "4Gi",
            "--env-vars", "MODEL_NAME=gpt2-medium", "DEVICE=cpu"
        ], "Deploying Model Service 2")
        if not success:
            return False
        
        # Get Model 2 URL
        success, m2_url = self.run_cmd([
            "az", "containerapp", "show",
            "--name", "model2",
            "--resource-group", self.rg_name,
            "--query", "properties.configuration.ingress.fqdn",
            "-o", "tsv"
        ], "Getting Model 2 URL", timeout=30)
        m2_url = m2_url.strip() if success else ""
        
        # Step 7: Deploy Orchestrator
        orch_env = f"MODEL_1_URL=https://{m1_url}/predict,MODEL_2_URL=https://{m2_url}/predict"
        success, _ = self.run_cmd([
            "az", "containerapp", "create",
            "--name", "orchestrator",
            "--resource-group", self.rg_name,
            "--environment", self.env_name,
            "--image", f"{self.acr_name}.azurecr.io/orchestrator:latest",
            "--target-port", "8001",
            "--ingress", "internal",
            "--min-replicas", "1",
            "--max-replicas", "3",
            "--cpu", "0.5",
            "--memory", "1Gi",
            "--env-vars", orch_env
        ], "Deploying Orchestrator")
        if not success:
            return False
        
        # Get Orchestrator URL
        success, orch_url = self.run_cmd([
            "az", "containerapp", "show",
            "--name", "orchestrator",
            "--resource-group", self.rg_name,
            "--query", "properties.configuration.ingress.fqdn",
            "-o", "tsv"
        ], "Getting Orchestrator URL", timeout=30)
        orch_url = orch_url.strip() if success else ""
        
        # Step 8: Deploy Public API
        api_env = f"ORCH_URL=https://{orch_url}"
        success, _ = self.run_cmd([
            "az", "containerapp", "create",
            "--name", "api",
            "--resource-group", self.rg_name,
            "--environment", self.env_name,
            "--image", f"{self.acr_name}.azurecr.io/api:latest",
            "--target-port", "8000",
            "--ingress", "external",
            "--min-replicas", "1",
            "--max-replicas", "5",
            "--cpu", "0.5",
            "--memory", "1Gi",
            "--env-vars", api_env
        ], "Deploying Public API")
        if not success:
            return False
        
        # Get Public API URL
        success, api_url = self.run_cmd([
            "az", "containerapp", "show",
            "--name", "api",
            "--resource-group", self.rg_name,
            "--query", "properties.configuration.ingress.fqdn",
            "-o", "tsv"
        ], "Getting Public API URL", timeout=30)
        api_url = api_url.strip() if success else ""
        
        # Save deployment info
        deployment_info = {
            "api_url": f"https://{api_url}",
            "resource_group": self.rg_name,
            "acr_name": self.acr_name,
            "environment": self.env_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.project_root / "deployment.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        # Display results
        self.log("=== DEPLOYMENT COMPLETE ===")
        self.log(f"Your API URL: https://{api_url}")
        self.log(f"Resource Group: {self.rg_name}")
        self.log("")
        self.log("Test commands:")
        self.log(f"  curl https://{api_url}/health")
        self.log(f"  curl -X POST https://{api_url}/predict -H 'Content-Type: application/json' -d '{{\"text\":\"Hello\"}}'")
        self.log("")
        self.log("To delete everything:")
        self.log(f"  az group delete --name {self.rg_name} --yes")
        self.log("")
        self.log("Deployment info saved to: deployment.json")
        
        return True
    
    def github_setup(self) -> bool:
        """Create GitHub repo and push code"""
        self.log("=== GITHUB SETUP STARTED ===")
        
        # Check if already has remote
        success, _ = self.run_cmd(["git", "remote", "get-url", "origin"], "Checking remote")
        if success:
            self.log("GitHub remote already configured")
            # Just push
            success, _ = self.run_cmd(["git", "push", "-u", "origin", "main"], "Pushing to GitHub")
            return success
        
        # Create GitHub repo
        success, _ = self.run_cmd([
            "gh", "repo", "create", "multi-ai-ensemble",
            "--public", "--source=.", "--remote=origin", "--push"
        ], "Creating GitHub repository and pushing")
        
        if success:
            self.log("✓ GitHub repository created and code pushed")
            return True
        else:
            self.log("GitHub CLI failed. Manual steps:", "ERROR")
            self.log("1. Go to github.com and create 'multi-ai-ensemble' repo")
            self.log("2. Run: git remote add origin https://github.com/YOUR_USERNAME/multi-ai-ensemble.git")
            self.log("3. Run: git push -u origin main")
            return False
    
    def full_deploy(self):
        """Do everything: GitHub + Azure"""
        self.log("=== FULL DEPLOYMENT MODE ===")
        self.log("This will:")
        self.log("  1. Push code to GitHub (if authenticated)")
        self.log("  2. Deploy to Azure Container Apps")
        self.log("")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.log("Prerequisites not met. Please authenticate first.", "ERROR")
            return False
        
        # Try GitHub setup (optional)
        self.github_setup()
        
        # Deploy to Azure
        return self.deploy_azure()
    
    def status(self):
        """Check deployment status"""
        self.log("=== DEPLOYMENT STATUS ===")
        
        # Check if deployment.json exists
        deploy_file = self.project_root / "deployment.json"
        if deploy_file.exists():
            with open(deploy_file) as f:
                info = json.load(f)
            self.log(f"Previous deployment found:")
            self.log(f"  API URL: {info.get('api_url', 'N/A')}")
            self.log(f"  Resource Group: {info.get('resource_group', 'N/A')}")
            self.log(f"  Deployed: {info.get('timestamp', 'N/A')}")
        else:
            self.log("No previous deployment found")
        
        # Check Azure resources
        success, _ = self.run_cmd([
            "az", "group", "show",
            "--name", self.rg_name
        ], "Checking Azure resource group", timeout=30)
        
        if success:
            self.log(f"✓ Resource group exists: {self.rg_name}")
        else:
            self.log(f"✗ Resource group not found: {self.rg_name}")
        
        return True
    
    def cleanup(self):
        """Delete all Azure resources"""
        self.log("=== CLEANUP MODE ===")
        self.log(f"This will DELETE all resources in: {self.rg_name}")
        self.log("Type 'yes' to confirm (or press Ctrl+C to cancel)")
        
        try:
            confirm = input("Confirm: ")
            if confirm.lower() == "yes":
                success, _ = self.run_cmd([
                    "az", "group", "delete",
                    "--name", self.rg_name,
                    "--yes"
                ], "Deleting resource group", timeout=300)
                if success:
                    self.log("✓ All resources deleted")
                    # Remove deployment.json
                    deploy_file = self.project_root / "deployment.json"
                    if deploy_file.exists():
                        deploy_file.unlink()
                return success
            else:
                self.log("Cleanup cancelled")
                return False
        except KeyboardInterrupt:
            self.log("Cleanup cancelled")
            return False


def main():
    """Main entry point"""
    kilo = KiloAgent()
    
    if len(sys.argv) < 2:
        print("KILO - Autonomous Deployment Agent")
        print("")
        print("Usage:")
        print("  python kilo.py deploy       - Deploy to Azure only")
        print("  python kilo.py github-setup - Setup GitHub repo")
        print("  python kilo.py full-deploy  - GitHub + Azure deployment")
        print("  python kilo.py status       - Check deployment status")
        print("  python kilo.py cleanup      - Delete all Azure resources")
        print("")
        print("Prerequisites:")
        print("  - Azure CLI: az login")
        print("  - GitHub CLI (optional): gh auth login")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "deploy":
        if not kilo.check_prerequisites():
            sys.exit(1)
        success = kilo.deploy_azure()
        sys.exit(0 if success else 1)
    
    elif command == "github-setup":
        success = kilo.github_setup()
        sys.exit(0 if success else 1)
    
    elif command == "full-deploy":
        success = kilo.full_deploy()
        sys.exit(0 if success else 1)
    
    elif command == "status":
        kilo.status()
        sys.exit(0)
    
    elif command == "cleanup":
        kilo.cleanup()
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        print("Run 'python kilo.py' for usage help")
        sys.exit(1)


if __name__ == "__main__":
    main()
