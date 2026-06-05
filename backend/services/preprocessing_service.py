import re


def clean_transcript(transcript) -> str:
    # youtube-transcript-api returns a FetchedTranscript object (iterable of dicts)
    # Each item has a 'text' key
    try:
        text = " ".join(
            item["text"] if isinstance(item, dict) else item.text for item in transcript
        )
    except Exception as e:
        raise RuntimeError(f"Failed to parse transcript: {e}")

    text = remove_noise(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_noise(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    return text
