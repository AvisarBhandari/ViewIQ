import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free"
)
EMBEDDING_API_URL = os.getenv(
    "EMBEDDING_API_URL", "https://openrouter.ai/api/v1/embeddings"
)

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

BATCH_SIZE = 10


def _embed(inputs: list) -> list[list[float]]:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set in environment variables")

    response = requests.post(
        url=EMBEDDING_API_URL,
        headers=HEADERS,
        data=json.dumps(
            {
                "model": EMBEDDING_MODEL,
                "input": inputs,
                "encoding_format": "float",
            }
        ),
    )

    if not response.ok:
        raise RuntimeError(
            f"Embedding API error {response.status_code}: {response.text}"
        )

    data = response.json()["data"]
    data.sort(key=lambda x: x["index"])
    return [item["embedding"] for item in data]


def generate_embeddings(chunks: list[str]) -> list[list[float]]:
    all_embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        inputs = [{"content": [{"type": "text", "text": chunk}]} for chunk in batch]
        all_embeddings.extend(_embed(inputs))
    return all_embeddings


def embed_query(query: str) -> list[float]:
    inputs = [{"content": [{"type": "text", "text": query}]}]
    return _embed(inputs)[0]
