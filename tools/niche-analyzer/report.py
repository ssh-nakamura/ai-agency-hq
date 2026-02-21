"""Generate comprehensive HTML report from all niche evaluations."""

import json
import sys
from datetime import datetime
from pathlib import Path

from config import OUTPUT_BASE

# Reuse scoring logic from scorecard.py
from scorecard import _score_step


def generate_report(scan_date: str, *, open_browser: bool = False) -> Path:
    """Generate a full HTML report covering all niches for a scan date."""
    scan_dir = OUTPUT_BASE / scan_date
    eval_dir = scan_dir / "eval"

    if not eval_dir.exists():
        print(f"Error: {eval_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Load all eval JSONs
    niches = []
    for f in sorted(eval_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        steps = data.get("steps", {})

        step_keys = [
            "step1_demand", "step2_engagement", "step3_knowledge_gap",
            "step4_supply", "step5_gap", "step6_localization", "step7_commercial",
        ]
        scores = {}
        total = 0
        for key in step_keys:
            score, comment = _score_step(key, data, steps)
            scores[key] = {"score": score, "comment": comment}
            total += score

        # Detect data quality issues
        warnings = _detect_warnings(data, steps)

        kw_en = data.get("keywords", {}).get("en", "") or data.get("niche_name_en", "")
        kw_jp = data.get("keywords", {}).get("jp", "") or data.get("niche_name_jp", "")
        if isinstance(kw_en, list):
            kw_en = kw_en[0] if kw_en else ""
        if isinstance(kw_jp, list):
            kw_jp = kw_jp[0] if kw_jp else ""

        niches.append({
            "id": data.get("niche_id", f.stem),
            "name_en": kw_en,
            "name_jp": kw_jp,
            "data": data,
            "steps": steps,
            "scores": scores,
            "total": total,
            "max": 21,
            "warnings": warnings,
        })

    # Sort by total score descending
    niches.sort(key=lambda n: n["total"], reverse=True)

    html = _build_html(scan_date, niches)

    report_path = scan_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"Report: {report_path}")

    if open_browser:
        import subprocess
        subprocess.run(["open", str(report_path)])

    return report_path


def _detect_warnings(data: dict, steps: dict) -> list:
    """Detect data quality issues in evaluation results."""
    warnings = []
    s1 = steps.get("step1_demand", {})
    s2 = steps.get("step2_engagement", {})
    s4 = steps.get("step4_supply", {})
    s3 = steps.get("step3_knowledge_gap", {})
    s7 = steps.get("step7_commercial", {})

    # YT data missing
    if s1.get("en", {}).get("yt_top20_views", 0) == 0 and s1.get("jp", {}).get("yt_top20_views", 0) == 0:
        warnings.append("YouTube data missing (yt-dlp timeout)")

    # Twitter publishers = 0 (Xpoz timeout)
    if s4.get("en", {}).get("twitter_publishers", 0) == 0 and s4.get("jp", {}).get("twitter_publishers", 0) == 0:
        warnings.append("Publisher data missing (Xpoz timeout)")

    # Grok failures
    for step, label in [(s3, "Knowledge Gap"), (s7, "Commercial Signals")]:
        for lang in ["en", "jp"]:
            raw = step.get(lang, {}).get("grok_raw", "")
            if isinstance(raw, str) and raw.startswith("ERROR"):
                warnings.append(f"{label} ({lang.upper()}) — Grok API failed")

    # Twitter count = 0
    if s1.get("en", {}).get("tweets_30d", 0) == 0 and s1.get("jp", {}).get("tweets_30d", 0) == 0:
        warnings.append("Twitter count data missing")

    return warnings


def _fmt(n, default="—"):
    """Format number with commas, or dash if zero/missing."""
    if n is None or n == 0:
        return default
    if isinstance(n, float):
        if n == int(n):
            return f"{int(n):,}"
        return f"{n:,.1f}"
    return f"{n:,}"


def _ratio_bar(ratio: float, max_ratio: float = 40.0) -> str:
    """Generate an inline bar for EN/JP ratio visualization."""
    if ratio <= 0:
        return '<span class="ratio-label">—</span>'
    pct = min(ratio / max_ratio * 100, 100)
    if ratio > 5:
        color = "#22c55e"
    elif ratio > 2:
        color = "#eab308"
    else:
        color = "#ef4444"
    return (
        f'<div class="ratio-bar">'
        f'<div class="ratio-fill" style="width:{pct:.0f}%;background:{color}"></div>'
        f'<span class="ratio-label">{ratio:.1f}x</span>'
        f'</div>'
    )


def _star_cell(score: int) -> str:
    colors = {3: "#22c55e", 2: "#eab308", 1: "#ef4444"}
    symbols = {3: "&#9733;&#9733;&#9733;", 2: "&#9733;&#9733;&#9734;", 1: "&#9733;&#9734;&#9734;"}
    return f'<span style="color:{colors[score]}">{symbols[score]}</span>'


def _grok_summary(raw: str, max_items: int = 5) -> str:
    """Extract a readable summary from Grok raw JSON response."""
    if not raw or raw.startswith("ERROR"):
        return '<span class="dimmed">Data unavailable</span>'
    try:
        items = json.loads(raw)
        if isinstance(items, list):
            html_parts = []
            for item in items[:max_items]:
                text = item.get("text", "")[:200]
                author = item.get("author", "")
                likes = item.get("likes", 0)
                html_parts.append(
                    f'<div class="grok-item">'
                    f'<div class="grok-text">{_esc(text)}</div>'
                    f'<div class="grok-meta">{_esc(author)} &middot; {likes} likes</div>'
                    f'</div>'
                )
            remaining = len(items) - max_items
            if remaining > 0:
                html_parts.append(f'<div class="grok-more">+{remaining} more results</div>')
            return "\n".join(html_parts)
    except (json.JSONDecodeError, TypeError):
        pass
    # Fallback: show truncated text
    return f'<div class="grok-text">{_esc(raw[:500])}</div>'


def _esc(text) -> str:
    """HTML escape. Handles str and list."""
    if isinstance(text, list):
        text = ", ".join(str(t) for t in text)
    text = str(text)
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _build_html(scan_date: str, niches: list) -> str:
    """Build the complete HTML report."""

    # --- Ranking table rows ---
    ranking_rows = ""
    for i, n in enumerate(niches, 1):
        s1 = n["steps"].get("step1_demand", {})
        s6 = n["steps"].get("step6_localization", {})
        s4 = n["steps"].get("step4_supply", {})
        yt_en = s1.get("en", {}).get("yt_top20_views", 0)
        yt_jp = s1.get("jp", {}).get("yt_top20_views", 0)
        yt_ratio = s6.get("yt_ratio", 0)
        pub_jp = s4.get("jp", {}).get("twitter_publishers", 0)

        warn_icon = ' <span class="warn-dot" title="Data quality issues">&#9888;</span>' if n["warnings"] else ""
        color = "#22c55e" if n["total"] >= 18 else "#eab308" if n["total"] >= 14 else "#ef4444"

        ranking_rows += f"""
        <tr class="rank-row" data-niche="{n['id']}">
            <td class="rank-num">{i}</td>
            <td>
                <div class="niche-name">{_esc(n['name_jp'])}{warn_icon}</div>
                <div class="niche-sub">{_esc(n['name_en'])}</div>
            </td>
            <td class="num" style="color:{color};font-weight:700">{n['total']}/{n['max']}</td>
            <td class="num">{_fmt(yt_en)}</td>
            <td class="num">{_fmt(yt_jp)}</td>
            <td>{_ratio_bar(yt_ratio)}</td>
            <td class="num">{_fmt(pub_jp)}</td>
        </tr>"""

    # --- Heatmap ---
    step_labels = ["需要", "反応", "質問", "競合", "需給差", "EN/JP", "商業"]
    step_keys = [
        "step1_demand", "step2_engagement", "step3_knowledge_gap",
        "step4_supply", "step5_gap", "step6_localization", "step7_commercial",
    ]

    heatmap_header = "".join(f"<th>{lbl}</th>" for lbl in step_labels)
    heatmap_rows = ""
    for n in niches:
        cells = ""
        for key in step_keys:
            sc = n["scores"][key]["score"]
            bg = {3: "rgba(34,197,94,0.2)", 2: "rgba(234,179,8,0.15)", 1: "rgba(239,68,68,0.15)"}[sc]
            cells += f'<td style="background:{bg};text-align:center">{_star_cell(sc)}</td>'
        heatmap_rows += f"""
        <tr>
            <td class="niche-name-sm">{_esc(n['name_jp'])}</td>
            {cells}
            <td class="num" style="font-weight:700">{n['total']}</td>
        </tr>"""

    # --- Per-niche detail sections ---
    detail_sections = ""
    for n in niches:
        s = n["steps"]
        s1 = s.get("step1_demand", {})
        s2 = s.get("step2_engagement", {})
        s4 = s.get("step4_supply", {})
        s5 = s.get("step5_gap", {})
        s6 = s.get("step6_localization", {})
        s3 = s.get("step3_knowledge_gap", {})
        s7 = s.get("step7_commercial", {})

        # Warning badges
        warn_html = ""
        if n["warnings"]:
            badges = "".join(f'<span class="warn-badge">&#9888; {_esc(w)}</span>' for w in n["warnings"])
            warn_html = f'<div class="warn-box">{badges}</div>'

        # Step score cards (compact)
        step_cards = ""
        for key, label in zip(step_keys, step_labels):
            sc = n["scores"][key]
            step_cards += (
                f'<div class="mini-card">'
                f'<div class="mini-label">{label}</div>'
                f'<div class="mini-score">{_star_cell(sc["score"])}</div>'
                f'<div class="mini-comment">{_esc(sc["comment"])}</div>'
                f'</div>'
            )

        # Grok qualitative data
        grok_gap_en = _grok_summary(s3.get("en", {}).get("grok_raw", ""))
        grok_gap_jp = _grok_summary(s3.get("jp", {}).get("grok_raw", ""))
        grok_com_en = _grok_summary(s7.get("en", {}).get("grok_raw", ""))
        grok_com_jp = _grok_summary(s7.get("jp", {}).get("grok_raw", ""))

        color = "#22c55e" if n["total"] >= 18 else "#eab308" if n["total"] >= 14 else "#ef4444"

        detail_sections += f"""
    <div class="detail-section" id="detail-{n['id']}">
        <div class="detail-header">
            <div>
                <h2>{_esc(n['name_jp'])} <span class="en-label">/ {_esc(n['name_en'])}</span></h2>
                <div class="detail-sub">ID: {n['id']}</div>
            </div>
            <div class="detail-score" style="color:{color}">{n['total']}/{n['max']}</div>
        </div>
        {warn_html}
        <div class="mini-grid">{step_cards}</div>

        <div class="data-block">
            <h3>Step 1: Demand Volume</h3>
            <table>
                <tr><th></th><th>EN</th><th>JP</th></tr>
                <tr><td>YouTube top20</td><td class="num">{_fmt(s1.get('en',{}).get('yt_top20_views',0))}</td><td class="num">{_fmt(s1.get('jp',{}).get('yt_top20_views',0))}</td></tr>
                <tr><td>Twitter (30d)</td><td class="num">{_fmt(s1.get('en',{}).get('tweets_30d',0))}</td><td class="num">{_fmt(s1.get('jp',{}).get('tweets_30d',0))}</td></tr>
                <tr><td>Reddit</td><td class="num">{_fmt(s1.get('en',{}).get('reddit_posts',0))}</td><td class="num">{_fmt(s1.get('jp',{}).get('reddit_posts',0))}</td></tr>
            </table>
        </div>

        <div class="data-block">
            <h3>Step 2: Engagement</h3>
            <table>
                <tr><th></th><th>EN</th><th>JP</th></tr>
                <tr><td>Twitter posts</td><td class="num">{_fmt(s2.get('en',{}).get('twitter_total_posts',0))}</td><td class="num">{_fmt(s2.get('jp',{}).get('twitter_total_posts',0))}</td></tr>
                <tr><td>Avg likes</td><td class="num">{_fmt(s2.get('en',{}).get('twitter_avg_likes',0))}</td><td class="num">{_fmt(s2.get('jp',{}).get('twitter_avg_likes',0))}</td></tr>
                <tr><td>Instagram</td><td class="num">{_fmt(s2.get('en',{}).get('instagram_total_posts',0))}</td><td class="num">{_fmt(s2.get('jp',{}).get('instagram_total_posts',0))}</td></tr>
                <tr><td>YT avg views</td><td class="num">{_fmt(s2.get('en',{}).get('yt_avg_views',0))}</td><td class="num">{_fmt(s2.get('jp',{}).get('yt_avg_views',0))}</td></tr>
            </table>
        </div>

        <div class="data-block">
            <h3>Step 4: Supply & Step 6: Localization</h3>
            <table>
                <tr><th></th><th>EN</th><th>JP</th><th>EN/JP</th></tr>
                <tr><td>YT channels</td><td class="num">{_fmt(s4.get('en',{}).get('yt_channels',0))}</td><td class="num">{_fmt(s4.get('jp',{}).get('yt_channels',0))}</td><td class="num">{_fmt(s6.get('yt_ratio',0))}x</td></tr>
                <tr><td>Twitter publishers</td><td class="num">{_fmt(s4.get('en',{}).get('twitter_publishers',0))}</td><td class="num">{_fmt(s4.get('jp',{}).get('twitter_publishers',0))}</td><td class="num">{_fmt(s6.get('publisher_ratio',0))}x</td></tr>
                <tr><td>Gap score</td><td class="num">{_fmt(s5.get('en',0))}</td><td class="num">{_fmt(s5.get('jp',0))}</td><td></td></tr>
            </table>
        </div>

        <details class="grok-details">
            <summary>Step 3: Knowledge Gap — Grok Raw Data</summary>
            <div class="grok-section">
                <h4>EN</h4>
                {grok_gap_en}
            </div>
            <div class="grok-section">
                <h4>JP</h4>
                {grok_gap_jp}
            </div>
        </details>

        <details class="grok-details">
            <summary>Step 7: Commercial Signals — Grok Raw Data</summary>
            <div class="grok-section">
                <h4>EN</h4>
                {grok_com_en}
            </div>
            <div class="grok-section">
                <h4>JP</h4>
                {grok_com_jp}
            </div>
        </details>
    </div>"""

    # --- Total API cost ---
    total_calls = sum(n["data"].get("api_calls", {}).get("total", 0) for n in niches)
    total_cost = sum(n["data"].get("api_calls", {}).get("estimated_cost_usd", 0) for n in niches)
    niches_with_warnings = sum(1 for n in niches if n["warnings"])

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Niche Analysis Report — {scan_date}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Sans',sans-serif;background:#0a0a0a;color:#d0d0d0;line-height:1.6}}
.report{{max-width:1100px;margin:0 auto;padding:32px 24px}}

/* Header */
.report-header{{margin-bottom:32px;border-bottom:1px solid #222;padding-bottom:24px}}
.report-header h1{{font-size:26px;font-weight:800;color:#fff;letter-spacing:-0.5px}}
.report-header .meta{{font-size:13px;color:#666;margin-top:6px}}
.report-header .meta span{{margin-right:16px}}

/* Summary cards */
.summary-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}}
.summary-card{{background:#111;border:1px solid #1e1e1e;border-radius:10px;padding:16px}}
.summary-card .val{{font-size:28px;font-weight:800;color:#fff}}
.summary-card .label{{font-size:12px;color:#666;margin-top:2px}}

/* Section headers */
.section-title{{font-size:18px;font-weight:700;color:#fff;margin:32px 0 16px;padding-top:16px;border-top:1px solid #1a1a1a}}

/* Ranking table */
.ranking-table{{width:100%;border-collapse:collapse;margin-bottom:8px}}
.ranking-table th{{font-size:11px;color:#666;font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid #222;text-transform:uppercase;letter-spacing:0.5px}}
.ranking-table th:nth-child(n+3){{text-align:right}}
.ranking-table th:nth-child(6){{text-align:left}}
.rank-row{{cursor:pointer;transition:background 0.15s}}
.rank-row:hover{{background:#151515}}
.rank-row td{{padding:10px;border-bottom:1px solid #151515}}
.rank-num{{color:#555;font-weight:700;font-size:18px;width:30px}}
.niche-name{{font-weight:600;color:#e0e0e0;font-size:14px}}
.niche-sub{{font-size:11px;color:#555}}
.niche-name-sm{{font-size:13px;font-weight:600;color:#ccc;white-space:nowrap}}
.num{{text-align:right;font-variant-numeric:tabular-nums;color:#aaa}}
.warn-dot{{color:#eab308;font-size:14px}}

/* Ratio bar */
.ratio-bar{{position:relative;height:20px;background:#1a1a1a;border-radius:4px;overflow:hidden;min-width:100px}}
.ratio-fill{{height:100%;border-radius:4px;transition:width 0.3s}}
.ratio-label{{position:absolute;right:6px;top:50%;transform:translateY(-50%);font-size:11px;font-weight:700;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,0.8)}}

/* Heatmap */
.heatmap-table{{width:100%;border-collapse:collapse;margin-bottom:32px}}
.heatmap-table th{{font-size:11px;color:#666;font-weight:600;padding:6px 8px;border-bottom:1px solid #222}}
.heatmap-table td{{padding:8px;border-bottom:1px solid #151515}}

/* Detail sections */
.detail-section{{background:#0f0f0f;border:1px solid #1a1a1a;border-radius:12px;padding:24px;margin-bottom:20px}}
.detail-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}}
.detail-header h2{{font-size:18px;font-weight:700;color:#fff}}
.en-label{{font-size:14px;color:#555;font-weight:400}}
.detail-sub{{font-size:12px;color:#444;margin-top:2px}}
.detail-score{{font-size:32px;font-weight:800}}

/* Mini step cards */
.mini-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:20px}}
.mini-card{{background:#141414;border:1px solid #1e1e1e;border-radius:8px;padding:10px;text-align:center}}
.mini-label{{font-size:10px;color:#666;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}}
.mini-score{{font-size:16px;margin:4px 0}}
.mini-comment{{font-size:10px;color:#555;line-height:1.3}}

/* Data blocks */
.data-block{{background:#111;border:1px solid #1a1a1a;border-radius:8px;padding:14px;margin-bottom:12px}}
.data-block h3{{font-size:13px;font-weight:600;color:#999;margin-bottom:10px}}
.data-block table{{width:100%;border-collapse:collapse;font-size:12px}}
.data-block th{{text-align:left;color:#555;font-size:10px;font-weight:600;padding:4px 8px;border-bottom:1px solid #1a1a1a;text-transform:uppercase}}
.data-block td{{padding:5px 8px;border-bottom:1px solid #141414;color:#aaa}}
.data-block td.num{{text-align:right}}

/* Grok details */
.grok-details{{margin-top:12px;border:1px solid #1a1a1a;border-radius:8px;overflow:hidden}}
.grok-details summary{{padding:12px 14px;background:#111;cursor:pointer;font-size:13px;font-weight:600;color:#888}}
.grok-details summary:hover{{background:#151515}}
.grok-details[open] summary{{border-bottom:1px solid #1a1a1a}}
.grok-section{{padding:12px 14px}}
.grok-section h4{{font-size:11px;color:#666;font-weight:600;margin-bottom:8px;text-transform:uppercase}}
.grok-item{{margin-bottom:10px;padding:8px;background:#0f0f0f;border-radius:6px;border-left:2px solid #2a2a2a}}
.grok-text{{font-size:12px;color:#bbb;line-height:1.4;word-break:break-word}}
.grok-meta{{font-size:10px;color:#555;margin-top:4px}}
.grok-more{{font-size:11px;color:#555;font-style:italic}}
.dimmed{{color:#444;font-style:italic}}

/* Warnings */
.warn-box{{margin-bottom:14px}}
.warn-badge{{display:inline-block;background:rgba(234,179,8,0.1);color:#eab308;font-size:11px;padding:3px 8px;border-radius:4px;margin-right:6px;margin-bottom:4px}}

/* Footer */
.report-footer{{text-align:center;font-size:11px;color:#333;margin-top:40px;padding-top:20px;border-top:1px solid #1a1a1a}}

/* Responsive */
@media(max-width:768px){{
    .summary-row{{grid-template-columns:repeat(2,1fr)}}
    .mini-grid{{grid-template-columns:repeat(4,1fr)}}
    .ranking-table th:nth-child(4),.ranking-table th:nth-child(5),
    .ranking-table td:nth-child(4),.ranking-table td:nth-child(5){{display:none}}
}}
</style>
</head>
<body>
<div class="report">

    <div class="report-header">
        <h1>Niche Demand Analysis Report</h1>
        <div class="meta">
            <span>Scan: {scan_date}</span>
            <span>Niches: {len(niches)}</span>
            <span>API Calls: {total_calls}</span>
            <span>Cost: ${total_cost:.2f}</span>
            <span>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
        </div>
    </div>

    <div class="summary-row">
        <div class="summary-card">
            <div class="val">{len(niches)}</div>
            <div class="label">Niches Evaluated</div>
        </div>
        <div class="summary-card">
            <div class="val" style="color:#22c55e">{niches[0]['total']}/{niches[0]['max']}</div>
            <div class="label">Top Score — {_esc(niches[0]['name_jp'])}</div>
        </div>
        <div class="summary-card">
            <div class="val" style="color:#eab308">{niches_with_warnings}</div>
            <div class="label">With Data Issues</div>
        </div>
        <div class="summary-card">
            <div class="val">${total_cost:.2f}</div>
            <div class="label">Total API Cost</div>
        </div>
    </div>

    <div class="section-title">Ranking</div>
    <table class="ranking-table">
        <tr>
            <th>#</th>
            <th>Niche</th>
            <th>Score</th>
            <th>YT EN</th>
            <th>YT JP</th>
            <th>EN/JP Ratio</th>
            <th>JP Publishers</th>
        </tr>
        {ranking_rows}
    </table>

    <div class="section-title">Heatmap — 7 Steps</div>
    <table class="heatmap-table">
        <tr><th></th>{heatmap_header}<th>Total</th></tr>
        {heatmap_rows}
    </table>

    <div class="section-title">Detail by Niche</div>
    {detail_sections}

    <div class="report-footer">
        AI Agency HQ — Niche Demand Analyzer v0.1<br>
        Framework: 7-Step Evaluation (Demand / Engagement / Knowledge Gap / Supply / Gap / Localization / Commercial)<br>
        Data sources: Grok API (x_search) + Xpoz MCP (Twitter/Reddit/Instagram) + yt-dlp (YouTube)
    </div>
</div>

<script>
// Click ranking row to scroll to detail
document.querySelectorAll('.rank-row').forEach(row => {{
    row.addEventListener('click', () => {{
        const niche = row.dataset.niche;
        const el = document.getElementById('detail-' + niche);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    open_it = "--open" in sys.argv
    generate_report(date, open_browser=open_it)
