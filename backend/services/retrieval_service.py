import chromadb
from services.embedding_service import model

client = chromadb.PersistentClient(path="./data/chroma_db")

collection = client.get_collection("videos")


def retrieve(query, k=3):

    query_embedding = model.encode(query).tolist()

    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    response = []

    for doc, meta in zip(docs, metas):
        response.append(
            {
                "text": doc,
                "title": meta["title"],
                "creator": meta["creator"],
                "source": meta["source"],
            }
        )

    return response
