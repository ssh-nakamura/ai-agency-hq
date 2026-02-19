#!/usr/bin/env python3
"""
reports/ 配下のHTMLファイルを一覧にするダッシュボード生成ツール

Usage:
    python3 tools/generate-reports-index.py
    python3 tools/generate-reports-index.py --open
"""

import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"

REPORT_TYPES = {
    "session": ("セッション報告", "#4CAF50"),
    "scenario": ("シナリオ分析", "#2196F3"),
    "architecture": ("アーキテクチャ", "#9C27B0"),
    "test": ("テスト", "#FF9800"),
    "org-chart": ("組織図", "#00BCD4"),
    "roadmap": ("ロードマップ", "#E91E63"),
    "usage": ("利用状況", "#795548"),
    "subagent": ("サブエージェント", "#607D8B"),
    "refactoring": ("リファクタリング", "#FF5722"),
}


def classify_report(name: str) -> tuple:
    """Classify a report by its filename."""
    for key, (label, color) in REPORT_TYPES.items():
        if key in name.lower():
            return label, color
    return "その他", "#9E9E9E"


def extract_date(name: str) -> str:
    """Extract date from filename."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return match.group(1) if match else ""


def generate_index():
    """Generate reports/index.html."""
    html_files = sorted(
        [
            f
            for f in REPORTS_DIR.iterdir()
            if f.suffix == ".html" and f.name != "index.html"
        ],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    rows = []
    for f in html_files:
        label, color = classify_report(f.name)
        date = extract_date(f.name)
        size_kb = f.stat().st_size / 1024
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        rows.append(
            f"""<tr>
<td><a href="{f.name}">{f.stem}</a></td>
<td><span class="badge" style="background:{color}22;color:{color}">{label}</span></td>
<td>{date}</td>
<td>{size_kb:.0f} KB</td>
<td>{mtime}</td>
</tr>"""
        )

    table_rows = "\n".join(rows)
    total = len(html_files)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>レポートダッシュボード — 仮想機関AI計画</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #f5f5f5;
    color: #1a1a1a;
    line-height: 1.7;
    padding: 2rem 1rem;
}}
.container {{ max-width: 1000px; margin: 0 auto; }}
header {{
    background: #fff;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
header h1 {{ font-size: 1.5rem; color: #111; }}
header .count {{ font-size: 2rem; font-weight: 700; color: #4CAF50; }}
table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}}
th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #f8f8f8; font-weight: 600; font-size: 0.85rem; color: #555; }}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: #f0f7ff; }}
a {{ color: #1a73e8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.badge {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}}
footer {{
    text-align: center;
    color: #999;
    font-size: 0.8rem;
    margin-top: 2rem;
}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>レポートダッシュボード</h1>
<div class="count">{total} 件</div>
</header>
<table>
<tr>
<th>レポート名</th>
<th>種別</th>
<th>日付</th>
<th>サイズ</th>
<th>更新日時</th>
</tr>
{table_rows}
</table>
<footer>仮想機関AI計画 — 最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</div>
</body>
</html>"""

    output = REPORTS_DIR / "index.html"
    output.write_text(html, encoding="utf-8")
    print(f"Generated: {output} ({total} reports)")
    return output


def main():
    output = generate_index()
    if "--open" in sys.argv:
        subprocess.run(["open", str(output)])


if __name__ == "__main__":
    main()
