#!/usr/bin/env python3
"""
セッションログ（Markdown）→ HTML報告書変換ツール

Usage:
    python3 tools/session-report.py content/logs/2026-02-19.md
    python3 tools/session-report.py content/logs/2026-02-19.md --open
    python3 tools/session-report.py content/logs/2026-02-19.md --recovery
"""

import sys
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>セッション報告 - {date}{suffix_title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #f5f5f5;
    color: #1a1a1a;
    line-height: 1.7;
    padding: 2rem 1rem;
}}
.container {{ max-width: 900px; margin: 0 auto; }}
header {{
    background: #fff;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
}}
header h1 {{ font-size: 1.5rem; color: #111; margin-bottom: 0.5rem; }}
header .meta {{ color: #666; font-size: 0.9rem; }}
.cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}}
.card {{
    background: #fff;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    text-align: center;
}}
.card .label {{ font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }}
.card .value {{ font-size: 1.8rem; font-weight: 700; color: #111; margin-top: 0.25rem; }}
section {{
    background: #fff;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
}}
section h2 {{
    font-size: 1.2rem;
    color: #111;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}}
section h3 {{ font-size: 1rem; color: #333; margin: 1rem 0 0.5rem; }}
ul, ol {{ padding-left: 1.5rem; }}
li {{ margin-bottom: 0.4rem; }}
table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin: 1rem 0;
}}
th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #f8f8f8; font-weight: 600; font-size: 0.85rem; color: #555; }}
tr:last-child td {{ border-bottom: none; }}
.badge {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.badge-new {{ background: #d4edda; color: #155724; }}
.badge-update {{ background: #cce5ff; color: #004085; }}
.badge-done {{ background: #d4edda; color: #155724; }}
.badge-pending {{ background: #fff3cd; color: #856404; }}
code {{
    background: #f0f0f0;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.85em;
}}
.recovery-notice {{
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
    color: #856404;
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
{content}
<footer>仮想機関AI計画 — 自動生成レポート</footer>
</div>
</body>
</html>
"""


def parse_markdown(md_text: str) -> dict:
    """Parse session log markdown into structured data."""
    sections = {}
    current_section = None
    current_content = []
    title = ""

    for line in md_text.split("\n"):
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return {"title": title, "sections": sections}


def md_to_html_basic(text: str) -> str:
    """Convert basic markdown to HTML."""
    lines = text.split("\n")
    html_lines = []
    in_list = False
    in_table = False
    table_header_done = False

    for line in lines:
        stripped = line.strip()

        # Table
        if "|" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue  # separator row
            if not in_table:
                html_lines.append("<table>")
                in_table = True
                table_header_done = False
            if not table_header_done:
                html_lines.append(
                    "<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>"
                )
                table_header_done = True
            else:
                html_lines.append(
                    "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
                )
            continue
        elif in_table:
            html_lines.append("</table>")
            in_table = False
            table_header_done = False

        # List items
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = stripped[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"`(.+?)`", r"<code>\1</code>", content)
            html_lines.append(f"<li>{content}</li>")
            continue
        elif in_list and not stripped:
            html_lines.append("</ul>")
            in_list = False

        # Headers
        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
            continue

        # Regular text
        if stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            content = re.sub(r"`(.+?)`", r"<code>\1</code>", content)
            html_lines.append(f"<p>{content}</p>")

    if in_list:
        html_lines.append("</ul>")
    if in_table:
        html_lines.append("</table>")

    return "\n".join(html_lines)


def generate_html(
    parsed: dict, date_str: str, suffix: str = "", is_recovery: bool = False
) -> str:
    """Generate full HTML report from parsed markdown."""
    parts = []

    suffix_title = f" ({suffix})" if suffix else ""

    # Header
    parts.append(
        f"""<header>
<h1>{parsed['title'] or f'セッション報告 — {date_str}'}</h1>
<div class="meta">日付: {date_str} | 自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</header>"""
    )

    # Recovery notice
    if is_recovery:
        parts.append(
            '<div class="recovery-notice">'
            "このレポートはセッションログから復元されたものです。"
            "リアルタイム生成ではないため、詳細が省略されている場合があります。"
            "</div>"
        )

    # Summary cards
    sections = parsed["sections"]
    card_data = []

    # Count achievements
    for key in ("本日の成果", "成果物一覧", "実施内容"):
        if key in sections:
            text = sections[key]
            count = text.count("\n- ") + text.count("\n* ") + 1
            table_rows = len(re.findall(r"\n\|[^|]+\|", text))
            total = max(count, table_rows)
            if total > 0:
                card_data.append(("成果物", str(total)))
            break

    # Count agents
    if "参加者" in sections:
        agents = sections["参加者"].count("- ")
        if agents > 0:
            card_data.append(("参加エージェント", str(agents)))

    # Shareholder items
    for key in ("株主への相談事項", "株主確認事項"):
        if key in sections and sections[key].strip() and sections[key].strip() != "-":
            card_data.append(("株主確認", "あり"))
            break

    if card_data:
        cards_html = "\n".join(
            f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value}</div></div>'
            for label, value in card_data
        )
        parts.append(f'<div class="cards">{cards_html}</div>')

    # Sections
    for section_name, content in sections.items():
        if not content.strip():
            continue
        parts.append(
            f"""<section>
<h2>{section_name}</h2>
{md_to_html_basic(content)}
</section>"""
        )

    return HTML_TEMPLATE.format(
        date=date_str, suffix_title=suffix_title, content="\n".join(parts)
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/session-report.py <log-file.md> [--open] [--recovery]")
        sys.exit(1)

    log_path = Path(sys.argv[1])
    do_open = "--open" in sys.argv
    is_recovery = "--recovery" in sys.argv

    if not log_path.exists():
        print(f"Error: {log_path} not found")
        sys.exit(1)

    md_text = log_path.read_text(encoding="utf-8")

    # Extract date from filename
    stem = log_path.stem
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", stem)
    if not date_match:
        print(f"Error: Cannot extract date from {log_path.name}")
        sys.exit(1)

    date_str = date_match.group(1)
    suffix = stem[len(date_str):]  # e.g., "" or "-s2"

    output_name = f"session-{date_str}{suffix}.html"
    output_path = REPO_ROOT / "reports" / output_name

    parsed = parse_markdown(md_text)
    html = generate_html(parsed, date_str, suffix, is_recovery=is_recovery)

    output_path.write_text(html, encoding="utf-8")
    print(f"Generated: {output_path}")

    if do_open:
        subprocess.run(["open", str(output_path)])


if __name__ == "__main__":
    main()
