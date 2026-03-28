from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import time

app = FastAPI(title="Orchestrator")

MODEL_1_URL = os.getenv("MODEL_1_URL", "http://model1:8002")
MODEL_2_URL = os.getenv("MODEL_2_URL", "http://model2:8003")

class PredictRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "healthy", "service": "orchestrator"}

@app.post("/predict")
async def predict(req: PredictRequest):
    start = time.time()
    
    # Call both models in parallel
    async with httpx.AsyncClient() as client:
        try:
            task1 = client.post(f"{MODEL_1_URL}/predict", json={"text": req.text}, timeout=60.0)
            task2 = client.post(f"{MODEL_2_URL}/predict", json={"text": req.text}, timeout=60.0)
            
            response1 = await task1
            response2 = await task2
            
            result1 = response1.json() if response1.status_code == 200 else {"error": "Model 1 failed"}
            result2 = response2.json() if response2.status_code == 200 else {"error": "Model 2 failed"}
        except Exception as e:
            return {"error": str(e), "text": req.text}
    
    # Simple ensemble: average scores if both succeeded
    ensemble_result = {
        "input": req.text,
        "model_1_result": result1,
        "model_2_result": result2,
        "ensemble_time_ms": round((time.time() - start) * 1000, 2)
    }
    
    return ensemble_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
