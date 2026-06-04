import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_or_create_collection(name="videos")


def store_chunks(chunk_objects):
    collection.add(
        documents=[c["text"] for c in chunk_objects],
        metadatas=[
            {
                "video_id": c["video_id"],
                "title": c["video_title"],
                "creator": c["creator"],
                "source": c["source_url"],
                "chunk_index": c["chunk_index"],
            }
            for c in chunk_objects
        ],
        embeddings=[c["embedding"] for c in chunk_objects],
        # Stable unique IDs — prevents duplicates on re-ingest
        ids=[f"{c['video_id']}_chunk_{c['chunk_index']}" for c in chunk_objects],
    )
