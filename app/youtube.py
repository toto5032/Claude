import re
from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?.*v=)([\w-]{11})",
        r"(?:youtu\.be/)([\w-]{11})",
        r"(?:youtube\.com/embed/)([\w-]{11})",
        r"(?:youtube\.com/shorts/)([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    parsed = urlparse(url)
    if parsed.hostname and "youtube.com" in parsed.hostname:
        qs = parse_qs(parsed.query)
        v = qs.get("v")
        if v and len(v[0]) == 11:
            return v[0]
    return None


def get_thumbnail_url(video_id: str) -> str:
    """Get YouTube thumbnail URL from video ID."""
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def get_embed_url(video_id: str) -> str:
    """Get YouTube embed URL from video ID."""
    return f"https://www.youtube.com/embed/{video_id}"
