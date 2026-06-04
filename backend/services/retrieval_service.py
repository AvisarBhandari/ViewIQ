import chromadb
from services.embedding_service import model

client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_collection("videos")


def retrieve(query: str, k: int = 5, video_id: str = None) -> list[dict]:
    query_embedding = model.encode(query).tolist()

    where = {"video_id": video_id} if video_id else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
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
    """Retrieve top-k chunks from each video separately, then merge."""
    chunks_a = retrieve(query, k=k_each, video_id="A")
    chunks_b = retrieve(query, k=k_each, video_id="B")
    return chunks_a + chunks_b
