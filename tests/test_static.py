"""
Static Document Integrity Tests
==================================
Quick checks on document structure, cross-references, and hygiene.
These overlap with validate-docs.py but are pytest-native for CI integration.
"""

import pytest
import re
from pathlib import Path
from conftest import (
    ALL_AGENTS, SUBORDINATE_AGENTS, BASE_DIR,
    read_file, extract_section,
)


@pytest.mark.static
class TestRequiredFiles:
    """All required files must exist."""

    REQUIRED_FILES = [
        "CLAUDE.md",
        "docs/plan.md",
        "docs/status.md",
        "docs/decisions.md",
        "docs/ceo-manual.md",
        "docs/design-rules.md",
    ]

    @pytest.mark.parametrize("path", REQUIRED_FILES)
    def test_required_file_exists(self, path):
        assert (BASE_DIR / path).exists(), f"Required file missing: {path}"

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_agent_file_exists(self, agent):
        assert (BASE_DIR / f".claude/agents/{agent}.md").exists(), \
            f"Agent file missing: {agent}.md"

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_memory_file_exists(self, agent):
        assert (BASE_DIR / f".claude/agent-memory/{agent}/MEMORY.md").exists(), \
            f"Memory file missing: {agent}/MEMORY.md"


@pytest.mark.static
class TestOldFilesRemoved:
    """Old files from pre-consolidation must be removed."""

    OLD_FILES = [
        "docs/business-plan.md",
        "docs/roadmap.md",
        "docs/actions.md",
        "docs/state.json",
        "docs/finances.md",
    ]

    @pytest.mark.parametrize("path", OLD_FILES)
    def test_old_file_removed(self, path):
        assert not (BASE_DIR / path).exists(), \
            f"Old file still exists: {path} (should have been removed after consolidation)"


@pytest.mark.static
class TestPhaseConsistency:
    """Phase information must be consistent across documents."""

    def test_plan_and_status_phase_match(self, plan_md, status_md):
        """plan.md and status.md must agree on current phase."""
        plan_phase = re.search(r"## 現在地:\s*(.+)", plan_md)
        status_phase = re.search(r"## 現在のフェーズ:\s*(.+)", status_md)

        assert plan_phase is not None, "plan.md must state current phase"
        assert status_phase is not None, "status.md must state current phase"
        assert plan_phase.group(1).strip() == status_phase.group(1).strip(), \
            f"Phase mismatch: plan.md='{plan_phase.group(1)}' vs status.md='{status_phase.group(1)}'"


@pytest.mark.static
class TestDocumentHygiene:
    """Document hygiene checks."""

    def test_no_youchousa_in_plan(self, plan_md):
        """plan.md should not have unresolved '要調査' items in tables."""
        lines_with_youchousa = [
            i + 1 for i, line in enumerate(plan_md.split("\n"))
            if "要調査" in line and "|" in line
        ]
        assert len(lines_with_youchousa) == 0, \
            f"plan.md has {len(lines_with_youchousa)} unresolved 要調査 items (lines: {lines_with_youchousa})"

    def test_completed_actions_within_limit(self, status_md):
        """Completed actions section should have max 10 items."""
        if "完了済み" not in status_md:
            return
        completed_section = status_md.split("完了済み")[-1]
        action_ids = re.findall(r"\|\s*A-\d+\s*\|", completed_section)
        assert len(action_ids) <= 10, \
            f"Completed actions: {len(action_ids)} items (limit: 10, archive excess)"


@pytest.mark.static
class TestDirectoryStructure:
    """Expected directories must exist."""

    EXPECTED_DIRS = [
        ".claude/agents",
        ".claude/agent-memory",
        "site",
        "docs",
        "docs/specs",
        "docs/legal",
        "content/logs",
        "content/tweets",
        "content/blog",
        "content/copy",
        "content/videos",
        "tools",
        "reports",
    ]

    @pytest.mark.parametrize("directory", EXPECTED_DIRS)
    def test_directory_exists(self, directory):
        path = BASE_DIR / directory
        assert path.is_dir(), f"Expected directory missing: {directory}/"
