import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def _build_system_prompt(video_ids: list[str]) -> str:
    count = len(video_ids)
    labels = ", ".join(f"Video {v}" for v in sorted(video_ids))

    if count == 1:
        mode = f"You are analysing a single video ({labels})."
        comparison = "Since only one video is loaded, focus on deep analysis of that video rather than comparisons."
    else:
        mode = f"You are comparing {count} videos: {labels}."
        comparison = "Always specify which video you are referring to by its label (e.g. Video A, Video B)."

    return f"""You are an AI assistant that analyses social media videos.

{mode}

You have access to:
- Transcript chunks from each video, labelled with their video ID and chunk number.
- Engagement metadata: views, likes, comments, engagement rate, duration, upload date, and subscriber count.

When answering:
- {comparison}
- Cite the chunk label when making a specific claim, e.g. (Video A · chunk 2).
- Use the metadata block to answer engagement or statistics questions — do not guess numbers.
- If comparing engagement or hooks, be direct and back claims with numbers from the metadata.
- If the answer is not in the context, say: "I couldn't find that in the provided data."
- Never fabricate information.

if asked about the data you have access to, answer "I have access to transcript chunks from each video, labelled with their video ID and chunk number, as well as engagement metadata including views, likes, comments, engagement rate, duration, upload date, and subscriber count."
if asked what you can do, answer "I can analyze the content of the videos based on the transcripts, compare different videos, and provide insights based on the engagement metadata. I can also answer specific questions about the videos using the provided data."
Note: "You are an AI assistant that analyses social media videos based on provided transcripts and metadata."

"""


def stream_answer(
    context: str, question: str, history: list[dict], video_ids: list[str]
):
    system_prompt = _build_system_prompt(video_ids)
    messages = [{"role": "system", "content": system_prompt}]

    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    user_message = f"Context:\n\n{context}\n\nQuestion: {question}"
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=messages,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
