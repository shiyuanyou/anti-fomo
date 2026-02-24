/**
 * Anti-FOMO v2 — Compare View
 * Handles the user-config vs. template comparison UI:
 *   - Calls /api/compare, renders diff table + charts
 *   - Calls /api/ai/profile-match and /api/ai/migrate
 */

// ============================================================
//  State
// ============================================================

let _currentCompareResult = null;   // last ComparisonResult from /api/compare
let _currentTemplateId = null;      // currently selected template id

// ============================================================
//  Run comparison
// ============================================================

async function runCompare() {
    const sel = document.getElementById("compare-template-select");
    const display = document.getElementById("compare-display");
    if (!sel || !display) return;

    const templateId = sel.value;
    if (!templateId) {
        display.innerHTML = `<div class="compare-empty">
            <div class="compare-empty-icon">&#9635;</div>
            <p>请先选择一个模板</p>
        </div>`;
        return;
    }

    display.innerHTML = `<div class="compare-loading">对比计算中...</div>`;

    try {
        // Pass current assets from the portfolio view (window.assets from app.js)
        const body = { template_id: templateId };
        if (window.assets && window.assets.length > 0) {
            body.web_assets = window.assets;
        }

        const resp = await fetch("/api/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || `HTTP ${resp.status}`);
        }

        const result = await resp.json();
        _currentCompareResult = result;
        _currentTemplateId = templateId;

        renderCompareResult(result);

        // Show AI migrate panel now that a template is selected
        const migratePanel = document.getElementById("panel-ai-migrate");
        if (migratePanel) migratePanel.style.display = "";

    } catch (err) {
        display.innerHTML = `<div class="compare-loading" style="color:#F87171">对比失败: ${err.message}</div>`;
    }
}

// ============================================================
//  Render comparison result
// ============================================================

function renderCompareResult(result) {
    const display = document.getElementById("compare-display");
    if (!display) return;

    const um = result.user_metrics;
    const drawdownStr = v => (v < 0 ? v.toFixed(1) : "+" + v.toFixed(1)) + "%";

    // Build diff table rows
    const diffRows = result.diffs.map(d => {
        const devPct = (d.deviation * 100).toFixed(1);
        const devClass = d.deviation > 0.005 ? "dev-over" : d.deviation < -0.005 ? "dev-under" : "dev-neutral";
        const devLabel = d.deviation > 0.005 ? `+${devPct}%` : `${devPct}%`;
        return `<tr>
            <td class="diff-cat">${d.category}</td>
            <td class="diff-num">${(d.user_weight * 100).toFixed(1)}%</td>
            <td class="diff-num">${(d.template_weight * 100).toFixed(1)}%</td>
            <td class="diff-dev ${devClass}">${devLabel}</td>
        </tr>`;
    }).join("");

    display.innerHTML = `
    <div class="compare-result">

        <!-- Summary -->
        <div class="compare-summary-row">
            <div class="compare-summary-text">
                <span class="compare-vs-label">当前配置</span>
                <span class="compare-vs-sep">vs</span>
                <span class="compare-tmpl-label">${result.template_name}</span>
            </div>
            <p class="compare-summary">${result.summary}</p>
        </div>

        <!-- Charts row -->
        <div class="compare-charts-row">
            <div class="chart-panel">
                <div class="chart-panel-title">配置权重对比（雷达图）</div>
                <div class="chart-canvas-wrap" style="height:280px">
                    <canvas id="chart-radar"></canvas>
                </div>
            </div>
            <div class="chart-panel">
                <div class="chart-panel-title">偏离度分析</div>
                <div class="chart-canvas-wrap" style="height:280px">
                    <canvas id="chart-deviation"></canvas>
                </div>
            </div>
        </div>

        <!-- Metrics comparison -->
        <div class="compare-metrics-row">
            <div class="chart-panel chart-panel-wide">
                <div class="chart-panel-title">关键指标对比</div>
                <table class="metrics-delta-table" id="metrics-delta-table">
                    <thead>
                        <tr>
                            <th>指标</th>
                            <th>我的配置</th>
                            <th>模板</th>
                            <th>差值</th>
                        </tr>
                    </thead>
                    <tbody id="metrics-delta-body"></tbody>
                </table>
                <div class="chart-canvas-wrap" style="height:180px;margin-top:14px">
                    <canvas id="chart-metrics"></canvas>
                </div>
                <p class="metrics-note">注：最大回撤取绝对值显示；夏普比率乘以10以便与其他指标同轴展示</p>
            </div>
        </div>

        <!-- Diff table -->
        <div class="compare-table-section">
            <div class="chart-panel-title">各类别权重明细</div>
            <table class="diff-table">
                <thead>
                    <tr>
                        <th>资产类别</th>
                        <th>我的配置</th>
                        <th>模板目标</th>
                        <th>偏离度</th>
                    </tr>
                </thead>
                <tbody>${diffRows}</tbody>
            </table>
        </div>

    </div>`;

    // Render charts after DOM is updated
    requestAnimationFrame(() => {
        renderRadarChart("chart-radar", result.diffs, result.template_name);
        renderDeviationChart("chart-deviation", result.diffs);

        // Fetch template metrics for the grouped bar chart + delta table
        fetch(`/api/templates/${result.template_id}`)
            .then(r => r.json())
            .then(tmpl => {
                renderMetricsChart("chart-metrics", result.user_metrics, tmpl.metrics, tmpl.name);
                renderMetricsDelta("metrics-delta-body", result.user_metrics, tmpl.metrics);
            })
            .catch(() => {
                // Non-critical: metrics chart just won't render
            });
    });
}

// ============================================================
//  Metrics delta table
// ============================================================

/**
 * Populate the metrics delta table with user vs. template values and colored diff.
 * @param {string} tbodyId - ID of the <tbody> element
 * @param {object} userM   - user_metrics from /api/compare
 * @param {object} tmplM   - template.metrics from /api/templates/{id}
 */
function renderMetricsDelta(tbodyId, userM, tmplM) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;

    // For max_drawdown: lower absolute value is better, so delta sign is flipped
    const rows = [
        {
            label: "年化收益",
            userVal: userM.annualized_return,
            tmplVal: tmplM.annualized_return,
            fmt: v => (v >= 0 ? "+" : "") + v.toFixed(1) + "%",
            diffFmt: d => (d >= 0 ? "+" : "−") + Math.abs(d).toFixed(1) + "%",
            higherIsBetter: true,
        },
        {
            label: "年化波动",
            userVal: userM.annualized_volatility,
            tmplVal: tmplM.annualized_volatility,
            fmt: v => v.toFixed(1) + "%",
            diffFmt: d => (d >= 0 ? "+" : "−") + Math.abs(d).toFixed(1) + "%",
            higherIsBetter: false,
        },
        {
            label: "最大回撤",
            userVal: userM.max_drawdown,
            tmplVal: tmplM.max_drawdown,
            fmt: v => v.toFixed(1) + "%",
            diffFmt: d => (d >= 0 ? "+" : "−") + Math.abs(d).toFixed(1) + "%",
            // max_drawdown is negative; user closer to zero (diff > 0) is better
            higherIsBetter: true,
        },
        {
            label: "夏普比率",
            userVal: userM.sharpe_ratio,
            tmplVal: tmplM.sharpe_ratio,
            fmt: v => v.toFixed(2),
            diffFmt: d => (d >= 0 ? "+" : "−") + Math.abs(d).toFixed(2),
            higherIsBetter: true,
        },
    ];

    tbody.innerHTML = rows.map(row => {
        const diff = row.userVal - row.tmplVal;
        const absDiff = Math.abs(diff);
        const isNeutral = absDiff < 0.005;

        // Determine if diff is favorable
        let favorable;
        if (isNeutral) {
            favorable = null;
        } else if (row.higherIsBetter) {
            favorable = diff > 0;
        } else {
            // For volatility and drawdown, user being lower (diff < 0) is better
            favorable = diff < 0;
        }

        // Format the diff value directly (avoids stripping/re-applying signs)
        const diffDisplay = row.diffFmt(diff);

        const cls = isNeutral ? "mdelta-neutral" : favorable ? "mdelta-good" : "mdelta-bad";

        return `<tr>
            <td class="mdelta-label">${row.label}</td>
            <td class="mdelta-num">${row.fmt(row.userVal)}</td>
            <td class="mdelta-num mdelta-tmpl">${row.fmt(row.tmplVal)}</td>
            <td class="mdelta-diff ${cls}">${diffDisplay}</td>
        </tr>`;
    }).join("");
}

// ============================================================
//  AI: personality match
// ============================================================

async function runAiProfileMatch() {
    const btn = document.getElementById("btn-ai-match");
    const resultEl = document.getElementById("ai-match-result");
    if (!btn || !resultEl) return;

    btn.disabled = true;
    btn.textContent = "分析中...";
    resultEl.textContent = "";
    resultEl.classList.remove("ai-result-visible");

    try {
        const body = {};
        if (window.assets && window.assets.length > 0) {
            body.web_assets = window.assets;
        }
        const resp = await fetch("/api/ai/profile-match", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        resultEl.textContent = data.result || data.error || "无返回结果";
        resultEl.classList.add("ai-result-visible");
    } catch (err) {
        resultEl.textContent = `请求失败: ${err.message}`;
        resultEl.classList.add("ai-result-visible");
    }

    btn.disabled = false;
    btn.textContent = "分析我的性格";
}

// ============================================================
//  AI: migration advice
// ============================================================

async function runAiMigrate() {
    const btn = document.getElementById("btn-ai-migrate");
    const resultEl = document.getElementById("ai-migrate-result");
    if (!btn || !resultEl || !_currentTemplateId) return;

    btn.disabled = true;
    btn.textContent = "生成中...";
    resultEl.textContent = "";
    resultEl.classList.remove("ai-result-visible");

    try {
        const body = { template_id: _currentTemplateId };
        if (window.assets && window.assets.length > 0) {
            body.web_assets = window.assets;
        }
        const resp = await fetch("/api/ai/migrate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        resultEl.textContent = data.result || data.error || "无返回结果";
        resultEl.classList.add("ai-result-visible");
    } catch (err) {
        resultEl.textContent = `请求失败: ${err.message}`;
        resultEl.classList.add("ai-result-visible");
    }

    btn.disabled = false;
    btn.textContent = "获取迁移建议";
}

// ============================================================
//  Init
// ============================================================

function initCompareView() {
    const runBtn = document.getElementById("btn-run-compare");
    if (runBtn) runBtn.addEventListener("click", runCompare);

    const aiMatchBtn = document.getElementById("btn-ai-match");
    if (aiMatchBtn) aiMatchBtn.addEventListener("click", runAiProfileMatch);

    const aiMigrateBtn = document.getElementById("btn-ai-migrate");
    if (aiMigrateBtn) aiMigrateBtn.addEventListener("click", runAiMigrate);
}
