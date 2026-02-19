"""
Category K: Teams Integration Tests — THICK
==============================================
Tests that verify the Agent Teams system is correctly configured.

Agent Teams is the mechanism by which CEO coordinates multiple agents.
Each agent must be correctly configured for spawning, communication,
and shared context.

Configuration chain:
  CLAUDE.md (auto-injected to all)
    → .claude/agents/{name}.md YAML frontmatter (parsed by Task tool)
    → .claude/agents/{name}.md body (loaded by agent's LLM context)
    → .claude/agent-memory/{name}/MEMORY.md (auto-injected)
"""

import pytest
import re
from pathlib import Path
from conftest import (
    SUBORDINATE_AGENTS, ALL_AGENTS, EXPECTED_MODELS,
    BASE_DIR,
    get_agent_config, get_agent_body, get_agent_memory,
    read_file, parse_frontmatter, extract_section,
)


# ============================================================
# K.1 Agent File Validity
# ============================================================

@pytest.mark.static
@pytest.mark.teams
class TestAgentFileValidity:
    """Every agent file must be syntactically valid and complete."""

    def test_all_agent_files_exist(self):
        """Every expected agent must have a definition file."""
        for agent in ALL_AGENTS:
            path = BASE_DIR / f".claude/agents/{agent}.md"
            assert path.exists(), \
                f"Agent definition file missing: .claude/agents/{agent}.md"

    def test_all_agent_files_have_valid_frontmatter(self):
        """Every agent file must have parseable YAML frontmatter."""
        for agent in ALL_AGENTS:
            config = get_agent_config(agent)
            assert config is not None, \
                f"{agent}.md must have valid YAML frontmatter"
            assert isinstance(config, dict), \
                f"{agent}.md frontmatter must be a dict, got {type(config)}"

    def test_all_agents_have_name_field(self, all_agent_configs):
        """Every agent frontmatter must have a 'name' field matching filename."""
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            assert config is not None, f"Missing config for {agent}"
            name = config.get("name")
            assert name is not None, \
                f"{agent}.md must have 'name' field in frontmatter"
            assert name == agent, \
                f"{agent}.md name='{name}' doesn't match filename '{agent}'"

    def test_all_agents_have_description(self, all_agent_configs):
        """Every agent must have a description field."""
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            assert config is not None
            desc = config.get("description")
            assert desc is not None and len(desc) > 10, \
                f"{agent}.md must have a meaningful description"

    def test_all_agents_have_model_specified(self, all_agent_configs):
        """Every agent must specify which model to use."""
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            assert config is not None
            model = config.get("model")
            assert model is not None, \
                f"{agent}.md must specify model"
            assert model in ("opus", "sonnet", "haiku"), \
                f"{agent}.md has invalid model: {model}"

    def test_agent_models_match_org_chart(self, all_agent_configs):
        """Model assignments must match the organizational cost tier plan.
        CEO = opus (full capability), key roles = sonnet, support = haiku.
        """
        for agent, expected_model in EXPECTED_MODELS.items():
            config = all_agent_configs.get(agent)
            assert config is not None, f"Missing config for {agent}"
            actual = config.get("model")
            assert actual == expected_model, \
                f"{agent} model: expected={expected_model}, actual={actual}"

    def test_all_agents_have_memory_project(self, all_agent_configs):
        """Every agent must use project-scoped memory."""
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            assert config is not None
            memory = config.get("memory")
            assert memory == "project", \
                f"{agent}.md must have memory=project, got: {memory}"

    def test_all_agents_have_tools_list(self, all_agent_configs):
        """Every agent must have a tools list."""
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            assert config is not None
            tools = config.get("tools")
            assert tools is not None and isinstance(tools, list), \
                f"{agent}.md must have a tools list"
            assert len(tools) >= 1, \
                f"{agent}.md must have at least one tool"

    def test_subordinates_have_maxturns_limit(self, all_agent_configs):
        """Subordinate agents must have maxTurns to prevent runaway costs."""
        for agent in SUBORDINATE_AGENTS:
            config = all_agent_configs.get(agent)
            assert config is not None
            max_turns = config.get("maxTurns")
            assert max_turns is not None, \
                f"{agent}.md must specify maxTurns limit"
            assert isinstance(max_turns, int) and max_turns > 0, \
                f"{agent}.md maxTurns must be a positive integer, got: {max_turns}"
            assert max_turns <= 50, \
                f"{agent}.md maxTurns={max_turns} is too high (max recommended: 50)"


# ============================================================
# K.2 Memory System
# ============================================================

@pytest.mark.static
@pytest.mark.teams
class TestMemorySystem:
    """Every agent must have a MEMORY.md file with correct structure."""

    def test_all_agents_have_memory_files(self):
        """Every agent must have a MEMORY.md file."""
        for agent in ALL_AGENTS:
            path = BASE_DIR / f".claude/agent-memory/{agent}/MEMORY.md"
            assert path.exists(), \
                f"MEMORY.md missing for {agent}"

    def test_memory_files_under_200_lines(self):
        """MEMORY.md files must stay under 200 lines (truncation risk)."""
        for agent in ALL_AGENTS:
            mem = get_agent_memory(agent)
            if mem is None:
                continue
            lines = mem.split("\n")
            assert len(lines) <= 200, \
                f"{agent}/MEMORY.md has {len(lines)} lines (>200 = truncation risk)"

    def test_ceo_memory_has_key_sections(self):
        """CEO MEMORY.md must contain essential management information."""
        mem = get_agent_memory("ceo")
        assert mem is not None
        required = ["確定事項", "株主", "失敗と学び", "自戒"]
        for section in required:
            assert section in mem, \
                f"CEO MEMORY.md must have '{section}' section"

    def test_agent_memory_directories_match_agent_list(self):
        """Memory directories must match the agent list (no orphans, no missing)."""
        memory_dir = BASE_DIR / ".claude/agent-memory"
        if not memory_dir.exists():
            pytest.fail("agent-memory directory doesn't exist")

        actual_dirs = {d.name for d in memory_dir.iterdir() if d.is_dir()}
        expected_dirs = set(ALL_AGENTS)

        missing = expected_dirs - actual_dirs
        assert len(missing) == 0, \
            f"Missing memory directories: {missing}"

        # Orphan directories are a warning, not a failure
        orphans = actual_dirs - expected_dirs
        if orphans:
            import warnings
            warnings.warn(f"Orphan memory directories: {orphans}")


# ============================================================
# K.3 Context Injection Chain
# ============================================================

@pytest.mark.static
@pytest.mark.teams
class TestContextInjectionChain:
    """Verify the 3-layer context model works correctly.

    Layer 1: CLAUDE.md (auto-injected to ALL agents)
    Layer 2: MEMORY.md (auto-injected to owning agent)
    Layer 3: agents/*.md body (loaded into LLM context at spawn time)
    """

    def test_claude_md_exists_and_is_reasonable_size(self):
        """CLAUDE.md must exist and be concise (injected to every agent)."""
        content = read_file("CLAUDE.md")
        assert content is not None, "CLAUDE.md must exist"
        lines = content.split("\n")
        # CLAUDE.md was reduced from 348 to ~200 lines
        assert len(lines) <= 300, \
            f"CLAUDE.md is {len(lines)} lines — too large for universal injection"

    def test_agent_bodies_contain_startup_routine(self):
        """Each agent body must include a startup routine."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            assert body is not None
            assert "起動時ルーティン" in body or "起動" in body, \
                f"{agent}.md must define a startup routine"

    def test_agent_startup_references_memory_file(self):
        """Each agent's startup must include reading its own MEMORY.md."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            assert body is not None
            assert "MEMORY.md" in body or "メモリ" in body, \
                f"{agent}'s startup must reference MEMORY.md"

    def test_agent_startup_references_relevant_docs(self):
        """Each agent's startup must read relevant shared docs."""
        for agent in SUBORDINATE_AGENTS:
            body = get_agent_body(agent)
            assert body is not None
            startup = extract_section(body, "起動時ルーティン")
            if startup is None:
                continue
            # Every agent should read some shared document
            references_shared_doc = (
                "docs/" in startup or
                "state.json" in startup or
                "status.md" in startup or
                "plan.md" in startup or
                "actions.md" in startup or
                "design-rules" in startup
            )
            assert references_shared_doc, \
                f"{agent}'s startup must reference at least one shared document"

    def test_ceo_has_separate_detailed_manual(self):
        """CEO must have docs/ceo-manual.md for detailed procedures."""
        manual = read_file("docs/ceo-manual.md")
        assert manual is not None, \
            "CEO must have a detailed manual at docs/ceo-manual.md"
        assert len(manual) > 500, \
            "CEO manual must be substantial (>500 chars)"


# ============================================================
# K.4 Agent Spawning Integration
# ============================================================

@pytest.mark.static
@pytest.mark.teams
class TestAgentSpawningIntegration:
    """End-to-end verification of the spawning pipeline."""

    def test_ceo_task_tool_matches_available_agents(self):
        """CEO's Task() tool list must match available agent files."""
        ceo_config = get_agent_config("ceo")
        assert ceo_config is not None
        tools = ceo_config.get("tools", [])
        task_entry = [t for t in tools if isinstance(t, str) and "Task(" in t]
        assert len(task_entry) == 1, \
            "CEO must have exactly one Task() tool entry"

        # Extract agents from Task(a, b, c)
        agents_in_task = set(
            a.strip() for a in
            task_entry[0].replace("Task(", "").replace(")", "").split(",")
        )
        # Every agent in Task() must have a file
        for agent in agents_in_task:
            path = BASE_DIR / f".claude/agents/{agent}.md"
            assert path.exists(), \
                f"CEO Task tool references '{agent}' but no agent file exists"

        # Every subordinate agent must be in Task()
        missing = set(SUBORDINATE_AGENTS) - agents_in_task
        assert len(missing) == 0, \
            f"CEO Task tool missing agents: {missing}"

    def test_agent_count_matches_expected(self):
        """Number of agent files must match the expected agent list (8 total)."""
        agents_dir = BASE_DIR / ".claude/agents"
        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) == len(ALL_AGENTS), \
            f"Agent file count ({len(agent_files)}) != expected ({len(ALL_AGENTS)})"

    def test_no_orphan_agent_files(self, claude_md):
        """No agent files should exist that aren't in CLAUDE.md."""
        agents_dir = BASE_DIR / ".claude/agents"
        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            assert agent_name in ALL_AGENTS, \
                f"Orphan agent file: {agent_name}.md (not in org chart)"

    def test_each_agent_has_output_directory(self):
        """Agents that produce files must have their output directories."""
        output_dirs = {
            "writer": ["content/blog", "content/copy"],
            "x-manager": ["content/tweets"],
            "video-creator": ["content/videos"],
            "site-builder": ["site"],
            "analyst": ["docs/specs"],
            "legal": ["docs/legal"],
        }
        for agent, dirs in output_dirs.items():
            for d in dirs:
                path = BASE_DIR / d
                assert path.exists() or path.parent.exists(), \
                    f"{agent}'s output directory '{d}' should exist"


# ============================================================
# K.5 Teams Communication Rules
# ============================================================

@pytest.mark.static
@pytest.mark.teams
class TestTeamsCommunicationRules:
    """Rules about how agents communicate within the team."""

    def test_ceo_memory_mandates_teams_method(self):
        """CEO memory must mandate using TeamCreate method (not independent Tasks)."""
        mem = get_agent_memory("ceo")
        assert mem is not None
        assert "Teams" in mem or "TeamCreate" in mem, \
            "CEO memory must mandate Teams method"

    def test_teams_method_documented_in_ceo_memory(self):
        """CEO memory must document that independent Task spawning is forbidden."""
        mem = get_agent_memory("ceo")
        assert mem is not None
        assert "バラ投げ" in mem or "独立Task" in mem, \
            "CEO memory must record that independent Task spawning is forbidden"

    def test_agent_teams_method_documented(self):
        """Agent Teams method must be documented (in CEO memory or ceo-manual)."""
        ceo_mem = get_agent_memory("ceo")
        assert ceo_mem is not None
        assert "Teams" in ceo_mem or "TeamCreate" in ceo_mem, \
            "CEO memory must document the Teams coordination method"

    def test_ceo_has_teamcreate_tool(self):
        """CEO must have TeamCreate in tools list to use Teams method."""
        config = get_agent_config("ceo")
        assert config is not None
        tools = config.get("tools", [])
        tool_names = [t if isinstance(t, str) else str(t) for t in tools]
        assert "TeamCreate" in tool_names, \
            "CEO must have TeamCreate tool to coordinate multi-agent work"

    def test_ceo_has_sendmessage_tool(self):
        """CEO must have SendMessage in tools list for agent communication."""
        config = get_agent_config("ceo")
        assert config is not None
        tools = config.get("tools", [])
        tool_names = [t if isinstance(t, str) else str(t) for t in tools]
        assert "SendMessage" in tool_names, \
            "CEO must have SendMessage tool for agent communication"

    def test_ceo_has_task_management_tools(self):
        """CEO must have TaskCreate/TaskList/TaskUpdate for shared task list."""
        config = get_agent_config("ceo")
        assert config is not None
        tools = config.get("tools", [])
        tool_names = [t if isinstance(t, str) else str(t) for t in tools]
        required = ["TaskCreate", "TaskList", "TaskUpdate"]
        for tool in required:
            assert tool in tool_names, \
                f"CEO must have {tool} tool for shared task management"

    def test_ceo_manual_documents_teams_vs_task(self):
        """CEO manual must document when to use TeamCreate vs Task."""
        manual = read_file("docs/ceo-manual.md")
        assert manual is not None
        assert "TeamCreate" in manual, \
            "CEO manual must document TeamCreate usage"
        assert "バラ投げ" in manual or "禁止" in manual, \
            "CEO manual must document that bare Task spawning for multi-agent is forbidden"


# ============================================================
# K.6 Live Teams Tests
# ============================================================

@pytest.mark.live
@pytest.mark.teams
class TestLiveTeams:
    """Tests that verify Teams actually work at runtime."""

    def test_ceo_can_spawn_analyst(self):
        """[LIVE] CEO can successfully spawn analyst agent.

        Verification:
        - Task tool call succeeds
        - analyst reads its MEMORY.md (check for character keyword in response)
        - analyst acknowledges CEO's instruction
        """
        pytest.skip("Live test")

    def test_team_task_list_shared(self):
        """[LIVE] TeamCreate produces shared task list accessible by all members.

        Steps:
        1. CEO creates team with TeamCreate
        2. CEO creates task with TaskCreate
        3. Spawned agent can see the task via TaskList
        """
        pytest.skip("Live test")

    def test_agent_completes_task_and_marks_done(self):
        """[LIVE] Agent marks task completed after finishing work.

        Steps:
        1. CEO assigns task to agent
        2. Agent performs work
        3. Agent calls TaskUpdate(status="completed")
        4. CEO sees task as completed
        """
        pytest.skip("Live test")

    def test_multi_agent_coordination(self):
        """[LIVE] Multiple agents can work on related tasks.

        Scenario: writer creates content → site-builder implements HTML
        Steps:
        1. CEO creates team with writer + site-builder
        2. Writer creates LP text in content/copy/
        3. site-builder reads the text and implements in site/
        4. Both mark tasks completed
        """
        pytest.skip("Live test")

    def test_team_shutdown_graceful(self):
        """[LIVE] Team can be shut down gracefully.

        Steps:
        1. CEO sends shutdown_request to all agents
        2. Agents respond with shutdown_response
        3. TeamDelete cleans up team files
        """
        pytest.skip("Live test")
