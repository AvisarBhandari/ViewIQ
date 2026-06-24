import os
import re
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

load_dotenv()

SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")


def get_video_id(url: str) -> str:
    match = re.search(
        r"(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})",
        url,
    )
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)


# 1. Supadata API
def _get_transcript_supadata(video_id: str):
    if not SUPADATA_API_KEY:
        print("[youtube] SUPADATA_API_KEY not set, skipping.")
        return None
    try:
        res = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            headers={"x-api-key": SUPADATA_API_KEY},
            params={"videoId": video_id, "text": "true"},
            timeout=10,  # fail fast so fallback runs immediately
        )
        if res.status_code == 404:
            print(f"[supadata] No transcript for {video_id}")
            return None
        if not res.ok:
            print(f"[supadata] {res.status_code}: {res.text[:120]}")
            return None

        text = res.json().get("content", "").strip()
        if not text:
            print(f"[supadata] Empty transcript for {video_id}")
            return None

        return [{"text": text, "start": 0, "duration": 0}]

    except requests.exceptions.Timeout:
        print("[supadata] Timed out — service may be down, trying fallback...")
        return None
    except Exception as e:
        print(f"[supadata] Exception: {e}")
        return None


# 2. youtube-transcript-api through ScraperAPI (v1.x proxy API)
def _get_transcript_proxy(video_id: str):
    proxy_config = None
    if SCRAPER_API_KEY:
        proxy_url = (
            f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001"
        )
        # v1.x uses ProxyConfig objects — NOT a plain dict
        proxy_config = GenericProxyConfig(
            http_url=proxy_url,
            https_url=proxy_url,
        )
    else:
        print(
            "[youtube] SCRAPER_API_KEY not set — trying without proxy (likely blocked on cloud)."
        )

    try:
        api = YouTubeTranscriptApi(proxy_config=proxy_config)
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en"])

        return transcript.fetch()

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"[youtube] No transcript for {video_id}: {e}")
        return None
    except ET.ParseError:
        print(f"[youtube] Blocked / invalid XML for {video_id}")
        return None
    except Exception as e:
        msg = str(e).lower()
        if any(kw in msg for kw in ("blocked", "ip", "bot", "sign in", "confirm")):
            print(f"[youtube] IP/bot block on {video_id}: {e}")
        else:
            print(f"[youtube] Error on {video_id}: {e}")
        return None


# 3. youtube-transcript-api direct (last resort, works locally)
def _get_transcript_direct(video_id: str):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en"])
        return transcript.fetch()
    except Exception as e:
        print(f"[youtube] Direct fetch failed for {video_id}: {e}")
        return None


# Public interface
def get_transcript(url: str):
    video_id = get_video_id(url)

    result = _get_transcript_supadata(video_id)
    if result:
        print(f"[youtube] ✓ Supadata — {video_id}")
        return result

    print(f"[youtube] Trying ScraperAPI proxy — {video_id}...")
    result = _get_transcript_proxy(video_id)
    if result:
        print(f"[youtube] ✓ Proxy — {video_id}")
        return result

    print(f"[youtube] Trying direct fetch — {video_id}...")
    result = _get_transcript_direct(video_id)
    if result:
        print(f"[youtube] ✓ Direct — {video_id}")
        return result

    print(f"[youtube] ✗ All methods failed for {video_id}")
    return None
