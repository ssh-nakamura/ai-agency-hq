// ── State ──
let chatData = {};
let hideTools = true;
let researchData = null;
let overviewPollTimer = null;

// ── Utilities ──
function esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}
function fmtT(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return n.toString();
}
function fmtNum(n) { return n.toLocaleString(); }

// ── Tab Switching ──
function startOverviewPoll() {
    stopOverviewPoll();
    overviewPollTimer = setInterval(() => { loadOverview(); }, 30000);
}
function stopOverviewPoll() {
    if (overviewPollTimer) { clearInterval(overviewPollTimer); overviewPollTimer = null; }
}

document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById("panel-" + btn.dataset.tab).classList.add("active");
        if (btn.dataset.tab === "agents" && !chatData.dms) loadAgents();
        if (btn.dataset.tab === "roadmap") loadRoadmap();
        if (btn.dataset.tab === "usage") loadUsage();
        if (btn.dataset.tab === "research" && !researchData) loadResearch();
        if (btn.dataset.tab === "niche") loadNiche();
        // Auto-polling for overview
        if (btn.dataset.tab === "overview") { startOverviewPoll(); }
        else { stopOverviewPoll(); }
    });
});

// ══════════════════════════════════════════════════════════
// OVERVIEW TAB
// ══════════════════════════════════════════════════════════

async function loadOverview() {
    const el = document.getElementById("overviewContent");
    try {
        const [kpi, health, actions, logs] = await Promise.all([
            fetch("/api/kpi").then(r => r.json()),
            fetch("/api/health").then(r => r.json()),
            fetch("/api/actions").then(r => r.json()),
            fetch("/api/logs").then(r => r.json()),
        ]);
        el.innerHTML = renderOverview(kpi, health, actions, logs);
        updateHealthDot(health);
    } catch (e) {
        el.innerHTML = '<div style="color:#f87171;padding:40px">Failed to load overview: ' + esc(e.message) + '</div>';
    }
}

function updateHealthDot(health) {
    const dot = document.getElementById("healthDot");
    const txt = document.getElementById("healthText");
    if (health.errors > 0) {
        dot.className = "status-dot";
        txt.textContent = `Error: ${health.errors}`;
    } else if (health.warnings > 0) {
        dot.className = "status-dot warn";
        txt.textContent = `Warn: ${health.warnings}`;
    } else {
        dot.className = "status-dot ok";
        txt.textContent = "All OK";
    }
}

function renderOverview(kpi, health, actions, logs) {
    const actual = kpi.kpi?.actual || {};
    const phase = kpi.phase || {};

    // KPI Cards
    let html = `
    <div style="margin-bottom:16px;font-size:12px;color:#666">
        Phase: <strong style="color:#5b8def">${esc(phase.step || "?")}</strong>
        &nbsp;&middot;&nbsp; Updated: ${esc(kpi.lastUpdated || "?")}
    </div>
    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-label">Revenue</div>
            <div class="kpi-val">&yen;${fmtNum(actual.revenue || 0)}</div>
            <div class="kpi-sub">Monthly</div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Users</div>
            <div class="kpi-val">${fmtNum(actual.users || 0)}</div>
            <div class="kpi-sub">ShieldMe</div>
        </div>
        <div class="kpi">
            <div class="kpi-label">X Followers</div>
            <div class="kpi-val">${fmtNum(actual.xFollowers || 0)}</div>
            <div class="kpi-sub">@ai_agency_jp</div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Operating Cost</div>
            <div class="kpi-val">&yen;${fmtNum(actual.operatingCost || 0)}</div>
            <div class="kpi-sub">/month</div>
        </div>
    </div>`;

    // Two-column: Health + Actions
    html += '<div class="two-col">';

    // Health Check
    const hBadge = health.errors > 0
        ? `<span class="badge badge-ng">${health.errors} errors</span>`
        : health.warnings > 0
            ? `<span class="badge badge-warn">${health.warnings} warns</span>`
            : `<span class="badge badge-ok">All OK</span>`;

    html += `<div class="section">
        <div class="section-title">Health Check ${hBadge}</div>`;

    for (const check of health.checks) {
        if (check.items) {
            // File check or memory check: summarize
            const ok = check.items.filter(i => i.ok || i.char).length;
            const total = check.items.length;
            const allOk = ok === total;
            html += `<div class="check-row">
                <div class="check-dot ${allOk ? 'ok' : 'ng'}"></div>
                <span class="check-label">${esc(check.name)}</span>
                <span class="check-detail">${ok}/${total}</span>
            </div>`;
        } else if (check.name === "フェーズ整合性") {
            html += `<div class="check-row">
                <div class="check-dot ${check.ok ? 'ok' : 'ng'}"></div>
                <span class="check-label">${esc(check.name)}</span>
                <span class="check-detail">${esc(check.current || "不整合")}</span>
            </div>`;
        } else if (check.name === "コスト整合") {
            const cls = check.ok === true ? "ok" : check.ok === false ? "ng" : "warn";
            html += `<div class="check-row">
                <div class="check-dot ${cls}"></div>
                <span class="check-label">${esc(check.name)}</span>
                <span class="check-detail">${esc(check.detail)}</span>
            </div>`;
        } else if (check.name === "要調査チェック") {
            html += `<div class="check-row">
                <div class="check-dot ${check.count === 0 ? 'ok' : 'warn'}"></div>
                <span class="check-label">${esc(check.name)}</span>
                <span class="check-detail">${check.count === 0 ? "なし" : check.count + "箇所"}</span>
            </div>`;
        } else if (check.name === "完了済みアクション") {
            html += `<div class="check-row">
                <div class="check-dot ${check.over ? 'warn' : 'ok'}"></div>
                <span class="check-label">${esc(check.name)}</span>
                <span class="check-detail">${check.count}件${check.over ? " (要アーカイブ)" : ""}</span>
            </div>`;
        }
    }
    html += '</div>';

    // Actions
    html += `<div class="section">
        <div class="section-title">Priority Actions <span class="badge badge-warn">${(actions.priority || []).length + (actions.next || []).length} pending</span></div>
        <table class="action-table">
            <tr><th>ID</th><th>Action</th><th>Assignee</th><th>Status</th></tr>`;

    for (const row of (actions.priority || [])) {
        html += `<tr>
            <td class="id">${esc(row[0])}</td>
            <td>${esc(row[1])}</td>
            <td>${esc(row[2])}</td>
            <td><span class="status s-pending">${esc(row[3] || "未着手")}</span></td>
        </tr>`;
    }
    for (const row of (actions.next || [])) {
        html += `<tr>
            <td class="id">${esc(row[0])}</td>
            <td>${esc(row[1])}</td>
            <td>${esc(row[2])}</td>
            <td><span class="status s-pending">${esc(row[3] || "未着手")}</span></td>
        </tr>`;
    }
    html += '</table></div>';
    html += '</div>'; // end two-col

    // Approval waiting
    if (actions.approval && actions.approval.length > 0) {
        html += `<div class="section">
            <div class="section-title">Awaiting Shareholder Approval <span class="badge badge-warn">${actions.approval.length}</span></div>
            <table class="action-table">
                <tr><th>ID</th><th>Item</th><th>Amount</th><th>Note</th></tr>`;
        for (const row of actions.approval) {
            html += `<tr>
                <td class="id">${esc(row[0])}</td>
                <td>${esc(row[1])}</td>
                <td>${esc(row[2] || "")}</td>
                <td>${esc(row[3] || "")}</td>
            </tr>`;
        }
        html += '</table></div>';
    }

    // Latest session log
    if (logs.logs && logs.logs.length > 0) {
        const latest = logs.logs[0];
        html += `<div class="section">
            <div class="section-title">Latest Session Log <span style="font-size:11px;color:#666;font-weight:400">${esc(latest.name)}</span></div>
            <div class="log-content">${esc(latest.content)}</div>
        </div>`;
    }

    return html;
}


// ══════════════════════════════════════════════════════════
// AGENTS TAB
// ══════════════════════════════════════════════════════════

async function loadAgents() {
    try {
        const r = await fetch("/api/agents");
        chatData = await r.json();
        renderSidebar();
        if (chatData.teams && chatData.teams.length > 0) selectView("team", 0);
        else if (chatData.dms && chatData.dms.length > 0) selectView("dm", 0);
    } catch (e) { console.error(e); }
}

function renderSidebar() {
    let html = "";
    if (chatData.teams && chatData.teams.length > 0) {
        html += '<div class="sidebar-header">Teams</div>';
        chatData.teams.forEach((t, i) => {
            const names = t.member_names.slice(0, 3).join(", ");
            const extra = t.member_names.length > 3 ? ` +${t.member_names.length - 3}` : "";
            html += `<div class="sidebar-item" data-type="team" data-idx="${i}" onclick="selectView('team',${i})">
                <div class="si-team-avatar">&#128101;</div>
                <div class="si-info">
                    <div class="si-name">Team ${esc(t.session)}</div>
                    <div class="si-sub">${esc(names)}${extra}</div>
                </div>
                <span class="si-badge">${t.msg_count}</span>
            </div>`;
        });
    }
    if (chatData.dms && chatData.dms.length > 0) {
        html += '<div class="sidebar-header">Direct Messages</div>';
        chatData.dms.forEach((d, i) => {
            html += `<div class="sidebar-item" data-type="dm" data-idx="${i}" onclick="selectView('dm',${i})">
                <div class="si-avatar" style="background:${d.color}">${esc(d.initials)}</div>
                <div class="si-info">
                    <div class="si-name">${esc(d.name)}</div>
                    <div class="si-sub">${esc(d.role)} &middot; ${esc(d.session_label)}</div>
                </div>
                <span class="si-badge">${d.msg_count}</span>
            </div>`;
        });
    }
    document.getElementById("agentsSidebar").innerHTML = html;
}

function selectView(type, idx) {
    document.querySelectorAll(".sidebar-item").forEach(el => el.classList.remove("active"));
    const el = document.querySelector(`.sidebar-item[data-type="${type}"][data-idx="${idx}"]`);
    if (el) el.classList.add("active");
    if (type === "team") renderTeamChat(idx);
    else renderDMChat(idx);
}

function renderDMChat(idx) {
    const d = chatData.dms[idx];
    if (!d) return;
    const panel = document.getElementById("chatPanel");
    panel.innerHTML = `
    <div class="chat-header">
        <div class="ch-avatar" style="background:${d.color}">${esc(d.initials)}</div>
        <div class="ch-info"><h3>${esc(d.name)}</h3><p>${esc(d.role)}</p></div>
        <div class="ch-meta">IN ${fmtT(d.tokens_in)} / OUT ${fmtT(d.tokens_out)}<br>${esc(d.session_label)} - ${esc(d.time_end)}</div>
    </div>
    <div class="toggle-row">
        <button class="toggle-btn ${hideTools ? 'active' : ''}" onclick="toggleTools()">Hide Tools</button>
    </div>
    <div class="chat-body ${hideTools ? 'hide-tools' : ''}" id="chatBody">
        ${renderBubbles(d.messages, d.agent_key, "dm")}
    </div>`;
}

function renderTeamChat(idx) {
    const t = chatData.teams[idx];
    if (!t) return;
    const panel = document.getElementById("chatPanel");
    const AGENTS = window._AGENTS || {};
    const avatars = t.members.map(k => {
        const a = AGENTS[k] || { color: "#888", initials: "?" };
        return `<div class="ch-avatar" style="background:${a.color};width:28px;height:28px;font-size:12px;margin-left:-6px">${a.initials}</div>`;
    }).join("");

    panel.innerHTML = `
    <div class="chat-header">
        <div style="display:flex;padding-left:6px">${avatars}</div>
        <div class="ch-info"><h3>Team ${esc(t.session)}</h3><p>${esc(t.member_names.join(", "))}</p></div>
        <div class="ch-meta">IN ${fmtT(t.tokens_in)} / OUT ${fmtT(t.tokens_out)}<br>${esc(t.label)}</div>
    </div>
    <div class="toggle-row">
        <button class="toggle-btn ${hideTools ? 'active' : ''}" onclick="toggleTools()">Hide Tools</button>
    </div>
    <div class="chat-body ${hideTools ? 'hide-tools' : ''}" id="chatBody">
        ${renderBubbles(t.messages, null, "team")}
    </div>`;
}

function renderBubbles(messages, dmAgentKey, mode) {
    let html = "";
    let lastSender = "";
    for (const m of messages) {
        if (m.role === "tool") {
            html += `<div class="msg-tool"><span class="tn">${esc(m.name)}</span> ${esc(m.input || "")}</div>`;
            continue;
        }
        const sender = m.sender;
        const continued = sender === lastSender;
        lastSender = sender;
        let side = "left";
        if (mode === "dm" && m.role === "assistant") side = "right";

        const avHidden = continued ? "hidden" : "";
        const nameHtml = continued ? ""
            : `<div class="msg-name" style="color:${m.sender_color}">${esc(m.sender_name)} <span class="ts">${esc(m.time)}</span></div>`;

        html += `<div class="msg-row ${side} ${continued ? 'continued' : ''}">
            <div class="msg-avatar ${avHidden}" style="background:${m.sender_color}">${esc(m.sender_initials)}</div>
            <div class="msg-content">
                ${nameHtml}
                <div class="bubble ${side}">${esc(m.text)}</div>
            </div>
        </div>`;
    }
    return html;
}

function toggleTools() {
    hideTools = !hideTools;
    const body = document.getElementById("chatBody");
    if (body) body.classList.toggle("hide-tools", hideTools);
    document.querySelectorAll(".toggle-btn").forEach(b => b.classList.toggle("active", hideTools));
}


// ══════════════════════════════════════════════════════════
// ROADMAP TAB
// ══════════════════════════════════════════════════════════

async function loadRoadmap() {
    try {
        const r = await fetch("/api/roadmap");
        const d = await r.json();
        document.getElementById("roadmapContent").innerHTML = renderRoadmap(d.markdown);
    } catch (e) {
        document.getElementById("roadmapContent").innerHTML = "Error loading roadmap";
    }
}

function renderRoadmap(md) {
    const lines = md.split("\n");
    let html = "";
    let inTable = false;
    let tasks = [];
    const colors = ["#3b82f6", "#eab308", "#ec4899"];
    let phaseIdx = -1;

    for (const line of lines) {
        if (line.startsWith("## Phase")) {
            if (inTable) { html += renderRoadmapTasks(tasks); tasks = []; inTable = false; }
            phaseIdx++;
            const m = line.match(/Phase (\d+): (.+)/);
            if (m) {
                const color = colors[parseInt(m[1])] || "#888";
                const tag = phaseIdx === 0
                    ? '<span class="phase-tag" style="background:#5b8def20;color:#5b8def">Active</span>'
                    : '<span class="phase-tag" style="background:#33333320;color:#888">Upcoming</span>';
                html += `<div class="phase"><div class="phase-head" style="background:${color}08">
                    <div class="phase-num" style="background:${color}">${m[1]}</div>
                    <div class="phase-info"><h3>${esc(m[2])}</h3></div>${tag}
                </div>`;
            }
        } else if (line.startsWith("### ")) {
            if (inTable) { html += renderRoadmapTasks(tasks); tasks = []; }
            html += `<div class="step"><div class="step-name">${esc(line.replace(/^### /, ""))}</div>`;
            inTable = true;
        } else if (inTable && line.startsWith("|") && !line.includes("---") && !line.includes("Task")) {
            const cols = line.split("|").map(c => c.trim()).filter(Boolean);
            if (cols.length >= 3) {
                const done = /done|complete|完了/i.test(cols[2]);
                tasks.push({ name: cols[0], assignee: cols[1], condition: cols[2], done });
            }
        }
    }
    if (inTable) { html += renderRoadmapTasks(tasks); }
    return html;
}

function renderRoadmapTasks(tasks) {
    let html = "";
    for (const t of tasks) {
        const cls = t.done ? "s-done" : "s-pending";
        html += `<div class="task-row">
            <span class="task-status ${cls}">${t.done ? "Done" : "Pending"}</span>
            <span class="task-name">${esc(t.name)}</span>
            <span class="task-assignee">${esc(t.assignee)}</span>
        </div>`;
    }
    html += "</div>";
    return html;
}


// ══════════════════════════════════════════════════════════
// USAGE TAB
// ══════════════════════════════════════════════════════════

async function loadUsage() {
    const el = document.getElementById("usageContent");
    try {
        const r = await fetch("http://localhost:3333/api/stats");
        if (!r.ok) throw new Error("ccboard not running");
        const d = await r.json();
        el.innerHTML = renderUsage(d);
    } catch (e) {
        el.innerHTML = `<div class="usage-banner err">
            ccboard API not available.<br>
            <code style="background:#0a0a0a;padding:2px 8px;border-radius:4px;font-size:12px">
                ccboard web --port 3333 &
            </code>
        </div>`;
    }
}

function renderUsage(d) {
    const models = d.modelUsage || {};
    const cacheHit = ((d.cacheHitRatio || 0) * 100).toFixed(1);
    let opusT = 0, sonnetT = 0, haikuT = 0;
    for (const [n, m] of Object.entries(models)) {
        const t = (m.inputTokens || 0) + (m.outputTokens || 0);
        if (n.includes("opus")) opusT += t;
        else if (n.includes("sonnet")) sonnetT += t;
        else haikuT += t;
    }
    const total = opusT + sonnetT + haikuT;
    const opusPct = total > 0 ? (opusT / total * 100) : 0;
    const daily = d.dailyActivity || [];
    const maxM = Math.max(...daily.map(x => x.messageCount), 1);

    return `
    <div class="usage-banner"><strong>Max Plan $100/mo</strong> - Rate limit consumption is the key metric</div>
    <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">Sessions</div><div class="kpi-val">${d.totalSessions || 0}</div><div class="kpi-sub">${fmtNum(d.totalMessages || 0)} msgs</div></div>
        <div class="kpi"><div class="kpi-label">Cache Hit</div><div class="kpi-val">${cacheHit}%</div><div class="kpi-sub">${parseFloat(cacheHit) > 95 ? "Excellent" : "Needs improvement"}</div></div>
        <div class="kpi"><div class="kpi-label">Opus Rate</div><div class="kpi-val">${opusPct.toFixed(0)}%</div><div class="kpi-sub">${opusPct > 70 ? "High - throttle risk" : opusPct > 40 ? "Moderate" : "Efficient"}</div></div>
        <div class="kpi"><div class="kpi-label">Total Tokens</div><div class="kpi-val">${fmtT(total)}</div><div class="kpi-sub">Opus:${fmtT(opusT)} Son:${fmtT(sonnetT)} Hai:${fmtT(haikuT)}</div></div>
    </div>
    <div class="section">
        <div class="section-title">Daily Activity (last 14 days)</div>
        <div style="display:flex;align-items:flex-end;gap:4px;height:80px">
            ${daily.slice(-14).map(day => {
                const h = Math.max((day.messageCount / maxM) * 100, 3);
                return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px">
                    <span style="font-size:9px;color:#888">${day.messageCount}</span>
                    <div style="width:100%;height:${h}%;background:linear-gradient(180deg,#5b8def,#2563eb);border-radius:3px 3px 0 0;min-height:2px"></div>
                    <span style="font-size:9px;color:#555">${day.date.slice(5)}</span>
                </div>`;
            }).join("")}
        </div>
    </div>`;
}


// ══════════════════════════════════════════════════════════
// RESEARCH TAB
// ══════════════════════════════════════════════════════════

async function loadResearch() {
    const sidebar = document.getElementById("researchSidebar");
    try {
        const r = await fetch("/api/research");
        researchData = await r.json();
        renderResearchSidebar();
    } catch (e) {
        sidebar.innerHTML = '<div class="sidebar-header">Research Files</div><div style="padding:16px;color:#f87171;font-size:13px">Failed to load: ' + esc(e.message) + '</div>';
    }
}

function renderResearchSidebar() {
    const sidebar = document.getElementById("researchSidebar");
    const files = researchData.files || [];
    let html = '<div class="sidebar-header">Research Files <span style="color:#555;font-weight:400">(' + files.length + ')</span></div>';
    if (files.length === 0) {
        html += '<div style="padding:16px;color:#555;font-size:13px">No research files found</div>';
    }
    files.forEach((f, i) => {
        html += '<div class="sidebar-item research-file-item" data-idx="' + i + '" onclick="selectResearchFile(' + i + ')">'
            + '<div class="research-file-icon"></div>'
            + '<div class="si-info">'
            + '<div class="si-name">' + esc(f.title) + '</div>'
            + '<div class="si-sub">' + f.lines + ' lines</div>'
            + '</div></div>';
    });
    sidebar.innerHTML = html;
}

function selectResearchFile(idx) {
    document.querySelectorAll(".research-file-item").forEach(el => el.classList.remove("active"));
    const el = document.querySelector('.research-file-item[data-idx="' + idx + '"]');
    if (el) el.classList.add("active");
    const f = researchData.files[idx];
    if (!f) return;
    const main = document.getElementById("researchMain");
    main.innerHTML = '<div class="research-reader"><h1 class="research-title">' + esc(f.title) + '</h1>'
        + '<div class="research-meta">' + esc(f.name) + ' &middot; ' + f.lines + ' lines &middot; ' + (f.size / 1024).toFixed(1) + ' KB</div>'
        + '<div class="research-body">' + renderMarkdown(f.content) + '</div></div>';
}

function renderMarkdown(md) {
    const lines = md.split("\n");
    let html = "";
    let inCode = false;
    let codeLang = "";
    let codeLines = [];
    let inList = false;
    let listItems = [];
    let inTable = false;
    let tableRows = [];
    let paragraph = [];

    function flushParagraph() {
        if (paragraph.length > 0) {
            html += "<p>" + paragraph.join(" ") + "</p>";
            paragraph = [];
        }
    }
    function flushList() {
        if (inList && listItems.length > 0) {
            html += "<ul>" + listItems.map(li => "<li>" + li + "</li>").join("") + "</ul>";
            listItems = [];
            inList = false;
        }
    }
    function flushTable() {
        if (inTable && tableRows.length > 0) {
            let t = "<table><thead><tr>";
            const header = tableRows[0];
            for (const cell of header) { t += "<th>" + cell + "</th>"; }
            t += "</tr></thead><tbody>";
            for (let i = 1; i < tableRows.length; i++) {
                t += "<tr>";
                for (const cell of tableRows[i]) { t += "<td>" + cell + "</td>"; }
                t += "</tr>";
            }
            t += "</tbody></table>";
            html += t;
            tableRows = [];
            inTable = false;
        }
    }

    function inlineFormat(text) {
        // Bold
        text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        // Inline code
        text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
        // Links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        return text;
    }

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Code block toggle
        if (line.trimStart().startsWith("```")) {
            if (!inCode) {
                flushParagraph(); flushList(); flushTable();
                inCode = true;
                codeLang = line.trimStart().slice(3).trim();
                codeLines = [];
            } else {
                html += '<pre><code' + (codeLang ? ' class="lang-' + esc(codeLang) + '"' : '') + '>' + esc(codeLines.join("\n")) + '</code></pre>';
                inCode = false;
                codeLang = "";
                codeLines = [];
            }
            continue;
        }
        if (inCode) { codeLines.push(line); continue; }

        // Headings
        if (line.startsWith("### ")) {
            flushParagraph(); flushList(); flushTable();
            html += "<h3>" + inlineFormat(esc(line.slice(4))) + "</h3>";
            continue;
        }
        if (line.startsWith("## ")) {
            flushParagraph(); flushList(); flushTable();
            html += "<h2>" + inlineFormat(esc(line.slice(3))) + "</h2>";
            continue;
        }
        if (line.startsWith("# ")) {
            flushParagraph(); flushList(); flushTable();
            html += "<h1>" + inlineFormat(esc(line.slice(2))) + "</h1>";
            continue;
        }

        // Table row
        if (line.startsWith("|")) {
            flushParagraph(); flushList();
            const cells = line.split("|").slice(1, -1).map(c => inlineFormat(esc(c.trim())));
            // Skip separator rows
            if (cells.every(c => /^[-:]+$/.test(c.replace(/<[^>]+>/g, "")))) { continue; }
            if (!inTable) { inTable = true; tableRows = []; }
            tableRows.push(cells);
            continue;
        }
        if (inTable) { flushTable(); }

        // List item
        if (/^[-*] /.test(line.trimStart())) {
            flushParagraph(); if (!inTable) flushTable();
            inList = true;
            listItems.push(inlineFormat(esc(line.trimStart().slice(2))));
            continue;
        }
        if (inList) { flushList(); }

        // Blockquote
        if (line.startsWith("> ")) {
            flushParagraph(); flushList(); flushTable();
            html += "<blockquote>" + inlineFormat(esc(line.slice(2))) + "</blockquote>";
            continue;
        }

        // Horizontal rule
        if (/^---+$/.test(line.trim())) {
            flushParagraph(); flushList(); flushTable();
            html += "<hr>";
            continue;
        }

        // Empty line = paragraph break
        if (line.trim() === "") {
            flushParagraph(); flushList(); flushTable();
            continue;
        }

        // Regular text
        paragraph.push(inlineFormat(esc(line)));
    }
    flushParagraph(); flushList(); flushTable();
    if (inCode && codeLines.length > 0) {
        html += '<pre><code>' + esc(codeLines.join("\n")) + '</code></pre>';
    }
    return html;
}


// ══════════════════════════════════════════════════════════
// NICHE TAB
// ══════════════════════════════════════════════════════════

let nicheData = null;

async function loadNiche() {
    const sidebar = document.getElementById("nicheSidebar");
    try {
        const r = await fetch("/api/niche-scans");
        nicheData = await r.json();
        renderNicheSidebar();
    } catch (e) {
        sidebar.innerHTML = '<div class="sidebar-header">Niche Scans</div><div style="padding:16px;color:#f87171;font-size:13px">Failed: ' + esc(e.message) + '</div>';
    }
}

function renderNicheSidebar() {
    const sidebar = document.getElementById("nicheSidebar");
    const scans = nicheData.scans || [];
    let html = '<div class="sidebar-header">Niche Scans <span style="color:#555;font-weight:400">(' + scans.length + ')</span></div>';
    if (scans.length === 0) {
        html += '<div style="padding:16px;color:#555;font-size:13px">No scans found.<br><code style="font-size:11px">python3 tools/niche-analyzer/cli.py evaluate --help</code></div>';
        sidebar.innerHTML = html;
        return;
    }
    scans.forEach((scan, si) => {
        html += '<div class="sidebar-subheader" style="display:flex;align-items:center;justify-content:space-between">'
            + esc(scan.date)
            + '<button class="report-btn" onclick="event.stopPropagation();openNicheReport(\'' + esc(scan.date) + '\')" title="Full Report">&#128202; Report</button>'
            + '</div>';
        scan.niches.forEach((n, ni) => {
            const views = n.yt_views_en + n.yt_views_jp;
            html += '<div class="sidebar-item niche-item" data-scan="' + si + '" data-niche="' + ni + '" onclick="selectNiche(' + si + ',' + ni + ')">'
                + '<div class="niche-icon">' + (n.yt_ratio > 3 ? '&#127775;' : n.yt_ratio > 1 ? '&#9733;' : '&#9898;') + '</div>'
                + '<div class="si-info">'
                + '<div class="si-name">' + esc(n.keyword_jp || n.id) + '</div>'
                + '<div class="si-sub">YT ' + fmtNum(views) + ' views</div>'
                + '</div></div>';
        });
    });
    sidebar.innerHTML = html;
}

function openNicheReport(scanDate) {
    const main = document.getElementById("nicheMain");
    document.querySelectorAll(".niche-item").forEach(el => el.classList.remove("active"));
    main.innerHTML = '<iframe src="/api/niche-report?date=' + encodeURIComponent(scanDate)
        + '" style="width:100%;height:100%;border:none;background:#0a0a0a"></iframe>';
}

function selectNiche(scanIdx, nicheIdx) {
    document.querySelectorAll(".niche-item").forEach(el => el.classList.remove("active"));
    const el = document.querySelector('.niche-item[data-scan="' + scanIdx + '"][data-niche="' + nicheIdx + '"]');
    if (el) el.classList.add("active");
    const scan = nicheData.scans[scanIdx];
    const niche = scan.niches[nicheIdx];
    renderNicheDetail(niche, scan.date);
}

function renderNicheDetail(niche, scanDate) {
    const main = document.getElementById("nicheMain");
    const d = niche.eval_data || {};
    const steps = d.steps || {};
    const s1 = steps.step1_demand || {};
    const s2 = steps.step2_engagement || {};
    const s4 = steps.step4_supply || {};
    const s5 = steps.step5_gap || {};
    const s6 = steps.step6_localization || {};
    const api = d.api_calls || {};

    // Score each step
    const stepScores = [
        scoreStep1(s1), scoreStep2(s2), scoreStep3(steps.step3_knowledge_gap || {}),
        scoreStep4(s4), scoreStep5(s5), scoreStep6(s6), scoreStep7(steps.step7_commercial || {}),
    ];
    const stepLabels = ["需要ボリューム", "エンゲージメント", "ナレッジギャップ", "競合供給量", "需給ギャップ", "ローカライズ倍率", "商業シグナル"];
    const total = stepScores.reduce((a, s) => a + s[0], 0);
    const maxTotal = stepScores.length * 3;
    const pct = (total / maxTotal * 100).toFixed(0);
    const colors = {3: "#22c55e", 2: "#eab308", 1: "#ef4444"};
    const stars = {3: "&#9733;&#9733;&#9733;", 2: "&#9733;&#9733;&#9734;", 1: "&#9733;&#9734;&#9734;"};
    const avgScore = Math.round(total / stepScores.length);
    const overallColor = colors[avgScore] || "#eab308";

    let html = '<div class="niche-detail">';

    // Header
    html += '<div class="niche-header"><h2>' + esc(d.niche_name_jp || niche.keyword_jp || niche.id) + ' / ' + esc(d.niche_name_en || niche.keyword_en || "") + '</h2>'
        + '<div class="niche-meta">Scan: ' + esc(scanDate) + ' | API: ' + (api.total || 0) + ' calls | Cost: $' + (api.estimated_cost_usd || 0).toFixed(2) + '</div></div>';

    // Overall score
    html += '<div class="niche-overall" style="border-color:' + overallColor + '40">'
        + '<div class="niche-score" style="color:' + overallColor + '">' + total + '/' + maxTotal + '</div>'
        + '<div class="niche-bar-wrap"><div class="niche-bar" style="width:' + pct + '%;background:' + overallColor + '"></div></div>'
        + '</div>';

    // Step cards grid
    html += '<div class="niche-steps-grid">';
    stepScores.forEach((s, i) => {
        const [score, comment] = s;
        html += '<div class="niche-step-card">'
            + '<div class="niche-step-head"><span>' + stepLabels[i] + '</span><span class="niche-step-stars" style="color:' + colors[score] + '">' + stars[score] + '</span></div>'
            + '<div class="niche-step-comment">' + esc(comment) + '</div>'
            + '</div>';
    });
    html += '</div>';

    // Data tables
    html += '<div class="niche-data-grid">';

    // Demand table
    html += '<div class="niche-data-card"><h3>Demand Volume</h3><table>'
        + '<tr><th>Source</th><th class="r">EN</th><th class="r">JP</th></tr>'
        + '<tr><td>YouTube Top 20</td><td class="r">' + fmtNum(s1.en?.yt_top20_views || 0) + '</td><td class="r">' + fmtNum(s1.jp?.yt_top20_views || 0) + '</td></tr>'
        + '<tr><td>Twitter 30d</td><td class="r">' + fmtNum(s1.en?.tweets_30d || 0) + '</td><td class="r">' + fmtNum(s1.jp?.tweets_30d || 0) + '</td></tr>'
        + '<tr><td>Reddit</td><td class="r">' + fmtNum(s1.en?.reddit_posts || 0) + '</td><td class="r">' + fmtNum(s1.jp?.reddit_posts || 0) + '</td></tr>'
        + '</table></div>';

    // Localization table
    html += '<div class="niche-data-card"><h3>Localization Ratio</h3><table>'
        + '<tr><th>Source</th><th class="r">EN/JP</th></tr>'
        + '<tr><td>YouTube</td><td class="r">' + (s6.yt_ratio || 0).toFixed(2) + 'x</td></tr>'
        + '<tr><td>Twitter</td><td class="r">' + (s6.twitter_ratio || 0).toFixed(2) + 'x</td></tr>'
        + '<tr><td>Publisher</td><td class="r">' + (s6.publisher_ratio || 0).toFixed(2) + 'x</td></tr>'
        + '</table></div>';

    html += '</div>';

    // Knowledge Gap raw (if available)
    const s3_jp = (steps.step3_knowledge_gap || {}).jp || {};
    if (s3_jp.grok_raw && s3_jp.grok_raw.length > 50) {
        html += '<div class="niche-data-card" style="margin-top:12px"><h3>Knowledge Gap (JP)</h3>'
            + '<div class="niche-raw">' + esc(s3_jp.grok_raw.substring(0, 1000)) + '</div></div>';
    }

    // Commercial raw (if available)
    const s7_jp = (steps.step7_commercial || {}).jp || {};
    if (s7_jp.grok_raw && s7_jp.grok_raw.length > 50) {
        html += '<div class="niche-data-card" style="margin-top:12px"><h3>Commercial Signals (JP)</h3>'
            + '<div class="niche-raw">' + esc(s7_jp.grok_raw.substring(0, 1000)) + '</div></div>';
    }

    html += '</div>';
    main.innerHTML = html;
}

function scoreStep1(s) {
    const yt = (s.en?.yt_top20_views || 0) + (s.jp?.yt_top20_views || 0);
    if (yt > 5e6) return [3, "Strong (" + fmtNum(yt) + " views)"];
    if (yt > 1e6) return [2, "Moderate (" + fmtNum(yt) + " views)"];
    return [1, "Low (" + fmtNum(yt) + " views)"];
}
function scoreStep2(s) {
    const avg = Math.max(s.en?.yt_avg_views || 0, s.jp?.yt_avg_views || 0);
    if (avg > 200000) return [3, "High avg " + fmtNum(Math.round(avg))];
    if (avg > 50000) return [2, "Moderate avg " + fmtNum(Math.round(avg))];
    return [1, "Low avg " + fmtNum(Math.round(avg))];
}
function scoreStep3(s) {
    const raw = s.jp?.grok_raw || "";
    if (raw.includes("ERROR")) return [1, "Grok failed"];
    if (raw.length > 500) return [3, "Rich how-to demand"];
    if (raw.length > 100) return [2, "Some questions"];
    return [1, "Minimal"];
}
function scoreStep4(s) {
    const pub = s.jp?.twitter_publishers || 0;
    if (pub > 30000) return [1, "Red ocean (" + fmtNum(pub) + ")"];
    if (pub > 10000) return [2, "Moderate (" + fmtNum(pub) + ")"];
    return [3, "Low competition (" + fmtNum(pub) + ")"];
}
function scoreStep5(s) {
    const gap = s.jp || 0;
    if (gap > 200) return [3, "High gap (" + Math.round(gap) + ")"];
    if (gap > 50) return [2, "Moderate (" + Math.round(gap) + ")"];
    return [1, "Low (" + Math.round(gap) + ")"];
}
function scoreStep6(s) {
    const r = s.yt_ratio || 1;
    if (r > 5) return [3, "Strong EN>JP (" + r.toFixed(1) + "x)"];
    if (r > 2) return [2, "Moderate (" + r.toFixed(1) + "x)"];
    return [1, "JP mature (" + r.toFixed(1) + "x)"];
}
function scoreStep7(s) {
    const raw = s.jp?.grok_raw || "";
    if (raw.includes("ERROR")) return [1, "Grok failed"];
    const kw = ["収益","アフィ","副業","稼","Brain","note","販売"];
    const hits = kw.filter(k => raw.includes(k)).length;
    if (hits >= 4) return [3, "Strong (" + hits + "/7)"];
    if (hits >= 2) return [2, "Some (" + hits + "/7)"];
    return [1, "Weak (" + hits + "/7)"];
}

// ══════════════════════════════════════════════════════════
// Init
// ══════════════════════════════════════════════════════════
loadOverview();
startOverviewPoll();
