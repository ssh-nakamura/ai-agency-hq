"""tests/test_status_parser.py — StatusParser のテスト

status.mdの構造パース、KPI/収支/アクション抽出、
トークンテーブル更新をテストする。
"""

import pytest
from pathlib import Path
from textwrap import dedent

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.core.status_parser import StatusParser


# ============================================================
# Fixtures
# ============================================================

SAMPLE_STATUS = dedent("""\
# 現在の状況

> CEOが毎セッション読むファイル。

---

## 現在のフェーズ: Phase 0 - Step 1→2 移行中

最終更新: 2026-02-19

---

## KPI

### 実績
| 指標 | 値 |
|------|-----|
| 売上 | ¥0 |
| ユーザー数 | 0 |
| Xフォロワー | 0 |
| 月間コスト | ¥15,000 |

### Phase 2 目標（標準シナリオ）
| 指標 | 目標 |
|------|------|
| ShieldMe MRR | ¥225,000 |

---

## アクション

### 最優先
| ID | アクション | 担当 | 状態 | 備考 |
|----|-----------|------|------|------|
| A-012 | ShieldMe価格プラン検証 | product-manager | 未着手 | 100件実測 |
| A-023 | ブログ基盤整備 | writer | 進行中 | |

### 次に着手
| ID | アクション | 担当 | 状態 | 前提条件 |
|----|-----------|------|------|---------|
| A-008 | X初投稿案 | x-manager | 未着手 | LP完成後 |

### 株主承認待ち
| ID | 承認事項 | 金額 | 備考 |
|----|---------|------|------|
| S-001 | X API Basic契約 | $100/月 | MVP開発に必須 |
| S-002 | ツール契約 | ¥3,000〜12,000/月 | 構成選択 |

### 完了済み（直近10件）
| ID | アクション | 担当 | 完了日 | 成果物 |
|----|-----------|------|--------|--------|
| A-022 | business-plan補完 | CEO | 2026-02-16 | 反映済み |

---

## 収支

### 固定費（月額）
| 費目 | 月額 | 備考 |
|------|------|------|
| Claude Max | ¥15,000 | $100/月 |

### 2026年2月
| 指標 | 金額 |
|------|------|
| 収入合計 | ¥0 |
| 支出合計 | ¥15,000 |
| 収支 | -¥15,000 |

### トークン消費（2026年2月）
- プラン: Claude Max $100/月

| 日付 | 合計トークン | コスト(USD) | 使用モデル |
|------|------------|------------|-----------|
| 02-01 | 7.0M | $6.04 | opus-4-5 |
| 02-14 | 16.1M | $11.34 | haiku-4-5, opus-4-6 |
| **合計** | **23.1M** | **$17.38** | |
""")


@pytest.fixture
def tmp_status(tmp_path):
    """テスト用の一時status.mdを作成する。"""
    p = tmp_path / "status.md"
    p.write_text(SAMPLE_STATUS)
    return p


@pytest.fixture
def parser(tmp_status):
    """テスト用StatusParserインスタンス。"""
    return StatusParser(path=tmp_status)


# ============================================================
# Phase
# ============================================================

@pytest.mark.static
class TestPhase:
    def test_get_phase(self, parser):
        phase = parser.get_phase()
        assert "Phase 0" in phase

    def test_get_phase_contains_step(self, parser):
        phase = parser.get_phase()
        assert "Step" in phase


# ============================================================
# KPI
# ============================================================

@pytest.mark.static
class TestKPI:
    def test_get_kpi_returns_dict(self, parser):
        kpi = parser.get_kpi()
        assert isinstance(kpi, dict)

    def test_get_kpi_has_expected_keys(self, parser):
        kpi = parser.get_kpi()
        assert "売上" in kpi
        assert "ユーザー数" in kpi
        assert "月間コスト" in kpi

    def test_get_kpi_values(self, parser):
        kpi = parser.get_kpi()
        assert kpi["売上"] == "¥0"
        assert kpi["ユーザー数"] == "0"

    def test_get_kpi_excludes_header_row(self, parser):
        kpi = parser.get_kpi()
        assert "指標" not in kpi


# ============================================================
# Finance
# ============================================================

@pytest.mark.static
class TestFinance:
    def test_get_finance_returns_dict(self, parser):
        finance = parser.get_finance()
        assert isinstance(finance, dict)

    def test_get_finance_has_revenue(self, parser):
        finance = parser.get_finance()
        assert "収入合計" in finance
        assert finance["収入合計"] == "¥0"

    def test_get_finance_has_balance(self, parser):
        finance = parser.get_finance()
        assert "収支" in finance
        assert "-¥15,000" in finance["収支"]

    def test_get_fixed_costs(self, parser):
        fixed = parser.get_fixed_costs()
        assert "Claude Max" in fixed
        assert "¥15,000" in fixed["Claude Max"]


# ============================================================
# Actions
# ============================================================

@pytest.mark.static
class TestActions:
    def test_get_actions_returns_sections(self, parser):
        sections = parser.get_actions_by_section()
        assert isinstance(sections, dict)
        assert len(sections) > 0

    def test_highest_priority_section_exists(self, parser):
        sections = parser.get_actions_by_section()
        found = any("最優先" in k for k in sections.keys())
        assert found, f"最優先セクションがない: {list(sections.keys())}"

    def test_action_has_id_and_action(self, parser):
        sections = parser.get_actions_by_section()
        for section_name, actions in sections.items():
            if "最優先" in section_name and actions:
                assert actions[0]["id"] == "A-012"
                assert "ShieldMe" in actions[0]["action"]
                break

    def test_stale_actions_returns_unstaffed(self, parser):
        stale = parser.get_stale_actions()
        # A-012 is 未着手 in 最優先 → should appear
        ids = [a["id"] for a in stale]
        assert "A-012" in ids

    def test_stale_actions_excludes_in_progress(self, parser):
        stale = parser.get_stale_actions()
        ids = [a["id"] for a in stale]
        # A-023 is 進行中 → should NOT appear
        assert "A-023" not in ids

    def test_pending_approvals(self, parser):
        pending = parser.get_pending_approvals()
        assert len(pending) == 2
        ids = [p["id"] for p in pending]
        assert "S-001" in ids
        assert "S-002" in ids


# ============================================================
# Token Table
# ============================================================

@pytest.mark.static
class TestTokenTable:
    def test_get_token_table(self, parser):
        rows = parser.get_token_table()
        assert len(rows) >= 2  # 02-01 + 02-14 (合計行は除外されるかも)

    def test_token_row_has_fields(self, parser):
        rows = parser.get_token_table()
        for row in rows:
            assert "date" in row
            assert "tokens" in row
            assert "cost" in row

    def test_update_token_table(self, parser, tmp_status):
        new_rows = [
            {"date": "02-20", "tokens": "5.0M", "cost": "$4.00", "models": "opus-4-6"},
            {"date": "02-21", "tokens": "3.0M", "cost": "$2.50", "models": "haiku-4-5"},
        ]
        result = parser.update_token_table(new_rows)
        assert result is True

        # Reload and verify
        parser.reload()
        rows = parser.get_token_table()
        dates = [r["date"] for r in rows]
        assert "02-20" in dates
        assert "02-21" in dates

    def test_update_preserves_other_sections(self, parser, tmp_status):
        new_rows = [
            {"date": "02-20", "tokens": "5.0M", "cost": "$4.00"},
        ]
        parser.update_token_table(new_rows)
        parser.reload()

        # KPI should still work
        kpi = parser.get_kpi()
        assert "売上" in kpi

        # Finance should still work
        finance = parser.get_finance()
        assert "収入合計" in finance


# ============================================================
# Reload
# ============================================================

@pytest.mark.static
class TestReload:
    def test_reload_reflects_external_changes(self, parser, tmp_status):
        original_kpi = parser.get_kpi()
        assert original_kpi["売上"] == "¥0"

        # Externally modify the file
        content = tmp_status.read_text()
        content = content.replace("| 売上 | ¥0 |", "| 売上 | ¥10,000 |")
        tmp_status.write_text(content)

        parser.reload()
        new_kpi = parser.get_kpi()
        assert new_kpi["売上"] == "¥10,000"


# ============================================================
# Live test: actual status.md
# ============================================================

@pytest.mark.static
class TestLiveStatusMd:
    """実際のstatus.mdが存在し、パースできることを確認する。"""

    def test_real_status_md_exists(self):
        from tools.core.status_parser import STATUS_PATH
        assert STATUS_PATH.exists(), f"status.md not found at {STATUS_PATH}"

    def test_real_status_md_parseable(self):
        sp = StatusParser()
        kpi = sp.get_kpi()
        assert isinstance(kpi, dict)
        assert len(kpi) > 0

    def test_real_phase_not_empty(self):
        sp = StatusParser()
        phase = sp.get_phase()
        assert phase != "Unknown"
