import re


def clean_transcript(transcript):

    text = " ".join(chunk.text for chunk in transcript)

    text = remove_noise(text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_noise(text):

    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)

    return text
