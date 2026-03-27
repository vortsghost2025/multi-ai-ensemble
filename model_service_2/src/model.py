"""
Model Service 2 - GPU-capable text generation
Uses GPT-2 for text generation tasks
"""
import os
import time
from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI(
    title="Model Service 2 - Text Generation",
    description="GPT-2 based text generator",
    version="1.0.0"
)

# Model configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gpt2-medium")
DEVICE = os.getenv("DEVICE", "cpu")
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "100"))

# Global model and tokenizer
model = None
tokenizer = None


class GenerateRequest(BaseModel):
    text: str
    max_length: Optional[int] = None
    temperature: Optional[float] = 0.7
    num_return_sequences: Optional[int] = 1


class GenerateResponse(BaseModel):
    generated_text: str
    original_text: str
    score: float  # Confidence/probability score
    processing_time_ms: float


@app.on_event("startup")
async def load_model():
    """Load model and tokenizer on startup"""
    global model, tokenizer
    print(f"Loading model: {MODEL_NAME}")
    print(f"Using device: {DEVICE}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    
    if DEVICE == "cuda" and torch.cuda.is_available():
        model = model.to("cuda")
        print("Using CUDA for inference")
    
    model.eval()
    print("Model loaded successfully")


@app.get("/")
async def root():
    return {
        "service": "Model Service 2 - Text Generation",
        "model": MODEL_NAME,
        "device": DEVICE,
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check"""
    if model is None or tokenizer is None:
        return {
            "status": "loading",
            "service": "model_2",
            "model": MODEL_NAME
        }
    
    return {
        "status": "healthy",
        "service": "model_2",
        "model": MODEL_NAME,
        "device": DEVICE,
        "timestamp": time.time()
    }


@app.post("/predict")
async def predict(request: GenerateRequest):
    """
    Generate text based on input prompt
    
    - **text**: Input prompt
    - **max_length**: Maximum length of generated text
    - **temperature**: Sampling temperature (higher = more random)
    - **num_return_sequences**: Number of sequences to generate
    """
    if model is None or tokenizer is None:
        return {
            "error": "Model not loaded",
            "generated_text": "",
            "score": 0.0
        }
    
    start_time = time.time()
    
    # Tokenize input
    inputs = tokenizer(
        request.text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )
    
    if DEVICE == "cuda" and torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}
    
    # Generate
    max_len = request.max_length or MAX_LENGTH
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_len,
            temperature=request.temperature,
            num_return_sequences=request.num_return_sequences,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True
        )
    
    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Calculate a simple "score" based on output length and diversity
    new_text = generated_text[len(request.text):].strip()
    score = min(len(new_text) / max_len, 1.0)  # Normalized by max length
    
    processing_time = (time.time() - start_time) * 1000
    
    return GenerateResponse(
        generated_text=new_text,
        original_text=request.text,
        score=score,
        processing_time_ms=processing_time
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
