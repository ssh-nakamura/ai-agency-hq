#!/usr/bin/env python3
"""
Test Catalog Generator
======================
Reads all test_*.py files in the tests/ directory, extracts every test class
and test method with their docstrings, categorizes them, identifies static vs
live tests, and generates a comprehensive HTML catalog.

Usage:
    python3 tests/generate_catalog.py
"""

import ast
import re
import textwrap
from pathlib import Path
from datetime import date
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# Configuration
# ============================================================

TESTS_DIR = Path(__file__).resolve().parent
BASE_DIR = TESTS_DIR.parent
OUTPUT_DIR = BASE_DIR / "reports"
TODAY = date.today().isoformat()
OUTPUT_FILE = OUTPUT_DIR / f"test-catalog-{TODAY}.html"

# Category mappings: filename stem -> (category_id, category_name, color)
CATEGORY_MAP = {
    "test_static": ("static", "Static Document Integrity", "#6366f1"),
    "test_role_boundaries": ("role_boundary", "Role Boundary Enforcement", "#ec4899"),
    "test_command_chain": ("command_chain", "Command Chain Hierarchy", "#f59e0b"),
    "test_escalation": ("escalation", "Escalation Flow", "#ef4444"),
    "test_financial": ("financial", "Financial Controls", "#10b981"),
    "test_teams": ("teams", "Teams Integration", "#3b82f6"),
}

# Priority assignment based on class/category keywords
PRIORITY_KEYWORDS = {
    "high": [
        "CEO", "Delegation", "Financial", "Budget", "Shareholder",
        "Legal", "L3", "L4", "Forbidden", "Hierarchy",
    ],
    "medium": [
        "Scope", "Tool", "Escalation", "Reporting", "Lateral",
        "Memory", "Context", "Spawning", "Communication",
    ],
    "low": [
        "Hygiene", "Directory", "Structure", "Consistency",
        "Completeness", "Validity", "Old", "Required",
    ],
}


# ============================================================
# Data Model
# ============================================================

@dataclass
class TestInfo:
    """Represents a single test method."""
    id: int = 0
    class_name: str = ""
    method_name: str = ""
    docstring: str = ""
    is_live: bool = False
    category_id: str = ""
    category_name: str = ""
    category_color: str = ""
    priority: str = "medium"
    # Parsed from live test docstrings
    scenario: str = ""
    expected: str = ""
    forbidden: str = ""
    is_parametrized: bool = False
    param_values: list = field(default_factory=list)


# ============================================================
# AST-based Test Extraction
# ============================================================

def determine_priority(class_name: str, method_name: str, docstring: str) -> str:
    """Determine test priority based on keywords in names and docstring."""
    combined = f"{class_name} {method_name} {docstring}"
    for priority, keywords in PRIORITY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined.lower():
                return priority
    return "medium"


def is_live_test(node: ast.FunctionDef, class_node: ast.ClassDef = None) -> bool:
    """Check if a test is a live test by examining decorators and body."""
    # Check method-level decorators
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute) and decorator.attr == "live":
            return True
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "live":
                return True

    # Check class-level decorators
    if class_node:
        for decorator in class_node.decorator_list:
            if isinstance(decorator, ast.Attribute) and decorator.attr == "live":
                return True
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "live":
                    return True

    # Check for pytest.skip("Live test") in body
    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Call):
            if isinstance(stmt.func, ast.Attribute) and stmt.func.attr == "skip":
                for arg in stmt.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        if "live" in arg.value.lower():
                            return True
    return False


def check_parametrize(node: ast.FunctionDef) -> tuple:
    """Check if a test method is parametrized, return (is_param, param_name, values)."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Attribute) and func.attr == "parametrize":
                if len(decorator.args) >= 2:
                    param_name = ""
                    values = []
                    if isinstance(decorator.args[0], ast.Constant):
                        param_name = decorator.args[0].value
                    # Try to extract values
                    val_node = decorator.args[1]
                    if isinstance(val_node, ast.Name):
                        # Reference to a class variable - we'll try to resolve later
                        return True, param_name, [f"<{val_node.id}>"]
                    elif isinstance(val_node, ast.List):
                        for elt in val_node.elts:
                            if isinstance(elt, ast.Constant):
                                values.append(str(elt.value))
                    return True, param_name, values
    return False, "", []


def resolve_class_variables(class_node: ast.ClassDef) -> dict:
    """Extract class-level variable assignments (for parametrize references)."""
    variables = {}
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    if isinstance(stmt.value, ast.List):
                        vals = []
                        for elt in stmt.value.elts:
                            if isinstance(elt, ast.Constant):
                                vals.append(str(elt.value))
                        variables[target.id] = vals
    return variables


def parse_live_docstring(docstring: str) -> tuple:
    """Parse scenario/expected/forbidden from live test docstrings."""
    scenario = ""
    expected = ""
    forbidden = ""

    if not docstring:
        return scenario, expected, forbidden

    lines = docstring.strip().split("\n")
    current_field = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Scenario:"):
            current_field = "scenario"
            scenario = stripped[len("Scenario:"):].strip()
        elif stripped.startswith("Expected:"):
            current_field = "expected"
            expected = stripped[len("Expected:"):].strip()
        elif stripped.startswith("Forbidden:"):
            current_field = "forbidden"
            forbidden = stripped[len("Forbidden:"):].strip()
        elif stripped.startswith("Verification:"):
            current_field = "expected"
            expected = stripped[len("Verification:"):].strip()
        elif stripped.startswith("Steps:"):
            current_field = "expected"
            expected = stripped[len("Steps:"):].strip()
        elif stripped.startswith("Estimated cost:"):
            continue
        elif current_field and stripped.startswith("-"):
            if current_field == "scenario":
                scenario += "\n" + stripped
            elif current_field == "expected":
                expected += "\n" + stripped
            elif current_field == "forbidden":
                forbidden += "\n" + stripped
        elif current_field and stripped and not stripped.startswith("["):
            if current_field == "scenario":
                scenario += " " + stripped
            elif current_field == "expected":
                expected += " " + stripped
            elif current_field == "forbidden":
                forbidden += " " + stripped

    return scenario.strip(), expected.strip(), forbidden.strip()


def extract_tests_from_file(filepath: Path) -> list:
    """Parse a test file and extract all test information."""
    stem = filepath.stem
    if stem not in CATEGORY_MAP:
        return []

    cat_id, cat_name, cat_color = CATEGORY_MAP[stem]

    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    tests = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            class_docstring = ast.get_docstring(node) or ""
            class_vars = resolve_class_variables(node)

            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    docstring = ast.get_docstring(item) or ""
                    live = is_live_test(item, node)
                    is_param, param_name, param_vals = check_parametrize(item)

                    # Resolve class variable references in parametrize
                    if is_param and param_vals and param_vals[0].startswith("<"):
                        var_name = param_vals[0][1:-1]
                        if var_name in class_vars:
                            param_vals = class_vars[var_name]

                    scenario, expected, forbidden = "", "", ""
                    if live:
                        scenario, expected, forbidden = parse_live_docstring(docstring)

                    priority = determine_priority(node.name, item.name, docstring)

                    info = TestInfo(
                        class_name=node.name,
                        method_name=item.name,
                        docstring=docstring,
                        is_live=live,
                        category_id=cat_id,
                        category_name=cat_name,
                        category_color=cat_color,
                        priority=priority,
                        scenario=scenario,
                        expected=expected,
                        forbidden=forbidden,
                        is_parametrized=is_param,
                        param_values=param_vals,
                    )
                    tests.append(info)

    return tests


# ============================================================
# HTML Generation
# ============================================================

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def first_line(docstring: str) -> str:
    """Extract the first meaningful line of a docstring."""
    if not docstring:
        return ""
    lines = docstring.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("[LIVE]"):
            return stripped
        elif stripped.startswith("[LIVE]"):
            return stripped[len("[LIVE]"):].strip()
    return ""


def generate_html(all_tests: list) -> str:
    """Generate the complete HTML catalog."""
    total = len(all_tests)
    static_count = sum(1 for t in all_tests if not t.is_live)
    live_count = sum(1 for t in all_tests if t.is_live)

    # Group by category
    categories = {}
    for t in all_tests:
        if t.category_id not in categories:
            categories[t.category_id] = {
                "name": t.category_name,
                "color": t.category_color,
                "tests": [],
            }
        categories[t.category_id]["tests"].append(t)

    cat_count = len(categories)

    # Count by priority
    high_count = sum(1 for t in all_tests if t.priority == "high")
    medium_count = sum(1 for t in all_tests if t.priority == "medium")
    low_count = sum(1 for t in all_tests if t.priority == "low")

    # Build HTML
    html_parts = []

    html_parts.append(f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Catalog - {TODAY}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #ffffff;
    color: #1e293b;
    line-height: 1.6;
  }}

  .container {{
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}

  header {{
    margin-bottom: 2.5rem;
  }}

  header h1 {{
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }}

  header p {{
    color: #64748b;
    font-size: 0.9rem;
  }}

  /* Summary Cards */
  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-bottom: 2.5rem;
  }}

  .summary-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }}

  .summary-card .value {{
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
  }}

  .summary-card .label {{
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  .summary-card.total .value {{ color: #0f172a; }}
  .summary-card.static .value {{ color: #3b82f6; }}
  .summary-card.live .value {{ color: #f97316; }}
  .summary-card.categories .value {{ color: #8b5cf6; }}
  .summary-card.high .value {{ color: #ef4444; }}

  /* Table of Contents */
  .toc {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }}

  .toc h2 {{
    font-size: 1rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  .toc-list {{
    list-style: none;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 0.5rem;
  }}

  .toc-list li {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}

  .toc-list a {{
    color: #3b82f6;
    text-decoration: none;
    font-size: 0.95rem;
    font-weight: 500;
  }}

  .toc-list a:hover {{
    text-decoration: underline;
  }}

  .toc-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
  }}

  .toc-count {{
    color: #94a3b8;
    font-size: 0.8rem;
    margin-left: auto;
  }}

  /* Category Sections */
  .category-section {{
    margin-bottom: 3rem;
  }}

  .category-header {{
    border-left: 4px solid #3b82f6;
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    background: #f8fafc;
    border-radius: 0 8px 8px 0;
  }}

  .category-header h2 {{
    font-size: 1.2rem;
    font-weight: 700;
    color: #0f172a;
  }}

  .category-header .cat-meta {{
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 0.15rem;
  }}

  /* Test Table */
  .test-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }}

  .test-table thead {{
    background: #f1f5f9;
  }}

  .test-table th {{
    text-align: left;
    padding: 0.6rem 0.75rem;
    font-weight: 600;
    color: #475569;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid #e2e8f0;
  }}

  .test-table td {{
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: top;
  }}

  .test-table tbody tr:hover {{
    background: #fafbfd;
  }}

  .test-table .id-col {{
    width: 50px;
    text-align: center;
    color: #94a3b8;
    font-weight: 600;
    font-size: 0.8rem;
  }}

  .test-table .name-col {{
    min-width: 200px;
  }}

  .test-table .desc-col {{
    min-width: 200px;
    color: #475569;
  }}

  .test-table .level-col {{
    width: 80px;
    text-align: center;
  }}

  .test-table .priority-col {{
    width: 80px;
    text-align: center;
  }}

  /* Badges */
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }}

  .badge-static {{
    background: #dbeafe;
    color: #1d4ed8;
  }}

  .badge-live {{
    background: #ffedd5;
    color: #c2410c;
  }}

  .badge-pass {{
    background: #dcfce7;
    color: #15803d;
  }}

  .badge-high {{
    background: #fee2e2;
    color: #b91c1c;
  }}

  .badge-medium {{
    background: #fef3c7;
    color: #92400e;
  }}

  .badge-low {{
    background: #e0e7ff;
    color: #3730a3;
  }}

  /* Test name styling */
  .test-name {{
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.8rem;
    color: #1e293b;
    word-break: break-all;
  }}

  .class-prefix {{
    color: #94a3b8;
    font-weight: 400;
  }}

  .param-tag {{
    display: inline-block;
    background: #f1f5f9;
    color: #64748b;
    font-size: 0.65rem;
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
    margin-left: 0.25rem;
    font-family: system-ui, sans-serif;
  }}

  /* Live test detail expansion */
  .live-detail {{
    margin-top: 0.5rem;
  }}

  .live-detail summary {{
    cursor: pointer;
    color: #f97316;
    font-size: 0.8rem;
    font-weight: 500;
    user-select: none;
    outline: none;
  }}

  .live-detail summary:hover {{
    color: #ea580c;
  }}

  .live-detail[open] summary {{
    margin-bottom: 0.4rem;
  }}

  .live-detail-content {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 0.8rem;
    line-height: 1.5;
  }}

  .live-detail-content .field-label {{
    font-weight: 600;
    color: #92400e;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }}

  .live-detail-content .field-value {{
    color: #78350f;
    margin-bottom: 0.4rem;
    padding-left: 0.5rem;
    white-space: pre-wrap;
  }}

  /* Footer */
  footer {{
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e2e8f0;
    text-align: center;
    color: #94a3b8;
    font-size: 0.8rem;
  }}

  /* Priority breakdown bar */
  .priority-bar {{
    display: flex;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
  }}

  .priority-bar .segment {{
    transition: width 0.3s;
  }}

  .priority-bar .segment-high {{ background: #ef4444; }}
  .priority-bar .segment-medium {{ background: #f59e0b; }}
  .priority-bar .segment-low {{ background: #6366f1; }}

  .priority-legend {{
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    margin-bottom: 2rem;
    font-size: 0.8rem;
    color: #64748b;
  }}

  .priority-legend span {{
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }}

  .legend-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }}
</style>
</head>
<body>
<div class="container">

<header>
  <h1>Test Catalog</h1>
  <p>Virtual AI Agency -- Organizational TDD Test Suite &middot; Generated {TODAY}</p>
</header>
""")

    # Summary cards
    html_parts.append(f"""
<div class="summary-grid">
  <div class="summary-card total">
    <div class="value">{total}</div>
    <div class="label">Total Tests</div>
  </div>
  <div class="summary-card static">
    <div class="value">{static_count}</div>
    <div class="label">Static</div>
  </div>
  <div class="summary-card live">
    <div class="value">{live_count}</div>
    <div class="label">Live Stubs</div>
  </div>
  <div class="summary-card categories">
    <div class="value">{cat_count}</div>
    <div class="label">Categories</div>
  </div>
  <div class="summary-card high">
    <div class="value">{high_count}</div>
    <div class="label">High Priority</div>
  </div>
</div>
""")

    # Priority bar
    if total > 0:
        high_pct = (high_count / total) * 100
        medium_pct = (medium_count / total) * 100
        low_pct = (low_count / total) * 100
        html_parts.append(f"""
<div class="priority-bar">
  <div class="segment segment-high" style="width: {high_pct:.1f}%"></div>
  <div class="segment segment-medium" style="width: {medium_pct:.1f}%"></div>
  <div class="segment segment-low" style="width: {low_pct:.1f}%"></div>
</div>
<div class="priority-legend">
  <span><span class="legend-dot" style="background:#ef4444"></span> High ({high_count})</span>
  <span><span class="legend-dot" style="background:#f59e0b"></span> Medium ({medium_count})</span>
  <span><span class="legend-dot" style="background:#6366f1"></span> Low ({low_count})</span>
</div>
""")

    # Table of Contents
    html_parts.append("""
<div class="toc">
  <h2>Table of Contents</h2>
  <ul class="toc-list">
""")
    for cat_id, cat_data in categories.items():
        count = len(cat_data["tests"])
        static_in_cat = sum(1 for t in cat_data["tests"] if not t.is_live)
        live_in_cat = sum(1 for t in cat_data["tests"] if t.is_live)
        html_parts.append(f"""    <li>
      <span class="toc-dot" style="background: {cat_data['color']}"></span>
      <a href="#cat-{cat_id}">{escape_html(cat_data['name'])}</a>
      <span class="toc-count">{count} tests ({static_in_cat}S / {live_in_cat}L)</span>
    </li>
""")
    html_parts.append("""  </ul>
</div>
""")

    # Category sections
    global_id = 0
    for cat_id, cat_data in categories.items():
        cat_tests = cat_data["tests"]
        static_in_cat = sum(1 for t in cat_tests if not t.is_live)
        live_in_cat = sum(1 for t in cat_tests if t.is_live)

        html_parts.append(f"""
<section class="category-section" id="cat-{cat_id}">
  <div class="category-header" style="border-left-color: {cat_data['color']}">
    <h2>{escape_html(cat_data['name'])}</h2>
    <div class="cat-meta">{len(cat_tests)} tests &middot; {static_in_cat} static &middot; {live_in_cat} live stubs</div>
  </div>

  <table class="test-table">
    <thead>
      <tr>
        <th class="id-col">ID</th>
        <th class="name-col">Test Name</th>
        <th class="desc-col">Description</th>
        <th class="level-col">Level</th>
        <th class="priority-col">Priority</th>
      </tr>
    </thead>
    <tbody>
""")
        for t in cat_tests:
            global_id += 1
            t.id = global_id

            # Level badge
            if t.is_live:
                level_badge = '<span class="badge badge-live">Live</span>'
            else:
                level_badge = '<span class="badge badge-static">Static</span>'

            # Priority badge
            priority_badge = f'<span class="badge badge-{t.priority}">{t.priority.capitalize()}</span>'

            # Test name with class prefix
            method_display = t.method_name
            class_display = t.class_name

            # Param tag
            param_html = ""
            if t.is_parametrized:
                count = len(t.param_values)
                if count > 0:
                    param_html = f' <span class="param-tag">x{count} params</span>'
                else:
                    param_html = ' <span class="param-tag">parametrized</span>'

            # Description
            desc = first_line(t.docstring)
            desc_html = escape_html(desc)

            # Live detail expansion
            live_detail_html = ""
            if t.is_live and (t.scenario or t.expected or t.forbidden):
                detail_parts = []
                if t.scenario:
                    detail_parts.append(
                        f'<div class="field-label">Scenario</div>'
                        f'<div class="field-value">{escape_html(t.scenario)}</div>'
                    )
                if t.expected:
                    detail_parts.append(
                        f'<div class="field-label">Expected</div>'
                        f'<div class="field-value">{escape_html(t.expected)}</div>'
                    )
                if t.forbidden:
                    detail_parts.append(
                        f'<div class="field-label">Forbidden</div>'
                        f'<div class="field-value">{escape_html(t.forbidden)}</div>'
                    )
                live_detail_html = f"""
              <details class="live-detail">
                <summary>View scenario details</summary>
                <div class="live-detail-content">
                  {"".join(detail_parts)}
                </div>
              </details>"""

            html_parts.append(f"""      <tr>
        <td class="id-col">{global_id}</td>
        <td class="name-col">
          <div class="test-name">
            <span class="class-prefix">{escape_html(class_display)}.</span>{escape_html(method_display)}{param_html}
          </div>
        </td>
        <td class="desc-col">{desc_html}{live_detail_html}</td>
        <td class="level-col">{level_badge}</td>
        <td class="priority-col">{priority_badge}</td>
      </tr>
""")

        html_parts.append("""    </tbody>
  </table>
</section>
""")

    # Footer
    html_parts.append(f"""
<footer>
  Generated by <strong>generate_catalog.py</strong> on {TODAY}
  &middot; Virtual AI Agency &middot; Organizational TDD
</footer>

</div>
</body>
</html>
""")

    return "".join(html_parts)


# ============================================================
# Main
# ============================================================

def main():
    """Main entry point."""
    # Collect all test files
    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    print(f"Found {len(test_files)} test files:")
    for f in test_files:
        print(f"  - {f.name}")

    # Extract tests
    all_tests = []
    for filepath in test_files:
        tests = extract_tests_from_file(filepath)
        all_tests.extend(tests)
        print(f"  {filepath.name}: {len(tests)} tests extracted")

    print(f"\nTotal tests: {len(all_tests)}")
    print(f"  Static: {sum(1 for t in all_tests if not t.is_live)}")
    print(f"  Live:   {sum(1 for t in all_tests if t.is_live)}")

    # Generate HTML
    html = generate_html(all_tests)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write output
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"\nCatalog written to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
