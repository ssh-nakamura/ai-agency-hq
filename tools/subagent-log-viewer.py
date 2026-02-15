#!/usr/bin/env python3
"""
Subagent Log Viewer - Slack風チャットUI
仮想機関AI計画のサブエージェントJSONLログを
チャットアプリ風HTMLに変換する。
"""

import json
import os
import sys
import glob
import html
from datetime import datetime

PROJECT_DIR = os.path.expanduser(
    "~/.claude/projects/-Users-soshunakamura-ai-prodcut-ai-agency-hq"
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "reports"
)

AGENTS = {
    "analyst":         {"name": "白河 凛",   "role": "経営企画部長",       "color": "#6366f1", "initials": "凛", "bg": "#eef2ff"},
    "product-manager": {"name": "桐谷 翔",   "role": "事業開発部長",       "color": "#f59e0b", "initials": "翔", "bg": "#fffbeb"},
    "writer":          {"name": "藤崎 あおい", "role": "広報部長",         "color": "#ec4899", "initials": "あ", "bg": "#fdf2f8"},
    "x-manager":       {"name": "七瀬 美咲",  "role": "マーケティング部長", "color": "#f97316", "initials": "美", "bg": "#fff7ed"},
    "site-builder":    {"name": "黒崎 蓮",   "role": "Web制作担当",       "color": "#6b7280", "initials": "蓮", "bg": "#f9fafb"},
    "video-creator":   {"name": "朝比奈 陸",  "role": "動画制作担当",      "color": "#10b981", "initials": "陸", "bg": "#ecfdf5"},
    "legal":           {"name": "氷室 志帆",  "role": "法務部長",         "color": "#8b5cf6", "initials": "志", "bg": "#f5f3ff"},
    "ceo":             {"name": "九条 零",    "role": "CEO",             "color": "#ef4444", "initials": "零", "bg": "#fef2f2"},
}

UNKNOWN_AGENT = {"name": "Unknown Agent", "role": "不明", "color": "#94a3b8", "initials": "?", "bg": "#f8fafc"}


def parse_jsonl(filepath):
    """Parse JSONL into structured messages."""
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
            agent_id = data.get("agentId", "")
            tool_use_result = data.get("toolUseResult", "")

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

            usage = message.get("usage", {})
            messages.append({
                "role": role,
                "content_text": content_text,
                "tool_calls": tool_calls,
                "tool_use_result": tool_use_result,
                "timestamp": timestamp,
                "agent_id": agent_id,
                "usage": usage,
            })
    return messages


def detect_agent(messages):
    """Detect agent type from conversation."""
    for msg in messages[:5]:
        text = msg.get("content_text", "").lower()
        for key in AGENTS:
            if key in text or AGENTS[key]["role"] in msg.get("content_text", ""):
                return key
    return "unknown"


def fmt_time(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, AttributeError):
        return ""


def fmt_tool_input_short(inp):
    """One-line summary of tool input."""
    if not isinstance(inp, dict):
        return html.escape(str(inp)[:100])
    parts = []
    for k, v in inp.items():
        s = str(v)
        if len(s) > 80:
            s = s[:80] + "..."
        parts.append(f"{k}={s}")
    return html.escape(" | ".join(parts)[:200])


def render_chat(agent_file, messages):
    """Render one agent conversation as Slack-style chat thread."""
    if not messages:
        return "", None

    agent_id = messages[0].get("agent_id", "unknown")
    agent_key = detect_agent(messages)
    info = AGENTS.get(agent_key, UNKNOWN_AGENT)
    is_compact = "compact" in os.path.basename(agent_file)

    # Token totals
    total_in = sum(
        m.get("usage", {}).get("input_tokens", 0) +
        m.get("usage", {}).get("cache_creation_input_tokens", 0) +
        m.get("usage", {}).get("cache_read_input_tokens", 0)
        for m in messages
    )
    total_out = sum(m.get("usage", {}).get("output_tokens", 0) for m in messages)

    timestamps = [m["timestamp"] for m in messages if m["timestamp"]]
    t_start = fmt_time(timestamps[0]) if timestamps else ""
    t_end = fmt_time(timestamps[-1]) if timestamps else ""

    ceo = AGENTS["ceo"]
    channel_id = f"ch-{agent_id[:7]}"

    out = f'<div class="chat-thread" id="{channel_id}" data-agent="{agent_key}">'

    # Thread header
    compact_tag = '<span class="tag tag-compact">compact</span>' if is_compact else ''
    out += f'''
    <div class="thread-header">
        <div class="thread-avatar" style="background:{info["color"]}">{info["initials"]}</div>
        <div class="thread-info">
            <span class="thread-name" style="color:{info["color"]}">{info["name"]}</span>
            <span class="thread-role">{info["role"]}</span>
            {compact_tag}
        </div>
        <div class="thread-meta">
            <span class="tag">{t_start} - {t_end}</span>
            <span class="tag">IN {total_in:,} / OUT {total_out:,}</span>
        </div>
    </div>
    <div class="chat-messages">
    '''

    last_role = None
    for msg in messages:
        role = msg["role"]
        text = msg["content_text"]
        time_str = fmt_time(msg["timestamp"])
        tool_result = msg.get("tool_use_result", "")

        # Skip empty tool results
        if role == "user" and not text and tool_result:
            if not isinstance(tool_result, str):
                tool_result = json.dumps(tool_result, ensure_ascii=False)
            preview = tool_result[:200] + ("..." if len(tool_result) > 200 else "")
            out += f'''
            <div class="chat-tool-result">
                <span class="tool-icon">&#8629;</span>
                <span class="tool-result-text">{html.escape(preview)}</span>
            </div>
            '''
            last_role = None
            continue

        if role == "user" and text:
            # CEO message
            show_header = last_role != "user"
            if len(text) > 1200:
                text = text[:1200] + "\n... (truncated)"
            header = ""
            if show_header:
                header = f'''
                <div class="msg-header">
                    <div class="msg-avatar" style="background:{ceo["color"]}">{ceo["initials"]}</div>
                    <span class="msg-name" style="color:{ceo["color"]}">{ceo["name"]}</span>
                    <span class="msg-time">{time_str}</span>
                </div>'''
            out += f'''
            <div class="chat-msg chat-msg-user">
                {header}
                <div class="msg-body">{html.escape(text).replace(chr(10), "<br>")}</div>
            </div>
            '''
            last_role = "user"

        elif role == "assistant":
            # Agent text message
            if text:
                show_header = last_role != "assistant"
                if len(text) > 2000:
                    text = text[:2000] + "\n... (truncated)"
                header = ""
                if show_header:
                    header = f'''
                    <div class="msg-header">
                        <div class="msg-avatar" style="background:{info["color"]}">{info["initials"]}</div>
                        <span class="msg-name" style="color:{info["color"]}">{info["name"]}</span>
                        <span class="msg-time">{time_str}</span>
                    </div>'''
                out += f'''
                <div class="chat-msg chat-msg-agent">
                    {header}
                    <div class="msg-body">{html.escape(text).replace(chr(10), "<br>")}</div>
                </div>
                '''
                last_role = "assistant"

            # Tool calls as compact attachments
            for tc in msg["tool_calls"]:
                summary = fmt_tool_input_short(tc["input"])
                out += f'''
                <div class="chat-tool-call">
                    <span class="tool-icon">&#9881;</span>
                    <span class="tool-name">{html.escape(tc["name"])}</span>
                    <span class="tool-summary">{summary}</span>
                </div>
                '''
                last_role = None

    out += '</div></div>'

    channel_info = {
        "key": agent_key,
        "name": info["name"],
        "role": info["role"],
        "color": info["color"],
        "initials": info["initials"],
        "id": channel_id,
        "agent_id": agent_id[:7],
        "compact": is_compact,
    }
    return out, channel_info


def generate_html(session_id=None):
    """Generate Slack-style chat HTML."""
    if session_id:
        session_dirs = [os.path.join(PROJECT_DIR, session_id)]
    else:
        session_dirs = sorted(glob.glob(os.path.join(PROJECT_DIR, "*")))
        session_dirs = [d for d in session_dirs if os.path.isdir(d) and "memory" not in d]

    all_threads = ""
    all_channels = []  # list of (session_label, [channel_info, ...])

    for session_dir in session_dirs:
        sid = os.path.basename(session_dir)
        subagents_dir = os.path.join(session_dir, "subagents")
        if not os.path.isdir(subagents_dir):
            continue

        jsonl_files = sorted(glob.glob(os.path.join(subagents_dir, "*.jsonl")))
        if not jsonl_files:
            continue

        session_time = ""
        try:
            with open(jsonl_files[0], "r") as f:
                first = json.loads(f.readline())
                ts = first.get("timestamp", "")
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    session_time = dt.strftime("%m/%d %H:%M")
        except Exception:
            pass

        session_label = session_time or sid[:8]
        session_channels = []

        for jf in jsonl_files:
            msgs = parse_jsonl(jf)
            if msgs:
                thread_html, ch_info = render_chat(jf, msgs)
                if ch_info:
                    all_threads += thread_html
                    session_channels.append(ch_info)

        if session_channels:
            all_channels.append((session_label, sid[:8], session_channels))

    # Build sidebar
    sidebar_html = ""
    for session_label, sid_short, channels in all_channels:
        sidebar_html += f'<div class="sidebar-section"><div class="sidebar-section-title">{html.escape(session_label)}</div>'
        for ch in channels:
            compact_mark = " (c)" if ch["compact"] else ""
            sidebar_html += f'''
            <a class="channel-link" href="#{ch["id"]}" data-target="{ch["id"]}" onclick="showThread('{ch["id"]}')">
                <span class="channel-dot" style="background:{ch["color"]}"></span>
                <span class="channel-name">{ch["name"]}</span>
                <span class="channel-sub">{ch["role"]}{compact_mark}</span>
            </a>'''
        sidebar_html += '</div>'

    generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agency HQ - Agent Chat Logs</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Sans',sans-serif;background:#1a1d21;color:#d1d2d3;height:100vh;display:flex;flex-direction:column;overflow:hidden}}

/* Top bar */
.topbar{{background:#1a1d21;border-bottom:1px solid #35373b;padding:8px 16px;display:flex;align-items:center;gap:12px;min-height:44px;flex-shrink:0}}
.topbar-title{{font-weight:700;color:#fff;font-size:15px}}
.topbar-sub{{color:#9ea0a5;font-size:12px}}
.topbar-right{{margin-left:auto;display:flex;gap:8px}}
.topbar-btn{{padding:4px 10px;border-radius:6px;font-size:12px;border:1px solid #35373b;background:transparent;color:#d1d2d3;cursor:pointer}}
.topbar-btn:hover{{background:#35373b}}
.topbar-btn.active{{background:#1264a3;color:#fff;border-color:#1264a3}}

/* Layout */
.app{{display:flex;flex:1;overflow:hidden}}

/* Sidebar */
.sidebar{{width:240px;background:#1a1d21;border-right:1px solid #35373b;overflow-y:auto;flex-shrink:0;padding:8px 0}}
.sidebar-section{{margin-bottom:12px}}
.sidebar-section-title{{padding:4px 16px;font-size:11px;font-weight:600;color:#9ea0a5;text-transform:uppercase;letter-spacing:.05em}}
.channel-link{{display:flex;align-items:center;gap:8px;padding:4px 16px;text-decoration:none;color:#d1d2d3;font-size:13px;border-radius:0;cursor:pointer}}
.channel-link:hover{{background:#27242c}}
.channel-link.active{{background:#1264a3;color:#fff}}
.channel-link.active .channel-sub{{color:#b8d4ea}}
.channel-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.channel-name{{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.channel-sub{{font-size:11px;color:#9ea0a5;margin-left:auto;white-space:nowrap}}

/* Main chat area */
.chat-area{{flex:1;display:flex;flex-direction:column;background:#1a1d21;overflow:hidden}}
.chat-thread{{display:none;flex-direction:column;flex:1;overflow:hidden}}
.chat-thread.visible{{display:flex}}

/* Thread header */
.thread-header{{display:flex;align-items:center;gap:12px;padding:12px 20px;border-bottom:1px solid #35373b;background:#1a1d21;flex-shrink:0}}
.thread-avatar{{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;color:#fff;flex-shrink:0}}
.thread-info{{display:flex;align-items:baseline;gap:8px}}
.thread-name{{font-size:16px;font-weight:700}}
.thread-role{{font-size:13px;color:#9ea0a5}}
.thread-meta{{margin-left:auto;display:flex;gap:6px}}
.tag{{font-size:11px;padding:2px 8px;background:#2b2d31;border-radius:4px;color:#9ea0a5}}
.tag-compact{{background:#92400e33;color:#fbbf24}}

/* Messages */
.chat-messages{{flex:1;overflow-y:auto;padding:8px 20px 20px}}

/* Chat message */
.chat-msg{{padding:6px 0}}
.msg-header{{display:flex;align-items:center;gap:8px;margin-bottom:2px}}
.msg-avatar{{width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0}}
.msg-name{{font-size:13px;font-weight:700}}
.msg-time{{font-size:11px;color:#616467}}
.msg-body{{font-size:14px;line-height:1.55;color:#d1d2d3;padding-left:36px;word-break:break-word}}
.chat-msg-user .msg-body{{color:#e8e8e8}}

/* Tool call - compact */
.chat-tool-call{{display:flex;align-items:center;gap:6px;padding:2px 0 2px 36px;font-size:12px;color:#7a7c80}}
.chat-tool-call .tool-icon{{font-size:11px;color:#616467}}
.chat-tool-call .tool-name{{color:#1d9bd1;font-weight:500}}
.chat-tool-call .tool-summary{{color:#616467;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:600px}}

/* Tool result - compact */
.chat-tool-result{{display:flex;align-items:flex-start;gap:6px;padding:1px 0 1px 36px;font-size:11px;color:#616467}}
.chat-tool-result .tool-icon{{color:#616467;flex-shrink:0;margin-top:2px}}
.chat-tool-result .tool-result-text{{font-family:'SF Mono','Fira Code',monospace;font-size:11px;color:#616467;max-height:60px;overflow:hidden;word-break:break-all}}

/* Show all mode */
.show-all .chat-thread{{display:flex !important}}
.show-all .chat-thread+.chat-thread{{margin-top:8px;border-top:1px solid #35373b;padding-top:8px}}

/* Hide tool calls mode */
.hide-tools .chat-tool-call,
.hide-tools .chat-tool-result{{display:none}}

/* Empty state */
.empty-state{{display:flex;align-items:center;justify-content:center;flex:1;color:#616467;font-size:14px}}

/* Scrollbar */
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:#35373b;border-radius:3px}}
::-webkit-scrollbar-thumb:hover{{background:#4a4d52}}

@media(max-width:768px){{
    .sidebar{{width:180px}}
    .msg-body,.chat-msg{{padding-left:0}}
}}
</style>
</head>
<body>

<div class="topbar">
    <div class="topbar-title">AI Agency HQ</div>
    <div class="topbar-sub">Agent Chat Logs - {generated_time}</div>
    <div class="topbar-right">
        <button class="topbar-btn" onclick="toggleShowAll(this)" id="btn-all">Show All</button>
        <button class="topbar-btn" onclick="toggleTools(this)" id="btn-tools">Hide Tools</button>
    </div>
</div>

<div class="app">
    <nav class="sidebar">
        {sidebar_html}
    </nav>
    <div class="chat-area" id="chatArea">
        <div class="empty-state" id="emptyState">&#8592; Select a conversation</div>
        {all_threads}
    </div>
</div>

<script>
function showThread(id) {{
    const area = document.getElementById('chatArea');
    area.classList.remove('show-all');
    document.getElementById('btn-all').classList.remove('active');

    document.querySelectorAll('.chat-thread').forEach(t => t.classList.remove('visible'));
    document.querySelectorAll('.channel-link').forEach(l => l.classList.remove('active'));

    const thread = document.getElementById(id);
    if (thread) {{
        thread.classList.add('visible');
        document.getElementById('emptyState').style.display = 'none';
        const msgs = thread.querySelector('.chat-messages');
        if (msgs) msgs.scrollTop = 0;
    }}
    const link = document.querySelector(`[data-target="${{id}}"]`);
    if (link) link.classList.add('active');
}}

function toggleShowAll(btn) {{
    const area = document.getElementById('chatArea');
    const isAll = area.classList.toggle('show-all');
    btn.classList.toggle('active', isAll);
    document.getElementById('emptyState').style.display = isAll ? 'none' : '';
    if (isAll) {{
        document.querySelectorAll('.chat-thread').forEach(t => t.classList.remove('visible'));
        document.querySelectorAll('.channel-link').forEach(l => l.classList.remove('active'));
    }}
}}

function toggleTools(btn) {{
    const area = document.getElementById('chatArea');
    const hidden = area.classList.toggle('hide-tools');
    btn.textContent = hidden ? 'Show Tools' : 'Hide Tools';
    btn.classList.toggle('active', hidden);
}}

// Auto-select first channel
const firstLink = document.querySelector('.channel-link');
if (firstLink) firstLink.click();
</script>
</body>
</html>'''


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    html_content = generate_html(session_id)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "subagent-logs.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
