#!/usr/bin/env python3
"""
AI Agency HQ - Scenario Test Runner v3 (Production-matched)
============================================================
End-to-end behavioral tests using the same agent definitions as production:
  - Uses `--agent <name>` for ALL agents (including CEO)
  - Uses each agent's defined model (from .claude/agents/*.md)
  - Captures tool calls via stream-json for dual verification
  - Separates main agent tools from sub-agent (delegated) tools

Usage:
  python3 tests/run_scenarios.py                    # Run all
  python3 tests/run_scenarios.py --category C       # Category C only
  python3 tests/run_scenarios.py --id SC-C01        # Single scenario
  python3 tests/run_scenarios.py --dry-run           # Preview only
  python3 tests/run_scenarios.py --priority critical # Critical only
"""

import subprocess
import sys
import os
import json
import time
import datetime
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenarios import SCENARIOS, AGENTS

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"

# Tools agents typically call during startup (reading MEMORY.md, docs, etc.)
# These are NOT counted as "forbidden" unless explicitly listed.
STARTUP_TOOLS = {"Read", "Glob", "Grep"}


# ============================================================
# Stream-JSON Parsing
# ============================================================

def parse_stream_json(raw_output: str) -> dict:
    """Parse stream-json output from claude -p --verbose.

    Separates the main agent's direct tool calls from sub-agent tool calls.
    Rule: After a Task tool_use is seen, subsequent tool calls are from
    the sub-agent (delegated), not from the main agent.
    """
    direct_tool_calls = []
    delegated_tool_calls = []
    text_parts = []
    total_cost = 0.0
    num_turns = 0
    in_delegation = False

    for line in raw_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type")

        if etype == "assistant":
            msg = event.get("message", {})
            content = msg.get("content", [])
            for block in content:
                if block.get("type") == "tool_use":
                    tc = {
                        "name": block.get("name", ""),
                        "input": block.get("input", {}),
                    }
                    if in_delegation:
                        delegated_tool_calls.append(tc)
                    else:
                        direct_tool_calls.append(tc)
                        if tc["name"] == "Task":
                            in_delegation = True
                elif block.get("type") == "text":
                    if not in_delegation:
                        text_parts.append(block.get("text", ""))

        elif etype == "result":
            total_cost = event.get("total_cost_usd", 0.0)
            num_turns = event.get("num_turns", 0)
            result_text = event.get("result", "")
            if result_text:
                text_parts.append(result_text)

    return {
        "direct_tool_calls": direct_tool_calls,
        "delegated_tool_calls": delegated_tool_calls,
        "all_tool_calls": direct_tool_calls + delegated_tool_calls,
        "text_response": "\n".join(text_parts).strip(),
        "total_cost_usd": total_cost,
        "num_turns": num_turns,
    }


# ============================================================
# Scenario Execution
# ============================================================

def run_single_scenario(scenario: dict, timeout: int = 180) -> dict:
    """Run a single scenario via claude -p --agent with stream-json output.

    Uses the same --agent flag and model as production.
    Verifies BOTH text keywords AND actual tool calls.
    """
    agent = scenario["agent_context"]
    prompt = scenario["prompt"]
    max_turns = scenario.get("max_turns", 3)

    # Resolve model from agent definition (production-matched)
    agent_meta = AGENTS.get(agent, {})
    model = agent_meta.get("model", "sonnet")

    # Text checks
    expected_kw = scenario.get("expected_any", [])
    forbidden_kw = scenario.get("forbidden_any", [])

    # Tool checks
    expected_tools = scenario.get("expected_tools", [])
    forbidden_tools = scenario.get("forbidden_tools", [])
    expected_tool_args = scenario.get("expected_tool_args", {})

    result = {
        "id": scenario["id"],
        "name": scenario["name"],
        "category": scenario["category"],
        "priority": scenario["priority"],
        "agent": agent,
        "model": model,
        "prompt": prompt,
        "pass_criteria": scenario.get("pass_criteria", ""),
        "max_turns": max_turns,
        # Text results
        "response": "",
        "expected_kw_found": [],
        "expected_kw_missing": [],
        "forbidden_kw_found": [],
        # Tool results
        "tool_calls": [],
        "tool_names": [],
        "direct_tool_names": [],
        "expected_tools_found": [],
        "expected_tools_missing": [],
        "forbidden_tools_found": [],
        "expected_args_found": [],
        "expected_args_missing": [],
        # Overall
        "passed": False,
        "text_passed": False,
        "tools_passed": False,
        "duration_sec": 0.0,
        "cost_usd": 0.0,
        "num_turns": 0,
        "error": None,
    }

    start = time.time()

    # Unset CLAUDECODE to allow nested invocation
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    # Build command — production-matched: --agent + agent's own model
    budget = scenario.get("budget") or ("0.25" if "Task" in expected_tools else "0.10")
    cmd = [
        "claude", "-p",
        "--agent", agent,
        "--output-format", "stream-json",
        "--verbose",
        "--model", model,
        "--max-budget-usd", budget,
        "--dangerously-skip-permissions",
    ]

    # Structural enforcement: physically block forbidden tools via CLI
    if forbidden_tools:
        cmd.extend(["--disallowedTools", ",".join(forbidden_tools)])

    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BASE_DIR),
            env=env,
        )
        raw = proc.stdout
    except subprocess.TimeoutExpired as e:
        timed_out = True
        raw = (e.stdout or "") if isinstance(e.stdout, str) else (e.stdout or b"").decode("utf-8", errors="replace")
        result["error"] = f"Timeout ({timeout}s) — partial output analyzed"
    except FileNotFoundError:
        result["error"] = "claude CLI not found"
        result["duration_sec"] = time.time() - start
        return result
    except Exception as e:
        result["error"] = str(e)
        result["duration_sec"] = time.time() - start
        return result

    result["duration_sec"] = time.time() - start

    # Parse stream-json
    parsed = parse_stream_json(raw)
    result["response"] = parsed["text_response"]
    result["tool_calls"] = parsed["all_tool_calls"]
    result["cost_usd"] = parsed["total_cost_usd"]
    result["num_turns"] = parsed["num_turns"]

    # Main agent's direct tool calls (what WE check for forbidden/expected)
    direct_tools = parsed["direct_tool_calls"]
    direct_tool_names = [tc["name"] for tc in direct_tools]
    result["direct_tool_names"] = list(dict.fromkeys(direct_tool_names))

    # All tool names for display
    all_tool_names = [tc["name"] for tc in parsed["all_tool_calls"]]
    result["tool_names"] = list(dict.fromkeys(all_tool_names))

    response = result["response"]

    # ── Text keyword checks ──
    result["expected_kw_found"] = [kw for kw in expected_kw if kw in response]
    result["expected_kw_missing"] = [kw for kw in expected_kw if kw not in response]
    result["forbidden_kw_found"] = [kw for kw in forbidden_kw if kw in response]

    text_expected_ok = len(expected_kw) == 0 or len(result["expected_kw_found"]) > 0
    text_forbidden_ok = len(result["forbidden_kw_found"]) == 0
    result["text_passed"] = text_expected_ok and text_forbidden_ok

    # ── Tool call checks (using DIRECT tools only, not sub-agent) ──
    non_startup_direct = [t for t in direct_tool_names if t not in STARTUP_TOOLS]

    result["expected_tools_found"] = [t for t in expected_tools if t in direct_tool_names]
    result["expected_tools_missing"] = [t for t in expected_tools if t not in direct_tool_names]

    result["forbidden_tools_found"] = [
        t for t in forbidden_tools
        if t in non_startup_direct
    ]

    for tool_name, expected_args in expected_tool_args.items():
        tool_inputs = [tc["input"] for tc in direct_tools if tc["name"] == tool_name]
        all_input_text = " ".join(
            str(v) for inp in tool_inputs for v in inp.values()
        )
        for arg in expected_args:
            if arg in all_input_text:
                result["expected_args_found"].append(f"{tool_name}({arg})")
            else:
                result["expected_args_missing"].append(f"{tool_name}({arg})")

    tools_expected_ok = len(expected_tools) == 0 or len(result["expected_tools_found"]) > 0
    tools_forbidden_ok = len(result["forbidden_tools_found"]) == 0
    tools_args_ok = len(result["expected_args_missing"]) == 0
    result["tools_passed"] = tools_expected_ok and tools_forbidden_ok and tools_args_ok

    # ── Overall pass ──
    result["passed"] = result["text_passed"] and result["tools_passed"]
    if timed_out and result["tools_passed"]:
        if not result["response"]:
            result["text_passed"] = True
            result["passed"] = result["tools_passed"]

    return result


# ============================================================
# Terminal Output (detailed, visible)
# ============================================================

def print_scenario_detail(r: dict):
    """Print detailed result for a scenario (always shown)."""
    status = "PASS" if r["passed"] else ("ERR" if r["error"] else "FAIL")
    icon = "+" if r["passed"] else ("!" if r["error"] else "x")

    # Header
    print(f"  [{icon}] {r['id']}: {r['name']}")
    print(f"      agent={r['agent']}  model={r['model']}  {r['duration_sec']:.1f}s  ${r.get('cost_usd',0):.4f}")

    # Direct tools (main agent's actions)
    direct = r.get("direct_tool_names", [])
    if direct:
        print(f"      direct tools: {', '.join(direct)}")

    # Delegated tools (if any)
    delegated_names = [tc["name"] for tc in r.get("tool_calls", [])
                       if tc["name"] not in direct and tc["name"] not in STARTUP_TOOLS]
    if delegated_names:
        unique = list(dict.fromkeys(delegated_names))
        print(f"      delegated:    {', '.join(unique)}")

    # Text check
    t_status = "OK" if r["text_passed"] else "NG"
    if r["expected_kw_found"]:
        print(f"      text [{t_status}]: found={r['expected_kw_found']}")
    if r["forbidden_kw_found"]:
        print(f"      text [{t_status}]: FORBIDDEN={r['forbidden_kw_found']}")

    # Tool check
    tool_status = "OK" if r["tools_passed"] else "NG"
    if r["expected_tools_found"]:
        print(f"      tools [{tool_status}]: expected called={r['expected_tools_found']}")
    if r["expected_tools_missing"]:
        print(f"      tools [{tool_status}]: expected MISSING={r['expected_tools_missing']}")
    if r["forbidden_tools_found"]:
        print(f"      tools [{tool_status}]: FORBIDDEN called={r['forbidden_tools_found']}")
    if r["expected_args_found"]:
        print(f"      args: matched={r['expected_args_found']}")
    if r["expected_args_missing"]:
        print(f"      args: MISSING={r['expected_args_missing']}")

    if r["error"]:
        print(f"      error: {r['error']}")

    # Response snippet
    resp = r.get("response", "")
    if resp:
        snippet = resp[:200].replace("\n", " ")
        if len(resp) > 200:
            snippet += "..."
        print(f"      response: {snippet}")

    print(f"      result: {status}")
    print()


# ============================================================
# HTML Report
# ============================================================

def generate_report(results: list, duration_sec: float) -> str:
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    errors = sum(1 for r in results if r["error"])
    total_cost = sum(r.get("cost_usd", 0) for r in results)
    pass_rate = (passed / max(total, 1)) * 100

    def esc(t):
        return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    cats = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r)
    cat_rows = ""
    for cn in sorted(cats):
        cr = cats[cn]
        cp = sum(1 for r in cr if r["passed"])
        cf = len(cr) - cp
        cat_rows += f'<tr class="{"pass" if cf==0 else "fail"}"><td><b>{cn}</b></td><td>{len(cr)}</td><td class="g">{cp}</td><td class="r">{cf}</td></tr>'

    scenario_html = ""
    for r in results:
        st = "PASS" if r["passed"] else ("ERR" if r["error"] else "FAIL")
        sc = "pass" if r["passed"] else "fail"
        bc = "bp" if r["passed"] else ("be" if r["error"] else "bf")

        tc_html = ""
        if r["tool_calls"]:
            tc_items = []
            for tc in r["tool_calls"]:
                name = tc["name"]
                inp = json.dumps(tc["input"], ensure_ascii=False)
                if len(inp) > 120:
                    inp = inp[:120] + "..."
                css = "tc-ok"
                if name in r.get("forbidden_tools_found", []):
                    css = "tc-bad"
                elif name in r.get("expected_tools_found", []):
                    css = "tc-good"
                tc_items.append(f'<span class="{css}">{esc(name)}</span><span class="tc-arg">{esc(inp)}</span>')
            tc_html = '<div class="tc-list">' + '<br>'.join(tc_items) + '</div>'
        else:
            tc_html = '<div class="tc-list tc-none">No tool calls</div>'

        ev = ""
        if r["expected_kw_found"]:
            kws = " ".join(f'<span class="kw kw-g">{esc(k)}</span>' for k in r["expected_kw_found"])
            ev += f'<div class="ev ev-ok">Text expected found: {kws}</div>'
        if r["forbidden_kw_found"]:
            kws = " ".join(f'<span class="kw kw-r">{esc(k)}</span>' for k in r["forbidden_kw_found"])
            ev += f'<div class="ev ev-bad">Text forbidden found: {kws}</div>'
        if r["expected_tools_found"]:
            ts = " ".join(f'<span class="kw kw-g">{t}</span>' for t in r["expected_tools_found"])
            ev += f'<div class="ev ev-ok">Tools expected called: {ts}</div>'
        if r["expected_tools_missing"]:
            ts = " ".join(f'<span class="kw kw-r">{t}</span>' for t in r["expected_tools_missing"])
            ev += f'<div class="ev ev-bad">Tools expected NOT called: {ts}</div>'
        if r["forbidden_tools_found"]:
            ts = " ".join(f'<span class="kw kw-r">{t}</span>' for t in r["forbidden_tools_found"])
            ev += f'<div class="ev ev-bad">Forbidden tools called: {ts}</div>'
        if r["expected_args_found"]:
            a = " ".join(f'<span class="kw kw-g">{esc(x)}</span>' for x in r["expected_args_found"])
            ev += f'<div class="ev ev-ok">Tool args matched: {a}</div>'
        if r["expected_args_missing"]:
            a = " ".join(f'<span class="kw kw-r">{esc(x)}</span>' for x in r["expected_args_missing"])
            ev += f'<div class="ev ev-bad">Tool args NOT matched: {a}</div>'
        if r["error"]:
            ev += f'<div class="ev ev-bad">Error: {esc(r["error"])}</div>'

        tb = f'<span class="{"bp" if r["text_passed"] else "bf"}">Text:{"OK" if r["text_passed"] else "NG"}</span>'
        tlb = f'<span class="{"bp" if r["tools_passed"] else "bf"}">Tools:{"OK" if r["tools_passed"] else "NG"}</span>'
        resp = esc(r["response"])

        scenario_html += f'''
<div class="sc {sc}" onclick="this.classList.toggle('open')">
  <div class="sh">
    <span class="{bc}">{st}</span>
    <span class="sid">{r["id"]}</span>
    <b class="sn">{esc(r["name"])}</b>
    <span class="sm">{r["agent"]} ({r.get("model","?")}) | {r["duration_sec"]:.1f}s | ${r.get("cost_usd",0):.4f}</span>
    {tb} {tlb}
  </div>
  <div class="sd">
    <div class="row"><span class="lb">Prompt:</span><span>{esc(r["prompt"])}</span></div>
    <div class="row"><span class="lb">Criteria:</span><span>{esc(r["pass_criteria"])}</span></div>
    <div class="row"><span class="lb">Direct tools:</span><span>{", ".join(r.get("direct_tool_names",[])) or "none"}</span></div>
    <div class="row"><span class="lb">All tools:</span>{tc_html}</div>
    <div class="row"><span class="lb">Response:</span><pre class="resp">{resp}</pre></div>
    {ev}
  </div>
</div>'''

    banner = "status-pass" if failed == 0 else "status-fail"
    status = "ALL PASS" if failed == 0 else f"{failed} FAIL"

    return f'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scenario Report v3 — {date_str}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#f8f9fa;color:#1a1a2e;padding:2rem}}
.c{{max-width:1000px;margin:0 auto}}
h1{{font-size:1.5rem;margin-bottom:.3rem}}h2{{font-size:1.1rem;margin:1.5rem 0 .8rem;border-bottom:2px solid #dee2e6;padding-bottom:.3rem}}
.meta{{color:#6c757d;font-size:.85rem;margin-bottom:.5rem}}
.status-pass{{display:inline-block;padding:.3rem 1rem;border-radius:4px;font-weight:700;background:#d4edda;color:#155724;margin-bottom:1rem}}
.status-fail{{display:inline-block;padding:.3rem 1rem;border-radius:4px;font-weight:700;background:#f8d7da;color:#721c24;margin-bottom:1rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.8rem;margin-bottom:2rem}}
.card{{background:#fff;border-radius:8px;padding:1rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.card .n{{font-size:1.8rem;font-weight:700}}.card .l{{font-size:.75rem;color:#6c757d;margin-top:.2rem}}
.card.p .n{{color:#198754}}.card.f .n{{color:#dc3545}}.card.e .n{{color:#fd7e14}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:1.5rem}}
th{{background:#f1f3f5;padding:.6rem .8rem;text-align:left;font-size:.8rem}}
td{{padding:.5rem .8rem;border-top:1px solid #e9ecef;font-size:.85rem}}
tr.pass td{{background:#f8fff8}}tr.fail td{{background:#fff8f8}}
.g{{color:#198754;font-weight:600}}.r{{color:#dc3545;font-weight:600}}
.sc{{background:#fff;border-radius:8px;margin-bottom:.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden;cursor:pointer}}
.sc.pass{{border-left:4px solid #198754}}.sc.fail{{border-left:4px solid #dc3545}}
.sh{{padding:.7rem 1rem;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}}
.sh:hover{{background:#f8f9fa}}
.sd{{display:none;padding:0 1rem 1rem;border-top:1px solid #e9ecef}}
.sc.open .sd{{display:block;padding-top:1rem}}
.sid{{font-family:monospace;font-weight:600;font-size:.8rem;color:#495057}}
.sn{{font-size:.88rem;flex:1;min-width:200px}}.sm{{font-size:.75rem;color:#6c757d}}
.bp{{background:#d4edda;color:#155724;padding:.1rem .4rem;border-radius:3px;font-size:.7rem;font-weight:700}}
.bf{{background:#f8d7da;color:#721c24;padding:.1rem .4rem;border-radius:3px;font-size:.7rem;font-weight:700}}
.be{{background:#fff3cd;color:#856404;padding:.1rem .4rem;border-radius:3px;font-size:.7rem;font-weight:700}}
.row{{display:grid;grid-template-columns:100px 1fr;gap:.3rem;font-size:.83rem;margin-bottom:.4rem}}
.lb{{font-weight:600;color:#6c757d}}
.resp{{background:#f8f9fa;border:1px solid #e9ecef;border-radius:4px;padding:.7rem;font-size:.78rem;white-space:pre-wrap;max-height:250px;overflow-y:auto;font-family:monospace}}
.tc-list{{font-size:.8rem;font-family:monospace}}.tc-none{{color:#adb5bd;font-style:italic}}
.tc-ok{{color:#495057}}.tc-good{{color:#198754;font-weight:600}}.tc-bad{{color:#dc3545;font-weight:700}}
.tc-arg{{color:#6c757d;font-size:.72rem;margin-left:.3rem}}
.ev{{padding:.3rem .7rem;border-radius:4px;font-size:.78rem;margin-top:.3rem}}
.ev-ok{{background:#d4edda;color:#155724}}.ev-bad{{background:#f8d7da;color:#721c24}}
.kw{{display:inline-block;padding:.05rem .3rem;border-radius:2px;font-family:monospace;font-size:.75rem;margin:0 .1rem}}
.kw-g{{background:#a3d9a5}}.kw-r{{background:#f5c6cb}}
.foot{{margin-top:2rem;text-align:center;color:#adb5bd;font-size:.78rem}}
</style></head><body><div class="c">
<h1>Scenario Test Report v3</h1>
<div class="meta">{date_str} | {total} scenarios | {duration_sec:.1f}s | ${total_cost:.4f}</div>
<div class="meta" style="font-style:italic;margin-bottom:1rem">Production-matched: --agent + agent model | Tool verification: direct vs delegated</div>
<div class="{banner}">{status}</div>
<div class="cards">
<div class="card"><div class="n">{total}</div><div class="l">Total</div></div>
<div class="card p"><div class="n">{passed}</div><div class="l">Passed</div></div>
<div class="card f"><div class="n">{failed}</div><div class="l">Failed</div></div>
<div class="card e"><div class="n">{errors}</div><div class="l">Errors</div></div>
<div class="card"><div class="n" style="color:{"#198754" if failed==0 else "#dc3545"}">{pass_rate:.0f}%</div><div class="l">Pass Rate</div></div>
</div>
<h2>By Category</h2>
<table><thead><tr><th>Category</th><th>Total</th><th>Passed</th><th>Failed</th></tr></thead><tbody>{cat_rows}</tbody></table>
<h2>Scenario Details</h2>
<p style="font-size:.83rem;color:#6c757d;margin-bottom:1rem">Click to expand. Shows: direct tools (agent's own), all tools (incl. delegated), text response, and evidence.</p>
{scenario_html}
<div class="foot">Generated by run_scenarios.py v3 | {date_str}</div>
</div></body></html>'''


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Run scenario tests (production-matched)")
    parser.add_argument("--category", "-c", type=str)
    parser.add_argument("--id", type=str)
    parser.add_argument("--priority", type=str, choices=["critical", "high", "medium"])
    parser.add_argument("--timeout", "-t", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    scenarios = SCENARIOS
    if args.id:
        scenarios = [s for s in scenarios if s["id"] == args.id]
    if args.category:
        scenarios = [s for s in scenarios if s["category"].startswith(args.category.upper())]
    if args.priority:
        scenarios = [s for s in scenarios if s["priority"] == args.priority]

    if not scenarios:
        print("No matching scenarios found.")
        return 1

    print()
    print("=" * 70)
    print("  Scenario Test Runner v3 — Production-matched")
    print("=" * 70)
    print()
    print(f"  Scenarios:  {len(scenarios)}")
    print(f"  Mode:       --agent <name> + agent's own model")
    print(f"  Checks:     Text keywords + Tool calls (direct vs delegated)")
    print()
    for s in scenarios:
        m = AGENTS.get(s["agent_context"], {}).get("model", "?")
        et = ",".join(s.get("expected_tools", [])) or "-"
        ft = ",".join(s.get("forbidden_tools", [])) or "-"
        print(f"  [{s['id']}] {s['name']} ({s['agent_context']}/{m}) expect=[{et}] forbid=[{ft}]")
    print()

    if args.dry_run:
        print("  (dry-run — exiting)")
        return 0

    print(f"  Running {len(scenarios)} scenarios...\n")
    print("-" * 70)

    results = []
    t0 = time.time()

    for i, s in enumerate(scenarios, 1):
        m = AGENTS.get(s["agent_context"], {}).get("model", "?")
        print(f"\n  [{i}/{len(scenarios)}] {s['id']}: {s['name']} ({s['agent_context']}/{m})")
        print(f"      prompt: {s['prompt'][:80]}...")
        print(f"      running...", flush=True)

        r = run_single_scenario(s, timeout=args.timeout)
        results.append(r)
        print_scenario_detail(r)

    total_dur = time.time() - t0
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    total_cost = sum(r.get("cost_usd", 0) for r in results)

    # ── Summary ──
    print("=" * 70)
    banner = "ALL PASS" if failed == 0 else f"{failed} FAILED"
    print(f"  {banner}: {passed}/{len(results)} passed | {total_dur:.1f}s | ${total_cost:.4f}")
    print("=" * 70)

    # Per-scenario summary
    print()
    for r in results:
        icon = "+" if r["passed"] else "x"
        print(f"  [{icon}] {r['id']} {r['name']}")
    print()

    # HTML report
    REPORTS_DIR.mkdir(exist_ok=True)
    tag = datetime.datetime.now().strftime("%Y-%m-%d")
    html_path = REPORTS_DIR / f"scenario-report-{tag}.html"
    html_path.write_text(generate_report(results, total_dur), encoding="utf-8")
    print(f"  HTML report: {html_path}")

    if args.json:
        json_path = REPORTS_DIR / f"scenario-report-{tag}.json"
        data = {"generated": datetime.datetime.now().isoformat(), "results": results}
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  JSON report: {json_path}")

    # Open report (macOS)
    if sys.platform == "darwin" and not args.no_open:
        os.system(f'open "{html_path}"')

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
