#!/usr/bin/env python3
"""
validate-docs.py - ドキュメント整合性チェッカー
CEO起動時（フルモード）セルフチェック用。ファイル間の矛盾を自動検出する。

対象ファイル構成:
  docs/plan.md    — 事業計画 + ロードマップ
  docs/status.md  — アクション + KPI + 収支
  docs/decisions.md — 意思決定ログ
"""

import re
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mNG\033[0m"
WARN = "\033[33mWARN\033[0m"

errors = []
warnings = []


def read_file(rel_path):
    p = BASE / rel_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def check_file_exists(rel_path, context):
    p = BASE / rel_path
    if not p.exists():
        errors.append(f"[欠落] {rel_path} が存在しない（{context}）")
        return False
    return True


# ─── 1. 必須ファイルの存在確認 ─────────────────────────

print("=" * 60)
print("ドキュメント整合性チェック")
print("=" * 60)

print("\n--- 1. 必須ファイルの存在確認 ---")

required_files = {
    "CLAUDE.md": "組織ハンドブック",
    "docs/plan.md": "事業計画 + ロードマップ",
    "docs/status.md": "アクション + KPI + 収支",
    "docs/decisions.md": "意思決定ログ",
    "docs/ceo-manual.md": "CEOマニュアル",
    "docs/design-rules.md": "デザインルール",
}

agents = ["analyst", "writer", "site-builder", "x-manager",
          "video-creator", "product-manager", "legal", "narrator"]

for a in agents:
    required_files[f".claude/agents/{a}.md"] = f"エージェント定義({a})"
    required_files[f".claude/agent-memory/{a}/MEMORY.md"] = f"メモリ({a})"

required_files[".claude/agent-memory/ceo/MEMORY.md"] = "メモリ(ceo)"

for path, desc in required_files.items():
    exists = check_file_exists(path, desc)
    print(f"  {PASS if exists else FAIL} {path}")


# ─── 2. plan.md / status.md のフェーズ整合 ──────────────

print("\n--- 2. フェーズ整合性 ---")

plan_raw = read_file("docs/plan.md")
status_raw = read_file("docs/status.md")

phase_values = {}

if plan_raw:
    m = re.search(r"## 現在地:\s*(.+)", plan_raw)
    phase_values["plan.md"] = m.group(1).strip() if m else "?"

if status_raw:
    m = re.search(r"## 現在のフェーズ:\s*(.+)", status_raw)
    phase_values["status.md"] = m.group(1).strip() if m else "?"

unique_phases = set(phase_values.values())
if len(unique_phases) > 1:
    errors.append(f"[フェーズ不整合] " + " / ".join(
        f"{k}={v}" for k, v in phase_values.items()))
    print(f"  {FAIL} フェーズが一致しない: {phase_values}")
elif unique_phases:
    print(f"  {PASS} フェーズ一致: {list(unique_phases)[0]}")
else:
    print(f"  {WARN} フェーズ情報なし")


# ─── 3. status.md のコスト整合チェック ──────────────────

print("\n--- 3. コスト整合（status.md内） ---")

if status_raw:
    # 固定費合計を計算（固定費テーブルから金額を抽出）
    fixed_costs = re.findall(r"\|\s*[^|]+\|\s*[¥￥]([\d,]+)\s*\|", status_raw)

    # 月次支出合計を取得
    expenditure_match = re.search(r"支出合計\s*\|\s*[¥￥]?([\d,]+)", status_raw)

    if expenditure_match:
        expenditure = int(expenditure_match.group(1).replace(",", ""))
        print(f"  {PASS} 月次支出合計: ¥{expenditure:,}")
    else:
        warnings.append("[status.md] 月次支出合計が見つからない")
        print(f"  {WARN} status.mdから支出合計を抽出できず")
else:
    print(f"  {WARN} status.md が存在しない")


# ─── 4. status.md のアクション未着手チェック ───────────

print("\n--- 4. status.md アクション未着手チェック ---")

if status_raw:
    pending_actions = re.findall(
        r"\|\s*(A-\d+)\s*\|([^|]+)\|([^|]+)\|\s*未着手\s*\|", status_raw)

    for aid, action, assignee in pending_actions:
        action = action.strip()
        print(f"  INFO {aid} が未着手: {action[:40]}...")

    if not pending_actions:
        print(f"  {PASS} 最優先セクションに未着手アクションなし")


# ─── 5. MEMORY.md 存在 & 行数チェック ─────────────────

print("\n--- 5. MEMORY.md 行数チェック ---")

all_agents_with_ceo = ["ceo"] + agents

for a in all_agents_with_ceo:
    mem_raw = read_file(f".claude/agent-memory/{a}/MEMORY.md")
    if mem_raw is None:
        continue

    lines = mem_raw.split("\n")
    line_count = len(lines)

    if line_count > 200:
        warnings.append(
            f"[{a}/MEMORY.md] {line_count}行（200行超過 → 末尾が切り捨てられる可能性）")
        print(f"  {WARN} {a}: {line_count}行（200行超過！）")
    elif line_count > 170:
        print(f"  {WARN} {a}: {line_count}行（200行に近い）")
    else:
        print(f"  {PASS} {a}: {line_count}行")


# ─── 6. narrator キャラ設定チェック ──────────────────────

print("\n--- 6. narrator キャラ一元管理チェック ---")

narrator_raw = read_file(".claude/agents/narrator.md")
if narrator_raw:
    # narrator.md に全8キャラの一人称が含まれているか
    expected_chars = {
        "九条": "CEO", "白河": "analyst", "桐谷": "PM",
        "藤崎": "writer", "黒崎": "site-builder", "七瀬": "x-manager",
        "朝比奈": "video-creator", "氷室": "legal",
    }
    for surname, role in expected_chars.items():
        if surname in narrator_raw:
            print(f"  {PASS} {surname}({role}): narrator.mdに定義あり")
        else:
            errors.append(f"[narrator.md] {surname}({role})のキャラ定義が見つからない")
            print(f"  {FAIL} {surname}({role}): narrator.mdに定義なし")
else:
    errors.append("[narrator.md] ファイルが存在しない")
    print(f"  {FAIL} narrator.md が存在しない")


# ─── 7. plan.md の「要調査」残存チェック ───────────────

print("\n--- 7. plan.md 要調査チェック ---")

if plan_raw:
    youchousa = [i + 1 for i, line in enumerate(plan_raw.split("\n"))
                 if "要調査" in line and "|" in line]
    if youchousa:
        warnings.append(
            f"[plan.md] 「要調査」が{len(youchousa)}箇所残存（行: {youchousa}）")
        print(f"  {WARN} 「要調査」が{len(youchousa)}箇所: 行{youchousa}")
    else:
        print(f"  {PASS} 「要調査」なし")


# ─── 8. ディレクトリ構成 vs 実ディレクトリ ──────────────

print("\n--- 8. ディレクトリ構成チェック ---")

expected_dirs = [
    ".claude/agents",
    ".claude/agent-memory",
    "site",
    "docs",
    "docs/specs",
    "docs/research",
    "docs/legal",
    "docs/archive",
    "content/logs",
    "content/tweets",
    "content/blog",
    "content/copy",
    "content/videos",
    "tools",
    "reports",
]

for d in expected_dirs:
    p = BASE / d
    if p.is_dir():
        print(f"  {PASS} {d}/")
    else:
        warnings.append(f"[ディレクトリ] {d}/ が存在しない")
        print(f"  {WARN} {d}/ なし")


# ─── 9. status.md の完了済みタスク数チェック ───────────

print("\n--- 9. status.md 完了済みタスク数 ---")

if status_raw:
    completed = re.findall(r"\|\s*A-\d+\s*\|", status_raw.split("完了済み")[-1]) \
        if "完了済み" in status_raw else []
    count = len(completed)
    if count > 10:
        warnings.append(
            f"[status.md] 完了済みが{count}件（上限10件ルール超過）")
        print(f"  {WARN} 完了済み{count}件（上限10件ルール超過、アーカイブ推奨）")
    else:
        print(f"  {PASS} 完了済み{count}件（上限10件以内）")


# ─── 10. 旧ファイル残存チェック ────────────────────────

print("\n--- 10. 旧ファイル残存チェック ---")

old_files = [
    "docs/business-plan.md",
    "docs/roadmap.md",
    "docs/actions.md",
    "docs/state.json",
    "docs/finances.md",
]

old_found = False
for f in old_files:
    if (BASE / f).exists():
        warnings.append(f"[旧ファイル] {f} が残存（統合済みなら削除推奨）")
        print(f"  {WARN} {f} が残存")
        old_found = True

if not old_found:
    print(f"  {PASS} 旧ファイルなし（統合完了）")


# ─── サマリー ──────────────────────────────────────────

print("\n" + "=" * 60)
print("サマリー")
print("=" * 60)

if errors:
    print(f"\n{FAIL} エラー: {len(errors)}件")
    for e in errors:
        print(f"  - {e}")

if warnings:
    print(f"\n{WARN} 警告: {len(warnings)}件")
    for w in warnings:
        print(f"  - {w}")

if not errors and not warnings:
    print(f"\n{PASS} 問題なし！")

total = len(errors) + len(warnings)
print(f"\n合計: エラー{len(errors)}件 / 警告{len(warnings)}件")

sys.exit(1 if errors else 0)
