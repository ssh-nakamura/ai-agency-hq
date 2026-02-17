#!/usr/bin/env python3
"""
AI Agency HQ Dashboard - API Server
python3 tools/dashboard/server.py [--port 8888]
"""

import http.server
import json
import os
import sys
import glob
import re
import urllib.parse
from datetime import datetime
from collections import defaultdict
from pathlib import Path

PORT = 8888
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent.parent
PROJECT_DIR = Path.home() / ".claude/projects/-Users-soshunakamura-ai-prodcut-ai-agency-hq"
CCBOARD_API = "http://localhost:3333/api"

AGENTS = {
    "analyst":         {"name": "白河 凛",   "role": "経営企画部長",       "color": "#6366f1", "initials": "凛"},
    "product-manager": {"name": "桐谷 翔",   "role": "事業開発部長",       "color": "#f59e0b", "initials": "翔"},
    "writer":          {"name": "藤崎 あおい", "role": "広報部長",         "color": "#ec4899", "initials": "あ"},
    "x-manager":       {"name": "七瀬 美咲",  "role": "マーケティング部長", "color": "#f97316", "initials": "美"},
    "site-builder":    {"name": "黒崎 蓮",   "role": "Web制作担当",       "color": "#6b7280", "initials": "蓮"},
    "video-creator":   {"name": "朝比奈 陸",  "role": "動画制作担当",      "color": "#10b981", "initials": "陸"},
    "legal":           {"name": "氷室 志帆",  "role": "法務部長",         "color": "#8b5cf6", "initials": "志"},
    "ceo":             {"name": "九条 零",    "role": "CEO",             "color": "#ef4444", "initials": "零"},
}
UNKNOWN = {"name": "Unknown", "role": "不明", "color": "#94a3b8", "initials": "?"}
TEAM_LEAD_ALIASES = {"team-lead": "ceo", "lead": "ceo"}


# ── File Helpers ──────────────────────────────────────────

def read_file(rel_path):
    p = REPO_DIR / rel_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


# ── JSONL Chat Parsing ────────────────────────────────────

def parse_jsonl(filepath):
    messages = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = data.get("message", {})
            role = message.get("role", "")
            content = message.get("content", "")
            timestamp = data.get("timestamp", "")

            content_text = ""
            tool_calls = []
            if isinstance(content, str):
                content_text = content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content_text += block.get("text", "")
                        elif block.get("type") == "tool_use":
                            tool_calls.append({
                                "name": block.get("name", ""),
                                "input": block.get("input", {}),
                            })
            messages.append({
                "role": role,
                "text": content_text,
                "tools": tool_calls,
                "tool_result": data.get("toolUseResult", ""),
                "time": timestamp,
                "agent_id": data.get("agentId", ""),
                "usage": message.get("usage", {}),
            })
    return messages


def detect_agent(messages):
    for msg in messages[:3]:
        if msg.get("role") != "user":
            continue
        text = msg.get("text", "")
        for key in AGENTS:
            if f"\uff08{key}\uff09" in text or f"({key})" in text:
                return key
    for msg in messages[:10]:
        if msg.get("role") != "assistant":
            continue
        text = msg.get("text", "")
        for key, info in AGENTS.items():
            if info["name"] in text or info["role"] in text:
                return key
    for msg in messages[:3]:
        aid = msg.get("agent_id", "").lower()
        for key in AGENTS:
            if key in aid:
                return key
    return "unknown"


def detect_msg_type(messages):
    for msg in messages[:5]:
        if "<teammate-message" in msg.get("text", ""):
            return "team"
    return "task"


def resolve_sender(text):
    if "<teammate-message" not in text:
        return "ceo", text
    m = re.search(r'teammate_id="([^"]+)"', text)
    sender = "ceo"
    if m:
        tid = m.group(1)
        sender = TEAM_LEAD_ALIASES.get(tid, tid)
        if sender == tid:
            for k in AGENTS:
                if k in tid:
                    sender = k
                    break
    text = re.sub(r'<teammate-message[^>]*>', '', text)
    text = re.sub(r'</teammate-message>', '', text).strip()
    if text.startswith('{') and '"type"' in text[:50]:
        try:
            jd = json.loads(text)
            msg_type = jd.get("type", "")
            if msg_type == "task_assignment":
                text = f"[Task] {jd.get('subject', '')}"
            elif msg_type in ("shutdown_request", "shutdown_approved", "idle_notification"):
                return sender, ""
            else:
                text = f"[{msg_type}] {jd.get('content', text[:200])}"
        except json.JSONDecodeError:
            pass
    return sender, text


def fmt_time(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, AttributeError):
        return ""


def fmt_date(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%m/%d %H:%M")
    except (ValueError, AttributeError):
        return ""


# ── API: /api/agents ──────────────────────────────────────

def api_agents():
    sessions = sorted(glob.glob(str(PROJECT_DIR / "*")))
    sessions = [d for d in sessions if os.path.isdir(d) and "memory" not in d]
    all_convos = []

    for sd in sessions:
        sid = os.path.basename(sd)
        sub_dir = os.path.join(sd, "subagents")
        if not os.path.isdir(sub_dir):
            continue
        for jf in sorted(glob.glob(os.path.join(sub_dir, "*.jsonl"))):
            if "compact" in os.path.basename(jf):
                continue
            msgs = parse_jsonl(jf)
            if not msgs:
                continue

            agent_key = detect_agent(msgs)
            msg_type = detect_msg_type(msgs)
            timestamps = [m["time"] for m in msgs if m["time"]]
            total_in = sum(
                m.get("usage", {}).get("input_tokens", 0) +
                m.get("usage", {}).get("cache_creation_input_tokens", 0)
                for m in msgs
            )
            total_out = sum(m.get("usage", {}).get("output_tokens", 0) for m in msgs)

            chat_msgs = []
            for msg in msgs:
                if msg["role"] == "user" and msg["tool_result"]:
                    continue
                if msg["role"] == "user" and msg["text"]:
                    sender_key, cleaned = resolve_sender(msg["text"])
                    if not cleaned:
                        continue
                    info = AGENTS.get(sender_key, UNKNOWN)
                    chat_msgs.append({
                        "role": "user", "sender": sender_key,
                        "sender_name": info["name"], "sender_color": info["color"],
                        "sender_initials": info["initials"],
                        "text": cleaned[:3000], "time": fmt_time(msg["time"]),
                        "sort_ts": msg["time"],
                    })
                elif msg["role"] == "assistant" and msg["text"]:
                    info = AGENTS.get(agent_key, UNKNOWN)
                    chat_msgs.append({
                        "role": "assistant", "sender": agent_key,
                        "sender_name": info["name"], "sender_color": info["color"],
                        "sender_initials": info["initials"],
                        "text": msg["text"][:3000], "time": fmt_time(msg["time"]),
                        "sort_ts": msg["time"],
                    })
                for tc in msg.get("tools", []):
                    inp = json.dumps(tc["input"], ensure_ascii=False)
                    chat_msgs.append({
                        "role": "tool", "name": tc["name"],
                        "input": inp[:150] + ("..." if len(inp) > 150 else ""),
                        "sort_ts": msg["time"],
                    })

            if len(chat_msgs) < 2:
                continue
            all_convos.append({
                "session": sid, "agent_key": agent_key, "type": msg_type,
                "t_start": timestamps[0] if timestamps else "",
                "tokens_in": total_in, "tokens_out": total_out,
                "messages": chat_msgs,
            })

    dm_groups = defaultdict(list)
    team_groups = defaultdict(list)
    for c in all_convos:
        if c["type"] == "task":
            dm_groups[(c["session"], c["agent_key"])].append(c)
        else:
            team_groups[c["session"]].append(c)

    dms = []
    for (sid, agent_key), convos in sorted(dm_groups.items(), key=lambda x: x[0][0]):
        if agent_key == "unknown" and sum(len(c["messages"]) for c in convos) < 4:
            continue
        info = AGENTS.get(agent_key, UNKNOWN)
        merged = []
        tin, tout = 0, 0
        for c in convos:
            merged.extend(c["messages"])
            tin += c["tokens_in"]
            tout += c["tokens_out"]
        merged.sort(key=lambda m: m.get("sort_ts", ""))
        timestamps = [m.get("sort_ts", "") for m in merged if m.get("sort_ts")]
        dms.append({
            "id": f"dm-{sid[:8]}-{agent_key}", "agent_key": agent_key,
            "name": info["name"], "role": info["role"],
            "color": info["color"], "initials": info["initials"],
            "session_label": fmt_date(timestamps[0]) if timestamps else sid[:8],
            "time_end": fmt_time(timestamps[-1]) if timestamps else "",
            "tokens_in": tin, "tokens_out": tout,
            "msg_count": len([m for m in merged if m.get("role") != "tool"]),
            "messages": merged,
        })

    teams = []
    for sid, convos in sorted(team_groups.items()):
        merged, tin, tout, members = [], 0, 0, set()
        for c in convos:
            merged.extend(c["messages"])
            tin += c["tokens_in"]
            tout += c["tokens_out"]
            members.add(c["agent_key"])
        merged.sort(key=lambda m: m.get("sort_ts", ""))
        merged = [m for m in merged if m.get("role") == "tool"
                  or (m.get("text", "").strip() and not m.get("text", "").startswith("[Shutdown"))]
        if len([m for m in merged if m.get("role") != "tool"]) < 3:
            continue
        timestamps = [m.get("sort_ts", "") for m in merged if m.get("sort_ts")]
        teams.append({
            "id": f"team-{sid[:8]}", "session": sid[:8],
            "label": fmt_date(timestamps[0]) if timestamps else sid[:8],
            "members": list(members),
            "member_names": [AGENTS.get(k, UNKNOWN)["name"] for k in sorted(members) if k != "unknown"],
            "tokens_in": tin, "tokens_out": tout,
            "msg_count": len([m for m in merged if m.get("role") != "tool"]),
            "messages": merged,
        })

    return {"dms": dms, "teams": teams}


# ── API: /api/health ──────────────────────────────────────

def api_health():
    checks = []
    err_count, warn_count = 0, 0

    # 1. Required files
    required = {
        "CLAUDE.md": "組織ハンドブック",
        "docs/plan.md": "事業計画 + ロードマップ",
        "docs/status.md": "アクション + KPI + 収支",
        "docs/decisions.md": "意思決定ログ",
        "docs/ceo-manual.md": "CEOマニュアル",
    }
    agents_list = ["analyst", "writer", "site-builder", "x-manager",
                   "video-creator", "product-manager", "legal"]
    for a in agents_list:
        required[f".claude/agents/{a}.md"] = f"エージェント定義({a})"
        required[f".claude/agent-memory/{a}/MEMORY.md"] = f"メモリ({a})"
    required[".claude/agent-memory/ceo/MEMORY.md"] = "メモリ(ceo)"

    file_results = []
    for path, desc in required.items():
        exists = (REPO_DIR / path).exists()
        file_results.append({"path": path, "desc": desc, "ok": exists})
        if not exists:
            err_count += 1
    checks.append({"name": "必須ファイル", "items": file_results})

    # 2. Phase consistency (plan.md vs status.md)
    phase_values = {}
    plan_raw = read_file("docs/plan.md")
    status_raw = read_file("docs/status.md")

    if plan_raw:
        m = re.search(r"## 現在地:\s*(.+)", plan_raw)
        phase_values["plan.md"] = m.group(1).strip() if m else "?"
    if status_raw:
        m = re.search(r"## 現在のフェーズ:\s*(.+)", status_raw)
        phase_values["status.md"] = m.group(1).strip() if m else "?"

    unique = set(phase_values.values())
    phase_ok = len(unique) <= 1
    if not phase_ok:
        err_count += 1
    checks.append({
        "name": "フェーズ整合性",
        "ok": phase_ok,
        "current": list(unique)[0] if len(unique) == 1 else None,
        "values": phase_values,
    })

    # 3. Cost check (within status.md)
    cost_check = {"name": "コスト整合", "ok": True, "detail": ""}
    if status_raw:
        expenditure_match = re.search(r"支出合計\s*\|\s*[¥￥]?([\d,]+)", status_raw)
        if expenditure_match:
            expenditure = int(expenditure_match.group(1).replace(",", ""))
            cost_check["detail"] = f"¥{expenditure:,}"
        else:
            cost_check["ok"] = None
            cost_check["detail"] = "status.mdから支出合計を抽出できず"
            warn_count += 1
    checks.append(cost_check)

    # 4. MEMORY.md character check
    mem_results = []
    all_agents = ["ceo"] + agents_list
    for a in all_agents:
        mem_raw = read_file(f".claude/agent-memory/{a}/MEMORY.md")
        if mem_raw is None:
            mem_results.append({"agent": a, "char": False, "lines": 0})
            continue
        lines = mem_raw.split("\n")
        has_char = any("口調" in l or "一人称" in l or "あなたは" in l for l in lines[:15])
        mem_results.append({"agent": a, "char": has_char, "lines": len(lines),
                            "over200": len(lines) > 200})
        if not has_char:
            err_count += 1
        if len(lines) > 200:
            warn_count += 1
    checks.append({"name": "MEMORY.mdキャラ設定", "items": mem_results})

    # 5. plan.md "要調査"
    youchousa = 0
    if plan_raw:
        youchousa = len([l for l in plan_raw.split("\n") if "要調査" in l and "|" in l])
    if youchousa > 0:
        warn_count += youchousa
    checks.append({"name": "要調査チェック", "count": youchousa})

    # 6. Completed actions count (from status.md)
    completed_count = 0
    if status_raw and "完了済み" in status_raw:
        completed_count = len(re.findall(r"\|\s*A-\d+\s*\|", status_raw.split("完了済み")[-1]))
    over_limit = completed_count > 10
    if over_limit:
        warn_count += 1
    checks.append({"name": "完了済みアクション", "count": completed_count, "over": over_limit})

    return {"checks": checks, "errors": err_count, "warnings": warn_count}


# ── API: /api/actions ─────────────────────────────────────

def api_actions():
    raw = read_file("docs/status.md")
    if not raw:
        return {"error": "status.md not found"}

    sections = {"priority": [], "next": [], "hold": [], "approval": [], "completed": []}
    current_section = None
    section_map = {
        "最優先": "priority", "次に着手": "next",
        "保留": "hold", "株主承認待ち": "approval", "完了済み": "completed",
    }

    for line in raw.split("\n"):
        for key, sec in section_map.items():
            if key in line and (line.startswith("###") or line.startswith("## 完了")):
                current_section = sec
                break
        if current_section and line.startswith("|") and not line.startswith("|--") and not line.startswith("| ID"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3 and re.match(r"[AS]-\d+", cols[0]):
                sections[current_section].append(cols)

    return sections


# ── API: /api/kpi ─────────────────────────────────────────

def api_kpi():
    raw = read_file("docs/status.md")
    if not raw:
        return {"error": "status.md not found"}

    result = {"phase": "", "actual": {}, "targets": {}, "infrastructure": {}, "products": {}}

    # Phase
    m = re.search(r"## 現在のフェーズ:\s*(.+)", raw)
    if m:
        result["phase"] = m.group(1).strip()

    # Parse KPI tables
    def parse_table(section_header, raw_text):
        data = {}
        in_section = False
        for line in raw_text.split("\n"):
            if section_header in line:
                in_section = True
                continue
            if in_section and line.startswith("###"):
                break
            if in_section and line.startswith("|") and not line.startswith("|--") and not line.startswith("| 指標") and not line.startswith("| 項目") and not line.startswith("| 名前"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 2:
                    data[cols[0]] = cols[1]
        return data

    result["actual"] = parse_table("### 実績", raw)
    result["targets"] = parse_table("### Phase 2 目標", raw)
    result["infrastructure"] = parse_table("### インフラ", raw)
    result["products"] = parse_table("### プロダクト", raw)

    return result


# ── API: /api/roadmap ─────────────────────────────────────

def api_roadmap():
    raw = read_file("docs/plan.md")
    if not raw:
        return {"error": "plan.md not found"}
    return {"markdown": raw}


# ── API: /api/logs ────────────────────────────────────────

def api_logs():
    logs_dir = REPO_DIR / "content" / "logs"
    if not logs_dir.exists():
        return {"logs": []}
    files = sorted(logs_dir.glob("*.md"), reverse=True)[:5]
    logs = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        logs.append({"name": f.name, "content": content[:3000]})
    return {"logs": logs}


# ── Static File Serving ───────────────────────────────────

MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API routes
        api_routes = {
            "/api/agents": api_agents,
            "/api/health": api_health,
            "/api/actions": api_actions,
            "/api/kpi": api_kpi,
            "/api/roadmap": api_roadmap,
            "/api/logs": api_logs,
        }

        if path in api_routes:
            data = api_routes[path]()
            self.respond(200, "application/json", json.dumps(data, ensure_ascii=False))
            return

        # Static files
        if path == "/" or path == "/index.html":
            path = "/index.html"
        file_path = SCRIPT_DIR / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            ext = file_path.suffix
            mime = MIME_TYPES.get(ext, "text/plain")
            self.respond(200, mime, file_path.read_text(encoding="utf-8"))
        else:
            self.respond(404, "text/plain", "Not Found")

    def respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


def main():
    port = PORT
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--port" and i + 2 <= len(sys.argv):
            port = int(sys.argv[i + 2])

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"AI Agency HQ Dashboard: http://localhost:{port}")
    print(f"Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
