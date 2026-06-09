import chromadb
from services.embedding_service import embed_query

client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_or_create_collection(name="videos")


def retrieve(query: str, k: int = 5, video_id: str = None) -> list[dict]:
    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)
    where = {"video_id": video_id} if video_id else None
    actual_k = min(k, collection.count())

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        where=where,
    )

    docs  = results["documents"][0]
    metas = results["metadatas"][0]

    return [
        {
            "text":             doc,
            "video_id":         meta["video_id"],
            "title":            meta["title"],
            "creator":          meta["creator"],
            "source":           meta["source"],
            "chunk_index":      meta["chunk_index"],
            "views":            meta.get("views", 0),
            "likes":            meta.get("likes", 0),
            "comments":         meta.get("comments", 0),
            "engagement_rate":  meta.get("engagement_rate", 0.0),
            "duration":         meta.get("duration", 0),
            "upload_date":      meta.get("upload_date", ""),
            "follower_count":   meta.get("follower_count", 0),
        }
        for doc, meta in zip(docs, metas)
    ]


def retrieve_per_video(query: str, video_ids: list[str], k_each: int = 3) -> list[dict]:
    """
    Retrieve k_each chunks from EVERY active video — not just A and B.
    video_ids is passed in from the chat request so we always query the right set.
    """
    chunks = []
    for vid in video_ids:
        chunks.extend(retrieve(query, k=k_each, video_id=vid))
    return chunks