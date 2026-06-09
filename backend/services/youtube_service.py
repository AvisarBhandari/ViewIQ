import os
import re
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv

load_dotenv()
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

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


# Primary: Supadata API
# Runs on Supadata's IPs — never blocked by YouTube.
def _get_transcript_supadata(video_id: str):
    if not SUPADATA_API_KEY:
        print("[youtube] SUPADATA_API_KEY not set, skipping.")
        return None
    try:
        res = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            headers={"x-api-key": SUPADATA_API_KEY},
            params={"videoId": video_id, "text": "true"},
            timeout=30,
        )
        if res.status_code == 404:
            print(f"[supadata] No transcript available for {video_id}")
            return None
        if not res.ok:
            print(f"[supadata] {res.status_code}: {res.text}")
            return None

        data = res.json()
        text = data.get("content", "").strip()
        if not text:
            print(f"[supadata] Empty transcript for {video_id}")
            return None

        # Normalise to the same shape as youtube-transcript-api
        # so preprocessing_service.clean_transcript works unchanged
        return [{"text": text, "start": 0, "duration": 0}]

    except Exception as e:
        print(f"[supadata] Exception: {e}")
        return None


# ── Fallback: youtube-transcript-api through ScraperAPI residential proxy ─────
def _get_transcript_proxy(video_id: str):
    proxies = None
    if SCRAPER_API_KEY:
        proxy_url = f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001"
        proxies = {"http": proxy_url, "https": proxy_url}
    else:
        print("[youtube] SCRAPER_API_KEY not set — trying without proxy (may be blocked).")

    try:
        api = YouTubeTranscriptApi(proxies=proxies)
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
            print(f"[youtube] Unexpected error on {video_id}: {e}")
        return None


# Public interface (called by ingestion_service) 
def get_transcript(url: str):
    video_id = get_video_id(url)

    # 1. Try Supadata (no YouTube IP exposure)
    result = _get_transcript_supadata(video_id)
    if result:
        print(f"[youtube] ✓ Supadata transcript for {video_id}")
        return result

    # 2. Try youtube-transcript-api through ScraperAPI proxy
    print(f"[youtube] Supadata failed, trying proxy fallback for {video_id}...")
    result = _get_transcript_proxy(video_id)
    if result:
        print(f"[youtube] ✓ Proxy transcript for {video_id}")
        return result

    print(f"[youtube] ✗ All methods failed for {video_id}")
    return None