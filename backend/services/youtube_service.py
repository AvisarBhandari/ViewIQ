import json
import tempfile
import yt_dlp
import re
import xml.etree.ElementTree as ET
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)


# Extract YouTube Video ID
def get_video_id(url: str) -> str:
    match = re.search(
        r"(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})",
        url,
    )

    if not match:
        raise ValueError("Invalid YouTube URL")

    return match.group(1)


# Fetch Transcript Safely
def get_transcript(url: str):
    """
    Returns:
        List of transcript segments OR None if unavailable
    """

    try:
        video_id = get_video_id(url)

        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            # fallback to auto-generated captions
            transcript = transcript_list.find_generated_transcript(["en"])

        return transcript.fetch()

    # Known transcript issues
    except TranscriptsDisabled:
        print("Transcript disabled for video:", url)
        return None

    except NoTranscriptFound:
        print("No transcript found for video:", url)
        return None

    # YouTube / IP blocking issues
    except ET.ParseError:
        print("YouTube blocked or returned invalid XML:", url)
        return None

    # Newer API / request blocking errors
    except Exception as e:
        msg = str(e).lower()

        if "blocked" in msg or "ip" in msg:
            print("YouTube blocked this request (IP restriction)")
            return None

        print("Unexpected transcript error:", str(e))
        return None


def get_transcript_ytdlp(url: str):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "skip_download": True,
                "subtitleslangs": ["en"],
                "outtmpl": f"{tmpdir}/%(id)s.%(ext)s",
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            subtitles = info.get("automatic_captions", {}) or info.get("subtitles", {})

            if not subtitles:
                return None

            return subtitles

    except Exception:
        return None
