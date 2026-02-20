"""ccusage実行・出力パーサー

kpi-update, session-log が使う。
npx ccusage@latest を実行して結果をパースする。

使い方:
    from tools.core.ccusage import run_daily, run_monthly
    rows = run_daily(since="20260201")
    monthly = run_monthly()

CLIとしても使える:
    python3 tools/core/ccusage.py --since 20260201
    python3 tools/core/ccusage.py --monthly
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]


def run_daily(since: str = "") -> List[Dict]:
    """ccusage dailyを実行してパースする。"""
    cmd = ["npx", "ccusage@latest", "daily"]
    if since:
        cmd += ["--since", since]
    return _run_and_parse(cmd)


def run_monthly() -> List[Dict]:
    """ccusage monthlyを実行してパースする。"""
    return _run_and_parse(["npx", "ccusage@latest", "monthly"])


def _run_and_parse(cmd: List[str]) -> List[Dict]:
    """コマンドを実行して出力テーブルをパースする。"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
    except subprocess.TimeoutExpired:
        print("Error: ccusage timed out after 30s", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("Error: npx not found. Is Node.js installed?", file=sys.stderr)
        return []

    if result.returncode != 0:
        print(f"Error: ccusage failed: {result.stderr[:200]}", file=sys.stderr)
        return []

    return _parse_table(result.stdout)


def _parse_table(output: str) -> List[Dict]:
    """ccusageのテーブル出力をパースする。

    ccusage daily format:
      Date      | Total Tokens | Cost     | Models
      2026-02-14| 16.1M        | $11.34   | haiku-4-5, opus-4-6

    ccusage monthly format:
      Month     | Total Tokens | Cost     | Models
    """
    rows = []
    for line in output.strip().splitlines():
        line = line.strip()
        # Skip headers, separators, empty lines
        if not line or "─" in line or line.startswith("Date") or line.startswith("Month"):
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3:
            rows.append({
                "date": parts[0],
                "tokens": parts[1],
                "cost": parts[2],
                "models": parts[3] if len(parts) > 3 else "",
            })
    return rows


def totals(rows: List[Dict]) -> Dict:
    """行リストから合計トークン・コストを計算する。"""
    total_tokens = 0.0
    total_cost = 0.0
    for row in rows:
        t = row["tokens"].replace("M", "").replace("K", "").replace(",", "").strip("*")
        c = row["cost"].replace("$", "").replace(",", "").strip("*")
        try:
            val = float(t)
            if "M" in row["tokens"]:
                total_tokens += val
            elif "K" in row["tokens"]:
                total_tokens += val / 1000
        except ValueError:
            pass
        try:
            total_cost += float(c)
        except ValueError:
            pass

    return {
        "total_tokens_m": round(total_tokens, 1),
        "total_cost_usd": round(total_cost, 2),
        "days": len([r for r in rows if not r["date"].startswith("*")]),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ccusage wrapper")
    parser.add_argument("--since", default="", help="Start date (YYYYMMDD)")
    parser.add_argument("--monthly", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.monthly:
        rows = run_monthly()
    else:
        since = args.since or datetime.now().strftime("%Y%m01")
        rows = run_daily(since)

    if args.json:
        print(json.dumps({"rows": rows, "totals": totals(rows)}, indent=2))
    else:
        t = totals(rows)
        print(f"Days: {t['days']}")
        print(f"Tokens: {t['total_tokens_m']}M")
        print(f"Cost: ${t['total_cost_usd']}")
        for row in rows:
            print(f"  {row['date']}: {row['tokens']} ({row['cost']})")
