#!/usr/bin/env python3
"""Niche Demand Analyzer — CLI entry point.

Usage:
    python3 tools/niche-analyzer/cli.py scan [--date YYYY-MM-DD]
    python3 tools/niche-analyzer/cli.py evaluate --niche ID --en KEYWORD --jp KEYWORD [--date YYYY-MM-DD]
    python3 tools/niche-analyzer/cli.py scorecard --niche ID --date YYYY-MM-DD [--html] [--open]
    python3 tools/niche-analyzer/cli.py test
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def cmd_scan(args):
    from trend_scan import run_scan
    run_scan(args.date, args.category)


def cmd_evaluate(args):
    from evaluation import evaluate_niche
    result = evaluate_niche(args.niche, args.en, args.jp, args.date)
    # Auto-generate scorecard
    from scorecard import generate_scorecard
    generate_scorecard(args.niche, args.date, html=True, open_browser=args.open)


def cmd_scorecard(args):
    from scorecard import generate_scorecard
    generate_scorecard(args.niche, args.date, html=args.html, open_browser=args.open)


def cmd_report(args):
    from report import generate_report
    generate_report(args.date, open_browser=args.open)


def cmd_test(args):
    """Test all data sources."""
    print("Testing data sources...\n")

    # 1. Grok API
    print("[1/3] Grok API...")
    try:
        import grok_client
        r = grok_client.search("What is trending on X today? 3 bullet points max.")
        text = grok_client.extract_text(r)
        print(f"  OK — {len(text)} chars returned")
    except Exception as e:
        print(f"  FAIL — {e}")

    # 2. yt-dlp
    print("[2/3] yt-dlp...")
    try:
        import ytdlp_client
        vids = ytdlp_client.search_videos("test", 3)
        print(f"  OK — {len(vids)} videos, {ytdlp_client.total_views(vids):,} total views")
    except Exception as e:
        print(f"  FAIL — {e}")

    # 3. Xpoz MCP
    print("[3/3] Xpoz MCP...")
    try:
        import xpoz_client
        client = xpoz_client.XpozClient()
        count = client.count_tweets("AI", "2026-02-01", "2026-02-21")
        print(f"  OK — 'AI' tweet count: {count:,}")
    except Exception as e:
        print(f"  FAIL — {e}")

    print("\nDone.")


def main():
    parser = argparse.ArgumentParser(
        description="Niche Demand Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # scan
    p_scan = sub.add_parser("scan", help="Stage 1: Trend Scan (Grok x_search)")
    p_scan.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    p_scan.add_argument("--category", default=None, help="Category filter (optional)")
    p_scan.set_defaults(func=cmd_scan)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Stage 3: Evaluate a niche (7-step)")
    p_eval.add_argument("--niche", required=True, help="Niche ID (e.g. trivia-shorts)")
    p_eval.add_argument("--en", required=True, help="English keyword")
    p_eval.add_argument("--jp", required=True, help="Japanese keyword")
    p_eval.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    p_eval.add_argument("--open", action="store_true", help="Open HTML in browser")
    p_eval.set_defaults(func=cmd_evaluate)

    # scorecard
    p_sc = sub.add_parser("scorecard", help="Generate scorecard from eval data")
    p_sc.add_argument("--niche", required=True)
    p_sc.add_argument("--date", required=True)
    p_sc.add_argument("--html", action="store_true")
    p_sc.add_argument("--open", action="store_true")
    p_sc.set_defaults(func=cmd_scorecard)

    # report
    p_report = sub.add_parser("report", help="Generate full HTML report for all niches")
    p_report.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    p_report.add_argument("--open", action="store_true", help="Open in browser")
    p_report.set_defaults(func=cmd_report)

    # test
    p_test = sub.add_parser("test", help="Test all data sources")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
