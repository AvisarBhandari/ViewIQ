import yt_dlp


def get_metadata(url: str):
    # "quiet": True stops yt-dlp from printing its usual progress logs, warnings, and download statuses on terminal.
    ydl_opts = {
        "quiet": True
    }

    # Initializes the core engine and safely closes network connections or cleans up memory automatically when the block finishes.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        
        return {
            "title": info.get("title"),
            "creator": info.get("uploader"),
            "views": info.get("view_count"),
            "likes": info.get("like_count"),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration"),
        }