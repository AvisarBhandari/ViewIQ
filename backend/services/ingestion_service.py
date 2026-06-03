from services.metadata_service import get_metadata
from services.youtube_service import get_transcript
from services.preprocessing_service import clean_transcript
from services.chunking_service import chunk_text
from services.embedding_service import generate_embeddings
from services.vectorstore_service import store_chunks, collection

def ingest_youtube(url: str):

    # 1. metadata
    metadata = get_metadata(url)

    # 2. transcript
    raw_transcript = get_transcript(url)
    transcript = clean_transcript(raw_transcript)
    chunks = chunk_text(transcript)
    embeddings = generate_embeddings(chunks).tolist()

    # 3. combine into single structure
    chunk_objects = []

    for chunk, embedding in zip(chunks, embeddings):
        chunk_objects.append(
            {
                "text": chunk,
                "embedding": embedding,
                "video_title": metadata["title"],
                "creator": metadata["creator"],
                "source_url": url,
            }
        )
    store_chunks(chunk_objects)
