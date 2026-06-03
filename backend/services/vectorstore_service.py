import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")

collection = client.get_or_create_collection(name="videos")


def store_chunks(chunk_objects):
    collection.add(
        documents=[c["text"] for c in chunk_objects],
        metadatas=[
            {
                "title": c["video_title"],
                "creator": c["creator"],
                "source": c["source_url"],
            }
            for c in chunk_objects
        ],
        embeddings=[c["embedding"] for c in chunk_objects],
        ids=[f"{c['video_title']}_{i}" for i, c in enumerate(chunk_objects)],
    )
