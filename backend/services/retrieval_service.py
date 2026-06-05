import chromadb
from services.embedding_service import embed_query

client = chromadb.PersistentClient(path="./data/chroma_db")
# Use get_or_create so retrieval doesn't crash before any video is ingested
collection = client.get_or_create_collection(name="videos")


def retrieve(query: str, k: int = 5, video_id: str = None) -> list[dict]:
    # Don't query empty collection
    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)
    where = {"video_id": video_id} if video_id else None

    # k can't exceed number of stored docs
    actual_k = min(k, collection.count())

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        where=where,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    return [
        {
            "text": doc,
            "video_id": meta["video_id"],
            "title": meta["title"],
            "creator": meta["creator"],
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
        }
        for doc, meta in zip(docs, metas)
    ]


def retrieve_per_video(query: str, k_each: int = 3) -> list[dict]:
    chunks_a = retrieve(query, k=k_each, video_id="A")
    chunks_b = retrieve(query, k=k_each, video_id="B")
    return chunks_a + chunks_b
