<template>
  <main class="main view-panel active" style="overflow-y: auto; flex-direction: column;">
    <div class="templates-layout">
      <div class="templates-header-row">
        <h2 class="section-title">配置模板库</h2>
        <p class="section-desc">经典资产配置策略，了解不同投资思路的量化特征与性格画像</p>
        <div class="metrics-disclaimer">
          数据来源：真实历史模拟回测，仅供认知参考，不构成投资建议
        </div>
      </div>

      <div class="templates-grid">
        <div v-if="loading" class="templates-loading">加载模板中...</div>

        <div
          v-for="t in templates"
          :key="t.id"
          class="template-card"
          @click="openTemplate(t)"
        >
          <!-- Header: name + risk badge + tagline + audience -->
          <div class="tcard-header">
            <div class="tcard-title-row">
              <span class="tcard-name">{{ t.name }}</span>
              <span
                v-if="t.risk_level"
                class="risk-badge"
                :style="riskStyle(t.risk_level)"
              >{{ t.risk_level }}风险</span>
            </div>
            <p class="tcard-tagline">{{ t.tagline }}</p>
            <p class="tcard-audience">{{ t.target_audience }}</p>
          </div>

          <!-- Allocation bar + chips -->
          <div class="tcard-alloc">
            <div class="alloc-bar">
              <div
                v-for="(seg, i) in allocSegments(t)"
                :key="seg.category"
                class="alloc-bar-seg"
                :style="{ width: seg.pct + '%', background: ALLOC_PALETTE[i % ALLOC_PALETTE.length] }"
                :title="`${seg.category} ${seg.pct}%`"
              ></div>
            </div>
            <div class="alloc-chips">
              <span
                v-for="(seg, i) in allocSegments(t)"
                :key="seg.category"
                class="alloc-chip"
              >
                <span class="alloc-dot" :style="{ background: ALLOC_PALETTE[i % ALLOC_PALETTE.length] }"></span>
                {{ seg.category }}
                <span class="alloc-chip-pct">{{ seg.pct }}%</span>
              </span>
            </div>
          </div>

          <!-- 4-metric grid -->
          <div class="tcard-metrics">
            <div class="metric-item">
              <span class="metric-label">年化收益</span>
              <span class="metric-value metric-pos">+{{ t.metrics.expected_return.toFixed(1) }}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">年化波动</span>
              <span class="metric-value">{{ t.metrics.volatility.toFixed(1) }}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">最大回撤</span>
              <span class="metric-value metric-neg">{{ t.metrics.max_drawdown.toFixed(1) }}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">夏普比率</span>
              <span class="metric-value">{{ t.metrics.sharpe_ratio.toFixed(2) }}</span>
            </div>
          </div>

          <!-- Personality tags + description -->
          <div class="tcard-personality">
            <div class="ptags">
              <span v-for="tag in t.personality_tags" :key="tag" class="ptag">{{ tag }}</span>
            </div>
            <p class="personality-desc">{{ personalityDesc(t) }}</p>
          </div>

          <!-- Footer: data period + compare button -->
          <div class="tcard-footer">
            <span
              class="data-period"
              :class="t.metrics.data_period.includes('真实') ? 'data-period-real' : 'data-period-est'"
            >{{ t.metrics.data_period }}</span>
            <button
              class="btn btn-compare-from-card"
              @click.stop="goToCompare(t.id)"
            >与我的配置对比</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Template Detail Modal -->
    <div
      v-if="selectedTemplate"
      class="modal-overlay visible"
      @click.self="closeTemplate"
    >
      <div class="modal" style="width: 560px; max-width: calc(100vw - 40px);">
        <div class="modal-header">
          <div class="modal-title">{{ selectedTemplate.name }}</div>
          <button class="modal-close" @click="closeTemplate">&times;</button>
        </div>
        <div class="modal-body" style="padding: 20px; gap: 16px; display: flex; flex-direction: column;">
          <!-- Description -->
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.7;">
            {{ personalityDesc(selectedTemplate) }}
          </p>

          <!-- Allocation chart -->
          <div>
            <div class="chart-panel-title" style="margin-bottom: 10px;">资产配置比例</div>
            <ChartPie :data="getPieData(selectedTemplate)" />
          </div>

          <!-- Metrics table -->
          <div>
            <div class="chart-panel-title" style="margin-bottom: 8px;">关键指标</div>
            <table class="metrics-delta-table">
              <thead>
                <tr>
                  <th>指标</th>
                  <th>数值</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="mdelta-label">年化收益</td>
                  <td class="mdelta-num mdelta-good">+{{ selectedTemplate.metrics.expected_return.toFixed(1) }}%</td>
                </tr>
                <tr>
                  <td class="mdelta-label">年化波动</td>
                  <td class="mdelta-num">{{ selectedTemplate.metrics.volatility.toFixed(1) }}%</td>
                </tr>
                <tr>
                  <td class="mdelta-label">最大回撤</td>
                  <td class="mdelta-num mdelta-bad">{{ selectedTemplate.metrics.max_drawdown.toFixed(1) }}%</td>
                </tr>
                <tr>
                  <td class="mdelta-label">夏普比率</td>
                  <td class="mdelta-num">{{ selectedTemplate.metrics.sharpe_ratio.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Actions -->
          <div style="display: flex; gap: 10px; justify-content: flex-end; padding-top: 4px;">
            <button class="btn btn-compare-from-card" @click="closeTemplate(); goToCompare(selectedTemplate!.id)">
              与我的配置对比
            </button>
            <button class="btn btn-primary" @click="copyTemplate(selectedTemplate!)">
              复制此配置到我的组合
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useConfigStore } from '@/store/configStore';
import { ALLOC_PALETTE, RISK_COLORS } from '@/utils';
import type { Template } from '@/types';
import ChartPie from '@/components/ChartPie.vue';

const router = useRouter();
const store = useConfigStore();

const templates = ref<Template[]>([]);
const loading = ref(true);
const selectedTemplate = ref<Template | null>(null);

onMounted(async () => {
  try {
    const res = await fetch('/api/templates');
    if (res.ok) {
      templates.value = await res.json();
    }
  } catch (e) {
    console.error('Failed to load templates', e);
  } finally {
    loading.value = false;
  }
});

// --- Helpers ---

const riskStyle = (level: string) => {
  const c = RISK_COLORS[level] || RISK_COLORS["中"];
  return { background: c.bg, borderColor: c.border, color: c.text };
};

/** Build allocation segments from allocations list (weight 0-1 decimal) */
const allocSegments = (t: Template) => {
  if (t.allocations && t.allocations.length > 0) {
    return t.allocations.map(a => ({
      category: a.category,
      pct: Math.round(a.weight * 100)
    }));
  }
  // Fall back to simple allocation dict (values already in %)
  if (t.allocation) {
    return Object.entries(t.allocation).map(([category, pct]) => ({
      category,
      pct: Math.round(pct)
    }));
  }
  return [];
};

const personalityDesc = (t: Template): string => {
  return t.original_data?.personality_description ?? t.description ?? '';
};

const openTemplate = (t: Template) => {
  selectedTemplate.value = t;
};

const closeTemplate = () => {
  selectedTemplate.value = null;
};

const goToCompare = (templateId: string) => {
  router.push({ path: '/compare', query: { templateId } });
};

const getPieData = (t: Template) => {
  const segs = allocSegments(t);
  return {
    labels: segs.map(s => s.category),
    datasets: [{
      data: segs.map(s => s.pct),
      backgroundColor: segs.map((_, i) => ALLOC_PALETTE[i % ALLOC_PALETTE.length]),
      borderWidth: 0
    }]
  };
};

const copyTemplate = (t: Template) => {
  if (confirm(`这将会覆盖你当前的配置。\n确定要复制【${t.name}】吗？`)) {
    // Prefer the detailed allocations list (has region per item).
    // Fall back to the simple allocation dict when allocations is empty.
    const BASE_AMOUNT = 100000;

    let newAssets: Omit<import('@/types').Asset, 'id'>[];

    if (t.allocations && t.allocations.length > 0) {
      newAssets = t.allocations.map(a => ({
        name: `${a.category}（${a.region}）`,
        code: '',
        amount: Math.round(a.weight * BASE_AMOUNT),
        type: a.category,
        region: a.region,
        style: '无'
      }));
    } else if (t.allocation) {
      newAssets = Object.entries(t.allocation).map(([category, pct]) => ({
        name: `${category}资产`,
        code: '',
        amount: Math.round((pct / 100) * BASE_AMOUNT),
        type: category,
        region: '全球',
        style: '无'
      }));
    } else {
      return;
    }

    store.setAssets(newAssets);

    if (store.mode === 'cloud') {
      store.saveConfig();
    }

    closeTemplate();
    router.push('/');
  }
};
</script>
