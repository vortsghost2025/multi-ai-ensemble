"""
Orchestrator Service - Routes requests and aggregates ensemble results
"""
import os
import asyncio
import httpx
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(
    title="Ensemble Orchestrator",
    description="Routes requests to model services and aggregates results",
    version="1.0.0"
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "orchestrator_requests_total",
    "Total requests per model",
    ["model"]
)
REQUEST_LATENCY = Histogram(
    "orchestrator_request_latency_seconds",
    "Request latency per model",
    ["model"]
)
ENSEMBLE_COUNT = Counter(
    "orchestrator_ensemble_total",
    "Total ensemble requests"
)
ENSEMBLE_LATENCY = Histogram(
    "orchestrator_ensemble_latency_seconds",
    "Ensemble request latency"
)

# Model endpoints from environment
MODEL_ENDPOINTS = {
    "model_1": os.getenv("MODEL_1_URL", "http://model_service_1:8002/predict"),
    "model_2": os.getenv("MODEL_2_URL", "http://model_service_2:8003/predict")
}


class EnsembleRequest(BaseModel):
    text: str
    model_filter: Optional[List[str]] = None


class EnsembleResponse(BaseModel):
    ensemble_score: float
    model_results: Dict[str, Any]
    models_used: List[str]
    latency_ms: float


async def call_model(model_name: str, url: str, payload: Dict) -> Dict[str, Any]:
    """Call a model service and return results"""
    REQUEST_COUNT.labels(model=model_name).inc()
    
    with REQUEST_LATENCY.labels(model=model_name).time():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                return {
                    "model": model_name,
                    "success": True,
                    "result": response.json()
                }
            except httpx.HTTPError as e:
                return {
                    "model": model_name,
                    "success": False,
                    "error": str(e)
                }
            except Exception as e:
                return {
                    "model": model_name,
                    "success": False,
                    "error": str(e)
                }


@app.get("/")
async def root():
    return {
        "service": "Ensemble Orchestrator",
        "version": "1.0.0",
        "models": list(MODEL_ENDPOINTS.keys()),
        "endpoints": ["/health", "/ensemble", "/metrics"]
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "orchestrator",
        "models_configured": len(MODEL_ENDPOINTS),
        "timestamp": time.time()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/ensemble", response_model=EnsembleResponse)
async def ensemble(request: EnsembleRequest):
    """
    Process ensemble prediction across multiple models
    
    - Aggregates results from all available models
    - Calculates weighted ensemble score
    - Returns individual model results
    """
    ENSEMBLE_COUNT.inc()
    start_time = time.time()
    
    # Determine which models to use
    if request.model_filter:
        models_to_call = {
            k: v for k, v in MODEL_ENDPOINTS.items()
            if k in request.model_filter
        }
    else:
        models_to_call = MODEL_ENDPOINTS
    
    if not models_to_call:
        raise HTTPException(status_code=400, detail="No valid models selected")
    
    # Call all models in parallel
    payload = {"text": request.text}
    tasks = [
        call_model(name, url, payload)
        for name, url in models_to_call.items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Process results
    model_results = {}
    successful_results = []
    
    for result in results:
        model_name = result["model"]
        if result["success"]:
            model_results[model_name] = result["result"]
            score = result["result"].get("score", 0)
            successful_results.append(score)
        else:
            model_results[model_name] = {"error": result.get("error")}
    
    # Calculate ensemble score (simple average for now)
    ensemble_score = 0
    if successful_results:
        ensemble_score = sum(successful_results) / len(successful_results)
    
    latency = (time.time() - start_time) * 1000
    ENSEMBLE_LATENCY.observe(time.time() - start_time)
    
    return EnsembleResponse(
        ensemble_score=ensemble_score,
        model_results=model_results,
        models_used=list(models_to_call.keys()),
        latency_ms=latency
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
