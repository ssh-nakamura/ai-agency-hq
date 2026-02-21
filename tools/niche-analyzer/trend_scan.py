"""Stage 1: Trend Scan — Grok x_search for niche discovery."""

import json
import sys
from datetime import datetime
from pathlib import Path

from config import OUTPUT_BASE, TREND_SCAN_PROMPT_EN, TREND_SCAN_PROMPT_JP
import grok_client


def run_scan(scan_date: str = None, category: str = None):
    """Run Stage 1 trend scan using Grok x_search."""
    scan_date = scan_date or datetime.now().strftime("%Y-%m-%d")
    scan_dir = OUTPUT_BASE / scan_date
    scan_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Stage 1: Trend Scan — {scan_date}")
    if category:
        print(f"  Category filter: {category}")
    print(f"{'='*60}\n")

    # EN scan
    print("  [1/2] Scanning EN trends...")
    prompt_en = TREND_SCAN_PROMPT_EN
    if category:
        prompt_en = f"Focus specifically on: {category}\n\n" + prompt_en

    resp_en = grok_client.search(prompt_en)
    text_en = grok_client.extract_text(resp_en)

    en_path = scan_dir / "stage1-raw-en.json"
    en_path.write_text(json.dumps({
        "scan_date": scan_date,
        "lang": "en",
        "category": category,
        "raw_response": resp_en,
        "extracted_text": text_en,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"    Saved: {en_path}")

    # JP scan
    print("  [2/2] Scanning JP trends...")
    prompt_jp = TREND_SCAN_PROMPT_JP
    if category:
        prompt_jp = f"特にこのカテゴリに注目: {category}\n\n" + prompt_jp

    resp_jp = grok_client.search(prompt_jp)
    text_jp = grok_client.extract_text(resp_jp)

    jp_path = scan_dir / "stage1-raw-jp.json"
    jp_path.write_text(json.dumps({
        "scan_date": scan_date,
        "lang": "jp",
        "category": category,
        "raw_response": resp_jp,
        "extracted_text": text_jp,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"    Saved: {jp_path}")

    # Update meta.json
    meta_path = scan_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update({
        "scan_date": scan_date,
        "stage1_completed": True,
        "stage1_cost_usd": 1.12,
        "category_filter": category,
        "grok_model": "grok-4-1-fast",
    })
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  Scan complete. Cost: ~$1.12")
    print(f"  Next: CEO reads stage1-raw-*.json and runs Stage 2 (Discovery)")

    # Print summary
    print(f"\n{'─'*60}")
    print("  EN Summary (first 500 chars):")
    print(f"  {text_en[:500]}")
    print(f"\n{'─'*60}")
    print("  JP Summary (first 500 chars):")
    print(f"  {text_jp[:500]}")


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else None
    cat = sys.argv[2] if len(sys.argv) > 2 else None
    run_scan(date, cat)
