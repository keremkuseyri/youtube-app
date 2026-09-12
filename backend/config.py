import os

class Config:
    YT_API_KEY = os.getenv("YT_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-20b")
    AI_FALLBACK_MODELS = [
        model.strip()
        for model in os.getenv("AI_FALLBACK_MODELS", "qwen/qwen3.6-27b").split(",")
        if model.strip()
    ]