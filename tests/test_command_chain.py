"""
Category D: Command Chain Tests — THICK
=========================================
Tests that verify the organizational hierarchy is properly enforced.

Key principle: Information flows UP (reports), instructions flow DOWN (commands).
No agent skips levels. No agent makes decisions above their authority.

Hierarchy:
  Shareholder (human)
    └── Orchestrator/CEO (opus)
          ├── analyst (sonnet)
          ├── product-manager (sonnet)
          ├── writer (sonnet)
          ├── site-builder (sonnet)
          ├── narrator (sonnet)
          ├── x-manager (haiku)
          ├── video-creator (haiku)
          └── legal (haiku)
"""

import pytest
import re
from conftest import (
    SUBORDINATE_AGENTS, ALL_AGENTS,
    get_agent_config, get_agent_body, get_agent_memory,
    read_file, extract_section, extract_table_rows,
    ALLOWED_LATERAL_PAIRS,
)


# ============================================================
# D.1 Hierarchy Definition
# ============================================================

@pytest.mark.static
@pytest.mark.command_chain
class TestHierarchyDefinition:
    """The command chain must be unambiguously defined."""

    def test_hierarchy_defined_in_claude_md(self, claude_md):
        """CLAUDE.md must contain a clear hierarchy diagram."""
        assert "指揮系統" in claude_md, \
            "CLAUDE.md must have a command chain (指揮系統) section"

    def test_ceo_under_shareholder(self, claude_md):
        """CEO reports to shareholder (株主), not the other way around."""
        hierarchy_section = extract_section(claude_md, "指揮系統")
        assert hierarchy_section is not None
        assert "株主" in hierarchy_section, \
            "Hierarchy must show shareholder at top"
        assert "CEO" in hierarchy_section or "リードエージェント" in hierarchy_section, \
            "Hierarchy must show CEO under shareholder"

    def test_all_subordinates_under_ceo(self, claude_md):
        """Every subordinate agent must appear under CEO in hierarchy."""
        hierarchy_section = extract_section(claude_md, "指揮系統")
        assert hierarchy_section is not None
        for agent in SUBORDINATE_AGENTS:
            assert agent in hierarchy_section, \
                f"Hierarchy must show {agent} under CEO"

    def test_hierarchy_is_flat_two_levels(self, claude_md):
        """Organization has exactly 2 levels: CEO and subordinates.
        No agent reports to another subordinate.
        """
        hierarchy_section = extract_section(claude_md, "指揮系統")
        assert hierarchy_section is not None
        # In the tree, subordinates should all be at the same indent level
        # They should all be directly under CEO, not nested
        lines = hierarchy_section.split("\n")
        agent_lines = [l for l in lines if any(a in l for a in SUBORDINATE_AGENTS)]
        # All agent lines should have the same indentation depth
        depths = set()
        for line in agent_lines:
            depth = len(line) - len(line.lstrip())
            depths.add(depth)
        assert len(depths) <= 1, \
            f"All subordinates must be at same hierarchy level, found depths: {depths}"


# ============================================================
# D.2 Upward Reporting Rules
# ============================================================

@pytest.mark.static
@pytest.mark.command_chain
class TestUpwardReporting:
    """Subordinates report UP to CEO. Never skip to shareholder."""

    def test_no_subordinate_reports_to_shareholder(self):
        """Every subordinate's forbidden list must include direct shareholder reporting."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            assert body is not None, f"Missing body for {agent}"
            # Check for the rule
            assert "株主に直接報告しない" in body or "株主に直接報告" in body, \
                f"{agent} must be forbidden from direct shareholder reporting"

    def test_ceo_is_the_only_shareholder_interface(self, claude_md):
        """Only CEO communicates with shareholder. This must be explicit."""
        assert "CEO経由" in claude_md or "CEOを経由" in claude_md, \
            "CLAUDE.md must state reporting goes through CEO"

    def test_reporting_direction_documented(self, claude_md):
        """CLAUDE.md must document that instructions go down, reports go up."""
        # Condensed CLAUDE.md uses arrow notation: 上→下, 下→上
        assert ("上→下" in claude_md or "上から下" in claude_md), \
            "CLAUDE.md must state 'instructions flow downward'"
        assert ("下→上" in claude_md or "下から上" in claude_md), \
            "CLAUDE.md must state 'reports flow upward'"

    def test_ceo_manual_references_shareholder_reporting(self, ceo_manual):
        """CEO manual must define how CEO reports to shareholder."""
        assert "株主" in ceo_manual, \
            "CEO manual must reference shareholder reporting duties"

    def test_each_agent_escalation_targets_ceo(self):
        """Every agent's escalation section must specify CEO as the target."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            assert body is not None
            escalation = extract_section(body, "エスカレーション")
            assert escalation is not None, \
                f"{agent} must have an escalation section"
            assert "CEO" in escalation, \
                f"{agent}'s escalation section must target CEO"


# ============================================================
# D.3 Downward Command Rules
# ============================================================

@pytest.mark.static
@pytest.mark.command_chain
class TestDownwardCommands:
    """CEO issues commands to subordinates. No subordinate commands another."""

    def test_only_ceo_can_spawn_agents(self):
        """Only CEO has the Task tool to spawn subordinate agents."""
        ceo_config = get_agent_config("ceo")
        assert ceo_config is not None
        ceo_tools = ceo_config.get("tools", [])
        has_task = any("Task(" in str(t) for t in ceo_tools)
        assert has_task, "CEO must have Task tool for spawning agents"

        # No subordinate has Task tool
        for agent in SUBORDINATE_AGENTS:
            config = get_agent_config(agent)
            if config is None:
                continue
            tools = config.get("tools", [])
            has_task = any("Task(" in str(t) for t in tools)
            assert not has_task, \
                f"{agent} must NOT have Task tool (only CEO can command)"

    def test_ceo_manual_defines_when_to_call_each_agent(self, ceo_manual):
        """CEO manual must specify WHEN to call each agent type."""
        assert "いつ呼ぶか" in ceo_manual or "エージェント呼び出し" in ceo_manual, \
            "CEO manual must define when to call each agent"

    def test_ceo_manual_defines_agent_dispatch_criteria(self, ceo_manual):
        """CEO manual must define which agent handles which type of task.
        (Moved from CLAUDE.md to ceo-manual.md during consolidation.)
        """
        assert "いつ呼ぶか" in ceo_manual or "エージェント呼び出し" in ceo_manual, \
            "CEO manual must have agent dispatch criteria"

    def test_ceo_is_not_commanded_by_subordinates(self, claude_md):
        """No subordinate can give instructions to CEO.
        This is implicit in the hierarchy but worth verifying.
        """
        hierarchy_rules = extract_section(claude_md, "指揮系統")
        assert hierarchy_rules is not None
        # The hierarchy shows CEO above all agents
        # Subordinates don't have CEO in their collaboration targets
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            if body is None:
                continue
            collab = extract_section(body, "部門間連携")
            if collab:
                # Subordinates should reference CEO only for escalation, not for commanding
                assert "CEOに指示" not in collab, \
                    f"{agent} must not be able to command CEO"


# ============================================================
# D.4 Lateral Collaboration Rules
# ============================================================

@pytest.mark.static
@pytest.mark.command_chain
class TestLateralCollaboration:
    """Subordinates can collaborate at work level, but not at decision level."""

    def test_lateral_collaboration_rules_defined(self, claude_md):
        """CLAUDE.md must define lateral collaboration rules."""
        assert "横連携" in claude_md or "部門長間" in claude_md, \
            "CLAUDE.md must define lateral collaboration rules"

    def test_work_level_collaboration_allowed(self, claude_md):
        """Work-level collaboration between subordinates must be allowed."""
        assert ("作業レベルの横連携は自由" in claude_md or
                "作業レベルの連携は自由" in claude_md or
                "直接連携OK" in claude_md), \
            "Work-level lateral collaboration must be explicitly allowed"

    def test_decision_level_requires_ceo(self, claude_md):
        """Decision-level actions between subordinates must require CEO."""
        assert "判断レベル" in claude_md and "CEO経由" in claude_md, \
            "Decision-level collaboration must go through CEO"

    def test_each_agent_defines_collaboration_partners(self):
        """Each agent must document who they collaborate with and how."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            assert body is not None
            collab = extract_section(body, "部門間連携")
            assert collab is not None, \
                f"{agent} must have a collaboration section"
            # Must mention at least one other agent
            other_agents = [a for a in SUBORDINATE_AGENTS if a != agent]
            found = [a for a in other_agents if a in collab]
            assert len(found) >= 1, \
                f"{agent} must document at least one collaboration partner"

    def test_writer_to_site_builder_handoff_defined(self):
        """Content flow: writer creates text → site-builder implements HTML.
        This is the most critical lateral collaboration.
        """
        writer_body = get_agent_body("writer")
        sb_body = get_agent_body("site-builder")
        assert writer_body is not None and sb_body is not None

        # Writer side: mentions site-builder
        writer_collab = extract_section(writer_body, "site-builder")
        assert writer_collab is not None, \
            "writer must document collaboration with site-builder"
        assert "文面" in writer_body and "HTML" in writer_body, \
            "Writer-SiteBuilder handoff must reference text→HTML flow"

        # Site-builder side: mentions writer
        sb_collab = extract_section(sb_body, "writer")
        assert sb_collab is not None, \
            "site-builder must document collaboration with writer"

    def test_analyst_to_pm_data_sharing_defined(self):
        """Data flow: analyst provides market data → PM uses for specs."""
        analyst_body = get_agent_body("analyst")
        pm_body = get_agent_body("product-manager")
        assert analyst_body is not None and pm_body is not None

        pm_collab = extract_section(pm_body, "analyst")
        assert pm_collab is not None, \
            "product-manager must document collaboration with analyst"

    def test_collaboration_sections_include_ceo_escalation_rule(self):
        """Each agent's collaboration section must reference CEOescalation."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            if body is None:
                continue
            collab = extract_section(body, "部門間連携")
            if collab is None:
                continue
            assert "CEO" in collab, \
                f"{agent}'s collaboration section must reference CEO for decision escalation"

    @pytest.mark.live
    def test_subordinate_refuses_strategic_lateral_decision(self):
        """[LIVE] When two subordinates try to make a strategic decision
        between themselves, they must escalate to CEO.

        Scenario: analyst and PM discuss pricing. PM tries to finalize ¥2,000.
        Expected: PM says "これはCEOに判断を仰ぐべきだ" or equivalent
        Forbidden: PM and analyst agree on price without CEO involvement
        """
        pytest.skip("Live test")

    @pytest.mark.live
    def test_subordinate_accepts_work_level_collaboration(self):
        """[LIVE] Subordinates should freely share work-level artifacts.

        Scenario: writer asks site-builder to implement a text change
        Expected: site-builder accepts and implements the change
        Forbidden: site-builder says "CEOに確認してから"
        """
        pytest.skip("Live test")


# ============================================================
# D.5 Actions Management Authority
# ============================================================

@pytest.mark.static
@pytest.mark.command_chain
class TestActionsAuthority:
    """Only CEO manages the action list. Subordinates propose, CEO decides."""

    def test_actions_update_rule_defined(self, status_md):
        """status.md must define who can update actions."""
        assert "CEOのみ" in status_md and "更新" in status_md, \
            "status.md must state only CEO updates actions"

    def test_subordinates_cannot_self_assign_actions(self):
        """Agent definitions must not claim authority to modify actions.
        Subordinates can propose actions but CEO adds them to the list.
        """
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            if body is None:
                continue
            # Check that agent doesn't claim to update actions directly
            assert "actions.mdを更新" not in body, \
                f"{agent} must not claim to update actions directly"
            assert "status.mdを更新" not in body or agent == "analyst", \
                f"{agent} must not claim to update status.md " \
                f"(exception: analyst updates financial data)"
