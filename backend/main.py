from fastapi import FastAPI
from pydantic import BaseModel
from services.ingestion_service import ingest_youtube

app = FastAPI()


class IngestRequest(BaseModel):
    url: str


@app.post("/ingest")
def ingest(req: IngestRequest):

    data = ingest_youtube(req.url)

    return {"status": "success", "data": data}
