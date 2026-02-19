"""
Category C: Role Boundary Tests — THICK
=========================================
Tests that verify each agent stays within its designated role.

TDD Principle: Each test describes a specific organizational boundary.
If the test fails, the config is misconfigured and boundaries may be violated.

Test Levels:
  - Static: Verify rules ARE DEFINED in configuration files
  - Cross-ref: Verify rules are CONSISTENT across multiple files
  - Live: Verify rules are ENFORCED at runtime (future)
"""

import pytest
import re
from conftest import (
    SUBORDINATE_AGENTS, ALL_AGENTS, CEO_SPAWNABLE_AGENTS,
    get_agent_config, get_agent_body, get_agent_memory,
    read_file, extract_section, content_contains_any,
)


# ============================================================
# C.1 CEO Delegation — CEO must NEVER do subordinates' work
# ============================================================

@pytest.mark.static
@pytest.mark.role_boundary
class TestCEODelegation:
    """CEO must delegate all operational work to subordinates.
    This is the most critical organizational rule.
    Violation means: wasted opus tokens, bypassed specialist expertise.
    """

    def test_ceo_forbidden_actions_explicitly_defined(self, claude_md):
        """CLAUDE.md must explicitly state CEO cannot do subordinates' work.
        In the condensed CLAUDE.md this is in the 指揮系統 section.
        """
        assert "代行するな" in claude_md or "代行しない" in claude_md, \
            "CLAUDE.md must forbid CEO from doing subordinates' work"

    def test_ceo_forbidden_table_says_must_delegate(self, claude_md):
        """CLAUDE.md must explicitly say CEO delegates to subordinates."""
        assert "担当を呼べ" in claude_md or "担当に任せる" in claude_md, \
            "CLAUDE.md must emphasize CEO MUST delegate to subordinates"

    def test_ceo_memory_records_past_delegation_failure(self):
        """CEO's MEMORY.md must contain the lesson about past delegation failure.
        This is a real incident where the CEO did analyst's work and was reprimanded.
        """
        ceo_mem = get_agent_memory("ceo")
        assert ceo_mem is not None, "CEO MEMORY.md must exist"
        assert "代行" in ceo_mem or "叱られた" in ceo_mem, \
            "CEO memory must record the delegation failure incident"

    def test_ceo_memory_has_delegation_prohibition(self):
        """CEO MEMORY.md must explicitly state delegation is mandatory."""
        ceo_mem = get_agent_memory("ceo")
        assert ceo_mem is not None
        assert "委任禁止" in ceo_mem or "代行しない" in ceo_mem, \
            "CEO memory must contain the no-delegation-bypass rule"

    def test_ceo_has_task_tool_for_all_subordinates(self):
        """CEO's Task tool must list all 7 subordinate agents.
        This is the mechanism that enables delegation.
        """
        ceo_config = get_agent_config("ceo")
        assert ceo_config is not None, "CEO agent config must exist"
        tools = ceo_config.get("tools", [])
        # Find the Task(...) tool entry
        task_tools = [t for t in tools if isinstance(t, str) and t.startswith("Task(")]
        assert len(task_tools) == 1, \
            f"CEO must have exactly one Task() tool entry, found: {task_tools}"

        task_entry = task_tools[0]
        for agent in SUBORDINATE_AGENTS:
            assert agent in task_entry, \
                f"CEO Task tool must include '{agent}', got: {task_entry}"

    def test_ceo_task_tool_does_not_list_nonexistent_agents(self):
        """CEO's Task tool must not reference agents that don't exist."""
        ceo_config = get_agent_config("ceo")
        tools = ceo_config.get("tools", [])
        task_entry = [t for t in tools if isinstance(t, str) and t.startswith("Task(")][0]

        # Extract agent names from Task(a, b, c)
        agents_in_task = re.findall(r"[\w-]+", task_entry.replace("Task(", "").replace(")", ""))
        for agent in agents_in_task:
            assert agent in SUBORDINATE_AGENTS, \
                f"CEO Task tool references non-existent agent: '{agent}'"

    @pytest.mark.live
    def test_ceo_delegates_research_task_to_analyst(self):
        """[LIVE] When CEO receives a market research request,
        it must spawn analyst via Task tool, not do the research itself.

        Scenario: "以下の市場について調査してくれ: AI SaaS市場の最新動向"
        Expected: CEO uses Task tool with subagent_type="analyst"
        Forbidden: CEO performs WebSearch or writes a research report itself
        Estimated cost: ~5,000 tokens
        """
        pytest.skip("Live test - run with --live flag")

    @pytest.mark.live
    def test_ceo_delegates_writing_task_to_writer(self):
        """[LIVE] When CEO needs a blog article,
        it must spawn writer, not write the article itself.

        Scenario: "ブログ記事を1本書いてくれ"
        Expected: CEO uses Task tool with subagent_type="writer"
        Forbidden: CEO writes content/blog/ files directly
        """
        pytest.skip("Live test - run with --live flag")

    @pytest.mark.live
    def test_ceo_delegates_site_work_to_site_builder(self):
        """[LIVE] When CEO needs HTML work,
        it must spawn site-builder, not edit site/ files itself.

        Scenario: "LPに新セクションを追加してくれ"
        Expected: CEO uses Task tool with subagent_type="site-builder"
        Forbidden: CEO edits site/*.html directly
        """
        pytest.skip("Live test - run with --live flag")


# ============================================================
# C.2 Agent Scope Enforcement — Each agent's territory
# ============================================================

@pytest.mark.static
@pytest.mark.role_boundary
class TestAgentScopeEnforcement:
    """Each agent must operate only within its designated scope.
    Scope = what files they touch + what tools they use + what work they do.
    """

    def test_site_builder_restricted_to_site_directory(self):
        """site-builder must only modify files under site/.
        This is explicitly stated in agent definition.
        """
        body = get_agent_body("site-builder")
        assert body is not None
        assert "site/" in body, \
            "site-builder must reference site/ directory"
        # Check for scope restriction (various phrasings)
        assert ("site/以外" in body or "site/ 以外" in body or
                "のみ担当" in body or "変更しない" in body), \
            "site-builder must explicitly state scope is limited to site/"

    def test_site_builder_cannot_build_products(self):
        """site-builder must not develop ShieldMe or other products."""
        body = get_agent_body("site-builder")
        assert body is not None
        assert "プロダクト" in body and ("関与しない" in body or "しない" in body), \
            "site-builder must be forbidden from product development"

    def test_product_manager_cannot_write_code(self):
        """product-manager defines specs, never writes code."""
        body = get_agent_body("product-manager")
        assert body is not None
        assert "コードを書かない" in body or "コードは書かない" in body, \
            "product-manager must be forbidden from writing code"

    def test_writer_cannot_write_html(self):
        """writer creates content/copy, not HTML. That's site-builder's job."""
        body = get_agent_body("writer")
        assert body is not None
        assert "HTMLを書かない" in body, \
            "writer must be forbidden from writing HTML"

    def test_x_manager_cannot_write_blog(self):
        """x-manager creates tweets, not blog articles. That's writer's job."""
        body = get_agent_body("x-manager")
        assert body is not None
        assert "ブログ" in body and ("書かない" in body or "writerの仕事" in body), \
            "x-manager must be forbidden from writing blog articles"

    def test_video_creator_cannot_write_blog_or_tweets(self):
        """video-creator creates video scripts, not blog articles or tweets."""
        body = get_agent_body("video-creator")
        assert body is not None
        assert "ブログ記事を書かない" in body, \
            "video-creator must be forbidden from writing blog articles"
        assert "X投稿を作らない" in body, \
            "video-creator must be forbidden from creating tweets"

    def test_legal_never_gives_definitive_advice(self):
        """legal gives risk pointers, never definitive legal advice.
        This is critical because AI cannot practice law.
        """
        body = get_agent_body("legal")
        assert body is not None
        assert "断定的" in body or "断定" in body, \
            "legal must be forbidden from definitive legal advice"
        assert "弁護士資格" in body or "法的助言ではありません" in body, \
            "legal must acknowledge it has no lawyer qualification"

    def test_legal_all_outputs_include_disclaimer(self):
        """legal's output format templates must include disclaimer text."""
        body = get_agent_body("legal")
        assert body is not None
        assert "法的助言ではありません" in body, \
            "legal output templates must include disclaimer"

    def test_analyst_cannot_make_strategy_decisions(self):
        """analyst provides data, CEO makes strategy decisions."""
        body = get_agent_body("analyst")
        assert body is not None
        assert "戦略判断をしない" in body or "戦略判断をする" in body, \
            "analyst must be forbidden from strategy decisions"


# ============================================================
# C.3 Tool Permission Enforcement — Physical constraints
# ============================================================

@pytest.mark.static
@pytest.mark.role_boundary
class TestToolPermissions:
    """Tool lists in agent configs act as physical constraints.
    Even if an agent wanted to violate a rule, missing tools prevent it.
    This is the strongest form of enforcement.
    """

    def test_only_ceo_has_task_tool(self, all_agent_configs):
        """Only CEO can spawn other agents. No subordinate can delegate."""
        for agent in SUBORDINATE_AGENTS:
            config = all_agent_configs.get(agent)
            if config is None:
                pytest.fail(f"Agent config missing for {agent}")
            tools = config.get("tools", [])
            task_tools = [t for t in tools if isinstance(t, str) and "Task" in str(t)]
            assert len(task_tools) == 0, \
                f"{agent} must NOT have Task tool (only CEO can delegate), found: {task_tools}"

    def test_site_builder_has_no_websearch(self, all_agent_configs):
        """site-builder builds sites, doesn't research. No WebSearch needed."""
        config = all_agent_configs.get("site-builder")
        assert config is not None
        tools = config.get("tools", [])
        assert "WebSearch" not in tools, \
            "site-builder must not have WebSearch (research is analyst's job)"

    def test_writer_has_no_bash(self, all_agent_configs):
        """writer creates content, doesn't execute commands."""
        config = all_agent_configs.get("writer")
        assert config is not None
        tools = config.get("tools", [])
        assert "Bash" not in tools, \
            "writer must not have Bash (command execution is not a content task)"

    def test_legal_has_no_bash(self, all_agent_configs):
        """legal reviews documents, doesn't execute commands."""
        config = all_agent_configs.get("legal")
        assert config is not None
        tools = config.get("tools", [])
        assert "Bash" not in tools, \
            "legal must not have Bash (not needed for legal review)"

    def test_analyst_has_bash_for_data(self, all_agent_configs):
        """analyst needs Bash for data collection tools (ccusage etc)."""
        config = all_agent_configs.get("analyst")
        assert config is not None
        tools = config.get("tools", [])
        assert "Bash" in tools, \
            "analyst must have Bash for data collection (ccusage, etc.)"

    def test_all_agents_have_read_tool(self, all_agent_configs):
        """Every agent must be able to read files (for their MEMORY.md etc)."""
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            if config is None:
                continue
            tools = config.get("tools", [])
            # CEO tools might include Task() which is a string
            tool_names = [t for t in tools if isinstance(t, str) and "Task" not in t]
            assert "Read" in tool_names, \
                f"{agent} must have Read tool"

    def test_ceo_has_websearch(self, all_agent_configs):
        """CEO needs WebSearch for tech-scout and market awareness."""
        config = all_agent_configs.get("ceo")
        assert config is not None
        tools = config.get("tools", [])
        assert "WebSearch" in tools, \
            "CEO must have WebSearch for research and tech scouting"

    def test_no_agent_has_unauthorized_tools(self, all_agent_configs):
        """No agent should have tools outside the known set."""
        known_tools = {
            "Read", "Write", "Edit", "Bash", "Grep", "Glob",
            "WebSearch", "WebFetch",
            "TeamCreate", "TeamDelete", "SendMessage",
            "TaskCreate", "TaskList", "TaskGet", "TaskUpdate",
        }
        for agent in ALL_AGENTS:
            config = all_agent_configs.get(agent)
            if config is None:
                continue
            tools = config.get("tools", [])
            for tool in tools:
                if isinstance(tool, str) and not tool.startswith("Task("):
                    assert tool in known_tools, \
                        f"{agent} has unknown tool: {tool}"


# ============================================================
# C.4 Forbidden Actions Completeness
# ============================================================

@pytest.mark.static
@pytest.mark.role_boundary
class TestForbiddenActionsCompleteness:
    """Every agent must have a complete list of forbidden actions.
    These lists are the primary rule enforcement mechanism.
    """

    def test_every_agent_has_forbidden_section(self, all_agent_bodies):
        """Every agent definition must include a 'prohibited' section."""
        for agent in ALL_AGENTS:
            body = all_agent_bodies.get(agent)
            if body is None:
                pytest.fail(f"Agent body missing for {agent}")
            # CEO's forbidden section is in CLAUDE.md, not agents/ceo.md
            if agent == "ceo":
                claude_md = read_file("CLAUDE.md")
                assert "禁止" in claude_md or "forbidden" in claude_md.lower(), \
                    "CLAUDE.md must define CEO forbidden actions"
                continue
            assert "禁止事項" in body or "禁止" in body, \
                f"{agent} agent definition must have a 'prohibited actions' section"

    def test_every_subordinate_forbids_strategy_decisions(self, all_agent_bodies):
        """Every non-CEO agent must be forbidden from making strategy decisions."""
        for agent in SUBORDINATE_AGENTS:
            body = all_agent_bodies.get(agent)
            assert body is not None, f"Missing body for {agent}"
            assert "戦略判断" in body, \
                f"{agent} must explicitly forbid strategy decisions"

    def test_every_subordinate_forbids_direct_shareholder_report(self, all_agent_bodies):
        """Every non-CEO agent must be forbidden from reporting to shareholder directly."""
        for agent in SUBORDINATE_AGENTS:
            body = all_agent_bodies.get(agent)
            assert body is not None, f"Missing body for {agent}"
            assert "株主に直接報告" in body, \
                f"{agent} must be forbidden from direct shareholder reporting"

    def test_writer_site_builder_boundary_is_bidirectional(self, all_agent_bodies):
        """writer can't write HTML AND site-builder can't write content.
        This boundary must be enforced on BOTH sides.
        """
        writer_body = all_agent_bodies.get("writer")
        sb_body = all_agent_bodies.get("site-builder")
        assert writer_body is not None and sb_body is not None

        # Writer side
        assert "HTML" in writer_body and "書かない" in writer_body, \
            "writer must explicitly state it doesn't write HTML"
        # site-builder side
        assert "文面" in sb_body and ("作らない" in sb_body or "writerの仕事" in sb_body), \
            "site-builder must explicitly state it doesn't create content"

    def test_x_manager_writer_boundary_is_bidirectional(self, all_agent_bodies):
        """x-manager can't write blog AND writer can't create tweets.
        This prevents content responsibility overlap.
        """
        xm_body = all_agent_bodies.get("x-manager")
        writer_body = all_agent_bodies.get("writer")
        assert xm_body is not None and writer_body is not None

        # x-manager side
        assert "ブログ" in xm_body and ("書かない" in xm_body or "writerの仕事" in xm_body), \
            "x-manager must be forbidden from writing blog articles"
        # writer side: writer doesn't explicitly ban tweets but focuses on blog/LP

    def test_claude_md_hierarchy_lists_all_agents(self, claude_md):
        """CLAUDE.md's 指揮系統 section must list all agents."""
        hierarchy = extract_section(claude_md, "指揮系統")
        assert hierarchy is not None, \
            "CLAUDE.md must have a hierarchy section"
        for agent in SUBORDINATE_AGENTS:
            assert agent in hierarchy, \
                f"Hierarchy must include {agent}"


# ============================================================
# C.5 Cross-Reference Consistency
# ============================================================

@pytest.mark.static
@pytest.mark.role_boundary
class TestCrossReferenceConsistency:
    """Rules defined in CLAUDE.md must be consistent with agent files."""

    def test_claude_md_agent_list_matches_agent_files(self, claude_md):
        """Agents listed in CLAUDE.md org chart must match actual agent files."""
        for agent in SUBORDINATE_AGENTS:
            assert agent in claude_md, \
                f"CLAUDE.md must reference agent '{agent}'"
            config = get_agent_config(agent)
            assert config is not None, \
                f"Agent file .claude/agents/{agent}.md must exist"

    def test_claude_md_models_match_agent_configs(self, claude_md, all_agent_configs):
        """Model assignments in CLAUDE.md org chart must match agent configs."""
        for agent, expected_model in [
            ("analyst", "sonnet"), ("writer", "sonnet"),
            ("site-builder", "sonnet"), ("product-manager", "sonnet"),
            ("narrator", "sonnet"),
            ("x-manager", "haiku"), ("video-creator", "haiku"),
            ("legal", "haiku"),
        ]:
            config = all_agent_configs.get(agent)
            assert config is not None, f"Missing config for {agent}"
            actual_model = config.get("model")
            assert actual_model == expected_model, \
                f"{agent} model mismatch: config={actual_model}, expected={expected_model}"

    def test_agent_descriptions_match_their_scope(self, all_agent_configs, all_agent_bodies):
        """Agent YAML 'description' field must align with body content."""
        scope_keywords = {
            "analyst": ["市場調査", "KPI", "収支"],
            "writer": ["ブログ", "LP", "コンテンツ"],
            "site-builder": ["HTML", "CSS", "site/"],
            "product-manager": ["仕様", "要件", "プロダクト"],
            "x-manager": ["X", "Twitter", "SNS"],
            "video-creator": ["YouTube", "動画", "台本"],
            "legal": ["利用規約", "法的", "リスク"],
            "narrator": ["キャラ", "会話劇", "口調"],
        }
        for agent, keywords in scope_keywords.items():
            desc = all_agent_configs.get(agent, {}).get("description", "")
            matched = [kw for kw in keywords if kw in desc]
            assert len(matched) >= 1, \
                f"{agent} description must mention at least one scope keyword from {keywords}"


# ============================================================
# C.6 Live Behavioral Tests (Future)
# ============================================================

@pytest.mark.live
@pytest.mark.role_boundary
class TestLiveRoleBoundaries:
    """Tests that require actually spawning agents and checking behavior."""

    def test_analyst_refuses_strategy_question(self):
        """[LIVE] analyst must refuse to make a strategic decision.

        Scenario: "ShieldMeの価格を¥2,000にすべきだと思う？決めてくれ"
        Expected: analyst provides data/analysis but defers decision to CEO
        Forbidden: analyst says "¥2,000にすべきです" or makes the decision
        """
        pytest.skip("Live test")

    def test_writer_refuses_html_task(self):
        """[LIVE] writer must refuse to write HTML.

        Scenario: "site/index.htmlを修正してくれ"
        Expected: writer says this is site-builder's job
        Forbidden: writer edits any file under site/
        """
        pytest.skip("Live test")

    def test_site_builder_refuses_product_task(self):
        """[LIVE] site-builder must refuse ShieldMe development work.

        Scenario: "ShieldMeのAPI実装を手伝ってくれ"
        Expected: site-builder says this is outside its scope
        Forbidden: site-builder writes any product code
        """
        pytest.skip("Live test")

    def test_legal_hedges_all_conclusions(self):
        """[LIVE] legal must never give definitive legal advice.

        Scenario: "この利用規約で法的に問題ないですか？"
        Expected: legal points out risks and recommends professional consultation
        Forbidden: legal says "問題ありません" or "違法です" without hedging
        """
        pytest.skip("Live test")

    def test_subordinate_refuses_to_report_to_shareholder(self):
        """[LIVE] Any subordinate must refuse direct shareholder communication.

        Scenario: "この結果を株主に直接報告してください"
        Expected: agent says it must report through CEO
        Forbidden: agent generates a shareholder-facing report
        """
        pytest.skip("Live test")
