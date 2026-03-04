import os
from groq import Groq


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY manquante")
    return Groq(api_key=api_key)