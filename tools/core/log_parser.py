"""セッションログパーサー

weekly-report, shareholder-report が使う。
content/logs/ のMarkdownログを読んでメタデータを抽出する。

使い方:
    from tools.core.log_parser import collect_week_logs, summarize_logs
    logs = collect_week_logs("2026-W08")
    summary = summarize_logs(logs)
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = ROOT / "content" / "logs"


def get_week_dates(week_str: str = "") -> tuple:
    """ISO week → (monday, sunday, week_str)"""
    if week_str:
        year, week = week_str.split("-W")
        monday = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
    else:
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday, monday.strftime("%Y-W%W")


def collect_week_logs(week_str: str = "") -> List[Dict]:
    """指定週のセッションログを収集する。"""
    monday, sunday, _ = get_week_dates(week_str)
    return collect_logs_in_range(monday, sunday)


def collect_logs_in_range(start: datetime, end: datetime) -> List[Dict]:
    """日付範囲のセッションログを収集する。"""
    if not LOGS_DIR.exists():
        return []

    logs = []
    for f in sorted(LOGS_DIR.glob("*.md")):
        match = re.match(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not match:
            continue
        date = datetime.strptime(match.group(1), "%Y-%m-%d")
        if start <= date <= end:
            logs.append(_parse_log(f))
    return logs


def collect_all_logs() -> List[Dict]:
    """全セッションログを収集する。"""
    if not LOGS_DIR.exists():
        return []
    return [_parse_log(f) for f in sorted(LOGS_DIR.glob("*.md"))]


def _parse_log(path: Path) -> Dict:
    """1ファイルをパースしてメタデータを返す。"""
    content = path.read_text()
    lines = content.splitlines()

    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
    date_str = date_match.group(1) if date_match else path.stem

    return {
        "file": path.name,
        "date": date_str,
        "is_recovery": "復元" in content,
        "participants": _extract_section_items(lines, "参加者"),
        "actions_done": _extract_section_items(lines, "実施内容"),
        "decisions": _extract_section_items(lines, "決定事項"),
        "deliverables": _extract_table_rows(lines, "成果物"),
        "next_actions": _extract_section_items(lines, "次回やること"),
        "shareholder_items": _extract_section_items(lines, "株主確認"),
        "line_count": len(lines),
    }


def _extract_section_items(lines: List[str], heading: str) -> List[str]:
    """## heading 以下の - リストアイテムを抽出する。"""
    items = []
    in_section = False
    for line in lines:
        if heading in line and line.startswith("#"):
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("- ") and stripped != "- " and stripped != "-":
                items.append(stripped[2:])
            elif stripped.startswith("#") or (stripped.startswith("|") and "ファイル" in stripped):
                break
    return items


def _extract_table_rows(lines: List[str], heading: str) -> List[Dict]:
    """## heading 以下のテーブル行を抽出する。"""
    rows = []
    in_section = False
    for line in lines:
        if heading in line:
            in_section = True
            continue
        if in_section and line.startswith("|") and "---" not in line and "ファイル" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts:
                rows.append({
                    "file": parts[0] if len(parts) > 0 else "",
                    "content": parts[1] if len(parts) > 1 else "",
                    "owner": parts[2] if len(parts) > 2 else "",
                })
        elif in_section and not line.startswith("|") and line.strip() and line.startswith("#"):
            break
    return rows


def summarize_logs(logs: List[Dict]) -> Dict:
    """ログリストのサマリーを返す。"""
    all_actions = []
    all_decisions = []
    all_deliverables = []
    all_next = []
    all_shareholder = []
    participants_set = set()

    for log in logs:
        all_actions.extend(log["actions_done"])
        all_decisions.extend(log["decisions"])
        all_deliverables.extend(log["deliverables"])
        all_next.extend(log["next_actions"])
        all_shareholder.extend(log["shareholder_items"])
        for p in log["participants"]:
            participants_set.add(p)

    return {
        "session_count": len(logs),
        "date_range": f"{logs[0]['date']}〜{logs[-1]['date']}" if logs else "N/A",
        "total_actions": len(all_actions),
        "total_decisions": len(all_decisions),
        "total_deliverables": len(all_deliverables),
        "participants": sorted(participants_set),
        "actions": all_actions,
        "decisions": all_decisions,
        "deliverables": all_deliverables,
        "next_actions": all_next,
        "shareholder_items": all_shareholder,
        "recovery_count": sum(1 for l in logs if l["is_recovery"]),
    }
