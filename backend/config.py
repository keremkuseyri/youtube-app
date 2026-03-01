import os

class Config:
    YT_API_KEY = os.getenv("YT_API_KEY", "AIzaSyCe_POTISdJFdUeSuKNUP7_MQFTmqwPUbE")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAnRiOeJ598q3ZxaU-dKkXwAXz_0RZgqco")
    AI_MODEL = os.getenv("AI_MODEL", "models/gemini-flash-lite-latest")
    AI_FALLBACK_MODELS = [
        model.strip()
        for model in os.getenv("AI_FALLBACK_MODELS", "models/gemini-2.0-flash-lite").split(",")
        if model.strip()
    ]