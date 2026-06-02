import re
import xml.etree.ElementTree as ET
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)


def get_video_id(url: str):
    # Matches standard, share, and short links
    match = re.search(
        r"(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})", url
    )
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)


def get_transcript(url: str):
    try:
        video_id = get_video_id(url)
    except ValueError as e:
        return {"error": str(e)}

    try:
        # Initialize the modern API client instance
        api = YouTubeTranscriptApi()

        # Use .list() instead of the deprecated static method
        transcript_list = api.list(video_id)

        # Try manually created English transcripts first
        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            # Fallback: auto-generated English captions
            transcript = transcript_list.find_generated_transcript(["en"])

        return transcript.fetch()

    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video"}

    except NoTranscriptFound:
        return {"error": "No transcript available for this video"}

    except ET.ParseError:
        return {
            "error": "YouTube blocked this request (XML Parse Error). Try using cookies or a proxy."
        }

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
