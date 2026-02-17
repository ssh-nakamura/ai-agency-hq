// ── State ──
let chatData = {};
let hideTools = true;

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
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById("panel-" + btn.dataset.tab).classList.add("active");
        if (btn.dataset.tab === "agents" && !chatData.dms) loadAgents();
        if (btn.dataset.tab === "roadmap") loadRoadmap();
        if (btn.dataset.tab === "usage") loadUsage();
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
// Init
// ══════════════════════════════════════════════════════════
loadOverview();
