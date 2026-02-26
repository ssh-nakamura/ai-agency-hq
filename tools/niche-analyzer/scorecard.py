"""Generate scorecard (Markdown + HTML) from eval JSON — v2 scoring."""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path

from config import OUTPUT_BASE


def generate_scorecard(
    niche_id: str,
    scan_date: str,
    *,
    html: bool = True,
    open_browser: bool = False,
) -> Path:
    """Generate scorecard from eval JSON. Returns path to MD file."""
    eval_path = OUTPUT_BASE / scan_date / "eval" / f"{niche_id}.json"
    if not eval_path.exists():
        print(f"Error: {eval_path} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(eval_path.read_text(encoding="utf-8"))
    steps = data.get("steps", {})

    # Build markdown
    md = _render_markdown(data, steps)

    # Save markdown
    sc_dir = OUTPUT_BASE / scan_date / "scorecards"
    sc_dir.mkdir(parents=True, exist_ok=True)
    md_path = sc_dir / f"{niche_id}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"  Scorecard MD: {md_path}")

    # Generate HTML
    if html:
        html_content = _render_html(data, steps)
        html_path = sc_dir / f"{niche_id}.html"
        html_path.write_text(html_content, encoding="utf-8")
        print(f"  Scorecard HTML: {html_path}")
        if open_browser:
            subprocess.run(["open", str(html_path)])

    return md_path


def _stars(value: float, thresholds: tuple = (1.5, 2.5)) -> str:
    """Convert numeric score to star rating."""
    if value >= thresholds[1]:
        return "★★★"
    elif value >= thresholds[0]:
        return "★★"
    return "★"


def _score_step(step_name: str, data: dict, steps: dict) -> tuple[int, str]:
    """Score a step 1-3 and return (score, comment). v2 scoring."""

    if step_name == "step0_trend":
        s = steps.get("step0_trend", {})
        en_dir = s.get("en", {}).get("direction", "UNKNOWN")
        jp_dir = s.get("jp", {}).get("direction", "UNKNOWN")
        dirs = [en_dir, jp_dir]
        if "GROWING" in dirs:
            return 3, f"Growing (EN:{en_dir} JP:{jp_dir})"
        if en_dir == "DECLINING" and jp_dir == "DECLINING":
            return 1, f"Both declining"
        # At least one STABLE (or UNKNOWN but not both DECLINING)
        return 2, f"Stable (EN:{en_dir} JP:{jp_dir})"

    elif step_name == "step1_demand":
        s = steps.get("step1_demand", {})
        en_median = s.get("en", {}).get("yt_median_views", 0)
        jp_median = s.get("jp", {}).get("yt_median_views", 0)
        yt_median = max(en_median, jp_median)
        # Multi-source check: demand exists beyond YouTube
        tweets = max(s.get("en", {}).get("tweets_30d", 0), s.get("jp", {}).get("tweets_30d", 0))
        reddit = max(s.get("en", {}).get("reddit_posts", 0), s.get("jp", {}).get("reddit_posts", 0))
        multi_source = (tweets > 100) or (reddit > 100)
        if yt_median >= 500_000 and multi_source:
            return 3, f"Strong (median {yt_median:,} + multi-source)"
        if yt_median >= 500_000:
            return 2, f"YT-only demand (median {yt_median:,})"
        if yt_median >= 100_000 and multi_source:
            return 2, f"Moderate + multi-source (median {yt_median:,})"
        return 1, f"Low demand (median {yt_median:,})"

    elif step_name == "step2_engagement":
        s1 = steps.get("step1_demand", {})
        s2 = steps.get("step2_engagement", {})
        # Use median from step1 data (more robust than avg)
        en_median = s1.get("en", {}).get("yt_median_views", 0)
        jp_median = s1.get("jp", {}).get("yt_median_views", 0)
        yt_median = max(en_median, jp_median)
        en_top1 = s1.get("en", {}).get("yt_top1_pct", 0)
        jp_top1 = s1.get("jp", {}).get("yt_top1_pct", 0)
        top1_pct = max(en_top1, jp_top1)
        # Base score from median views
        if yt_median > 200_000:
            base = 3
        elif yt_median > 50_000:
            base = 2
        else:
            base = 1
        # Penalize outlier dependency
        if top1_pct > 0.5:
            base = max(base - 1, 1)
            return base, f"Outlier-dependent (top1={top1_pct:.0%}, median {yt_median:,})"
        return base, f"Median {yt_median:,} views (top1={top1_pct:.0%})"

    elif step_name == "step3_knowledge_gap":
        s = steps.get("step3_knowledge_gap", {})
        # Try both EN and JP, take the better one
        best_count = 0
        for lang in ("en", "jp"):
            raw = s.get(lang, {}).get("grok_raw", "")
            if isinstance(raw, str) and not raw.startswith("ERROR"):
                try:
                    items = json.loads(raw)
                    if isinstance(items, list):
                        best_count = max(best_count, len(items))
                except (json.JSONDecodeError, TypeError):
                    pass
        if best_count >= 10:
            return 3, f"Rich ({best_count} questions)"
        if best_count >= 5:
            return 2, f"Moderate ({best_count} questions)"
        return 1, f"Weak ({best_count} questions)"

    elif step_name == "step4_supply":
        s = steps.get("step4_supply", {})
        s1 = steps.get("step1_demand", {})
        en_pub = s.get("en", {}).get("twitter_publishers", 0)
        jp_pub = s.get("jp", {}).get("twitter_publishers", 0)
        pub = max(en_pub, jp_pub)
        en_median = s1.get("en", {}).get("yt_median_views", 0)
        jp_median = s1.get("jp", {}).get("yt_median_views", 0)
        yt_median = max(en_median, jp_median)
        # Cross-reference demand vs competition
        if pub < 50_000 and yt_median >= 100_000:
            return 3, f"Blue ocean (pub {pub:,}, median {yt_median:,})"
        if pub < 50_000 and yt_median < 100_000:
            return 1, f"Dead market (pub {pub:,}, median {yt_median:,})"
        if pub < 200_000:
            return 2, f"Moderate competition ({pub:,})"
        return 1, f"Red ocean ({pub:,} publishers)"

    elif step_name == "step5_gap":
        s = steps.get("step5_gap", {})
        jp_gap = s.get("jp", 0)
        if jp_gap > 200:
            return 3, f"High gap ({jp_gap:.0f})"
        elif jp_gap > 50:
            return 2, f"Moderate gap ({jp_gap:.0f})"
        return 1, f"Low gap ({jp_gap:.0f})"

    elif step_name == "step6_localization":
        s = steps.get("step6_localization", {})
        yt_ratio = s.get("yt_ratio", 1.0)
        if yt_ratio > 5.0:
            return 3, f"Strong EN→JP opportunity ({yt_ratio:.1f}x)"
        elif yt_ratio > 2.0:
            return 2, f"Moderate opportunity ({yt_ratio:.1f}x)"
        return 1, f"JP already mature ({yt_ratio:.1f}x)"

    elif step_name == "step7_commercial":
        s = steps.get("step7_commercial", {})
        jp_raw = s.get("jp", {}).get("grok_raw", "")
        if "ERROR" in jp_raw:
            return 1, "Grok failed"
        commercial_keywords = ["収益", "アフィ", "副業", "稼", "Brain", "note", "販売"]
        hits = sum(1 for kw in commercial_keywords if kw in jp_raw)
        if hits >= 4:
            return 3, f"Strong commercial signals ({hits}/7 keywords)"
        elif hits >= 2:
            return 2, f"Some commercial signals ({hits}/7)"
        return 1, f"Weak signals ({hits}/7)"

    return 1, "Unknown"


def _declining_penalty(steps: dict) -> int:
    """Calculate point penalty for DECLINING trends."""
    s0 = steps.get("step0_trend", {})
    en_dir = s0.get("en", {}).get("direction", "UNKNOWN")
    jp_dir = s0.get("jp", {}).get("direction", "UNKNOWN")
    if en_dir == "DECLINING" and jp_dir == "DECLINING":
        return 3
    if en_dir == "DECLINING" or jp_dir == "DECLINING":
        return 1
    return 0


def _overall_rating(total: int, steps: dict) -> tuple[str, int]:
    """Determine overall star rating (24-point scale) with DECLINING penalty.

    Returns (rating_str, adjusted_total).
    """
    penalty = _declining_penalty(steps)
    adjusted = total - penalty

    # Base rating from adjusted points
    if adjusted >= 20:
        rating = "★★★"
    elif adjusted >= 14:
        rating = "★★"
    else:
        rating = "★"

    # Additional tier downgrade when both DECLINING
    s0 = steps.get("step0_trend", {})
    en_dir = s0.get("en", {}).get("direction", "UNKNOWN")
    jp_dir = s0.get("jp", {}).get("direction", "UNKNOWN")
    if en_dir == "DECLINING" and jp_dir == "DECLINING":
        if rating == "★★★":
            rating = "★★"
        elif rating == "★★":
            rating = "★"

    return rating, adjusted


def _render_markdown(data: dict, steps: dict) -> str:
    """Render scorecard as Markdown."""
    niche_id = data.get("niche_id", "unknown")
    kw_en = data.get("keywords", {}).get("en", "")
    kw_jp = data.get("keywords", {}).get("jp", "")

    step_names = [
        ("step0_trend", "トレンド方向性"),
        ("step1_demand", "需要ボリューム"),
        ("step2_engagement", "エンゲージメント"),
        ("step3_knowledge_gap", "ナレッジギャップ"),
        ("step4_supply", "競合供給量"),
        ("step5_gap", "需給ギャップ"),
        ("step6_localization", "ローカライズ倍率"),
        ("step7_commercial", "商業シグナル"),
    ]

    scores = []
    for key, label in step_names:
        score, comment = _score_step(key, data, steps)
        scores.append((key, label, score, comment))

    total_raw = sum(s[2] for s in scores)
    max_total = len(scores) * 3  # 24
    overall, adjusted = _overall_rating(total_raw, steps)
    penalty = _declining_penalty(steps)

    # Trend direction icons
    s0 = steps.get("step0_trend", {})
    en_dir = s0.get("en", {}).get("direction", "UNKNOWN")
    jp_dir = s0.get("jp", {}).get("direction", "UNKNOWN")
    decline_note = ""
    if penalty > 0:
        decline_note = f" *(DECLINING -{penalty}pt penalty)*"

    lines = [
        f"# スコアカード: {kw_jp} / {kw_en}",
        f"",
        f"**評価日**: {data.get('evaluated_at', '')[:10]}",
        f"**ニッチID**: {niche_id}",
        f"**総合判定**: {overall} ({adjusted}/{max_total}){decline_note}",
        f"",
        f"---",
        f"",
        f"| # | Step | スコア | 備考 |",
        f"|---|------|--------|------|",
    ]

    star_map = {3: "★★★", 2: "★★", 1: "★"}
    for i, (key, label, score, comment) in enumerate(scores):
        lines.append(f"| {i} | {label} | {star_map[score]} | {comment} |")

    lines.append(f"| | **合計** | **{overall}** | **{adjusted}/{max_total}** |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Step 0 detail
    lines.extend([
        "## Step 0: トレンド方向性",
        "",
        f"| 言語 | 方向 | 理由 |",
        f"|------|------|------|",
        f"| EN | {en_dir} | {s0.get('en', {}).get('reason', '')} |",
        f"| JP | {jp_dir} | {s0.get('jp', {}).get('reason', '')} |",
        "",
    ])

    # Detail sections
    s1 = steps.get("step1_demand", {})
    lines.extend([
        "## Step 1: 需要ボリューム",
        "",
        "| ソース | EN | JP |",
        "|--------|---:|---:|",
        f"| YouTube top20再生数 | {s1.get('en', {}).get('yt_top20_views', 0):,} | {s1.get('jp', {}).get('yt_top20_views', 0):,} |",
        f"| YouTube中央値 | {s1.get('en', {}).get('yt_median_views', 0):,} | {s1.get('jp', {}).get('yt_median_views', 0):,} |",
        f"| YT top1集中度 | {s1.get('en', {}).get('yt_top1_pct', 0):.1%} | {s1.get('jp', {}).get('yt_top1_pct', 0):.1%} |",
        f"| Twitter (30d) | {s1.get('en', {}).get('tweets_30d', 0):,} | {s1.get('jp', {}).get('tweets_30d', 0):,} |",
        f"| Reddit投稿数 | {s1.get('en', {}).get('reddit_posts', 0):,} | {s1.get('jp', {}).get('reddit_posts', 0):,} |",
        "",
    ])

    s6 = steps.get("step6_localization", {})
    lines.extend([
        "## Step 6: ローカライズ倍率",
        "",
        f"| ソース | EN/JP比率 |",
        f"|--------|----------:|",
        f"| YouTube | {s6.get('yt_ratio', 0):.2f}x |",
        f"| Twitter | {s6.get('twitter_ratio', 0):.2f}x |",
        f"| Publisher | {s6.get('publisher_ratio', 0):.2f}x |",
        "",
    ])

    api = data.get("api_calls", {})
    lines.extend([
        "---",
        "",
        f"API calls: {api.get('total', 0)} | Cost: ${api.get('estimated_cost_usd', 0):.2f}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ])

    return "\n".join(lines)


def _render_html(data: dict, steps: dict) -> str:
    """Render scorecard as standalone HTML (dashboard-compatible)."""
    niche_id = data.get("niche_id", "unknown")
    kw_en = data.get("keywords", {}).get("en", "")
    kw_jp = data.get("keywords", {}).get("jp", "")

    step_names = [
        ("step0_trend", "トレンド方向性", "Trend Direction"),
        ("step1_demand", "需要ボリューム", "Demand Volume"),
        ("step2_engagement", "エンゲージメント", "Engagement"),
        ("step3_knowledge_gap", "ナレッジギャップ", "Knowledge Gap"),
        ("step4_supply", "競合供給量", "Competition"),
        ("step5_gap", "需給ギャップ", "Supply-Demand Gap"),
        ("step6_localization", "ローカライズ倍率", "Localization"),
        ("step7_commercial", "商業シグナル", "Commercial"),
    ]

    scores = []
    total = 0
    for key, label_jp, label_en in step_names:
        score, comment = _score_step(key, data, steps)
        scores.append((key, label_jp, label_en, score, comment))
        total += score

    max_total = len(scores) * 3  # 24
    overall, adjusted = _overall_rating(total, steps)
    pct = adjusted / max_total * 100

    s1 = steps.get("step1_demand", {})
    s6 = steps.get("step6_localization", {})
    api = data.get("api_calls", {})

    # Build step cards
    step_cards = ""
    colors = {3: "#22c55e", 2: "#eab308", 1: "#ef4444"}
    star_html = {3: "&#9733;&#9733;&#9733;", 2: "&#9733;&#9733;&#9734;", 1: "&#9733;&#9734;&#9734;"}
    for key, label_jp, label_en, score, comment in scores:
        step_cards += f"""
        <div class="step-card">
            <div class="step-header">
                <span class="step-label">{label_jp}</span>
                <span class="step-stars" style="color:{colors[score]}">{star_html[score]}</span>
            </div>
            <div class="step-comment">{comment}</div>
        </div>"""

    # Demand table rows
    demand_rows = ""
    for src, en_key, jp_key in [
        ("YouTube Top 20", "yt_top20_views", "yt_top20_views"),
        ("Twitter 30d", "tweets_30d", "tweets_30d"),
        ("Reddit", "reddit_posts", "reddit_posts"),
    ]:
        en_val = s1.get("en", {}).get(en_key, 0)
        jp_val = s1.get("jp", {}).get(jp_key, 0)
        demand_rows += f"<tr><td>{src}</td><td class='num'>{en_val:,}</td><td class='num'>{jp_val:,}</td></tr>\n"

    # Determine color from overall star rating
    if overall == "★★★":
        overall_color = "#22c55e"
    elif overall == "★★":
        overall_color = "#eab308"
    else:
        overall_color = "#ef4444"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scorecard: {kw_jp}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Sans',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:24px}}
.container{{max-width:800px;margin:0 auto}}
.header{{margin-bottom:24px}}
.header h1{{font-size:22px;font-weight:700;color:#fff}}
.header .sub{{font-size:13px;color:#888;margin-top:4px}}
.overall{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:20px;margin-bottom:20px;display:flex;align-items:center;gap:20px}}
.overall-score{{font-size:36px;font-weight:800;color:{overall_color}}}
.overall-detail{{flex:1}}
.overall-detail .label{{font-size:13px;color:#888}}
.overall-detail .bar{{height:8px;background:#2a2a2a;border-radius:4px;margin-top:6px;overflow:hidden}}
.overall-detail .bar-fill{{height:100%;background:{overall_color};border-radius:4px;width:{pct:.0f}%}}
.steps-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}}
.step-card{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:14px}}
.step-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
.step-label{{font-size:13px;font-weight:600;color:#ccc}}
.step-stars{{font-size:16px}}
.step-comment{{font-size:12px;color:#888}}
.data-section{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:16px;margin-bottom:16px}}
.data-section h3{{font-size:14px;font-weight:600;color:#fff;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:#888;font-size:11px;font-weight:600;padding:6px 10px;border-bottom:1px solid #2a2a2a}}
td{{padding:6px 10px;border-bottom:1px solid #1e1e1e;color:#ccc}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
.footer{{font-size:11px;color:#555;margin-top:16px;text-align:center}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{kw_jp} / {kw_en}</h1>
        <div class="sub">Niche ID: {niche_id} | Evaluated: {data.get('evaluated_at', '')[:10]}</div>
    </div>
    <div class="overall">
        <div class="overall-score">{adjusted}/{max_total}</div>
        <div class="overall-detail">
            <div class="label">Total Score</div>
            <div class="bar"><div class="bar-fill"></div></div>
        </div>
    </div>
    <div class="steps-grid">{step_cards}
    </div>
    <div class="data-section">
        <h3>Demand Volume (Step 1)</h3>
        <table>
            <tr><th>Source</th><th style="text-align:right">EN</th><th style="text-align:right">JP</th></tr>
            {demand_rows}
        </table>
    </div>
    <div class="data-section">
        <h3>Localization Ratio (Step 6)</h3>
        <table>
            <tr><th>Source</th><th style="text-align:right">EN/JP</th></tr>
            <tr><td>YouTube</td><td class="num">{s6.get('yt_ratio', 0):.2f}x</td></tr>
            <tr><td>Twitter</td><td class="num">{s6.get('twitter_ratio', 0):.2f}x</td></tr>
            <tr><td>Publisher</td><td class="num">{s6.get('publisher_ratio', 0):.2f}x</td></tr>
        </table>
    </div>
    <div class="footer">
        API calls: {api.get('total', 0)} | Cost: ${api.get('estimated_cost_usd', 0):.2f} |
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
</div>
</body>
</html>"""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scorecard.py <niche-id> <scan-date> [--html] [--open]")
        sys.exit(1)
    generate_scorecard(
        sys.argv[1], sys.argv[2],
        html="--html" in sys.argv or "--open" in sys.argv,
        open_browser="--open" in sys.argv,
    )
