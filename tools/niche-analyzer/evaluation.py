"""Stage 3: Niche evaluation — 7-step data collection."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from config import OUTPUT_BASE, DEFAULT_YT_RESULTS, DEFAULT_TWITTER_DAYS
import grok_client
import ytdlp_client
import xpoz_client


def evaluate_niche(
    niche_id: str,
    keyword_en: str,
    keyword_jp: str,
    scan_date: str = None,
) -> dict:
    """Run full 7-step evaluation for a single niche.

    All data collection happens here (zero Claude tokens).
    Judgment/interpretation is left to the CEO session.
    """
    scan_date = scan_date or datetime.now().strftime("%Y-%m-%d")
    end_date = scan_date
    start_date = (
        datetime.strptime(scan_date, "%Y-%m-%d") - timedelta(days=DEFAULT_TWITTER_DAYS)
    ).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  Evaluating: {niche_id}")
    print(f"  EN: {keyword_en}  |  JP: {keyword_jp}")
    print(f"  Date range: {start_date} → {end_date}")
    print(f"{'='*60}\n")

    xpoz = xpoz_client.XpozClient()

    result = {
        "niche_id": niche_id,
        "niche_name_en": keyword_en,
        "niche_name_jp": keyword_jp,
        "evaluated_at": datetime.now().isoformat(),
        "date_range": {"start": start_date, "end": end_date},
        "keywords": {"en": keyword_en, "jp": keyword_jp},
        "steps": {},
        "api_calls": {"grok": 0, "xpoz": 0, "ytdlp": 0},
    }

    # ── Step 1: Demand Volume ──
    print("  [1/7] Demand Volume...")
    yt_en = ytdlp_client.search_videos(keyword_en, DEFAULT_YT_RESULTS)
    yt_jp = ytdlp_client.search_videos(keyword_jp, DEFAULT_YT_RESULTS)
    result["api_calls"]["ytdlp"] += 2

    tw_count_en = _safe_count(xpoz, keyword_en, start_date, end_date)
    tw_count_jp = _safe_count(xpoz, keyword_jp, start_date, end_date)
    result["api_calls"]["xpoz"] += 2

    reddit_en = _safe_call(xpoz.get_reddit_posts, keyword_en, start_date, end_date)
    reddit_jp = _safe_call(xpoz.get_reddit_posts, keyword_jp, start_date, end_date)
    result["api_calls"]["xpoz"] += 2

    result["steps"]["step1_demand"] = {
        "en": {
            "yt_top20_views": ytdlp_client.total_views(yt_en),
            "yt_video_count": len(yt_en),
            "tweets_30d": tw_count_en,
            "reddit_posts": _count_items(reddit_en),
        },
        "jp": {
            "yt_top20_views": ytdlp_client.total_views(yt_jp),
            "yt_video_count": len(yt_jp),
            "tweets_30d": tw_count_jp,
            "reddit_posts": _count_items(reddit_jp),
        },
    }
    print(f"        YT EN: {ytdlp_client.total_views(yt_en):,} views | JP: {ytdlp_client.total_views(yt_jp):,} views")

    # ── Step 2: Engagement Density ──
    print("  [2/7] Engagement Density...")
    tw_posts_en = _safe_call(xpoz.get_twitter_posts, keyword_en, start_date, end_date)
    tw_posts_jp = _safe_call(xpoz.get_twitter_posts, keyword_jp, start_date, end_date)
    ig_posts_en = _safe_call(xpoz.get_instagram_posts, keyword_en, start_date, end_date)
    result["api_calls"]["xpoz"] += 3

    result["steps"]["step2_engagement"] = {
        "en": {
            "twitter_total_posts": _count_items(tw_posts_en),
            "twitter_avg_likes": _avg_field(_get_items(tw_posts_en), "likeCount"),
            "twitter_avg_retweets": _avg_field(_get_items(tw_posts_en), "retweetCount"),
            "instagram_total_posts": _count_items(ig_posts_en),
            "yt_avg_views": ytdlp_client.avg_views(yt_en),
        },
        "jp": {
            "twitter_total_posts": _count_items(tw_posts_jp),
            "twitter_avg_likes": _avg_field(_get_items(tw_posts_jp), "likeCount"),
            "twitter_avg_retweets": _avg_field(_get_items(tw_posts_jp), "retweetCount"),
            "yt_avg_views": ytdlp_client.avg_views(yt_jp),
        },
    }

    # ── Step 3: Knowledge Gap ──
    print("  [3/7] Knowledge Gap (Grok)...")
    grok_gap_en = _safe_grok(
        f'Search X/Twitter for people asking questions about "{keyword_en}". '
        f'Look for "how to", "beginner", "help", "tips" related to {keyword_en}. '
        f'Return up to 15 results as JSON array: text, author, date, likes.'
    )
    grok_gap_jp = _safe_grok(
        f'X/Twitterで「{keyword_jp} 始め方」「{keyword_jp} 初心者」「{keyword_jp} 教えて」'
        f'など質問を検索。15件まで。JSON配列で: text, author, date, likes'
    )
    result["api_calls"]["grok"] += 2

    result["steps"]["step3_knowledge_gap"] = {
        "en": {"grok_raw": grok_gap_en},
        "jp": {"grok_raw": grok_gap_jp},
    }

    # ── Step 4: Competitive Supply ──
    print("  [4/7] Competitive Supply...")
    tw_users_en = _safe_call(xpoz.get_twitter_users, keyword_en, start_date, end_date)
    tw_users_jp = _safe_call(xpoz.get_twitter_users, keyword_jp, start_date, end_date)
    result["api_calls"]["xpoz"] += 2

    en_publishers = _count_items(tw_users_en)
    jp_publishers = _count_items(tw_users_jp)

    result["steps"]["step4_supply"] = {
        "en": {
            "yt_channels": ytdlp_client.unique_channels(yt_en),
            "twitter_publishers": en_publishers,
        },
        "jp": {
            "yt_channels": ytdlp_client.unique_channels(yt_jp),
            "twitter_publishers": jp_publishers,
        },
    }
    print(f"        Publishers EN: {en_publishers:,} | JP: {jp_publishers:,}")

    # ── Step 5: Supply-Demand Gap ──
    print("  [5/7] Supply-Demand Gap (calculated)...")
    s1 = result["steps"]["step1_demand"]
    s4 = result["steps"]["step4_supply"]
    result["steps"]["step5_gap"] = {
        "en": round(s1["en"]["yt_top20_views"] / max(s4["en"]["twitter_publishers"], 1), 1),
        "jp": round(s1["jp"]["yt_top20_views"] / max(s4["jp"]["twitter_publishers"], 1), 1),
    }

    # ── Step 6: Localization Ratio ──
    print("  [6/7] Localization Ratio (calculated)...")
    result["steps"]["step6_localization"] = {
        "yt_ratio": round(s1["en"]["yt_top20_views"] / max(s1["jp"]["yt_top20_views"], 1), 2),
        "twitter_ratio": round(s1["en"]["tweets_30d"] / max(s1["jp"]["tweets_30d"], 1), 2),
        "publisher_ratio": round(s4["en"]["twitter_publishers"] / max(s4["jp"]["twitter_publishers"], 1), 2),
    }

    # ── Step 7: Commercial Signals ──
    print("  [7/7] Commercial Signals (Grok)...")
    grok_com_en = _safe_grok(
        f'Search X/Twitter for monetization activity around "{keyword_en}". '
        f'Look for: affiliate, sponsorship, course selling, "make money", income reports. '
        f'Return up to 15 results as JSON array: text, author, date, likes, commercial_type.'
    )
    grok_com_jp = _safe_grok(
        f'X/Twitterで「{keyword_jp} 収益」「{keyword_jp} アフィリエイト」「{keyword_jp} 副業」'
        f'など収益化に関する投稿を検索。15件まで。'
        f'JSON配列で: text, author, date, likes, commercial_type'
    )
    result["api_calls"]["grok"] += 2

    result["steps"]["step7_commercial"] = {
        "en": {"grok_raw": grok_com_en},
        "jp": {"grok_raw": grok_com_jp},
    }

    # ── Save ──
    total_calls = sum(result["api_calls"].values())
    grok_cost = result["api_calls"]["grok"] * 0.56
    result["api_calls"]["total"] = total_calls
    result["api_calls"]["estimated_cost_usd"] = round(grok_cost, 2)

    scan_dir = OUTPUT_BASE / scan_date
    eval_dir = scan_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    eval_path = eval_dir / f"{niche_id}.json"
    eval_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  Saved: {eval_path}")
    print(f"  API calls: {total_calls} (Grok: {result['api_calls']['grok']}, "
          f"Xpoz: {result['api_calls']['xpoz']}, yt-dlp: {result['api_calls']['ytdlp']})")
    print(f"  Estimated cost: ${grok_cost:.2f}")

    return result


# ── Helpers ──

def _safe_count(xpoz, phrase, start, end):
    try:
        return xpoz.count_tweets(phrase, start, end)
    except Exception as e:
        print(f"    [warn] countTweets failed for '{phrase}': {e}", file=sys.stderr)
        return 0


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"    [warn] {fn.__name__} failed: {e}", file=sys.stderr)
        return {}


def _safe_grok(prompt):
    try:
        resp = grok_client.search(prompt)
        return grok_client.extract_text(resp)
    except Exception as e:
        print(f"    [warn] Grok search failed: {e}", file=sys.stderr)
        return f"ERROR: {e}"


def _get_items(data: dict) -> list:
    """Extract items list from Xpoz response (various shapes)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Check top-level list keys
        for key in ("rows", "posts", "users", "items", "results"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Check nested data dict (Xpoz: {success, data: {rows: [...], ...}})
        nested = data.get("data", {})
        if isinstance(nested, dict):
            for key in ("rows", "posts", "users", "items", "results"):
                if key in nested and isinstance(nested[key], list):
                    return nested[key]
    return []


def _count_items(data) -> int:
    """Count items, checking totalCount/totalRows/resultsCount first."""
    if isinstance(data, dict):
        for key in ("totalCount", "totalRows", "resultsCount", "total", "count"):
            if key in data:
                val = data[key]
                if isinstance(val, (int, float)):
                    return int(val)
        # Check nested data dict (Xpoz wraps in data: {})
        nested = data.get("data", {})
        if isinstance(nested, dict):
            for key in ("totalRows", "resultsCount", "totalCount", "results"):
                if key in nested:
                    val = nested[key]
                    if isinstance(val, (int, float)):
                        return int(val)
        return len(_get_items(data))
    if isinstance(data, list):
        return len(data)
    return 0


def _avg_field(items: list, field: str) -> float:
    if not items:
        return 0.0
    values = []
    for item in items:
        val = item.get(field, 0)
        if val is None:
            val = 0
        try:
            values.append(float(val))
        except (ValueError, TypeError):
            continue  # Skip non-numeric values (CSV parse misalignment)
    return round(sum(values) / len(values), 1) if values else 0.0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python evaluation.py <niche-id> <keyword-en> <keyword-jp> [date]")
        sys.exit(1)
    niche_id = sys.argv[1]
    kw_en = sys.argv[2]
    kw_jp = sys.argv[3]
    date = sys.argv[4] if len(sys.argv) > 4 else None
    evaluate_niche(niche_id, kw_en, kw_jp, date)
