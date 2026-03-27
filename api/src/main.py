"""
API Service - Public-facing API for the Multi-AI Ensemble
"""
import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time

app = FastAPI(
    title="Multi-AI Ensemble API",
    description="Public API for ensemble AI model predictions",
    version="1.0.0"
)

ORCH_URL = os.getenv("ORCH_URL", "http://orchestrator:8001")


class PredictRequest(BaseModel):
    text: str
    model_filter: Optional[list] = None
    timeout: Optional[float] = 30.0


class PredictResponse(BaseModel):
    ensemble_result: Dict[str, Any]
    processing_time_ms: float
    models_used: list


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response


@app.get("/")
async def root():
    return {
        "service": "Multi-AI Ensemble API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/predict",
            "/info"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api",
        "timestamp": time.time()
    }


@app.get("/info")
async def info():
    """Service information"""
    return {
        "service": "api",
        "orchestrator_url": ORCH_URL,
        "version": "1.0.0"
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Submit a prediction request to the ensemble
    
    - **text**: Input text for prediction
    - **model_filter**: Optional list of models to use
    - **timeout**: Request timeout in seconds
    """
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "text": request.text,
                "model_filter": request.model_filter
            }
            
            response = await client.post(
                f"{ORCH_URL}/ensemble",
                json=payload,
                timeout=request.timeout
            )
            response.raise_for_status()
            result = response.json()
            
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Orchestrator error: {str(exc)}"
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Internal error: {str(exc)}"
            ) from exc
    
    processing_time = (time.time() - start_time) * 1000
    
    return PredictResponse(
        ensemble_result=result,
        processing_time_ms=processing_time,
        models_used=result.get("models_used", [])
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
