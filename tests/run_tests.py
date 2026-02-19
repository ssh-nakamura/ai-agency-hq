#!/usr/bin/env python3
"""
AI Agency HQ - Test Runner
============================
Runs the full test suite and generates an HTML report.

Usage:
  python3 tests/run_tests.py           # Run static tests only
  python3 tests/run_tests.py --live    # Include live behavioral tests
  python3 tests/run_tests.py -v        # Verbose output
  python3 tests/run_tests.py -k role   # Run only role boundary tests
"""

import subprocess
import sys
import os
import re
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = BASE_DIR / "tests"
REPORTS_DIR = BASE_DIR / "reports"


def run_pytest(extra_args=None):
    """Run pytest and capture results."""
    cmd = [
        sys.executable, "-m", "pytest",
        str(TESTS_DIR),
        "-v",
        "--tb=short",
        "-q",
    ]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
    )
    return result


def parse_pytest_output(output):
    """Parse pytest verbose output into structured data."""
    results = {
        "passed": [],
        "failed": [],
        "skipped": [],
        "errors": [],
    }

    for line in output.split("\n"):
        line = line.strip()
        if " PASSED" in line:
            results["passed"].append(line.replace(" PASSED", ""))
        elif " FAILED" in line:
            results["failed"].append(line.replace(" FAILED", ""))
        elif " SKIPPED" in line:
            # Extract skip reason
            results["skipped"].append(line.replace(" SKIPPED", ""))
        elif " ERROR" in line:
            results["errors"].append(line.replace(" ERROR", ""))

    # Parse summary line
    summary_match = re.search(
        r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?(?:, (\d+) error)?",
        output
    )
    if summary_match:
        results["summary"] = {
            "passed": int(summary_match.group(1) or 0),
            "failed": int(summary_match.group(2) or 0),
            "skipped": int(summary_match.group(3) or 0),
            "errors": int(summary_match.group(4) or 0),
        }
    else:
        results["summary"] = {
            "passed": len(results["passed"]),
            "failed": len(results["failed"]),
            "skipped": len(results["skipped"]),
            "errors": len(results["errors"]),
        }

    return results


def categorize_test(test_name):
    """Categorize a test by its module."""
    if "role_boundaries" in test_name:
        return "C: Role Boundary"
    elif "command_chain" in test_name:
        return "D: Command Chain"
    elif "escalation" in test_name:
        return "E: Escalation"
    elif "teams" in test_name:
        return "K: Teams"
    elif "financial" in test_name:
        return "I: Financial"
    elif "static" in test_name:
        return "S: Static"
    return "Other"


def generate_html_report(results, pytest_output, duration_sec):
    """Generate HTML test report."""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    s = results["summary"]
    total = s["passed"] + s["failed"] + s["skipped"] + s["errors"]
    pass_rate = (s["passed"] / max(total - s["skipped"], 1)) * 100

    # Categorize results
    categories = {}
    for test in results["passed"]:
        cat = categorize_test(test)
        categories.setdefault(cat, {"passed": [], "failed": [], "skipped": []})
        categories[cat]["passed"].append(test)
    for test in results["failed"]:
        cat = categorize_test(test)
        categories.setdefault(cat, {"passed": [], "failed": [], "skipped": []})
        categories[cat]["failed"].append(test)
    for test in results["skipped"]:
        cat = categorize_test(test)
        categories.setdefault(cat, {"passed": [], "failed": [], "skipped": []})
        categories[cat]["skipped"].append(test)

    # Generate category rows
    category_html = ""
    for cat_name in sorted(categories.keys()):
        cat = categories[cat_name]
        cp = len(cat["passed"])
        cf = len(cat["failed"])
        cs = len(cat["skipped"])
        ct = cp + cf + cs
        rate = (cp / max(ct - cs, 1)) * 100
        status_class = "pass" if cf == 0 else "fail"
        category_html += f"""
        <tr class="{status_class}">
          <td><strong>{cat_name}</strong></td>
          <td>{ct}</td>
          <td class="num-pass">{cp}</td>
          <td class="num-fail">{cf}</td>
          <td>{cs}</td>
          <td>{rate:.0f}%</td>
        </tr>"""

    # Generate failed test details
    failed_html = ""
    if results["failed"]:
        failed_html = "<h2>Failed Tests</h2><div class='failed-list'>"
        for test in results["failed"]:
            failed_html += f"<div class='failed-item'><code>{test}</code></div>"
        failed_html += "</div>"

        # Add failure details from pytest output
        if "FAILURES" in pytest_output:
            failure_text = pytest_output[pytest_output.find("FAILURES"):]
            # Escape HTML
            failure_text = failure_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            failed_html += f"<h3>Details</h3><pre class='failure-detail'>{failure_text}</pre>"

    status_emoji = "ALL PASS" if s["failed"] == 0 else f"{s['failed']} FAILURES"
    status_class = "status-pass" if s["failed"] == 0 else "status-fail"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Report - {date_str}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: system-ui, sans-serif; background: #f8f9fa; color: #1a1a2e; padding: 2rem; }}
  .container {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.5rem; }}
  h2 {{ font-size: 1.2rem; margin: 1.5rem 0 0.8rem; padding-bottom: 0.3rem; border-bottom: 2px solid #dee2e6; }}
  h3 {{ font-size: 1rem; margin: 1rem 0 0.5rem; }}
  .meta {{ color: #6c757d; margin-bottom: 1.5rem; font-size: 0.9rem; }}

  .summary-cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem; margin-bottom: 2rem;
  }}
  .card {{
    background: white; border-radius: 8px; padding: 1.2rem; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }}
  .card .num {{ font-size: 2rem; font-weight: 700; }}
  .card .label {{ font-size: 0.8rem; color: #6c757d; margin-top: 0.3rem; }}
  .card.total .num {{ color: #495057; }}
  .card.passed .num {{ color: #198754; }}
  .card.failed .num {{ color: #dc3545; }}
  .card.skipped .num {{ color: #6c757d; }}
  .card.rate .num {{ color: {("#198754" if s["failed"] == 0 else "#dc3545")}; }}

  .{status_class} {{
    display: inline-block; padding: 0.3rem 1rem; border-radius: 4px; font-weight: 700;
    background: {"#d4edda; color: #155724;" if s["failed"] == 0 else "#f8d7da; color: #721c24;"}
    margin-bottom: 1rem;
  }}

  table {{
    width: 100%; border-collapse: collapse; background: white;
    border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
  }}
  th {{ background: #f1f3f5; padding: 0.7rem 1rem; text-align: left; font-size: 0.85rem; }}
  td {{ padding: 0.6rem 1rem; border-top: 1px solid #e9ecef; font-size: 0.85rem; }}
  tr.pass td {{ background: #f8fff8; }}
  tr.fail td {{ background: #fff8f8; }}
  .num-pass {{ color: #198754; font-weight: 600; }}
  .num-fail {{ color: #dc3545; font-weight: 600; }}

  .failed-list {{ margin-bottom: 1rem; }}
  .failed-item {{
    background: #fff3f3; border-left: 3px solid #dc3545;
    padding: 0.5rem 1rem; margin: 0.3rem 0; font-size: 0.85rem;
  }}
  .failure-detail {{
    background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;
    padding: 1rem; font-size: 0.8rem; overflow-x: auto; max-height: 600px;
    overflow-y: auto; white-space: pre-wrap;
  }}
  .footer {{ margin-top: 2rem; font-size: 0.8rem; color: #adb5bd; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>AI Agency HQ - Test Report</h1>
  <div class="meta">{date_str} | Duration: {duration_sec:.1f}s | pytest {subprocess.run([sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True).stdout.strip().split()[-1] if True else ""}</div>

  <div class="{status_class}">{status_emoji}</div>

  <div class="summary-cards">
    <div class="card total"><div class="num">{total}</div><div class="label">Total</div></div>
    <div class="card passed"><div class="num">{s["passed"]}</div><div class="label">Passed</div></div>
    <div class="card failed"><div class="num">{s["failed"]}</div><div class="label">Failed</div></div>
    <div class="card skipped"><div class="num">{s["skipped"]}</div><div class="label">Skipped</div></div>
    <div class="card rate"><div class="num">{pass_rate:.0f}%</div><div class="label">Pass Rate</div></div>
  </div>

  <h2>Results by Category</h2>
  <table>
    <thead><tr><th>Category</th><th>Total</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Rate</th></tr></thead>
    <tbody>{category_html}</tbody>
  </table>

  {failed_html}

  <div class="footer">Generated by tests/run_tests.py</div>
</div>
</body>
</html>"""

    return html


def main():
    """Run tests and generate report."""
    import time

    # Pass through CLI args to pytest
    extra_args = sys.argv[1:]

    print("=" * 60)
    print("AI Agency HQ - Organizational Test Suite")
    print("=" * 60)
    print()

    start = time.time()
    result = run_pytest(extra_args)
    duration = time.time() - start

    # Print pytest output
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Parse and generate HTML report
    combined_output = result.stdout + result.stderr
    parsed = parse_pytest_output(combined_output)

    # Generate HTML
    html = generate_html_report(parsed, combined_output, duration)

    # Save report
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"test-report-{datetime.datetime.now().strftime('%Y-%m-%d')}.html"
    report_path.write_text(html, encoding="utf-8")

    print()
    print("=" * 60)
    s = parsed["summary"]
    print(f"Results: {s['passed']} passed, {s['failed']} failed, "
          f"{s['skipped']} skipped ({duration:.1f}s)")
    print(f"Report: {report_path}")
    print("=" * 60)

    # Auto-open on macOS
    if sys.platform == "darwin":
        os.system(f'open "{report_path}"')

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
