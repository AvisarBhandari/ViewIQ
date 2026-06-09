import os
import json

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services.ingestion_service import ingest_video
from services.vectorstore_service import collection
from services.retrieval_service import retrieve
from services.rag_service import rag_chat_stream

load_dotenv()

MAX_VIDEOS = 4  # hard limit on concurrent videos

app = FastAPI()
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
print(f"--- CORS origin: '{frontend_url}' ---")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models 

class IngestRequest(BaseModel):
    """Start a session with 1 or 2 videos."""
    url_a: str
    url_b: str | None = None   # optional — user may start with one video


class IngestOneRequest(BaseModel):
    """Add a single video to an existing session."""
    url: str
    video_id: str              # "A", "B", "C", "D" assigned by frontend


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []
    video_ids: list[str] = []  # which videos are currently loaded


# Routes 

@app.post("/ingest")
def ingest(req: IngestRequest):
    """
    Start a fresh session with 1 or 2 videos.
    Clears all existing data first.
    """
    # Wipe everything so a new session starts clean
    _clear_all()

    results = {}
    try:
        results["videoA"] = ingest_video(req.url_a, video_id="A")
        if req.url_b and req.url_b.strip():
            results["videoB"] = ingest_video(req.url_b, video_id="B")
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    return {"status": "success", "data": results}


@app.post("/ingest-one")
def ingest_one(req: IngestOneRequest):
    """
    Add a video to the current session.
    Enforces MAX_VIDEOS limit.
    """
    # Count distinct video_ids currently stored
    active = _active_video_ids()
    # Allow re-ingesting same id (replace), only block truly new ones over limit
    if req.video_id not in active and len(active) >= MAX_VIDEOS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_VIDEOS} videos allowed. Remove one first."
        )

    # Remove stale chunks for this slot before re-ingesting
    try:
        collection.delete(where={"video_id": req.video_id})
    except Exception:
        pass

    try:
        data = ingest_video(req.url, video_id=req.video_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {"status": "success", "data": data}


@app.delete("/remove/{video_id}")
def remove_video(video_id: str):
    """Remove a single video's chunks from the store."""
    try:
        collection.delete(where={"video_id": video_id})
    except Exception:
        pass
    return {"status": "success", "video_id": video_id}


@app.post("/clear")
def clear_session():
    """Wipe all stored vectors — call when user leaves / resets."""
    _clear_all()
    return {"status": "cleared"}


@app.get("/debug/chroma")
def debug_chroma():
    ids = _active_video_ids()
    return {"count": collection.count(), "video_ids": ids}


@app.get("/search")
def search(question: str = Query(...), video_id: str = Query(None)):
    return retrieve(question, video_id=video_id)


@app.post("/chat")
def chat(req: ChatRequest):
    def generate():
        for chunk in rag_chat_stream(req.question, req.history, req.video_ids):
            yield (json.dumps(chunk) + "\n").encode("utf-8")
    return StreamingResponse(generate(), media_type="text/plain")


# Helpers 

def _active_video_ids() -> list[str]:
    """Return the distinct video_ids currently in the collection."""
    if collection.count() == 0:
        return []
    try:
        all_meta = collection.get(include=["metadatas"])["metadatas"]
        return list({m["video_id"] for m in all_meta if m})
    except Exception:
        return []


def _clear_all():
    try:
        ids = collection.get()["ids"]
        if ids:
            collection.delete(ids=ids)
    except Exception:
        pass