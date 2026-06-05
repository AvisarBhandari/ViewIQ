import os

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ingestion_service import ingest_video
from services.vectorstore_service import collection
from services.retrieval_service import retrieve
from services.rag_service import rag_chat_stream
import json

app = FastAPI()
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Debugging: Check your terminal logs when the server starts!
print(f"--- DEBUG: CORS allowed origin is set to: '{frontend_url}' ---")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    url_a: str
    url_b: str


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []  # [{role, content}, ...] for memory


class IngestOneRequest(BaseModel):
    url: str
    video_id: str  # "A", "B", "C" ...


@app.post("/ingest-one")
def ingest_one(req: IngestOneRequest):
    # Remove old chunks for this video_id before re-ingesting
    try:
        collection.delete(where={"video_id": req.video_id})
    except Exception:
        pass
    data = ingest_video(req.url, video_id=req.video_id)
    return {"status": "success", "data": data}


@app.post("/ingest")
def ingest(req: IngestRequest):
    # Clear existing collection so re-ingests don't duplicate
    collection.delete(where={"video_id": {"$in": ["A", "B"]}})

    data_a = ingest_video(req.url_a, video_id="A")
    data_b = ingest_video(req.url_b, video_id="B")

    return {
        "status": "success",
        "data": {
            "videoA": data_a,
            "videoB": data_b,
        },
    }


@app.get("/debug/chroma")
def debug_chroma():
    return {"count": collection.count()}


@app.get("/search")
def search(question: str = Query(...), video_id: str = Query(None)):
    return retrieve(question, video_id=video_id)


@app.post("/chat")
def chat(req: ChatRequest):
    def generate():
        for chunk in rag_chat_stream(req.question, req.history):
            yield (json.dumps(chunk) + "\n").encode("utf-8")

    return StreamingResponse(generate(), media_type="text/plain")
