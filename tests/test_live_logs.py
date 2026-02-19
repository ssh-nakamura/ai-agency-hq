"""
Dashboard agent detection tests (TDD).
Tests for tools/dashboard/server.py agent detection & message parsing.
"""

import json
import sys
import pytest
from pathlib import Path

# Add dashboard directory to sys.path
DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "tools" / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

import server  # noqa: E402


# ── Helpers ──────────────────────────────────────────────


def _write_jsonl(path: str, records: list):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _make_user_msg(text: str, timestamp: str = "2026-02-19T10:00:00Z") -> dict:
    return {
        "type": "user",
        "message": {"role": "user", "content": text},
        "timestamp": timestamp,
        "uuid": "u1",
    }


def _make_assistant_msg(
    text: str, model: str = "claude-sonnet-4-6", timestamp: str = "2026-02-19T10:00:01Z"
) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "model": model,
        },
        "timestamp": timestamp,
        "uuid": "a1",
        "requestId": "req_test",
    }


def _make_agent_setting(agent_name: str) -> dict:
    return {
        "type": "agent-setting",
        "agentSetting": agent_name,
        "sessionId": "test-session",
    }


def _make_task_tool_call(subagent_type: str, prompt: str, tool_id: str = "toolu_01") -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": "Task",
                    "input": {
                        "subagent_type": subagent_type,
                        "description": "test task",
                        "prompt": prompt,
                    },
                }
            ],
            "model": "claude-opus-4-6",
        },
        "timestamp": "2026-02-19T10:00:02Z",
        "uuid": "a2",
    }


def _make_read_tool_call(file_path: str) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_read",
                    "name": "Read",
                    "input": {"file_path": file_path},
                }
            ],
            "model": "claude-sonnet-4-6",
        },
        "timestamp": "2026-02-19T10:00:01Z",
        "uuid": "a_read",
    }


# ── Tests: detect_agent with agent-setting ───────────────


class TestAgentSettingDetection:
    """Sessions with agent-setting records should be identified reliably."""

    def test_ceo_from_agent_setting(self, tmp_path):
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl(str(jsonl), [
            _make_agent_setting("ceo"),
            _make_user_msg("状況報告"),
            _make_assistant_msg("わかった"),
        ])
        msgs = server.parse_jsonl(str(jsonl))
        assert server.detect_agent(msgs) == "ceo"

    def test_all_known_agents(self, tmp_path):
        for agent_key in server.AGENTS:
            jsonl = tmp_path / f"{agent_key}.jsonl"
            _write_jsonl(str(jsonl), [
                _make_agent_setting(agent_key),
                _make_user_msg("テスト"),
            ])
            msgs = server.parse_jsonl(str(jsonl))
            assert server.detect_agent(msgs) == agent_key, f"Failed: {agent_key}"


class TestSubagentDetection:
    """Subagent sessions identified via parent Task calls."""

    def test_single_subagent_from_parent(self, tmp_path):
        parent_id = "parent-123"
        parent_dir = tmp_path / parent_id / "subagents"
        parent_dir.mkdir(parents=True)
        prompt = "サイトを更新してくれ"

        parent_jsonl = tmp_path / f"{parent_id}.jsonl"
        _write_jsonl(str(parent_jsonl), [
            _make_agent_setting("ceo"),
            _make_task_tool_call("site-builder", prompt),
        ])

        sub_jsonl = parent_dir / "agent-a123456.jsonl"
        _write_jsonl(str(sub_jsonl), [
            _make_user_msg(prompt),
            _make_assistant_msg("読む。"),
        ])

        msgs = server.parse_jsonl(str(sub_jsonl))
        assert server.detect_agent(msgs, jsonl_path=str(sub_jsonl)) == "site-builder"

    def test_multiple_subagents_matched_by_prompt(self, tmp_path):
        parent_id = "parent-multi"
        parent_dir = tmp_path / parent_id / "subagents"
        parent_dir.mkdir(parents=True)
        prompt_a = "市場分析してくれ"
        prompt_w = "記事を書いてくれ"

        parent_jsonl = tmp_path / f"{parent_id}.jsonl"
        _write_jsonl(str(parent_jsonl), [
            _make_agent_setting("ceo"),
            _make_task_tool_call("analyst", prompt_a, "toolu_01"),
            _make_task_tool_call("writer", prompt_w, "toolu_02"),
        ])

        sub1 = parent_dir / "agent-c111.jsonl"
        sub2 = parent_dir / "agent-c222.jsonl"
        _write_jsonl(str(sub1), [_make_user_msg(prompt_a)])
        _write_jsonl(str(sub2), [_make_user_msg(prompt_w)])

        msgs1 = server.parse_jsonl(str(sub1))
        msgs2 = server.parse_jsonl(str(sub2))
        assert server.detect_agent(msgs1, jsonl_path=str(sub1)) == "analyst"
        assert server.detect_agent(msgs2, jsonl_path=str(sub2)) == "writer"


class TestFilePathDetection:
    """Detect agent from Read tool calls to agent-specific files."""

    def test_read_memory_file(self, tmp_path):
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl(str(jsonl), [
            _make_user_msg("テスト"),
            _make_read_tool_call(".claude/agent-memory/analyst/MEMORY.md"),
        ])
        msgs = server.parse_jsonl(str(jsonl))
        assert server.detect_agent(msgs) == "analyst"

    def test_read_agent_definition(self, tmp_path):
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl(str(jsonl), [
            _make_user_msg("テスト"),
            _make_read_tool_call("/Users/test/.claude/agents/writer.md"),
        ])
        msgs = server.parse_jsonl(str(jsonl))
        assert server.detect_agent(msgs) == "writer"

    def test_no_data_returns_unknown(self, tmp_path):
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl(str(jsonl), [
            _make_user_msg("こんにちは"),
            _make_assistant_msg("はい"),
        ])
        msgs = server.parse_jsonl(str(jsonl))
        assert server.detect_agent(msgs) == "unknown"


class TestDetectMsgType:
    """Distinguish Task (DM) vs Teams messages."""

    def test_task_type(self, tmp_path):
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl(str(jsonl), [
            _make_user_msg("分析してくれ"),
            _make_assistant_msg("了解"),
        ])
        msgs = server.parse_jsonl(str(jsonl))
        assert server.detect_msg_type(msgs) == "task"

    def test_team_type(self, tmp_path):
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl(str(jsonl), [
            _make_user_msg('<teammate-message teammate_id="team-lead">指示内容</teammate-message>'),
            _make_assistant_msg("承知"),
        ])
        msgs = server.parse_jsonl(str(jsonl))
        assert server.detect_msg_type(msgs) == "team"


class TestResolveSender:
    """Parse teammate-message tags to identify sender."""

    def test_plain_text_is_ceo(self):
        sender, text = server.resolve_sender("普通のテキスト")
        assert sender == "ceo"
        assert text == "普通のテキスト"

    def test_team_lead_resolves_to_ceo(self):
        raw = '<teammate-message teammate_id="team-lead">指示内容</teammate-message>'
        sender, text = server.resolve_sender(raw)
        assert sender == "ceo"
        assert "指示内容" in text

    def test_analyst_teammate_id(self):
        raw = '<teammate-message teammate_id="analyst">報告</teammate-message>'
        sender, text = server.resolve_sender(raw)
        assert sender == "analyst"
        assert "報告" in text

    def test_shutdown_request_returns_empty(self):
        raw = '<teammate-message teammate_id="team-lead">{"type":"shutdown_request","requestId":"abc"}</teammate-message>'
        sender, text = server.resolve_sender(raw)
        assert sender == "ceo"
        assert text == ""

    def test_task_assignment_formatted(self):
        raw = '<teammate-message teammate_id="team-lead">{"type":"task_assignment","subject":"市場調査"}</teammate-message>'
        sender, text = server.resolve_sender(raw)
        assert sender == "ceo"
        assert "市場調査" in text
