import os

class Config:
    YT_API_KEY = os.getenv("YT_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "llama-3.1-8b-instant")
    AI_FALLBACK_MODELS = [
        model.strip()
        for model in os.getenv("AI_FALLBACK_MODELS", "mixtral-8x7b-32768").split(",")
        if model.strip()
    ]