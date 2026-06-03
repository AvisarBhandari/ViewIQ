from fastapi import FastAPI, Query
from pydantic import BaseModel
from services.ingestion_service import ingest_youtube
from services.vectorstore_service import collection
from services.retrieval_service import retrieve

app = FastAPI()


class IngestRequest(BaseModel):
    url: str


@app.post("/ingest")
def ingest(req: IngestRequest):

    data = ingest_youtube(req.url)

    return {"status": "success", "data": data}


@app.get("/debug/chroma")
def debug_chroma():

    return {"count": collection.count()}


@app.get("/search")
def search(question: str = Query(...)):
    return retrieve(question)
