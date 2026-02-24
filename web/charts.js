/**
 * Anti-FOMO v2 — Chart utilities (Chart.js wrappers)
 * Provides radar chart and grouped bar chart for comparison views.
 */

// ============================================================
//  Global chart registry (to allow destroy/recreate)
// ============================================================

const _charts = {};

function _destroyChart(id) {
    if (_charts[id]) {
        _charts[id].destroy();
        delete _charts[id];
    }
}

// ============================================================
//  Shared Chart.js defaults
// ============================================================

const CHART_DEFAULTS = {
    color: {
        user:     "rgba(56, 189, 248, 0.75)",     // --accent (sky blue)
        userBg:   "rgba(56, 189, 248, 0.15)",
        tmpl:     "rgba(129, 140, 248, 0.75)",     // indigo
        tmplBg:   "rgba(129, 140, 248, 0.15)",
        grid:     "rgba(56, 189, 248, 0.08)",
        tick:     "#64748B",
        label:    "#94A3B8",
    },
    font: {
        family: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        size: 11,
    },
};

// ============================================================
//  Radar chart: user allocation vs. template allocation
// ============================================================

/**
 * Render or update a radar chart comparing user vs. template allocation weights.
 *
 * @param {string} canvasId   - ID of the <canvas> element
 * @param {Array}  diffs      - AllocationDiff array from /api/compare
 * @param {string} tmplName   - Template display name
 */
function renderRadarChart(canvasId, diffs, tmplName) {
    _destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Use top N categories by template weight for readability
    const sorted = [...diffs]
        .filter(d => d.template_weight > 0 || d.user_weight > 0)
        .sort((a, b) => b.template_weight - a.template_weight)
        .slice(0, 8);

    const labels = sorted.map(d => d.category);
    const userData = sorted.map(d => +(d.user_weight * 100).toFixed(1));
    const tmplData = sorted.map(d => +(d.template_weight * 100).toFixed(1));

    const c = CHART_DEFAULTS.color;

    _charts[canvasId] = new Chart(canvas, {
        type: "radar",
        data: {
            labels,
            datasets: [
                {
                    label: "我的配置",
                    data: userData,
                    borderColor: c.user,
                    backgroundColor: c.userBg,
                    pointBackgroundColor: c.user,
                    pointRadius: 3,
                    borderWidth: 2,
                },
                {
                    label: tmplName,
                    data: tmplData,
                    borderColor: c.tmpl,
                    backgroundColor: c.tmplBg,
                    pointBackgroundColor: c.tmpl,
                    pointRadius: 3,
                    borderWidth: 2,
                    borderDash: [4, 3],
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: {
                    labels: {
                        color: c.label,
                        font: CHART_DEFAULTS.font,
                        boxWidth: 12,
                        padding: 14,
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    borderColor: "rgba(56, 189, 248, 0.25)",
                    borderWidth: 1,
                    titleColor: "#E2E8F0",
                    bodyColor: "#94A3B8",
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}%`,
                    },
                },
            },
            scales: {
                r: {
                    beginAtZero: true,
                    grid: { color: c.grid },
                    angleLines: { color: c.grid },
                    pointLabels: {
                        color: c.label,
                        font: { ...CHART_DEFAULTS.font, size: 10 },
                    },
                    ticks: {
                        color: c.tick,
                        backdropColor: "transparent",
                        font: { ...CHART_DEFAULTS.font, size: 9 },
                        callback: v => v + "%",
                    },
                },
            },
        },
    });
}

// ============================================================
//  Bar chart: deviation per category (user - template)
// ============================================================

/**
 * Render a horizontal deviation bar chart.
 *
 * @param {string} canvasId - ID of the <canvas> element
 * @param {Array}  diffs    - AllocationDiff array
 */
function renderDeviationChart(canvasId, diffs) {
    _destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Show only categories with meaningful deviation (>1%)
    const filtered = [...diffs]
        .filter(d => Math.abs(d.deviation) > 0.005)
        .sort((a, b) => b.deviation - a.deviation)
        .slice(0, 10);

    const labels = filtered.map(d => d.category);
    const values = filtered.map(d => +(d.deviation * 100).toFixed(1));
    const colors = values.map(v =>
        v > 0 ? "rgba(248, 113, 113, 0.7)" : "rgba(52, 211, 153, 0.7)"
    );
    const borderColors = values.map(v =>
        v > 0 ? "rgba(248, 113, 113, 1)" : "rgba(52, 211, 153, 1)"
    );

    const c = CHART_DEFAULTS.color;

    _charts[canvasId] = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "偏离度（当前 − 模板）",
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1,
                borderRadius: 3,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    borderColor: "rgba(56, 189, 248, 0.25)",
                    borderWidth: 1,
                    titleColor: "#E2E8F0",
                    bodyColor: "#94A3B8",
                    callbacks: {
                        label: ctx => {
                            const v = ctx.raw;
                            return ` ${v > 0 ? "超配" : "低配"} ${Math.abs(v).toFixed(1)}%`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: c.grid },
                    ticks: {
                        color: c.tick,
                        font: CHART_DEFAULTS.font,
                        callback: v => (v > 0 ? "+" : "") + v + "%",
                    },
                    border: { color: c.grid },
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: c.label,
                        font: { ...CHART_DEFAULTS.font, size: 10 },
                    },
                    border: { color: c.grid },
                },
            },
        },
    });
}

// ============================================================
//  Metrics comparison bar chart (4-metric grouped bar)
// ============================================================

/**
 * Render a grouped bar chart comparing 4 key metrics.
 *
 * @param {string} canvasId   - ID of the <canvas> element
 * @param {object} userM      - user_metrics object from /api/compare
 * @param {object} tmplM      - template.metrics object
 * @param {string} tmplName   - Template display name
 */
function renderMetricsChart(canvasId, userM, tmplM, tmplName) {
    _destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = ["年化收益%", "年化波动%", "最大回撤%", "夏普比率×10"];
    const scale = (v, label) => label === "夏普比率×10" ? v * 10 : v;

    const userData = [
        userM.annualized_return,
        userM.annualized_volatility,
        Math.abs(userM.max_drawdown),
        userM.sharpe_ratio * 10,
    ];
    const tmplData = [
        tmplM.annualized_return,
        tmplM.annualized_volatility,
        Math.abs(tmplM.max_drawdown),
        tmplM.sharpe_ratio * 10,
    ];

    const c = CHART_DEFAULTS.color;

    _charts[canvasId] = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "我的配置",
                    data: userData,
                    backgroundColor: c.userBg,
                    borderColor: c.user,
                    borderWidth: 1.5,
                    borderRadius: 3,
                },
                {
                    label: tmplName,
                    data: tmplData,
                    backgroundColor: c.tmplBg,
                    borderColor: c.tmpl,
                    borderWidth: 1.5,
                    borderRadius: 3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: {
                    labels: {
                        color: c.label,
                        font: CHART_DEFAULTS.font,
                        boxWidth: 12,
                        padding: 14,
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    borderColor: "rgba(56, 189, 248, 0.25)",
                    borderWidth: 1,
                    titleColor: "#E2E8F0",
                    bodyColor: "#94A3B8",
                },
            },
            scales: {
                x: {
                    grid: { color: c.grid },
                    ticks: { color: c.label, font: CHART_DEFAULTS.font },
                    border: { color: c.grid },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: c.grid },
                    ticks: { color: c.tick, font: CHART_DEFAULTS.font },
                    border: { color: c.grid },
                },
            },
        },
    });
}
