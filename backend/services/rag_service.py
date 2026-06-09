from services.retrieval_service import retrieve_per_video
from services.llm_service import stream_answer


def rag_chat_stream(question: str, history: list[dict], video_ids: list[str]):
    # Fall back to querying all stored videos if frontend didn't send ids
    if not video_ids:
        from services.vectorstore_service import collection
        try:
            all_meta = collection.get(include=["metadatas"])["metadatas"]
            video_ids = list({m["video_id"] for m in all_meta if m})
        except Exception:
            video_ids = []

    chunks = retrieve_per_video(question, video_ids=video_ids, k_each=3)

    # Build context: transcript chunks + engagement metadata per video 
    # Collect unique per-video metadata to prepend as a fact block
    seen_videos: dict[str, dict] = {}
    for c in chunks:
        vid = c["video_id"]
        if vid not in seen_videos:
            seen_videos[vid] = c  # first chunk carries the metadata

    meta_lines = []
    for vid, c in sorted(seen_videos.items()):
        dur_min = f"{c['duration'] // 60}m {c['duration'] % 60}s" if c.get("duration") else "unknown"
        followers = f"{c['follower_count']:,}" if c.get("follower_count") else "hidden"
        meta_lines.append(
            f"Video {vid} — {c['title']}\n"
            f"  Creator : {c['creator']}  |  Subscribers: {followers}\n"
            f"  Views   : {c['views']:,}  |  Likes: {c['likes']:,}  |  Comments: {c['comments']:,}\n"
            f"  Eng.Rate: {c['engagement_rate']}%  |  Duration: {dur_min}  |  Uploaded: {c['upload_date']}"
        )

    metadata_block = "=== Video Metadata ===\n" + "\n\n".join(meta_lines) if meta_lines else ""

    # Transcript chunks
    context_parts = []
    for c in chunks:
        label = f"[Video {c['video_id']} · chunk {c['chunk_index']} · {c['title']}]"
        context_parts.append(f"{label}\n{c['text']}")

    transcript_block = "\n\n---\n\n".join(context_parts)
    context = f"{metadata_block}\n\n=== Transcript Chunks ===\n{transcript_block}".strip()

    # Yield sources first so frontend can render them immediately
    sources = [
        {
            "video_id":    c["video_id"],
            "title":       c["title"],
            "creator":     c["creator"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]
    yield {"type": "sources", "sources": sources}

    # Stream answer tokens
    for token in stream_answer(
        context=context,
        question=question,
        history=history,
        video_ids=video_ids,
    ):
        yield {"type": "token", "token": token}