import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_video_id(url: str) -> str:
    match = re.search(
        r"(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})", url
    )
    if not match:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    return match.group(1)


def get_metadata(url: str) -> dict:
    video_id = get_video_id(url)

    # Fetch snippet (title, creator) + statistics (views, likes, comments)
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
            "key": YOUTUBE_API_KEY,
        },
    )

    if not response.ok:
        raise RuntimeError(f"YouTube API error {response.status_code}: {response.text}")

    data = response.json()

    if not data.get("items"):
        raise RuntimeError(f"No video found for ID: {video_id}")

    item = data["items"][0]
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})

    # Parse ISO 8601 duration (PT1H2M3S) to seconds
    duration_seconds = parse_duration(details.get("duration", "PT0S"))

    # Channel subscriber count requires a separate call
    channel_id = snippet.get("channelId")
    follower_count = get_channel_subscribers(channel_id) if channel_id else None

    return {
        "title": snippet.get("title"),
        "creator": snippet.get("channelTitle"),
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0)),
        "comments": int(stats.get("commentCount", 0)),
        "upload_date": snippet.get("publishedAt", "")[:10],
        "duration": duration_seconds,
        "follower_count": follower_count,
        "source_url": url,
        "hashtags": snippet.get("tags", []),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
    }


def get_channel_subscribers(channel_id: str) -> int | None:
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "part": "statistics",
            "id": channel_id,
            "key": YOUTUBE_API_KEY,
        },
    )
    if not response.ok:
        return None
    data = response.json()
    if not data.get("items"):
        return None
    stats = data["items"][0].get("statistics", {})
    # Some channels hide subscriber count
    count = stats.get("subscriberCount")
    return int(count) if count else None


def parse_duration(duration: str) -> int:
    """Convert ISO 8601 duration (PT1H2M3S) to total seconds."""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
