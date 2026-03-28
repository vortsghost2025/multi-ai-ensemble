from fastapi import FastAPI
from pydantic import BaseModel
import time
import random

app = FastAPI(title="Model Service 1 - Sentiment")

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    result: dict
    model: str
    inference_time_ms: float

@app.get("/health")
def health():
    return {"status": "healthy", "service": "model1", "model": "sentiment-mock"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start = time.time()
    
    # Simple sentiment analysis mock
    positive_words = ["good", "great", "excellent", "amazing", "love", "happy"]
    negative_words = ["bad", "terrible", "awful", "hate", "sad", "angry"]
    
    text_lower = req.text.lower()
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        label = "POSITIVE"
        score = 0.85 + random.random() * 0.14
    elif neg_count > pos_count:
        label = "NEGATIVE"
        score = 0.85 + random.random() * 0.14
    else:
        label = "NEUTRAL"
        score = 0.5 + random.random() * 0.3
    
    inference_time = (time.time() - start) * 1000
    
    return PredictResponse(
        result={"label": label, "score": round(score, 4)},
        model="distilbert-sentiment-mock",
        inference_time_ms=round(inference_time, 2)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
