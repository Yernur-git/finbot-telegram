import os
import requests

PROVIDER = os.environ.get("AI_PROVIDER", "openrouter").lower()
API_KEY  = os.environ.get("AI_API_KEY", "")

# Модели по умолчанию для каждого провайдера
DEFAULT_MODELS = {
    "openrouter": "meta-llama/llama-3.1-8b-instruct:free",
    "claude":     "claude-haiku-4-5-20251001",
    "openai":     "gpt-4o-mini",
    "gemini":     "gemini-1.5-flash"
}

MODEL = os.environ.get("AI_MODEL", DEFAULT_MODELS.get(PROVIDER, ""))

def get_ai_response(prompt: str) -> str:
    if PROVIDER == "openrouter":
        return _openrouter(prompt)
    elif PROVIDER == "claude":
        return _claude(prompt)
    elif PROVIDER == "openai":
        return _openai(prompt)
    elif PROVIDER == "gemini":
        return _gemini(prompt)
    else:
        return f"Неизвестный провайдер: {PROVIDER}"

def _openrouter(prompt):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/finbot",
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _claude(prompt):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]

def _openai(prompt):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _gemini(prompt):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
