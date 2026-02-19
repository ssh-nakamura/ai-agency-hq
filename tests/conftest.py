"""
AI Agency HQ - Test Configuration
==================================
Shared fixtures, helpers, and constants for organizational TDD.

Design principle: Each test reads like a specification for how the organization
should behave. Tests verify the *system of constraints* works together.

Layers:
  - static: Config/file checks (instant, zero cost)
  - live:   Agent spawning & behavioral verification (future, token cost)
"""

import pytest
import re
import yaml
from pathlib import Path
from typing import Optional, Dict, List

# ============================================================
# Constants
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SUBORDINATE_AGENTS = [
    "analyst", "writer", "site-builder", "x-manager",
    "video-creator", "product-manager", "legal", "narrator",
]
ALL_AGENTS = ["ceo"] + SUBORDINATE_AGENTS

# Expected model assignments (cost tier enforcement)
EXPECTED_MODELS = {
    "ceo": "opus",
    "analyst": "sonnet",
    "writer": "sonnet",
    "site-builder": "sonnet",
    "product-manager": "sonnet",
    "narrator": "sonnet",
    "x-manager": "haiku",
    "video-creator": "haiku",
    "legal": "haiku",
}

# Agents CEO must be able to spawn via Task tool
CEO_SPAWNABLE_AGENTS = set(SUBORDINATE_AGENTS)

# Budget thresholds
MONTHLY_BUDGET_LIMIT = 55_000        # yen
CEO_DISCRETION_THRESHOLD = 30_000    # yen (above this = shareholder approval)

# Escalation level definitions
ESCALATION_LEVELS = ["L1", "L2", "L3", "L4"]

# Work-level lateral collaboration pairs (allowed)
ALLOWED_LATERAL_PAIRS = [
    ("writer", "site-builder"),      # content handoff
    ("analyst", "product-manager"),  # data sharing
    ("writer", "legal"),             # legal review
    ("analyst", "writer"),           # fact check
    ("x-manager", "writer"),         # content coordination
    ("video-creator", "writer"),     # content coordination
    ("video-creator", "x-manager"),  # social promotion
    ("product-manager", "legal"),    # legal risk check
    ("product-manager", "site-builder"),  # tech feasibility
    ("narrator", "writer"),              # content character conversion
    ("narrator", "video-creator"),       # video script character conversion
    ("narrator", "x-manager"),           # tweet character conversion
]


# ============================================================
# File Helpers
# ============================================================

def read_file(rel_path: str) -> Optional[str]:
    """Read a file relative to project root. Returns None if missing."""
    p = BASE_DIR / rel_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def parse_frontmatter(content: str) -> Optional[Dict]:
    """Parse YAML frontmatter from markdown content."""
    if not content or not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    yaml_text = content[3:end].strip()
    try:
        return yaml.safe_load(yaml_text)
    except Exception:
        return None


def extract_section(content: str, heading_text: str) -> Optional[str]:
    """Extract a markdown section by heading text (fuzzy match).

    Returns the content between the matched heading and the next
    heading of equal or higher level.
    """
    if not content:
        return None
    pattern = r"^(#{1,4})\s+.*" + re.escape(heading_text) + r".*$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    level = len(match.group(1))
    start = match.end()
    # Find next heading of same or higher level
    next_heading = re.search(
        rf"^#{{{1},{level}}}\s+", content[start:], re.MULTILINE
    )
    if next_heading:
        return content[start:start + next_heading.start()]
    return content[start:]


def extract_table_rows(section: str) -> List[List[str]]:
    """Extract markdown table rows as lists of cell values."""
    if not section:
        return []
    rows = []
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("|") and not re.match(r"\|[\s\-:]+\|", line):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if cells:
                rows.append(cells)
    return rows


def get_agent_config(agent_name: str) -> Optional[Dict]:
    """Get parsed YAML frontmatter for an agent."""
    content = read_file(f".claude/agents/{agent_name}.md")
    if not content:
        return None
    return parse_frontmatter(content)


def get_agent_body(agent_name: str) -> Optional[str]:
    """Get the markdown body (after frontmatter) of an agent file."""
    content = read_file(f".claude/agents/{agent_name}.md")
    if not content:
        return None
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:]
    return content


def get_agent_memory(agent_name: str) -> Optional[str]:
    """Read an agent's MEMORY.md file."""
    return read_file(f".claude/agent-memory/{agent_name}/MEMORY.md")


def content_contains_any(content: str, keywords: List[str]) -> List[str]:
    """Check which keywords appear in content. Returns found keywords."""
    if not content:
        return []
    return [kw for kw in keywords if kw in content]


def content_contains_all(content: str, keywords: List[str]) -> List[str]:
    """Check which keywords are MISSING from content. Returns missing ones."""
    if not content:
        return keywords
    return [kw for kw in keywords if kw not in content]


# ============================================================
# Pytest Configuration
# ============================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "static: Config/file verification (zero cost)")
    config.addinivalue_line("markers", "live: Requires agent spawning (token cost)")
    config.addinivalue_line("markers", "role_boundary: Category C - Role boundary tests")
    config.addinivalue_line("markers", "command_chain: Category D - Command chain tests")
    config.addinivalue_line("markers", "escalation: Category E - Escalation flow tests")
    config.addinivalue_line("markers", "teams: Category K - Teams integration tests")
    config.addinivalue_line("markers", "financial: Category I - Financial control tests")


def pytest_collection_modifyitems(config, items):
    """Auto-skip live tests unless --live flag is passed."""
    if not config.getoption("--live", default=False):
        skip_live = pytest.mark.skip(reason="Live test requires --live flag")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)


def pytest_addoption(parser):
    """Add --live option for running behavioral tests."""
    parser.addoption(
        "--live", action="store_true", default=False,
        help="Run live behavioral tests (requires agent spawning, costs tokens)"
    )


# ============================================================
# Session-scoped Fixtures
# ============================================================

@pytest.fixture(scope="session")
def claude_md():
    content = read_file("CLAUDE.md")
    assert content is not None, "CLAUDE.md must exist"
    return content


@pytest.fixture(scope="session")
def plan_md():
    content = read_file("docs/plan.md")
    assert content is not None, "docs/plan.md must exist"
    return content


@pytest.fixture(scope="session")
def status_md():
    content = read_file("docs/status.md")
    assert content is not None, "docs/status.md must exist"
    return content


@pytest.fixture(scope="session")
def ceo_manual():
    content = read_file("docs/ceo-manual.md")
    assert content is not None, "docs/ceo-manual.md must exist"
    return content


@pytest.fixture(scope="session")
def all_agent_configs():
    """All agent YAML configs keyed by agent name."""
    configs = {}
    for agent in ALL_AGENTS:
        config = get_agent_config(agent)
        if config:
            configs[agent] = config
    return configs


@pytest.fixture(scope="session")
def all_agent_bodies():
    """All agent markdown bodies keyed by agent name."""
    bodies = {}
    for agent in ALL_AGENTS:
        body = get_agent_body(agent)
        if body:
            bodies[agent] = body
    return bodies
