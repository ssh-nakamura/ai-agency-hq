"""status.md パーサー・更新モジュール

kpi-update, weekly-report, startup, shareholder-report が共有する。
status.mdの構造を理解し、セクション単位で読み書きする。

使い方:
    from tools.core.status_parser import StatusParser
    sp = StatusParser()
    kpi = sp.get_kpi()
    finance = sp.get_finance()
    actions = sp.get_actions_by_status("未着手")
    sp.update_token_table(rows)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = ROOT / "docs" / "status.md"


class StatusParser:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or STATUS_PATH
        self._content = ""
        self._lines = []
        self.reload()

    def reload(self):
        self._content = self.path.read_text()
        self._lines = self._content.splitlines()

    # ── KPI ──

    def get_kpi(self) -> Dict[str, str]:
        """実績テーブルをdictで返す。{"売上": "¥0", ...}"""
        return self._parse_table_after("### 実績")

    def get_phase(self) -> str:
        """現在のフェーズ文字列を返す。"""
        for line in self._lines:
            if "現在のフェーズ" in line:
                return line.split(":", 1)[-1].strip() if ":" in line else line
        return "Unknown"

    # ── 収支 ──

    def get_finance(self) -> Dict[str, str]:
        """月次収支テーブルをdictで返す。"""
        # Find the current year-month section
        for i, line in enumerate(self._lines):
            if re.match(r"### \d{4}年\d{1,2}月", line):
                return self._parse_table_at(i + 1)
        return {}

    def get_fixed_costs(self) -> Dict[str, str]:
        """固定費テーブルをdictで返す。"""
        return self._parse_table_after("### 固定費")

    # ── アクション ──

    def get_actions_by_section(self) -> Dict[str, List[Dict]]:
        """セクション別にアクションを返す。
        {"最優先": [...], "次に着手": [...], "保留": [...], ...}
        """
        sections = {}
        current_section = None

        for line in self._lines:
            if line.startswith("### ") and "アクション" not in line:
                section_name = line.replace("### ", "").strip()
                if any(k in section_name for k in ["最優先", "次に着手", "保留", "株主承認", "完了済み"]):
                    current_section = section_name
                    sections[current_section] = []
                    continue

            if current_section and line.startswith("|") and "---" not in line and "ID" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if parts:
                    sections[current_section].append({
                        "id": parts[0] if len(parts) > 0 else "",
                        "action": parts[1] if len(parts) > 1 else "",
                        "owner": parts[2] if len(parts) > 2 else "",
                        "status": parts[3] if len(parts) > 3 else "",
                    })

        return sections

    def get_stale_actions(self, days: int = 14) -> List[Dict]:
        """指定日数以上放置されている未着手アクションを返す。"""
        # This is a heuristic — status.mdには作成日がないので完全な判定はできない
        # 「最優先」と「次に着手」の「未着手」を返す（放置の可能性）
        sections = self.get_actions_by_section()
        stale = []
        for section_name in ["最優先", "次に着手"]:
            for section_key, actions in sections.items():
                if section_name in section_key:
                    for a in actions:
                        if "未着手" in a.get("status", ""):
                            stale.append({**a, "section": section_key})
        return stale

    def get_pending_approvals(self) -> List[Dict]:
        """株主承認待ちリストを返す。"""
        sections = self.get_actions_by_section()
        for key, actions in sections.items():
            if "株主承認" in key:
                return actions
        return []

    # ── トークン消費 ──

    def get_token_table(self) -> List[Dict]:
        """トークン消費テーブルをパースして返す。"""
        rows = []
        in_token = False
        for line in self._lines:
            if "トークン消費" in line:
                in_token = True
                continue
            if in_token and line.startswith("|") and "---" not in line and "日付" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    rows.append({
                        "date": parts[0],
                        "tokens": parts[1],
                        "cost": parts[2],
                        "models": parts[3] if len(parts) > 3 else "",
                    })
            elif in_token and not line.startswith("|") and not line.startswith("-") and line.strip():
                if line.startswith(">") or (line.startswith("#") and "トークン" not in line):
                    break
        return rows

    def update_token_table(self, rows: List[Dict]) -> bool:
        """トークン消費テーブルを新しいデータで置き換える。"""
        start, end = self._find_token_table_range()
        if start < 0:
            return False

        new_table_lines = [
            "| 日付 | 合計トークン | コスト(USD) | 使用モデル |",
            "|------|------------|------------|-----------|",
        ]
        total_tokens = 0.0
        total_cost = 0.0

        for row in rows:
            new_table_lines.append(
                f"| {row['date']} | {row['tokens']} | {row['cost']} | {row.get('models', '')} |"
            )
            try:
                total_tokens += float(row["tokens"].replace("M", "").replace(",", ""))
            except ValueError:
                pass
            try:
                total_cost += float(row["cost"].replace("$", "").replace(",", ""))
            except ValueError:
                pass

        new_table_lines.append(f"| **合計** | **{total_tokens:.1f}M** | **${total_cost:.2f}** | |")

        new_lines = self._lines[:start] + new_table_lines + self._lines[end + 1:]
        self.path.write_text("\n".join(new_lines) + "\n")
        self.reload()
        return True

    def _find_token_table_range(self) -> Tuple[int, int]:
        """トークン消費テーブルの行範囲(start, end)を返す。"""
        start = -1
        end = -1
        in_token_section = False

        for i, line in enumerate(self._lines):
            if "トークン消費" in line:
                in_token_section = True
                continue
            if in_token_section and line.startswith("| 日付"):
                start = i
                continue
            if start >= 0 and line.startswith("|"):
                end = i
            elif start >= 0 and not line.startswith("|"):
                break

        return start, end

    # ── 内部ヘルパー ──

    def _parse_table_after(self, heading: str) -> Dict[str, str]:
        """指定見出しの直後のテーブルをdictで返す。"""
        found = False
        for i, line in enumerate(self._lines):
            if heading in line:
                found = True
                continue
            if found:
                return self._parse_table_at(i)
        return {}

    def _parse_table_at(self, start_idx: int) -> Dict[str, str]:
        """指定行からのMarkdownテーブルをdictで返す。"""
        result = {}
        for line in self._lines[start_idx:]:
            if line.startswith("|") and "---" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2 and parts[0] not in ("指標", "費目", "項目"):
                    result[parts[0]] = parts[1]
            elif not line.startswith("|") and line.strip():
                break
        return result
