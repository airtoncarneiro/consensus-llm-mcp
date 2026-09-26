import os

from dotenv import load_dotenv

from openrouter_client import ask_model

load_dotenv()

model = os.getenv("CONSENSUS_MODEL_1")

if not model:
    raise RuntimeError("CONSENSUS_MODEL_1 not found")

print(
    ask_model(
        prompt="Reply with exactly: OpenRouter funcionando",
        model=model,
    )
)
