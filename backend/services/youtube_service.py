import re
from weakref import proxy
import xml.etree.ElementTree as ET
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)


def get_video_id(url: str) -> str:
    match = re.search(
        r"(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})", url
    )
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)


def get_transcript(url: str):
    # If the HTTP proxy worked
    proxies = {
        "http": "http://203.19.38.114:1080",
        "https": "http://203.19.38.114:1080",
    }

    # If the HTTPS proxy worked
    proxies = {"http": "http://3.29.67.17:4480", "https": "https://3.29.67.17:4480"}

    try:
        video_id = get_video_id(url)
    except ValueError as e:
        raise ValueError(str(e))

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id, proxies=proxies)

        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en"])

        return transcript.fetch()

    except TranscriptsDisabled:
        raise RuntimeError("Transcripts are disabled for this video")
    except NoTranscriptFound:
        raise RuntimeError("No transcript available for this video")
    except ET.ParseError:
        raise RuntimeError("YouTube blocked this request. Try again later.")
    except Exception as e:
        raise RuntimeError(f"Transcript error: {str(e)}")
