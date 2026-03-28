from fastapi import FastAPI
from pydantic import BaseModel
import time
import random

app = FastAPI(title="Model Service 2 - Generation")

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    result: dict
    model: str
    inference_time_ms: float

@app.get("/health")
def health():
    return {"status": "healthy", "service": "model2", "model": "generation-mock"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start = time.time()
    
    # Mock text generation
    responses = [
        f"Based on your input: '{req.text}', I think that's interesting!",
        f"Regarding '{req.text}', here's what I found...",
        f"Your message '{req.text}' has been processed successfully.",
        f"Analysis of '{req.text}' complete. Result: positive."
    ]
    
    generated = random.choice(responses)
    
    inference_time = (time.time() - start) * 1000
    
    return PredictResponse(
        result={"generated_text": generated, "tokens": len(generated.split())},
        model="gpt2-medium-mock",
        inference_time_ms=round(inference_time, 2)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
