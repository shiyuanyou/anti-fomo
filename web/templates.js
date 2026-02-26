/**
 * Anti-FOMO v2 — Template Library View
 * Fetches /api/templates and renders template cards in the templates grid.
 */

// ============================================================
//  Risk level badge colors
// ============================================================

const RISK_COLORS = {
    "低":   { bg: "rgba(16, 185, 129, 0.12)", border: "rgba(16, 185, 129, 0.3)", text: "#34D399" },
    "中":   { bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.3)", text: "#38BDF8" },
    "中高": { bg: "rgba(245, 158, 11, 0.12)", border: "rgba(245, 158, 11, 0.3)", text: "#FBBF24" },
    "高":   { bg: "rgba(239, 68, 68, 0.12)",  border: "rgba(239, 68, 68, 0.3)",  text: "#F87171" },
};

// Palette for allocation bars
const ALLOC_PALETTE = [
    "#38BDF8", "#818CF8", "#34D399", "#FBBF24", "#F87171",
    "#A78BFA", "#F472B6", "#2DD4BF", "#FB923C", "#A3E635",
];

// ============================================================
//  Template card rendering
// ============================================================

function renderTemplateCard(tmpl) {
    const risk = RISK_COLORS[tmpl.risk_level] || RISK_COLORS["中"];
    const m = tmpl.metrics;

    // Allocation bar segments
    const allocBars = tmpl.allocations.map((a, i) => {
        const pct = (a.weight * 100).toFixed(0);
        const color = ALLOC_PALETTE[i % ALLOC_PALETTE.length];
        return `<div class="alloc-bar-seg" style="width:${pct}%;background:${color}" title="${a.category} ${pct}%"></div>`;
    }).join("");

    // Allocation legend chips
    const allocChips = tmpl.allocations.map((a, i) => {
        const color = ALLOC_PALETTE[i % ALLOC_PALETTE.length];
        const pct = (a.weight * 100).toFixed(0);
        return `<span class="alloc-chip">
            <span class="alloc-dot" style="background:${color}"></span>
            ${a.category} <span class="alloc-chip-pct">${pct}%</span>
        </span>`;
    }).join("");

    // Personality tags
    const tagHtml = tmpl.personality_tags.map(t =>
        `<span class="ptag">${t}</span>`
    ).join("");

    // Metric sign helpers
    const drawdownStr = m.max_drawdown < 0
        ? m.max_drawdown.toFixed(1) + "%"
        : "+" + m.max_drawdown.toFixed(1) + "%";

    return `
    <div class="template-card" data-id="${tmpl.id}">
        <div class="tcard-header">
            <div class="tcard-title-row">
                <span class="tcard-name">${tmpl.name}</span>
                <span class="risk-badge" style="background:${risk.bg};border-color:${risk.border};color:${risk.text}">${tmpl.risk_level}风险</span>
            </div>
            <p class="tcard-tagline">${tmpl.tagline}</p>
            <p class="tcard-audience">${tmpl.target_audience}</p>
        </div>

        <div class="tcard-alloc">
            <div class="alloc-bar">${allocBars}</div>
            <div class="alloc-chips">${allocChips}</div>
        </div>

        <div class="tcard-metrics">
            <div class="metric-item">
                <span class="metric-label">年化收益</span>
                <span class="metric-value metric-pos">+${m.annualized_return.toFixed(1)}%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">年化波动</span>
                <span class="metric-value">${m.annualized_volatility.toFixed(1)}%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">最大回撤</span>
                <span class="metric-value metric-neg">${drawdownStr}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">夏普比率</span>
                <span class="metric-value">${m.sharpe_ratio.toFixed(2)}</span>
            </div>
        </div>

        <div class="tcard-personality">
            <div class="ptags">${tagHtml}</div>
            <p class="personality-desc">${tmpl.personality_description}</p>
        </div>

        <div class="tcard-footer">
            <span class="data-period ${m.data_period.includes('真实') ? 'data-period-real' : 'data-period-est'}">${m.data_period}</span>
            <button class="btn btn-compare-from-card" data-id="${tmpl.id}">
                与我的配置对比
            </button>
        </div>
    </div>`;
}

// ============================================================
//  Load and render templates
// ============================================================

async function loadTemplates() {
    const grid = document.getElementById("templates-grid");
    if (!grid) return;

    try {
        const resp = await fetch("/api/templates");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const templates = await resp.json();

        if (!templates.length) {
            grid.innerHTML = `<div class="templates-loading">暂无模板数据</div>`;
            return;
        }

        grid.innerHTML = templates.map(renderTemplateCard).join("");

        // Wire "与我的配置对比" buttons
        grid.querySelectorAll(".btn-compare-from-card").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const templateId = btn.dataset.id;
                switchToCompareView(templateId);
            });
        });

        // Populate the compare view template selector
        populateCompareSelect(templates);

    } catch (err) {
        grid.innerHTML = `<div class="templates-loading" style="color:#F87171">加载失败: ${err.message}</div>`;
    }
}

function populateCompareSelect(templates) {
    const sel = document.getElementById("compare-template-select");
    if (!sel) return;
    sel.innerHTML = `<option value="">-- 请选择模板 --</option>` +
        templates.map(t => `<option value="${t.id}">${t.name} — ${t.tagline}</option>`).join("");
}

// ============================================================
//  View switching helper (called by compare buttons in cards)
// ============================================================

function switchToCompareView(templateId) {
    // Switch to compare view
    document.querySelectorAll(".view-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));
    const tab = document.querySelector(`.view-tab[data-view="compare"]`);
    if (tab) tab.classList.add("active");
    const panel = document.getElementById("view-compare");
    if (panel) panel.classList.add("active");

    // Pre-select the template
    const sel = document.getElementById("compare-template-select");
    if (sel && templateId) sel.value = templateId;
}

// ============================================================
//  Init (called from global init after DOM ready)
// ============================================================

function initTemplatesView() {
    loadTemplates();
}
