from services.metadata_service import get_metadata
from services.youtube_service import get_transcript
from services.preprocessing_service import clean_transcript
from services.chunking_service import chunk_text
from services.embedding_service import generate_embeddings
from services.vectorstore_service import store_chunks


def ingest_video(url: str, video_id: str):
    metadata = get_metadata(url)

    raw_transcript = get_transcript(url)
    if not raw_transcript:
        raise ValueError(
            "Could not retrieve transcript from YouTube. "
            "The video may have transcripts disabled, or the server IP is blocked."
        )

    transcript = clean_transcript(raw_transcript)
    chunks = chunk_text(transcript)
    embeddings = generate_embeddings(chunks)

    views    = metadata.get("views", 0) or 0
    likes    = metadata.get("likes", 0) or 0
    comments = metadata.get("comments", 0) or 0
    engagement_rate = round(((likes + comments) / views * 100), 2) if views else 0

    chunk_objects = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_objects.append({
            "text":             chunk,
            "embedding":        embedding,
            "video_id":         video_id,
            "video_title":      metadata["title"],
            "creator":          metadata["creator"],
            "views":            views,
            "likes":            likes,
            "comments":         comments,
            "engagement_rate":  engagement_rate,
            "duration":         metadata.get("duration", 0),
            "upload_date":      metadata.get("upload_date", ""),
            "follower_count":   metadata.get("follower_count") or 0,
            "source_url":       url,
            "chunk_index":      i,
        })

    if not chunk_objects:
        raise ValueError(f"No chunks generated for video {video_id}")

    store_chunks(chunk_objects)

    return {
        "metadata": {**metadata, "engagement_rate": engagement_rate},
        "num_chunks": len(chunks),
        "video_id": video_id,
    }