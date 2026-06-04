import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

SYSTEM_PROMPT = """You are an AI assistant that compares two social media videos (Video A and Video B).

You have access to transcript chunks from both videos, labelled with their video ID.

When answering:
- Always specify which video you are referring to (Video A or Video B).
- Cite the chunk label when making a specific claim, e.g. (Video A · chunk 2).
- If comparing engagement or hooks, be direct and specific.
- If the answer is not in the context, say: "I couldn't find that in the video transcripts."
- Never fabricate information."""


def stream_answer(context: str, question: str, history: list[dict]):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include conversation memory
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    user_message = f"""Context from both videos:

{context}

Question: {question}"""

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=messages,
        stream=True,  # ← real streaming, not post-split
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
