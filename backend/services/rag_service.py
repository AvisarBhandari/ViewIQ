from services.retrieval_service import retrieve_per_video
from services.llm_service import stream_answer


def rag_chat_stream(question: str, history: list[dict]):
    chunks = retrieve_per_video(question, k_each=3)

    # Build labelled context with citation markers
    context_parts = []
    for c in chunks:
        label = f"[Video {c['video_id']} · chunk {c['chunk_index']} · {c['title']}]"
        context_parts.append(f"{label}\n{c['text']}")

    context = "\n\n---\n\n".join(context_parts)

    # Yield citation metadata first so the frontend can display sources
    sources = [
        {
            "video_id": c["video_id"],
            "title": c["title"],
            "creator": c["creator"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]
    yield {"type": "sources", "sources": sources}

    # Stream answer tokens
    for token in stream_answer(context=context, question=question, history=history):
        yield {"type": "token", "token": token}
