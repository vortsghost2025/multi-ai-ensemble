from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="API Gateway")

ORCH_URL = os.getenv("ORCH_URL", "http://orchestrator:8001")

class PredictRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "healthy", "service": "api"}

@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ORCH_URL}/predict",
                json={"text": req.text},
                timeout=60.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
