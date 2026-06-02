from services.metadata_service import get_metadata
from services.youtube_service import get_transcript
from services.preprocessing_service import clean_transcript
from services.chunking_service import chunk_text


def ingest_youtube(url: str):

    # 1. metadata
    metadata = get_metadata(url)

    # 2. transcript
    raw_transcript = get_transcript(url)
    transcript = clean_transcript(raw_transcript)
    chunks = chunk_text(transcript)

    print(len(chunks))

    print(chunks[0][:200])

    # 3. combine into single structure
    return {
        "metadata": metadata,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "source": url,
    }
