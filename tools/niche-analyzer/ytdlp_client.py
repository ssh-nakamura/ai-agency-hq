"""yt-dlp wrapper for YouTube search."""

import json
import subprocess
import sys

from config import YTDLP_PATH


def search_videos(query: str, max_results: int = 20) -> list[dict]:
    """Search YouTube and return video metadata."""
    cmd = [
        str(YTDLP_PATH),
        "--flat-playlist",
        "--dump-json",
        f"ytsearch{max_results}:{query}",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:
        print(f"[ytdlp] yt-dlp not found at {YTDLP_PATH}", file=sys.stderr)
        return []
    except subprocess.TimeoutExpired:
        print("[ytdlp] Search timed out", file=sys.stderr)
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            videos.append({
                "id": data.get("id", ""),
                "title": data.get("title", ""),
                "channel": data.get("channel", "") or data.get("uploader", ""),
                "channel_id": data.get("channel_id", "") or data.get("uploader_id", ""),
                "view_count": data.get("view_count", 0) or 0,
                "duration": data.get("duration", 0) or 0,
            })
        except json.JSONDecodeError:
            continue

    return videos


def total_views(videos: list[dict]) -> int:
    """Sum of view counts."""
    return sum(v.get("view_count", 0) for v in videos)


def unique_channels(videos: list[dict]) -> int:
    """Count unique channels."""
    return len({v.get("channel_id", "") for v in videos if v.get("channel_id")})


def avg_views(videos: list[dict]) -> float:
    """Average views per video."""
    if not videos:
        return 0.0
    return total_views(videos) / len(videos)


def median_views(videos: list[dict]) -> int:
    """Median view count across videos."""
    views = sorted(v.get("view_count", 0) for v in videos)
    n = len(views)
    if n == 0:
        return 0
    if n % 2:
        return views[n // 2]
    return (views[n // 2 - 1] + views[n // 2]) // 2


def top1_concentration(videos: list[dict]) -> float:
    """Fraction of total views held by the top video (0.0-1.0). High = outlier-dependent."""
    if not videos:
        return 0.0
    total = total_views(videos)
    if total == 0:
        return 0.0
    top1 = max(v.get("view_count", 0) for v in videos)
    return round(top1 / total, 3)


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "trivia shorts"
    vids = search_videos(q, 5)
    for v in vids:
        print(f"  {v['view_count']:>10,} views | {v['channel'][:30]:30s} | {v['title'][:50]}")
    print(f"  Total: {total_views(vids):,} views from {unique_channels(vids)} channels")
