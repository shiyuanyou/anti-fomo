/**
 * Anti-FOMO 资产配置可视化
 * Step 1-4: Treemap + 维度切换 + 过渡动画 + 明细图例 + 编辑/删除弹窗 + 新增资产
 */

// ============================================================
//  Default Sample Data (used when no saved config exists)
// ============================================================

const DEFAULT_ASSETS = [
    { name: "中证A500",    code: "000510", amount: 50000, type: "股票",    region: "中国大陆", style: "大盘价值" },
    { name: "中证A50",     code: "930050", amount: 30000, type: "股票",    region: "中国大陆", style: "大盘成长" },
    { name: "中证2000",    code: "932000", amount: 20000, type: "股票",    region: "中国大陆", style: "中小盘" },
    { name: "标普500ETF",  code: "513500", amount: 25000, type: "股票",    region: "美国",     style: "大盘成长" },
    { name: "恒生科技ETF", code: "513130", amount: 15000, type: "股票",    region: "中国香港", style: "大盘成长" },
    { name: "黄金ETF",     code: "518880", amount: 20000, type: "大宗商品", region: "全球",     style: "商品对冲" },
    { name: "货币基金",    code: "511880", amount: 15000, type: "货币基金", region: "中国大陆", style: "防御型" },
    { name: "德国DAX",     code: "513030", amount: 10000, type: "股票",    region: "欧洲",     style: "大盘价值" },
    { name: "印度基金",    code: "164824", amount: 8000,  type: "股票",    region: "印度",     style: "新兴市场" },
];

let assets = [...DEFAULT_ASSETS];

// ============================================================
//  Color Palette — gradient pairs for blocks
// ============================================================

const PALETTE = [
    { from: "#0EA5E9", to: "#0284C7" },   // sky
    { from: "#8B5CF6", to: "#7C3AED" },   // violet
    { from: "#F43F5E", to: "#E11D48" },   // rose
    { from: "#10B981", to: "#059669" },   // emerald
    { from: "#F59E0B", to: "#D97706" },   // amber
    { from: "#6366F1", to: "#4F46E5" },   // indigo
    { from: "#EC4899", to: "#DB2777" },   // pink
    { from: "#14B8A6", to: "#0D9488" },   // teal
    { from: "#EF4444", to: "#DC2626" },   // red
    { from: "#84CC16", to: "#65A30D" },   // lime
];

// ============================================================
//  Squarified Treemap Layout
// ============================================================

function worstAspectRatio(row, sideLength) {
    if (row.length === 0) return Infinity;
    const rowArea = row.reduce((s, item) => s + item.area, 0);
    const rowSide = rowArea / sideLength;
    let worst = 0;
    for (const item of row) {
        const otherSide = item.area / rowSide;
        const ratio = Math.max(rowSide / otherSide, otherSide / rowSide);
        if (ratio > worst) worst = ratio;
    }
    return worst;
}

function computeTreemap(items, rect) {
    if (items.length === 0) return [];

    const totalValue = items.reduce((s, i) => s + i.value, 0);
    const totalArea = rect.w * rect.h;

    // Sort descending, attach normalized area
    const sorted = items
        .map(item => ({ ...item, area: (item.value / totalValue) * totalArea }))
        .sort((a, b) => b.area - a.area);

    const results = [];
    let remaining = [...sorted];
    let cur = { ...rect };

    while (remaining.length > 0) {
        if (remaining.length === 1) {
            results.push({ ...remaining[0], x: cur.x, y: cur.y, w: cur.w, h: cur.h });
            break;
        }

        const shortSide = Math.min(cur.w, cur.h);
        const row = [remaining[0]];
        remaining = remaining.slice(1);

        while (remaining.length > 0) {
            const candidate = [...row, remaining[0]];
            if (worstAspectRatio(candidate, shortSide) <= worstAspectRatio(row, shortSide)) {
                row.push(remaining.shift());
            } else {
                break;
            }
        }

        // Layout the finalized row
        const rowArea = row.reduce((s, i) => s + i.area, 0);
        const isHorizontal = cur.w >= cur.h;

        if (isHorizontal) {
            const rowW = rowArea / cur.h;
            let y = cur.y;
            for (const item of row) {
                const h = item.area / rowW;
                results.push({ ...item, x: cur.x, y, w: rowW, h });
                y += h;
            }
            cur = { x: cur.x + rowW, y: cur.y, w: cur.w - rowW, h: cur.h };
        } else {
            const rowH = rowArea / cur.w;
            let x = cur.x;
            for (const item of row) {
                const w = item.area / rowH;
                results.push({ ...item, x, y: cur.y, w, h: rowH });
                x += w;
            }
            cur = { x: cur.x, y: cur.y + rowH, w: cur.w, h: cur.h - rowH };
        }
    }

    return results;
}

// ============================================================
//  Data Aggregation by Dimension
// ============================================================

function aggregateByDimension(assets, dimKey) {
    const groups = {};
    for (const a of assets) {
        const key = a[dimKey];
        if (!groups[key]) {
            groups[key] = { name: key, value: 0, items: [] };
        }
        groups[key].value += a.amount;
        groups[key].items.push(a);
    }
    return Object.values(groups).sort((a, b) => b.value - a.value);
}

// ============================================================
//  Rendering
// ============================================================

const GAP = 3; // px gap between blocks

function classifySize(w, h) {
    if (w < 60 || h < 35) return "size-tiny";
    if (w < 110 || h < 65) return "size-small";
    if (w < 160 || h < 90) return "size-medium";
    return "size-large";
}

function formatAmount(n) {
    if (n >= 10000) return (n / 10000).toFixed(1) + "万";
    return n.toLocaleString();
}

function renderTreemap(data, container, onComplete) {
    container.innerHTML = "";

    const rect = {
        x: 0,
        y: 0,
        w: container.clientWidth,
        h: container.clientHeight
    };

    if (rect.w === 0 || rect.h === 0) return;

    const totalValue = data.reduce((s, d) => s + d.value, 0);
    const blocks = computeTreemap(data, rect);

    blocks.forEach((block, i) => {
        const pct = ((block.value / totalValue) * 100).toFixed(1);
        const color = PALETTE[i % PALETTE.length];

        const el = document.createElement("div");
        el.className = "treemap-block " + classifySize(block.w - GAP * 2, block.h - GAP * 2);

        el.style.left = (block.x + GAP) + "px";
        el.style.top = (block.y + GAP) + "px";
        el.style.width = Math.max(0, block.w - GAP * 2) + "px";
        el.style.height = Math.max(0, block.h - GAP * 2) + "px";
        el.style.background = `linear-gradient(135deg, ${color.from} 0%, ${color.to} 100%)`;
        el.style.borderRadius = "4px";
        el.style.animationDelay = (i * 0.06) + "s";

        el.innerHTML = `
            <span class="block-name">${block.name}</span>
            <span class="block-pct">${pct}%</span>
            <span class="block-amount">${formatAmount(block.value)}</span>
        `;

        // Tooltip data
        el.dataset.name = block.name;
        el.dataset.pct = pct;
        el.dataset.amount = block.value;
        el.dataset.count = block.items ? block.items.length : 1;
        // Store child items as JSON for enhanced tooltip
        if (block.items) {
            el.dataset.items = JSON.stringify(
                block.items.map(it => ({ name: it.name, amount: it.amount }))
            );
        }

        // Click to open edit modal for this group
        el.addEventListener("click", () => openModal(block.name, DIM_MAP[currentDim].key));

        container.appendChild(el);
    });

    if (onComplete) onComplete();
}

// ============================================================
//  Tooltip (enhanced with child item list)
// ============================================================

function initTooltip() {
    const tip = document.createElement("div");
    tip.className = "treemap-tooltip";
    tip.innerHTML = `
        <div class="tip-name"></div>
        <div class="tip-row"><span>占比</span><span class="tip-val tip-pct"></span></div>
        <div class="tip-row"><span>金额</span><span class="tip-val tip-amt"></span></div>
        <div class="tip-row"><span>标的数</span><span class="tip-val tip-cnt"></span></div>
        <div class="tip-items"></div>
    `;
    document.body.appendChild(tip);

    const treemap = document.getElementById("treemap");

    treemap.addEventListener("mousemove", (e) => {
        const block = e.target.closest(".treemap-block");
        if (!block) {
            tip.classList.remove("visible");
            return;
        }
        tip.querySelector(".tip-name").textContent = block.dataset.name;
        tip.querySelector(".tip-pct").textContent = block.dataset.pct + "%";
        tip.querySelector(".tip-amt").textContent = formatAmount(Number(block.dataset.amount));
        tip.querySelector(".tip-cnt").textContent = block.dataset.count + " 项";

        // Render child items list
        const itemsEl = tip.querySelector(".tip-items");
        if (block.dataset.items) {
            try {
                const items = JSON.parse(block.dataset.items);
                if (items.length > 1) {
                    itemsEl.innerHTML = `<div class="tip-items-title">包含标的</div>` +
                        items.map(it =>
                            `<div class="tip-item"><span>${it.name}</span><span class="tip-item-val">${formatAmount(it.amount)}</span></div>`
                        ).join("");
                    itemsEl.style.display = "";
                } else {
                    itemsEl.style.display = "none";
                }
            } catch (_) {
                itemsEl.style.display = "none";
            }
        } else {
            itemsEl.style.display = "none";
        }

        tip.classList.add("visible");

        // Position with edge detection
        const tx = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 10);
        const ty = Math.min(e.clientY + 14, window.innerHeight - tip.offsetHeight - 10);
        tip.style.left = tx + "px";
        tip.style.top = ty + "px";
    });

    treemap.addEventListener("mouseleave", () => {
        tip.classList.remove("visible");
    });
}

// ============================================================
//  Summary Panel Update
// ============================================================

function updateSummary(assets, dimLabel) {
    const total = assets.reduce((s, a) => s + a.amount, 0);
    document.getElementById("asset-count").textContent = assets.length;
    document.getElementById("total-amount").textContent = formatAmount(total);
    document.getElementById("current-dim").textContent = dimLabel;
}

// ============================================================
//  Detail Bar (color-coded legend below treemap)
// ============================================================

function renderDetailBar(data) {
    const bar = document.getElementById("detail-bar");
    const totalValue = data.reduce((s, d) => s + d.value, 0);

    bar.innerHTML = data.map((item, i) => {
        const color = PALETTE[i % PALETTE.length];
        const pct = ((item.value / totalValue) * 100).toFixed(1);
        return `<div class="detail-chip" style="animation-delay:${i * 0.04}s">
            <span class="detail-dot" style="background:${color.from}"></span>
            <span class="detail-name">${item.name}</span>
            <span class="detail-pct">${pct}%</span>
            <span class="detail-amt">${formatAmount(item.value)}</span>
        </div>`;
    }).join("");
}

// ============================================================
//  Tab Badges (group count per dimension)
// ============================================================

function updateTabBadges() {
    document.querySelectorAll(".tab").forEach(tab => {
        const dim = tab.dataset.dim;
        const count = aggregateByDimension(assets, DIM_MAP[dim].key).length;
        let badge = tab.querySelector(".tab-badge");
        if (!badge) {
            badge = document.createElement("span");
            badge.className = "tab-badge";
            tab.appendChild(badge);
        }
        badge.textContent = count;
    });
}

// ============================================================
//  Dimension Switching with Transition
// ============================================================

const DIM_MAP = {
    type:   { key: "type",   label: "类型" },
    region: { key: "region", label: "区域" },
    style:  { key: "style",  label: "风格" },
};

let currentDim = "type";
let isTransitioning = false;

function switchDimension(dim, skipAnimation) {
    if (isTransitioning && !skipAnimation) return;
    if (dim === currentDim && !skipAnimation) return;

    currentDim = dim;
    const container = document.getElementById("treemap");
    const data = aggregateByDimension(assets, DIM_MAP[dim].key);

    // Update active tab
    document.querySelectorAll(".tab").forEach(t => {
        t.classList.toggle("active", t.dataset.dim === dim);
    });

    updateSummary(assets, DIM_MAP[dim].label);

    if (skipAnimation) {
        // No animation (initial render or resize)
        renderTreemap(data, container);
        renderDetailBar(data);
        return;
    }

    // Animated transition: fade out → re-render → fade in
    isTransitioning = true;
    container.classList.add("fading-out");

    setTimeout(() => {
        renderTreemap(data, container);
        renderDetailBar(data);
        container.classList.remove("fading-out");
        container.classList.add("fading-in");

        setTimeout(() => {
            container.classList.remove("fading-in");
            isTransitioning = false;
        }, 350);
    }, 200);
}

// ============================================================
//  Modal: Create / Open / Close / Render / Edit / Delete
// ============================================================

let modalOverlay = null;
let modalTitleEl = null;
let modalBodyEl = null;
let currentModalGroup = null; // { name, dimKey }

function createModal() {
    modalOverlay = document.createElement("div");
    modalOverlay.className = "modal-overlay";
    modalOverlay.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title"></span>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body"></div>
        </div>
    `;
    document.body.appendChild(modalOverlay);

    modalTitleEl = modalOverlay.querySelector(".modal-title");
    modalBodyEl = modalOverlay.querySelector(".modal-body");

    // Close on X button
    modalOverlay.querySelector(".modal-close").addEventListener("click", closeModal);

    // Close on overlay background click
    modalOverlay.addEventListener("click", (e) => {
        if (e.target === modalOverlay) closeModal();
    });

    // Close on Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modalOverlay.classList.contains("visible")) {
            closeModal();
        }
    });
}

function openModal(groupName, dimKey) {
    currentModalGroup = { name: groupName, dimKey };
    modalTitleEl.textContent = groupName;
    renderModalBody();
    modalOverlay.classList.add("visible");
}

function closeModal() {
    modalOverlay.classList.remove("visible");
    currentModalGroup = null;
}

function renderModalBody() {
    if (!currentModalGroup) return;

    const { name, dimKey } = currentModalGroup;
    const groupAssets = assets.filter(a => a[dimKey] === name);

    if (groupAssets.length === 0) {
        modalBodyEl.innerHTML = `<div class="modal-empty">该分组暂无资产</div>`;
        return;
    }

    modalBodyEl.innerHTML = groupAssets.map((a, idx) => {
        const globalIdx = assets.indexOf(a);
        return `
        <div class="modal-asset" data-idx="${globalIdx}">
            <div class="modal-asset-row">
                <div class="modal-asset-info">
                    <div class="modal-asset-name">${a.name}</div>
                    <div class="modal-asset-meta">
                        <span class="modal-asset-code">${a.code}</span>
                        <span class="modal-asset-amount">${formatAmount(a.amount)}</span>
                    </div>
                    <div class="modal-asset-tags">
                        <span class="modal-tag">${a.type}</span>
                        <span class="modal-tag">${a.region}</span>
                        <span class="modal-tag">${a.style}</span>
                    </div>
                </div>
                <div class="modal-asset-actions">
                    <button class="btn-edit" data-idx="${globalIdx}">编辑</button>
                    <button class="btn-delete" data-idx="${globalIdx}">删除</button>
                </div>
            </div>
        </div>`;
    }).join("");

    // Wire edit buttons
    modalBodyEl.querySelectorAll(".btn-edit").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            openEditForm(Number(btn.dataset.idx));
        });
    });

    // Wire delete buttons (double-click-to-confirm pattern)
    modalBodyEl.querySelectorAll(".btn-delete").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            handleDelete(btn, Number(btn.dataset.idx));
        });
    });
}

function openEditForm(idx) {
    const a = assets[idx];
    if (!a) return;

    const card = modalBodyEl.querySelector(`.modal-asset[data-idx="${idx}"]`);
    if (!card) return;

    // If form already open, skip
    if (card.querySelector(".modal-edit-form")) return;

    const form = document.createElement("div");
    form.className = "modal-edit-form";
    form.innerHTML = `
        <div class="edit-grid">
            <div class="form-group">
                <label>资产名</label>
                <input type="text" data-field="name" value="${a.name}">
            </div>
            <div class="form-group">
                <label>股票代码</label>
                <input type="text" data-field="code" value="${a.code}">
            </div>
            <div class="form-group">
                <label>金额</label>
                <input type="number" data-field="amount" value="${a.amount}">
            </div>
            <div class="form-group">
                <label>类型</label>
                <select data-field="type">
                    ${["股票", "大宗商品", "货币基金"].map(v =>
                        `<option ${v === a.type ? "selected" : ""}>${v}</option>`
                    ).join("")}
                </select>
            </div>
            <div class="form-group">
                <label>区域</label>
                <select data-field="region">
                    ${["中国大陆", "中国香港", "美国", "欧洲", "印度", "全球"].map(v =>
                        `<option ${v === a.region ? "selected" : ""}>${v}</option>`
                    ).join("")}
                </select>
            </div>
            <div class="form-group">
                <label>风格</label>
                <select data-field="style">
                    ${["大盘价值", "大盘成长", "中小盘", "商品对冲", "防御型", "新兴市场"].map(v =>
                        `<option ${v === a.style ? "selected" : ""}>${v}</option>`
                    ).join("")}
                </select>
            </div>
        </div>
        <div class="edit-actions">
            <button class="btn btn-cancel-action">取消</button>
            <button class="btn btn-save-action">保存</button>
        </div>
    `;
    card.appendChild(form);

    // Cancel
    form.querySelector(".btn-cancel-action").addEventListener("click", (e) => {
        e.stopPropagation();
        form.remove();
    });

    // Save
    form.querySelector(".btn-save-action").addEventListener("click", (e) => {
        e.stopPropagation();

        const nameVal = form.querySelector('[data-field="name"]').value.trim();
        const codeVal = form.querySelector('[data-field="code"]').value.trim();
        const amountVal = Number(form.querySelector('[data-field="amount"]').value);
        const typeVal = form.querySelector('[data-field="type"]').value;
        const regionVal = form.querySelector('[data-field="region"]').value;
        const styleVal = form.querySelector('[data-field="style"]').value;

        if (!nameVal || isNaN(amountVal) || amountVal <= 0) return;

        assets[idx] = {
            name: nameVal,
            code: codeVal,
            amount: amountVal,
            type: typeVal,
            region: regionVal,
            style: styleVal,
        };

        refreshView();
        renderModalBody(); // re-render modal content
    });
}

let deleteTimers = {};

function handleDelete(btn, idx) {
    if (btn.classList.contains("confirming")) {
        // Second click within window — confirm delete
        clearTimeout(deleteTimers[idx]);
        delete deleteTimers[idx];
        assets.splice(idx, 1);
        refreshView();

        // Check if group still has items
        if (currentModalGroup) {
            const remaining = assets.filter(a => a[currentModalGroup.dimKey] === currentModalGroup.name);
            if (remaining.length === 0) {
                closeModal();
            } else {
                renderModalBody();
            }
        }
    } else {
        // First click — enter confirming state
        btn.classList.add("confirming");
        btn.textContent = "确认?";

        deleteTimers[idx] = setTimeout(() => {
            btn.classList.remove("confirming");
            btn.textContent = "删除";
            delete deleteTimers[idx];
        }, 3000);
    }
}

function refreshView() {
    switchDimension(currentDim, true);
    updateTabBadges();
}

// ============================================================
//  Sidebar: Add New Asset
// ============================================================

function initAddAssetForm() {
    const btn = document.getElementById("btn-add-asset");
    const nameEl = document.getElementById("add-name");
    const amountEl = document.getElementById("add-amount");
    const codeEl = document.getElementById("add-code");
    const styleEl = document.getElementById("add-style");
    const regionEl = document.getElementById("add-region");
    const typeEl = document.getElementById("add-type");

    function showFieldError(el) {
        el.style.borderColor = "#F43F5E";
        el.style.boxShadow = "0 0 0 2px rgba(244,63,94,0.2)";
        setTimeout(() => {
            el.style.borderColor = "";
            el.style.boxShadow = "";
        }, 1500);
    }

    btn.addEventListener("click", () => {
        const name = nameEl.value.trim();
        const amount = Number(amountEl.value);
        const code = codeEl.value.trim();
        const style = styleEl.value;
        const region = regionEl.value;
        const type = typeEl.value;

        // Validate required fields
        let valid = true;
        if (!name)                       { showFieldError(nameEl);   valid = false; }
        if (isNaN(amount) || amount <= 0) { showFieldError(amountEl); valid = false; }
        if (!type)                       { showFieldError(typeEl);   valid = false; }
        if (!region)                     { showFieldError(regionEl); valid = false; }
        if (!style)                      { showFieldError(styleEl);  valid = false; }
        if (!valid) return;

        assets.push({
            name,
            code: code || "------",
            amount,
            type,
            region,
            style,
        });

        // Reset form
        nameEl.value = "";
        amountEl.value = "";
        codeEl.value = "";
        styleEl.value = "";
        regionEl.value = "";
        typeEl.value = "";

        refreshView();

        // Brief flash on button to confirm add
        btn.style.boxShadow = "0 0 16px rgba(56,189,248,0.4)";
        setTimeout(() => { btn.style.boxShadow = ""; }, 600);
    });
}

// ============================================================
//  API: Load / Save Assets
// ============================================================

async function loadAssetsFromServer() {
    try {
        const resp = await fetch("/api/assets");
        if (!resp.ok) return false;
        const data = await resp.json();
        if (Array.isArray(data) && data.length > 0) {
            assets = data;
            return true;
        }
    } catch (_) {
        // server may not support API (e.g. opened as static file)
    }
    return false;
}

async function saveAssetsToServer() {
    const btn = document.getElementById("btn-save-config");
    const status = document.getElementById("save-status");
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = "保存中...";
    status.textContent = "";
    status.className = "save-status";

    try {
        const resp = await fetch("/api/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(assets),
        });
        const result = await resp.json();
        if (result.ok) {
            status.textContent = "config.asset.yaml 已生成";
            status.classList.add("save-ok");
        } else {
            status.textContent = result.error || "保存失败";
            status.classList.add("save-err");
        }
    } catch (e) {
        status.textContent = "网络错误";
        status.classList.add("save-err");
    }

    btn.disabled = false;
    btn.textContent = "生成配置文件";

    // Auto-clear status after 4s
    setTimeout(() => {
        status.textContent = "";
        status.className = "save-status";
    }, 4000);
}

// ============================================================
//  Init
// ============================================================

async function init() {
    createModal();
    initTooltip();
    initAddAssetForm();

    // Load saved assets from server (fallback to defaults)
    await loadAssetsFromServer();

    updateTabBadges();

    // Tab click events
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => {
            switchDimension(tab.dataset.dim);
        });
    });

    // Save config button
    const saveBtn = document.getElementById("btn-save-config");
    if (saveBtn) {
        saveBtn.addEventListener("click", saveAssetsToServer);
    }

    // Render default dimension (no animation)
    switchDimension("type", true);

    // Re-render on resize
    let resizeTimer;
    window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => switchDimension(currentDim, true), 150);
    });
}

// ============================================================
//  View Navigation (v2)
// ============================================================

function initViewNav() {
    const tabs = document.querySelectorAll(".view-tab");
    const panels = document.querySelectorAll(".view-panel");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const view = tab.dataset.view;
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));
            tab.classList.add("active");
            const panel = document.getElementById("view-" + view);
            if (panel) panel.classList.add("active");
        });
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    initViewNav();
    await init();

    // v2 feature initialisation (defined in templates.js / compare.js)
    if (typeof initTemplatesView === "function") initTemplatesView();
    if (typeof initCompareView === "function") initCompareView();
});
