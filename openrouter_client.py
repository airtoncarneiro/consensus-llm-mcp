import os

import httpx
from dotenv import load_dotenv


load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def ask_model(prompt: str, model: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY_PLUGIN")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY_PLUGIN not found"
        )

    response = httpx.post(
        OPENROUTER_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]