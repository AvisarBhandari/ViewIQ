import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_or_create_collection(name="videos")


def store_chunks(chunk_objects):
    if not chunk_objects:
        raise ValueError("Attempted to store empty chunk list")

    collection.add(
        documents=[c["text"] for c in chunk_objects],
        metadatas=[
            {
                "video_id": c["video_id"],
                "title": c["video_title"],
                "creator": c["creator"],
                "source": c["source_url"],
                "chunk_index": c["chunk_index"],
                "views": c.get("views", 0),
                "likes": c.get("likes", 0),
                "comments": c.get("comments", 0),
                "engagement_rate": c.get("engagement_rate", 0.0),
                "duration": c.get("duration", 0),
                "upload_date": c.get("upload_date", ""),
                "follower_count": c.get("follower_count") or 0,
            }
            for c in chunk_objects
        ],
        embeddings=[c["embedding"] for c in chunk_objects],
        ids=[f"{c['video_id']}_chunk_{c['chunk_index']}" for c in chunk_objects],
    )
