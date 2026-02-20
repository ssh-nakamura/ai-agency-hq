"""tests/test_log_parser.py — log_parser のテスト

セッションログのパース、日付範囲収集、サマリー生成をテストする。
"""

import pytest
from pathlib import Path
from datetime import datetime
from textwrap import dedent

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.core.log_parser import (
    _parse_log,
    _extract_section_items,
    _extract_table_rows,
    collect_logs_in_range,
    summarize_logs,
    get_week_dates,
)


# ============================================================
# Fixtures
# ============================================================

SAMPLE_LOG = dedent("""\
# セッションログ 2026-02-19

## 参加者
- CEO（オーケストレーター）
- analyst（市場調査）
- writer（記事執筆）

## 実施内容
- スキル体系の全面見直し
- tools/core/ 共有モジュール3本作成
- 新規スキル11本作成

## 決定事項
- データ処理が必要なスキルのみPython裏付けを入れる
- 判断系スキルはプロンプト品質で勝負する

## 成果物
| ファイル | 内容 | 担当 |
|---------|------|------|
| tools/core/status_parser.py | ステータスパーサー | CEO |
| tools/core/log_parser.py | ログパーサー | CEO |
| .claude/commands/*.md | 新規スキル11本 | CEO |

## 次回やること
- テスト追加
- ai-trading-hq Phase 2

## 株主確認事項
- Grok API設定完了を確認
""")


@pytest.fixture
def tmp_logs_dir(tmp_path):
    """テスト用ログディレクトリを作成する。"""
    logs_dir = tmp_path / "content" / "logs"
    logs_dir.mkdir(parents=True)
    return logs_dir


@pytest.fixture
def sample_log_file(tmp_logs_dir):
    """サンプルログファイルを作成する。"""
    p = tmp_logs_dir / "2026-02-19-session.md"
    p.write_text(SAMPLE_LOG)
    return p


@pytest.fixture
def multi_log_dir(tmp_logs_dir):
    """複数日のログを作成する。"""
    for day in [17, 18, 19]:
        p = tmp_logs_dir / f"2026-02-{day:02d}-session.md"
        content = SAMPLE_LOG.replace("2026-02-19", f"2026-02-{day:02d}")
        if day == 17:
            content = content.replace("スキル体系の全面見直し", "組織設計の見直し")
        elif day == 18:
            content = content.replace("スキル体系の全面見直し", "ai-trading-hq Phase 1構築")
        p.write_text(content)
    return tmp_logs_dir


# ============================================================
# _extract_section_items
# ============================================================

@pytest.mark.static
class TestExtractSectionItems:
    def test_extract_participants(self):
        lines = SAMPLE_LOG.splitlines()
        items = _extract_section_items(lines, "参加者")
        assert len(items) == 3
        assert "CEO（オーケストレーター）" in items[0]

    def test_extract_actions(self):
        lines = SAMPLE_LOG.splitlines()
        items = _extract_section_items(lines, "実施内容")
        assert len(items) == 3
        assert "スキル体系" in items[0]

    def test_extract_decisions(self):
        lines = SAMPLE_LOG.splitlines()
        items = _extract_section_items(lines, "決定事項")
        assert len(items) == 2

    def test_extract_next_actions(self):
        lines = SAMPLE_LOG.splitlines()
        items = _extract_section_items(lines, "次回やること")
        assert len(items) == 2

    def test_extract_shareholder_items(self):
        lines = SAMPLE_LOG.splitlines()
        items = _extract_section_items(lines, "株主確認")
        assert len(items) == 1
        assert "Grok" in items[0]

    def test_missing_section_returns_empty(self):
        lines = SAMPLE_LOG.splitlines()
        items = _extract_section_items(lines, "存在しないセクション")
        assert items == []


# ============================================================
# _extract_table_rows
# ============================================================

@pytest.mark.static
class TestExtractTableRows:
    def test_extract_deliverables(self):
        lines = SAMPLE_LOG.splitlines()
        rows = _extract_table_rows(lines, "成果物")
        assert len(rows) == 3

    def test_table_row_has_fields(self):
        lines = SAMPLE_LOG.splitlines()
        rows = _extract_table_rows(lines, "成果物")
        assert rows[0]["file"] == "tools/core/status_parser.py"
        assert rows[0]["content"] == "ステータスパーサー"
        assert rows[0]["owner"] == "CEO"


# ============================================================
# _parse_log
# ============================================================

@pytest.mark.static
class TestParseLog:
    def test_parse_log_basic(self, sample_log_file):
        result = _parse_log(sample_log_file)
        assert result["date"] == "2026-02-19"
        assert result["file"] == "2026-02-19-session.md"

    def test_parse_log_participants(self, sample_log_file):
        result = _parse_log(sample_log_file)
        assert len(result["participants"]) == 3

    def test_parse_log_actions(self, sample_log_file):
        result = _parse_log(sample_log_file)
        assert len(result["actions_done"]) == 3

    def test_parse_log_is_not_recovery(self, sample_log_file):
        result = _parse_log(sample_log_file)
        assert result["is_recovery"] is False

    def test_parse_log_recovery_detection(self, tmp_logs_dir):
        p = tmp_logs_dir / "2026-02-20-recovery.md"
        p.write_text("# 復元セッション\n## 参加者\n- CEO\n")
        result = _parse_log(p)
        assert result["is_recovery"] is True


# ============================================================
# collect_logs_in_range
# ============================================================

@pytest.mark.static
class TestCollectLogs:
    def test_collect_range(self, multi_log_dir, monkeypatch):
        # Monkeypatch LOGS_DIR to use tmp dir
        import tools.core.log_parser as lp
        monkeypatch.setattr(lp, "LOGS_DIR", multi_log_dir)

        start = datetime(2026, 2, 17)
        end = datetime(2026, 2, 19)
        logs = collect_logs_in_range(start, end)
        assert len(logs) == 3

    def test_collect_range_subset(self, multi_log_dir, monkeypatch):
        import tools.core.log_parser as lp
        monkeypatch.setattr(lp, "LOGS_DIR", multi_log_dir)

        start = datetime(2026, 2, 18)
        end = datetime(2026, 2, 19)
        logs = collect_logs_in_range(start, end)
        assert len(logs) == 2

    def test_collect_empty_range(self, multi_log_dir, monkeypatch):
        import tools.core.log_parser as lp
        monkeypatch.setattr(lp, "LOGS_DIR", multi_log_dir)

        start = datetime(2026, 3, 1)
        end = datetime(2026, 3, 7)
        logs = collect_logs_in_range(start, end)
        assert len(logs) == 0

    def test_collect_nonexistent_dir(self, tmp_path, monkeypatch):
        import tools.core.log_parser as lp
        monkeypatch.setattr(lp, "LOGS_DIR", tmp_path / "nonexistent")

        start = datetime(2026, 2, 1)
        end = datetime(2026, 2, 28)
        logs = collect_logs_in_range(start, end)
        assert logs == []


# ============================================================
# summarize_logs
# ============================================================

@pytest.mark.static
class TestSummarizeLogs:
    def test_summarize_multi(self, multi_log_dir, monkeypatch):
        import tools.core.log_parser as lp
        monkeypatch.setattr(lp, "LOGS_DIR", multi_log_dir)

        start = datetime(2026, 2, 17)
        end = datetime(2026, 2, 19)
        logs = collect_logs_in_range(start, end)
        summary = summarize_logs(logs)

        assert summary["session_count"] == 3
        assert "2026-02-17" in summary["date_range"]
        assert "2026-02-19" in summary["date_range"]
        assert summary["total_actions"] == 9  # 3 actions × 3 logs
        assert summary["total_decisions"] == 6  # 2 decisions × 3 logs
        assert len(summary["participants"]) >= 1

    def test_summarize_empty(self):
        summary = summarize_logs([])
        assert summary["session_count"] == 0
        assert summary["date_range"] == "N/A"

    def test_summarize_recovery_count(self, tmp_logs_dir, monkeypatch):
        import tools.core.log_parser as lp
        monkeypatch.setattr(lp, "LOGS_DIR", tmp_logs_dir)

        # Create a recovery log
        p = tmp_logs_dir / "2026-02-20-recovery.md"
        p.write_text("# 復元セッション\n## 参加者\n- CEO\n## 実施内容\n- 復旧作業\n")

        start = datetime(2026, 2, 20)
        end = datetime(2026, 2, 20)
        logs = collect_logs_in_range(start, end)
        summary = summarize_logs(logs)
        assert summary["recovery_count"] == 1


# ============================================================
# get_week_dates
# ============================================================

@pytest.mark.static
class TestGetWeekDates:
    def test_returns_tuple(self):
        monday, sunday, week_str = get_week_dates()
        assert monday.weekday() == 0  # Monday
        assert sunday.weekday() == 6  # Sunday

    def test_sunday_after_monday(self):
        monday, sunday, _ = get_week_dates()
        assert sunday > monday
        assert (sunday - monday).days == 6
