#!/usr/bin/env python3
"""
テスト観点レポート生成
======================
全テストの「何を」「なぜ」「どうやって」テストしているかを
日本語で詳細に説明するHTMLレポートを生成する。

Usage:
    python3 tests/generate_perspective_report.py
"""

import ast
import re
import sys
from pathlib import Path
from datetime import date

TESTS_DIR = Path(__file__).resolve().parent
BASE_DIR = TESTS_DIR.parent
OUTPUT_DIR = BASE_DIR / "reports"
TODAY = date.today().isoformat()

sys.path.insert(0, str(TESTS_DIR))

# ============================================================
# Category Definitions (in Japanese)
# ============================================================

CATEGORIES = [
    {
        "id": "S",
        "file": "test_static.py",
        "name": "静的整合性チェック",
        "color": "#6366f1",
        "icon": "S",
        "summary": "ファイル構造・ドキュメントの存在と整合性を検証する",
        "why": (
            "組織の土台となるファイルが欠けていたり、"
            "ドキュメント間で情報が矛盾していると、エージェントが正しく動作しない。"
            "コスト: ゼロ（ファイルの存在チェックのみ）。"
        ),
        "what": [
            "必須ファイル（CLAUDE.md, plan.md, status.md等）が全て存在するか",
            "8エージェント全員の定義ファイル（.claude/agents/*.md）が揃っているか",
            "8エージェント全員のメモリファイル（MEMORY.md）が揃っているか",
            "統合前の旧ファイル（business-plan.md等）が残っていないか",
            "plan.mdとstatus.mdでフェーズ情報が一致しているか",
            "必要なディレクトリ構造（site/, docs/, content/等 13ディレクトリ）が揃っているか",
        ],
    },
    {
        "id": "C",
        "file": "test_role_boundaries.py",
        "name": "役割境界テスト",
        "color": "#ec4899",
        "icon": "C",
        "summary": "各エージェントが自分の担当範囲を守り、他の仕事に手を出さないことを検証",
        "why": (
            "**最重要カテゴリ。** "
            "CEOが調査や執筆を自分でやると、opusトークンが無駄に消費される。"
            "エージェント同士の担当が曖昧だと、重複作業や責任の空白が生まれる。"
            "各エージェントの禁止事項リストが、組織の境界線を物理的に守る。"
        ),
        "what": [
            "【CEO委任】CEOが部下の仕事を代行しないルールが明文化されているか",
            "【CEO委任】CEOのMEMORY.mdに過去の代行失敗（叱られた経験）が記録されているか",
            "【CEO委任】CEOのTask toolに全7エージェントが登録されているか",
            "【領域制限】site-builderがsite/以外を触らないか",
            "【領域制限】product-managerがコードを書かないか",
            "【領域制限】writerがHTMLを書かないか（site-builderの仕事）",
            "【領域制限】x-managerがブログを書かないか（writerの仕事）",
            "【領域制限】video-creatorがブログ・ツイートを作らないか",
            "【領域制限】legalが断定的な法的助言をしないか",
            "【領域制限】analystが戦略判断をしないか（CEOの仕事）",
            "【ツール制約】CEO以外がTask tool（エージェント召喚）を持っていないか",
            "【ツール制約】site-builderがWebSearchを持っていないか（調査はanalystの仕事）",
            "【ツール制約】writer・legalがBashを持っていないか",
            "【ツール制約】未知のツールが混入していないか",
            "【禁止事項】全エージェントに禁止事項セクションがあるか",
            "【禁止事項】全部下が「戦略判断禁止」を持っているか",
            "【禁止事項】全部下が「株主に直接報告禁止」を持っているか",
            "【境界の双方向性】writer⇔site-builder、x-manager⇔writerの境界が両側から定義されているか",
            "【整合性】CLAUDE.mdのエージェント一覧 = 実際のエージェントファイル",
            "【整合性】CLAUDE.mdのモデル指定 = 各エージェントの設定ファイル",
        ],
    },
    {
        "id": "D",
        "file": "test_command_chain.py",
        "name": "指揮系統テスト",
        "color": "#f59e0b",
        "icon": "D",
        "summary": "上→下の指示、下→上の報告、横連携のルールが正しく定義されているかを検証",
        "why": (
            "指揮系統が壊れると、エージェントが勝手に判断したり、"
            "株主への報告ルートが混乱する。"
            "フラットな2階層（CEO + 7部門長）の構造を厳密に維持することが"
            "組織のガバナンスの基盤。"
        ),
        "what": [
            "【階層定義】CLAUDE.mdに指揮系統の図が定義されているか",
            "【階層定義】株主→CEO→部門長の2階層構造になっているか（3階層以上は禁止）",
            "【階層定義】全7部門長がCEO直下に同じ深さで配置されているか",
            "【上向き報告】全部下が「株主に直接報告しない」ルールを持っているか",
            "【上向き報告】CLAUDE.mdに「CEO経由」のルールが明記されているか",
            "【上向き報告】「上→下へ指示、下→上へ報告」の方向が明記されているか",
            "【上向き報告】各エージェントのエスカレーション先がCEOになっているか",
            "【下向き指示】CEO以外がTask toolを持っていないか（= 他のエージェントに指示できない）",
            "【下向き指示】CEOマニュアルに「いつ誰を呼ぶか」の基準があるか",
            "【横連携】作業レベルの横連携が「自由」と明記されているか",
            "【横連携】判断レベルの横連携が「CEO経由」と明記されているか",
            "【横連携】各エージェントに部門間連携セクションがあるか",
            "【横連携】writer→site-builderの成果物受け渡しフローが定義されているか",
            "【横連携】analyst→PMのデータ共有フローが定義されているか",
            "【アクション管理】アクション更新権限がCEOのみと定義されているか",
        ],
    },
    {
        "id": "E",
        "file": "test_escalation.py",
        "name": "エスカレーションテスト",
        "color": "#ef4444",
        "icon": "E",
        "summary": "異常事態・判断困難時のエスカレーション経路が正しく設計されているかを検証",
        "why": (
            "エスカレーションは組織の安全ネット。"
            "法的リスクを見逃す（L3失敗）、予算超過を報告しない（L4失敗）といった"
            "事態が起きると、実害が発生する。"
            "各エージェントが「何が起きたら誰に報告するか」を具体的に知っている必要がある。"
        ),
        "what": [
            "【レベル定義】CLAUDE.mdにL1〜L4の4段階が定義されているか",
            "【L1】「迷うが続行可能」→ メモして後で報告、と定義されているか",
            "【L2】「方針不明で進められない」→ 中断してCEO判断、と定義されているか",
            "【L3】「法的・倫理リスク」→ 即座にCEO報告、と定義されているか",
            "【L4】「予算超過」→ CEO報告→株主承認、と定義されているか",
            "【財務閾値】¥30,000以上は株主承認必須、がCLAUDE.mdにあるか",
            "【財務閾値】¥55,000月間上限がstatus.mdにあるか",
            "【財務閾値】CEOマニュアルに月額・年額の明記義務があるか",
            "【自律支出禁止】AIが勝手にお金を使えない、が明記されているか",
            "【エージェント別】全7部門長にエスカレーションセクションがあるか",
            "【エージェント別】各セクションに3件以上の具体的な発火条件があるか",
            "【analyst固有】予想外のコスト発見 → CEO報告",
            "【analyst固有】競合の重要な動き → CEO報告",
            "【analyst固有】KPIの急激な悪化 → CEO報告",
            "【writer固有】法的リスクのあるコンテンツ → CEO報告",
            "【writer固有】炎上リスクのあるコンテンツ → CEO報告",
            "【site-builder固有】新フレームワーク導入 → CEO報告",
            "【site-builder固有】デザインルール変更 → CEO報告",
            "【PM固有】スコープ変更 → CEO報告",
            "【PM固有】技術的に実現困難 → CEO報告",
            "【legal固有】コンプライアンス違反発見 → 即座にCEO報告（L3）",
            "【x-manager固有】炎上・ネガティブ反応 → CEO報告",
            "【video-creator固有】外部ツールのコスト発生 → CEO報告",
            "【一貫性】全エージェントのエスカレーション先がCEOか（横にエスカレしない）",
            "【一貫性】CEO→株主のエスカレーション経路が定義されているか",
        ],
    },
    {
        "id": "K",
        "file": "test_teams.py",
        "name": "Teams連携テスト",
        "color": "#3b82f6",
        "icon": "K",
        "summary": "Agent Teamsシステムの設定・メモリ・起動パイプラインが正しく構成されているかを検証",
        "why": (
            "Agent Teamsは複数エージェントを並行稼働させる仕組み。"
            "YAMLフロントマターのミス1つでエージェントが起動しなかったり、"
            "メモリの読み込み失敗で人格崩壊する。"
            "Teams連携が壊れるとCEOの指示が部下に届かない。"
        ),
        "what": [
            "【ファイル健全性】8エージェント全員の定義ファイルが存在するか",
            "【ファイル健全性】全ファイルに有効なYAMLフロントマターがあるか",
            "【ファイル健全性】YAMLのname = ファイル名が一致しているか",
            "【ファイル健全性】全員にdescriptionフィールドがあるか",
            "【ファイル健全性】全員にmodelフィールドがあるか（opus/sonnet/haiku）",
            "【ファイル健全性】モデル割り当てが組織設計（コスト階層）と一致するか",
            "【ファイル健全性】全員にmemory=projectが設定されているか",
            "【ファイル健全性】全員にtoolsリストがあるか",
            "【ファイル健全性】部下全員にmaxTurns制限があるか（暴走防止、上限50）",
            "【メモリ】全エージェントのMEMORY.mdファイルが存在するか",
            "【メモリ】MEMORY.mdが200行以内か（超えると切り詰めリスク）",
            "【メモリ】CEOのMEMORY.mdに必須セクション（確定事項/株主/失敗と学び/自戒）があるか",
            "【メモリ】メモリディレクトリとエージェント一覧が一致するか（孤児ディレクトリ検出）",
            "【コンテキスト注入】CLAUDE.mdが300行以内か（全エージェントに注入されるため）",
            "【コンテキスト注入】各エージェントに起動時ルーティンがあるか",
            "【コンテキスト注入】起動ルーティンでMEMORY.mdを読んでいるか",
            "【コンテキスト注入】起動ルーティンで共有ドキュメントを参照しているか",
            "【コンテキスト注入】CEOマニュアル（docs/ceo-manual.md）が存在し、十分な分量があるか",
            "【起動連携】CEOのTask toolに列挙されたエージェント = 実ファイル",
            "【起動連携】エージェント数が想定通り（8体）か",
            "【起動連携】孤児エージェントファイルがないか",
            "【起動連携】ファイル出力するエージェントの出力ディレクトリが存在するか",
            "【Teams通信】CEOのMEMORY.mdにTeams/TeamCreate方式が記載されているか",
            "【Teams通信】独立Task投げ（バラ投げ）が禁止と記録されているか",
        ],
    },
    {
        "id": "I",
        "file": "test_financial.py",
        "name": "財務管理テスト",
        "color": "#10b981",
        "icon": "I",
        "summary": "予算定義・コスト追跡・承認フローが正しく設計されているかを検証",
        "why": (
            "実際のお金（最低¥15,000/月）がかかっている。"
            "AIが勝手に支出できないこと、予算超過を検知できること、"
            "承認待ちの項目が管理されていることは、株主への説明責任の根幹。"
        ),
        "what": [
            "【予算定義】月間上限¥55,000がstatus.mdに記載されているか",
            "【予算定義】予算がカテゴリ別（AI基盤/インフラ/等）に分割されているか",
            "【予算定義】各カテゴリに承認者が定義されているか",
            "【予算定義】¥30,000閾値がCLAUDE.mdとstatus.mdで一致しているか",
            "【予算定義】AIの自律支出禁止が明文化されているか",
            "【コスト追跡】固定費（Claude Max等）が記載されているか",
            "【コスト追跡】今月の支出合計が記録されているか",
            "【コスト追跡】収入（¥0でも）が追跡されているか",
            "【コスト追跡】累計投資額が追跡されているか",
            "【コスト追跡】月次収支（収入−支出）が計算されているか",
            "【トークン】status.mdにトークン消費セクションがあるか",
            "【トークン】Claudeプラン種別とコストが記載されているか",
            "【トークン】plan.mdにサービス別コスト内訳があるか",
            "【承認フロー】status.mdに承認待ちセクションがあるか",
            "【承認フロー】承認待ち項目にコスト見積もりが含まれているか",
        ],
    },
]

# Scenario test definitions
SCENARIO_CATEGORIES = {
    "C: Role Boundary": {
        "name": "役割境界シナリオ",
        "color": "#ec4899",
        "description": "エージェントが正しく委任・拒否するかを実際の応答で検証",
    },
    "D: Command Chain": {
        "name": "指揮系統シナリオ",
        "color": "#f59e0b",
        "description": "報告ルート・横連携のルールが行動レベルで守られるかを検証",
    },
    "E: Escalation": {
        "name": "エスカレーションシナリオ",
        "color": "#ef4444",
        "description": "異常事態で正しくCEOに報告するかを実際の応答で検証",
    },
    "K: Teams": {
        "name": "Teams連携シナリオ",
        "color": "#3b82f6",
        "description": "複数エージェント協調が機能するかを検証",
    },
    "I: Financial": {
        "name": "財務管理シナリオ",
        "color": "#10b981",
        "description": "予算に関わる判断を正しく拒否・エスカレートするかを検証",
    },
}


def count_tests_in_file(filepath: Path) -> dict:
    """Count static and live tests in a file using AST."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    static = 0
    live = 0
    classes = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            class_doc = ast.get_docstring(node) or ""
            class_is_live = any(
                isinstance(d, ast.Attribute) and d.attr == "live"
                for d in node.decorator_list
            )
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    method_is_live = class_is_live or any(
                        "skip" in ast.dump(stmt) and "Live" in ast.dump(stmt)
                        for stmt in ast.walk(item)
                    )
                    if method_is_live:
                        live += 1
                    else:
                        static += 1
                    doc = ast.get_docstring(item) or ""
                    methods.append({
                        "name": item.name,
                        "doc": doc.split("\n")[0].strip() if doc else "",
                        "is_live": method_is_live,
                    })
            classes.append({
                "name": node.name,
                "doc": class_doc.split("\n")[0].strip() if class_doc else "",
                "methods": methods,
            })

    return {"static": static, "live": live, "classes": classes}


def load_scenarios():
    """Load scenario definitions."""
    try:
        from scenarios import SCENARIOS
        return SCENARIOS
    except ImportError:
        return []


def escape(text):
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def generate_html():
    """Generate comprehensive test perspective HTML report."""
    # Count tests
    total_static = 0
    total_live = 0
    cat_data = []

    for cat in CATEGORIES:
        filepath = TESTS_DIR / cat["file"]
        if not filepath.exists():
            cat_data.append({**cat, "counts": {"static": 0, "live": 0, "classes": []}})
            continue
        counts = count_tests_in_file(filepath)
        total_static += counts["static"]
        total_live += counts["live"]
        cat_data.append({**cat, "counts": counts})

    total_tests = total_static + total_live

    # Load scenarios
    scenarios = load_scenarios()
    scenario_count = len(scenarios)

    # Build HTML
    parts = []

    parts.append(f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>テスト観点レポート — 仮想機関AI計画</title>
<style>
  :root {{
    --bg: #fafbfc;
    --text: #1a1a2e;
    --muted: #6b7280;
    --border: #e5e7eb;
    --card-bg: #ffffff;
    --accent: #2563eb;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Hiragino Kaku Gothic ProN", "Noto Sans JP", system-ui, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.7;
  }}
  .container {{ max-width: 1000px; margin: 0 auto; padding: 2.5rem 1.5rem; }}

  /* Header */
  .hero {{
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    color: white; border-radius: 16px; padding: 2.5rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
  }}
  .hero::after {{
    content: ""; position: absolute; top: -50%; right: -10%;
    width: 300px; height: 300px; border-radius: 50%;
    background: rgba(255,255,255,0.03);
  }}
  .hero h1 {{ font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; }}
  .hero p {{ color: rgba(255,255,255,0.7); font-size: 0.95rem; }}
  .hero .date {{ color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 0.5rem; }}

  /* Summary */
  .summary {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem; margin-bottom: 2.5rem;
  }}
  .summary-card {{
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.3rem; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .summary-card .val {{
    font-size: 2.2rem; font-weight: 800; line-height: 1.1;
  }}
  .summary-card .lbl {{
    font-size: 0.75rem; color: var(--muted); margin-top: 0.3rem;
    text-transform: uppercase; letter-spacing: 0.08em;
  }}
  .val-blue {{ color: #2563eb; }}
  .val-pink {{ color: #ec4899; }}
  .val-orange {{ color: #f97316; }}
  .val-green {{ color: #10b981; }}

  /* Architecture */
  .arch-section {{
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 16px; padding: 2rem; margin-bottom: 2.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .arch-section h2 {{
    font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 0.5rem;
  }}
  .arch-layers {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
  }}
  .arch-layer {{
    border: 2px solid var(--border); border-radius: 12px; padding: 1.2rem;
    text-align: center;
  }}
  .arch-layer.active {{ border-color: #2563eb; background: #eff6ff; }}
  .arch-layer h3 {{ font-size: 1rem; font-weight: 700; margin-bottom: 0.4rem; }}
  .arch-layer .layer-num {{ font-size: 0.7rem; color: var(--muted); margin-bottom: 0.3rem; }}
  .arch-layer p {{ font-size: 0.82rem; color: #4b5563; }}
  .arch-layer .cost {{ font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; font-style: italic; }}
  .arch-arrow {{ display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: #d1d5db; }}

  /* Category Sections */
  .cat-section {{ margin-bottom: 2.5rem; }}
  .cat-header {{
    display: flex; align-items: flex-start; gap: 1rem;
    padding: 1.2rem 1.5rem; border-radius: 12px;
    margin-bottom: 1rem;
  }}
  .cat-icon {{
    width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; font-weight: 800; color: white; flex-shrink: 0;
  }}
  .cat-header h2 {{ font-size: 1.3rem; font-weight: 700; }}
  .cat-header .cat-summary {{ font-size: 0.9rem; color: #4b5563; margin-top: 0.2rem; }}
  .cat-header .cat-count {{ font-size: 0.8rem; color: var(--muted); margin-top: 0.3rem; }}

  /* Why box */
  .why-box {{
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 1rem; font-size: 0.88rem;
  }}
  .why-box strong {{ color: #92400e; }}
  .why-box p {{ color: #78350f; }}

  /* Test perspective list */
  .perspective-list {{
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .perspective-list h3 {{
    font-size: 0.85rem; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.08em;
    padding: 0.8rem 1.2rem; border-bottom: 1px solid var(--border);
    background: #f9fafb;
  }}
  .perspective-item {{
    display: flex; align-items: flex-start; gap: 0.8rem;
    padding: 0.6rem 1.2rem; border-bottom: 1px solid #f3f4f6;
    font-size: 0.88rem;
  }}
  .perspective-item:last-child {{ border-bottom: none; }}
  .perspective-item:hover {{ background: #fafbfc; }}
  .p-badge {{
    display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px;
    font-size: 0.7rem; font-weight: 700; flex-shrink: 0; margin-top: 0.15rem;
    white-space: nowrap;
  }}
  .p-badge-rule {{ background: #dbeafe; color: #1d4ed8; }}
  .p-badge-tool {{ background: #fce7f3; color: #be185d; }}
  .p-badge-scope {{ background: #d1fae5; color: #065f46; }}
  .p-badge-check {{ background: #e0e7ff; color: #3730a3; }}
  .p-badge-agent {{ background: #fef3c7; color: #92400e; }}
  .p-badge-level {{ background: #fee2e2; color: #991b1b; }}
  .p-badge-fin {{ background: #d1fae5; color: #065f46; }}
  .p-badge-file {{ background: #e5e7eb; color: #374151; }}

  /* Scenario section */
  .scenario-grid {{
    display: grid; gap: 0.8rem; margin-bottom: 1.5rem;
  }}
  .scenario-card {{
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.2rem; overflow: hidden;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    cursor: pointer; transition: box-shadow 0.2s;
  }}
  .scenario-card:hover {{ box-shadow: 0 3px 12px rgba(0,0,0,0.08); }}
  .scenario-card.expanded .scenario-detail {{ display: block; }}
  .sc-header {{
    display: flex; align-items: center; gap: 0.8rem;
  }}
  .sc-id {{
    font-family: monospace; font-weight: 700; font-size: 0.8rem;
    color: white; padding: 0.15rem 0.5rem; border-radius: 4px;
  }}
  .sc-name {{ font-size: 0.92rem; font-weight: 600; flex: 1; }}
  .sc-agent {{
    font-size: 0.75rem; color: var(--muted);
    background: #f3f4f6; padding: 0.1rem 0.5rem; border-radius: 4px;
  }}
  .sc-criteria {{
    font-size: 0.82rem; color: #4b5563; margin-top: 0.5rem;
    padding-left: 0.5rem; border-left: 3px solid #e5e7eb;
  }}
  .scenario-detail {{
    display: none; margin-top: 0.8rem; padding-top: 0.8rem;
    border-top: 1px solid #f3f4f6;
  }}
  .sd-row {{
    display: grid; grid-template-columns: 80px 1fr; gap: 0.3rem;
    font-size: 0.82rem; margin-bottom: 0.3rem;
  }}
  .sd-label {{ font-weight: 700; color: var(--muted); }}
  .sd-keywords {{
    display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.2rem;
  }}
  .kw {{
    display: inline-block; padding: 0.1rem 0.4rem; border-radius: 4px;
    font-size: 0.72rem; font-family: monospace;
  }}
  .kw-expected {{ background: #d1fae5; color: #065f46; }}
  .kw-forbidden {{ background: #fee2e2; color: #991b1b; }}

  /* Coverage matrix */
  .matrix {{
    width: 100%; border-collapse: collapse; font-size: 0.82rem;
    margin-bottom: 1.5rem;
  }}
  .matrix th {{
    background: #f9fafb; padding: 0.6rem 0.8rem; text-align: left;
    border-bottom: 2px solid var(--border); font-weight: 600; color: var(--muted);
  }}
  .matrix td {{
    padding: 0.5rem 0.8rem; border-bottom: 1px solid #f3f4f6;
  }}
  .matrix tr:hover td {{ background: #fafbfc; }}
  .matrix .num {{ text-align: center; font-weight: 600; }}
  .matrix .bar-cell {{ padding: 0.5rem 0.8rem; }}
  .bar {{ height: 8px; border-radius: 4px; background: #e5e7eb; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; }}

  .footer {{
    margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border);
    text-align: center; color: var(--muted); font-size: 0.8rem;
  }}

  @media (max-width: 700px) {{
    .arch-layers {{ grid-template-columns: 1fr; }}
    .summary {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
<script>
  document.addEventListener("click", function(e) {{
    var card = e.target.closest(".scenario-card");
    if (card) card.classList.toggle("expanded");
  }});
</script>
</head>
<body>
<div class="container">
""")

    # Hero
    parts.append(f"""
<div class="hero">
  <h1>テスト観点レポート</h1>
  <p>仮想機関AI計画 — 組織TDDテストスイートの全観点解説</p>
  <div class="date">{TODAY} 生成 | pytest {total_tests}件 + シナリオ {scenario_count}件</div>
</div>
""")

    # Summary cards
    parts.append(f"""
<div class="summary">
  <div class="summary-card"><div class="val val-blue">{total_tests + scenario_count}</div><div class="lbl">全テスト件数</div></div>
  <div class="summary-card"><div class="val" style="color:#1e293b">{total_static}</div><div class="lbl">静的テスト</div></div>
  <div class="summary-card"><div class="val val-orange">{total_live}</div><div class="lbl">Liveスタブ</div></div>
  <div class="summary-card"><div class="val val-pink">{scenario_count}</div><div class="lbl">シナリオテスト</div></div>
  <div class="summary-card"><div class="val val-green">{len(CATEGORIES)}</div><div class="lbl">カテゴリ数</div></div>
</div>
""")

    # Architecture section
    parts.append("""
<div class="arch-section">
  <h2>テストアーキテクチャ — 3層構造</h2>
  <div class="arch-layers">
    <div class="arch-layer active">
      <div class="layer-num">Layer 1</div>
      <h3>静的チェック</h3>
      <p>設定ファイルの存在・構造・整合性を検証。テスト実行にLLMを使わない。</p>
      <div class="cost">コスト: ゼロ（0.18秒で完了）</div>
    </div>
    <div class="arch-layer">
      <div class="layer-num">Layer 2</div>
      <h3>クロスリファレンス</h3>
      <p>複数ファイルにまたがるルールの一貫性を検証。CLAUDE.md ⇔ エージェント定義の矛盾検出。</p>
      <div class="cost">コスト: ゼロ（Layer 1と同時実行）</div>
    </div>
    <div class="arch-layer">
      <div class="layer-num">Layer 3</div>
      <h3>シナリオテスト</h3>
      <p>実際にエージェントを起動し、プロンプトを与え、応答のキーワードで合否判定。</p>
      <div class="cost">コスト: ~48,000トークン（haiku, ~110秒）</div>
    </div>
  </div>
</div>
""")

    # Category sections
    for cat in cat_data:
        counts = cat["counts"]
        n_static = counts["static"]
        n_live = counts["live"]
        n_total = n_static + n_live

        parts.append(f"""
<section class="cat-section" id="cat-{cat['id']}">
  <div class="cat-header" style="background: {cat['color']}10; border: 1px solid {cat['color']}30;">
    <div class="cat-icon" style="background: {cat['color']}">{cat['icon']}</div>
    <div>
      <h2>カテゴリ {cat['id']}: {cat['name']}</h2>
      <div class="cat-summary">{cat['summary']}</div>
      <div class="cat-count">{n_total}件（静的 {n_static} / Liveスタブ {n_live}）</div>
    </div>
  </div>

  <div class="why-box">
    <strong>なぜ重要か:</strong>
    <p>{cat['why']}</p>
  </div>

  <div class="perspective-list">
    <h3>テスト観点 — {len(cat['what'])}項目</h3>
""")

        for item in cat["what"]:
            # Detect badge type from brackets
            badge = ""
            text = item
            if item.startswith("【") and "】" in item:
                tag_end = item.index("】")
                tag = item[1:tag_end]
                text = item[tag_end + 1:]
                # Map tag to badge class
                badge_class = "p-badge-check"
                if "ツール" in tag:
                    badge_class = "p-badge-tool"
                elif "領域" in tag or "スコープ" in tag:
                    badge_class = "p-badge-scope"
                elif "CEO" in tag or "委任" in tag:
                    badge_class = "p-badge-rule"
                elif "整合" in tag or "一貫" in tag:
                    badge_class = "p-badge-check"
                elif any(x in tag for x in ["analyst", "writer", "site", "PM", "legal", "x-manager", "video"]):
                    badge_class = "p-badge-agent"
                elif "固有" in tag:
                    badge_class = "p-badge-agent"
                elif any(x in tag for x in ["レベル", "L1", "L2", "L3", "L4"]):
                    badge_class = "p-badge-level"
                elif any(x in tag for x in ["予算", "財務", "コスト", "トークン", "承認"]):
                    badge_class = "p-badge-fin"
                elif "ファイル" in tag or "メモリ" in tag or "コンテキスト" in tag or "起動" in tag or "Teams" in tag:
                    badge_class = "p-badge-file"
                elif any(x in tag for x in ["上向き", "下向き", "横連携", "アクション", "階層"]):
                    badge_class = "p-badge-rule"
                elif "禁止" in tag or "境界" in tag:
                    badge_class = "p-badge-tool"
                badge = f'<span class="p-badge {badge_class}">{escape(tag)}</span>'

            parts.append(f'    <div class="perspective-item">{badge}<span>{escape(text)}</span></div>\n')

        parts.append("""  </div>
""")

        # Classes detail (collapsible)
        if counts["classes"]:
            parts.append(f"""  <div class="perspective-list">
    <h3>テストクラス・メソッド一覧</h3>
""")
            for cls in counts["classes"]:
                for m in cls["methods"]:
                    level = '<span class="p-badge p-badge-level">Live</span>' if m["is_live"] else '<span class="p-badge p-badge-file">Static</span>'
                    doc = escape(m["doc"]) if m["doc"] else ""
                    parts.append(f'    <div class="perspective-item">{level}<span><code style="font-size:0.78rem;color:#4b5563">{escape(cls["name"])}.{escape(m["name"])}</code>')
                    if doc:
                        parts.append(f'<br><span style="font-size:0.8rem;color:#6b7280">{doc}</span>')
                    parts.append('</span></div>\n')

            parts.append("  </div>\n")

        parts.append("</section>\n")

    # Scenario Tests Section
    parts.append(f"""
<section class="cat-section" id="cat-scenario">
  <div class="cat-header" style="background: #7c3aed10; border: 1px solid #7c3aed30;">
    <div class="cat-icon" style="background: #7c3aed">!</div>
    <div>
      <h2>シナリオテスト（実動テスト）</h2>
      <div class="cat-summary">実際にエージェントを <code>claude -p</code> で起動し、応答内容からキーワードマッチで合否を判定</div>
      <div class="cat-count">{scenario_count}件 | haiku使用 | ~48,000トークン | ~110秒</div>
    </div>
  </div>

  <div class="why-box">
    <strong>なぜ重要か:</strong>
    <p>静的テストは「ルールが書いてあるか」を検証するが、シナリオテストは「ルール通りに行動するか」を検証する。
    LLMは設定通りに動くとは限らないため、実際にプロンプトを投げて応答を確認する必要がある。
    コストを抑えるためhaikuモデルを使用（1シナリオ ~3,000トークン）。</p>
  </div>

  <div class="scenario-grid">
""")

    for s in scenarios:
        cat_info = SCENARIO_CATEGORIES.get(s["category"], {"color": "#6b7280"})
        color = cat_info["color"]
        expected_kws = ""
        forbidden_kws = ""
        if s.get("expected_any"):
            expected_kws = "".join(
                f'<span class="kw kw-expected">{escape(k)}</span>'
                for k in s["expected_any"]
            )
        if s.get("forbidden_any"):
            forbidden_kws = "".join(
                f'<span class="kw kw-forbidden">{escape(k)}</span>'
                for k in s["forbidden_any"]
            )

        parts.append(f"""
    <div class="scenario-card">
      <div class="sc-header">
        <span class="sc-id" style="background:{color}">{s['id']}</span>
        <span class="sc-name">{escape(s['name'])}</span>
        <span class="sc-agent">{s['agent_context']}</span>
      </div>
      <div class="sc-criteria">{escape(s['pass_criteria'])}</div>
      <div class="scenario-detail">
        <div class="sd-row"><span class="sd-label">プロンプト:</span><span>{escape(s['prompt'])}</span></div>
        <div class="sd-row"><span class="sd-label">期待KW:</span><div class="sd-keywords">{expected_kws}</div></div>
        <div class="sd-row"><span class="sd-label">禁止KW:</span><div class="sd-keywords">{forbidden_kws}</div></div>
      </div>
    </div>
""")

    parts.append("""  </div>
</section>
""")

    # Coverage Matrix
    parts.append("""
<div class="arch-section">
  <h2>カバレッジマトリックス</h2>
  <table class="matrix">
    <thead>
      <tr>
        <th>カテゴリ</th>
        <th>静的テスト</th>
        <th>Liveスタブ</th>
        <th>シナリオ</th>
        <th class="num">合計</th>
        <th>カバー範囲</th>
      </tr>
    </thead>
    <tbody>
""")

    scenario_by_cat = {}
    for s in scenarios:
        key = s["category"][0]  # first letter
        scenario_by_cat[key] = scenario_by_cat.get(key, 0) + 1

    max_total = 0
    for cat in cat_data:
        c = cat["counts"]
        s_count = scenario_by_cat.get(cat["id"], 0)
        t = c["static"] + c["live"] + s_count
        if t > max_total:
            max_total = t

    for cat in cat_data:
        c = cat["counts"]
        s_count = scenario_by_cat.get(cat["id"], 0)
        t = c["static"] + c["live"] + s_count
        bar_pct = (t / max(max_total, 1)) * 100

        parts.append(f"""      <tr>
        <td><strong style="color:{cat['color']}">{cat['id']}: {cat['name']}</strong></td>
        <td class="num">{c['static']}</td>
        <td class="num">{c['live']}</td>
        <td class="num">{s_count}</td>
        <td class="num"><strong>{t}</strong></td>
        <td class="bar-cell"><div class="bar"><div class="bar-fill" style="width:{bar_pct:.0f}%;background:{cat['color']}"></div></div></td>
      </tr>
""")

    parts.append("""    </tbody>
  </table>
</div>
""")

    # How to run
    parts.append("""
<div class="arch-section">
  <h2>実行方法</h2>
  <div style="font-size:0.88rem;">
    <p style="margin-bottom:0.8rem;"><strong>静的テスト（コストゼロ、0.2秒）:</strong></p>
    <pre style="background:#1e293b;color:#e2e8f0;padding:1rem;border-radius:8px;font-size:0.82rem;margin-bottom:1rem;overflow-x:auto">python3 -m pytest tests/ -v          # 全静的テスト
python3 -m pytest tests/ -k role     # 役割境界のみ
python3 -m pytest tests/ -k escal    # エスカレーションのみ
python3 tests/run_tests.py           # HTML付きレポート生成</pre>
    <p style="margin-bottom:0.8rem;"><strong>シナリオテスト（~48,000トークン、~110秒）:</strong></p>
    <pre style="background:#1e293b;color:#e2e8f0;padding:1rem;border-radius:8px;font-size:0.82rem;margin-bottom:1rem;overflow-x:auto">python3 tests/run_scenarios.py                     # 全シナリオ
python3 tests/run_scenarios.py --category C        # 役割境界のみ
python3 tests/run_scenarios.py --priority critical  # 重要度criticalのみ
python3 tests/run_scenarios.py --id SC-C01         # 1件だけ
python3 tests/run_scenarios.py --dry-run            # 何が走るか確認</pre>
  </div>
</div>
""")

    # Footer
    parts.append(f"""
<div class="footer">
  テスト観点レポート — 仮想機関AI計画 | {TODAY} 自動生成 | tests/generate_perspective_report.py
</div>
</div>
</body>
</html>
""")

    return "".join(parts)


def main():
    html = generate_html()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"test-perspectives-{TODAY}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Report generated: {out_path}")
    print(f"File size: {out_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
