"""
Model Service 1 - CPU-based sentiment analysis
Uses DistilBERT for sentiment classification
"""
import os
import time
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

app = FastAPI(
    title="Model Service 1 - Sentiment Analysis",
    description="DistilBERT-based sentiment classifier",
    version="1.0.0"
)

# Model configuration
MODEL_NAME = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
DEVICE = os.getenv("DEVICE", "cpu")

# Global model and tokenizer (loaded once at startup)
model = None
tokenizer = None


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    score: float
    confidence: float
    processing_time_ms: float


@app.on_event("startup")
async def load_model():
    """Load model and tokenizer on startup"""
    global model, tokenizer
    print(f"Loading model: {MODEL_NAME}")
    print(f"Using device: {DEVICE}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    
    if DEVICE == "cuda" and torch.cuda.is_available():
        model = model.to("cuda")
    
    model.eval()
    print("Model loaded successfully")


@app.get("/")
async def root():
    return {
        "service": "Model Service 1 - Sentiment Analysis",
        "model": MODEL_NAME,
        "device": DEVICE,
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check - model is ready when this returns"""
    if model is None or tokenizer is None:
        return {
            "status": "loading",
            "service": "model_1",
            "model": MODEL_NAME
        }
    
    return {
        "status": "healthy",
        "service": "model_1",
        "model": MODEL_NAME,
        "device": DEVICE,
        "timestamp": time.time()
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Perform sentiment analysis on input text
    
    Returns sentiment label (positive/negative) and confidence score
    """
    if model is None or tokenizer is None:
        return PredictResponse(
            label="error",
            score=0.0,
            confidence=0.0,
            processing_time_ms=0.0
        )
    
    start_time = time.time()
    
    # Tokenize input
    inputs = tokenizer(
        request.text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )
    
    if DEVICE == "cuda" and torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}
    
    # Inference
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
    
    # Get probabilities
    probs = torch.softmax(logits, dim=-1)
    probs = probs.cpu().numpy()[0]
    
    # Determine label
    if probs[1] > probs[0]:
        label = "positive"
        score = float(probs[1])
    else:
        label = "negative"
        score = float(probs[0])
    
    confidence = max(probs)
    
    processing_time = (time.time() - start_time) * 1000
    
    return PredictResponse(
        label=label,
        score=score,
        confidence=float(confidence),
        processing_time_ms=processing_time
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
