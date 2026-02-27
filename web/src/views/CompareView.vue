<template>
  <main class="main view-panel active">
    <div class="compare-layout">
      <!-- Left sidebar: template selector + AI panel -->
      <aside class="compare-sidebar">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-indicator"></span>
            选择对比模板
          </div>
          <div class="panel-body">
            <select class="compare-select" v-model="selectedTemplateId" @change="runCompare">
              <option value="">-- 请选择模板 --</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">
                {{ t.name }}{{ t.tagline ? ' — ' + t.tagline : '' }}
              </option>
            </select>
          </div>
        </div>

        <!-- AI personality match -->
        <div class="panel panel-ai">
          <div class="panel-header">
            <span class="panel-indicator panel-indicator-ai"></span>
            AI 性格分析
          </div>
          <div class="panel-body">
            <p class="ai-hint">基于当前配置，分析你的投资性格并推荐匹配模板</p>
            <button class="btn btn-ai" @click="runAiMatch" :disabled="isAnalyzing">
              {{ isAnalyzing ? '分析中...' : '分析我的性格' }}
            </button>
            <div
              class="ai-result"
              :class="{ 'ai-result-visible': showAiResult }"
              v-show="showAiResult"
              v-html="formatMarkdown(aiMatchResult)"
            ></div>
          </div>
        </div>

        <!-- AI migration advice (only after a comparison is run) -->
        <div class="panel panel-ai" v-if="compareResult">
          <div class="panel-header">
            <span class="panel-indicator panel-indicator-ai"></span>
            AI 迁移建议
          </div>
          <div class="panel-body">
            <button class="btn btn-ai" @click="runAiMigrate" :disabled="isMigrating">
              {{ isMigrating ? '生成中...' : '获取迁移建议' }}
            </button>
            <div
              class="ai-result"
              :class="{ 'ai-result-visible': showMigrateResult }"
              v-show="showMigrateResult"
              v-html="formatMarkdown(aiMigrateResult)"
            ></div>
          </div>
        </div>
      </aside>

      <!-- Right: comparison results -->
      <section class="compare-display">
        <!-- Empty state -->
        <div v-if="!selectedTemplateId && !compareResult" class="compare-empty">
          <div class="compare-empty-icon">&#9635;</div>
          <p>在左侧选择一个模板，开始与当前配置进行对比</p>
        </div>

        <!-- Loading state -->
        <div v-else-if="isComparing" class="compare-loading">
          对比计算中...
        </div>

        <!-- Compare result -->
        <div v-else-if="compareResult" class="compare-result">

          <!-- Summary row -->
          <div class="compare-summary-row">
            <div class="compare-summary-text">
              <span class="compare-vs-label">当前配置</span>
              <span class="compare-vs-sep">vs</span>
              <span class="compare-tmpl-label">{{ compareResult.template_name }}</span>
            </div>
            <p v-if="compareResult.summary" class="compare-summary">{{ compareResult.summary }}</p>
          </div>

          <!-- Charts row: radar + deviation bar -->
          <div class="compare-charts-row">
            <div class="chart-panel">
              <div class="chart-panel-title">配置权重对比（雷达图）</div>
              <ChartRadar :data="radarData" />
            </div>
            <div class="chart-panel">
              <div class="chart-panel-title">偏离度分析</div>
              <ChartBar :data="deviationData" :options="deviationOptions" />
            </div>
          </div>

          <!-- Metrics comparison row -->
          <div class="compare-metrics-row">
            <div class="chart-panel chart-panel-wide">
              <div class="chart-panel-title">关键指标对比</div>
              <table class="metrics-delta-table">
                <thead>
                  <tr>
                    <th>指标</th>
                    <th>我的配置</th>
                    <th>模板</th>
                    <th>差值</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in metricsDeltaRows" :key="row.label">
                    <td class="mdelta-label">{{ row.label }}</td>
                    <td class="mdelta-num">{{ row.userStr }}</td>
                    <td class="mdelta-num mdelta-tmpl">{{ row.tmplStr }}</td>
                    <td class="mdelta-diff" :class="row.cls">{{ row.diffStr }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Weight detail table -->
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
              <tbody>
                <tr v-for="d in compareResult.diffs" :key="d.category">
                  <td class="diff-cat">{{ d.category }}</td>
                  <td class="diff-num">{{ (d.user_weight * 100).toFixed(1) }}%</td>
                  <td class="diff-num">{{ (d.template_weight * 100).toFixed(1) }}%</td>
                  <td class="diff-dev" :class="deviationClass(d.deviation)">
                    {{ formatDeviation(d.deviation) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useConfigStore } from '@/store/configStore';
import type { Template } from '@/types';
import ChartRadar from '@/components/ChartRadar.vue';
import ChartBar from '@/components/ChartBar.vue';

const route = useRoute();
const store = useConfigStore();

const templates = ref<Template[]>([]);
const selectedTemplateId = ref('');
const compareResult = ref<any>(null);
const isComparing = ref(false);

const isAnalyzing = ref(false);
const aiMatchResult = ref('');
const showAiResult = ref(false);

const isMigrating = ref(false);
const aiMigrateResult = ref('');
const showMigrateResult = ref(false);

// Watch aiMatchResult to trigger smooth expand animation
watch(aiMatchResult, (val) => {
  if (val) {
    // Small delay so the element is in the DOM before transition starts
    setTimeout(() => { showAiResult.value = true; }, 10);
  } else {
    showAiResult.value = false;
  }
});

watch(aiMigrateResult, (val) => {
  if (val) {
    setTimeout(() => { showMigrateResult.value = true; }, 10);
  } else {
    showMigrateResult.value = false;
  }
});

onMounted(async () => {
  store.loadConfig();

  try {
    const res = await fetch('/api/templates');
    if (res.ok) {
      templates.value = await res.json();
    }
  } catch (e) {
    console.error('Failed to load templates', e);
  }

  // Pre-select template if navigated here from TemplatesView
  const preselected = route.query.templateId as string | undefined;
  if (preselected) {
    selectedTemplateId.value = preselected;
    await runCompare();
  }
});

const runCompare = async () => {
  if (!selectedTemplateId.value) {
    compareResult.value = null;
    return;
  }

  isComparing.value = true;
  compareResult.value = null;
  // Reset migration AI when template changes
  aiMigrateResult.value = '';
  showMigrateResult.value = false;

  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        portfolio: { total_amount: store.totalAmount, holdings: store.assets },
        template_id: selectedTemplateId.value
      })
    });

    if (res.ok) {
      compareResult.value = await res.json();
    } else {
      const err = await res.json().catch(() => ({}));
      console.error('Compare failed:', err);
    }
  } catch (e) {
    console.error('Failed to compare', e);
  } finally {
    isComparing.value = false;
  }
};

// --- Chart data ---

const CHART_COLORS = {
  user: { line: '#38BDF8', fill: 'rgba(56, 189, 248, 0.15)' },
  tmpl: { line: '#818CF8', fill: 'rgba(129, 140, 248, 0.15)' },
};

const radarData = computed(() => {
  if (!compareResult.value) return null;
  const diffs = compareResult.value.diffs as any[];
  if (!diffs || diffs.length === 0) return null;

  // Only show categories with non-zero weight in either portfolio
  const visible = diffs.filter(d => d.user_weight > 0 || d.template_weight > 0);
  const labels = visible.map(d => d.category);
  const tmplName = compareResult.value.template_name || '模板';

  return {
    labels,
    datasets: [
      {
        label: '当前配置',
        data: visible.map(d => +(d.user_weight * 100).toFixed(1)),
        backgroundColor: CHART_COLORS.user.fill,
        borderColor: CHART_COLORS.user.line,
        pointBackgroundColor: CHART_COLORS.user.line,
        borderWidth: 2,
      },
      {
        label: tmplName,
        data: visible.map(d => +(d.template_weight * 100).toFixed(1)),
        backgroundColor: CHART_COLORS.tmpl.fill,
        borderColor: CHART_COLORS.tmpl.line,
        pointBackgroundColor: CHART_COLORS.tmpl.line,
        borderWidth: 2,
        borderDash: [4, 3],
      }
    ]
  };
});

/** Horizontal bar chart showing deviation per category (only >0.5% absolute deviation, sorted) */
const deviationData = computed(() => {
  if (!compareResult.value?.diffs) return null;

  const diffs = (compareResult.value.diffs as any[])
    .filter(d => Math.abs(d.deviation) > 0.005)
    .sort((a, b) => Math.abs(b.deviation) - Math.abs(a.deviation))
    .slice(0, 10);

  if (diffs.length === 0) return null;

  return {
    labels: diffs.map(d => d.category),
    datasets: [{
      data: diffs.map(d => +(d.deviation * 100).toFixed(1)),
      backgroundColor: diffs.map(d =>
        d.deviation > 0 ? 'rgba(248, 113, 113, 0.7)' : 'rgba(52, 211, 153, 0.7)'
      ),
      borderColor: diffs.map(d =>
        d.deviation > 0 ? 'rgba(248, 113, 113, 1)' : 'rgba(52, 211, 153, 1)'
      ),
      borderWidth: 1,
    }]
  };
});

const deviationOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  scales: {
    x: {
      grid: { color: 'rgba(56, 189, 248, 0.08)' },
      ticks: {
        color: '#64748B',
        callback: (v: any) => (v > 0 ? '+' : '') + v + '%'
      }
    },
    y: {
      grid: { display: false },
      ticks: { color: '#64748B' }
    }
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const v = ctx.raw;
          return v > 0 ? `超配 ${v.toFixed(1)}%` : `低配 ${Math.abs(v).toFixed(1)}%`;
        }
      }
    }
  }
};

// --- Metrics delta table ---

const metricsDeltaRows = computed(() => {
  if (!compareResult.value?.metrics_delta) return [];
  const { user, template: tmpl, delta } = compareResult.value.metrics_delta;

  const rows = [
    {
      label: '年化收益',
      userVal: user.expected_return,
      tmplVal: tmpl.expected_return,
      diff: delta.expected_return,
      fmt: (v: number) => (v >= 0 ? '+' : '') + v.toFixed(1) + '%',
      higherIsBetter: true,
    },
    {
      label: '年化波动',
      userVal: user.volatility,
      tmplVal: tmpl.volatility,
      diff: delta.volatility,
      fmt: (v: number) => v.toFixed(1) + '%',
      higherIsBetter: false,
    },
    {
      label: '最大回撤',
      userVal: user.max_drawdown,
      tmplVal: tmpl.max_drawdown,
      diff: delta.max_drawdown,
      fmt: (v: number) => v.toFixed(1) + '%',
      // max_drawdown is negative; closer to zero (diff > 0) is better for user
      higherIsBetter: true,
    },
    {
      label: '夏普比率',
      userVal: user.sharpe_ratio ?? 0,
      tmplVal: tmpl.sharpe_ratio ?? 0,
      diff: (user.sharpe_ratio ?? 0) - (tmpl.sharpe_ratio ?? 0),
      fmt: (v: number) => v.toFixed(2),
      higherIsBetter: true,
    },
  ];

  return rows.map(row => {
    const absD = Math.abs(row.diff);
    const neutral = absD < 0.005;
    let cls = 'mdelta-neutral';
    if (!neutral) {
      const favorable = row.higherIsBetter ? row.diff > 0 : row.diff < 0;
      cls = favorable ? 'mdelta-good' : 'mdelta-bad';
    }
    const sign = row.diff > 0 ? '+' : row.diff < 0 ? '−' : '';
    return {
      label: row.label,
      userStr: row.fmt(row.userVal),
      tmplStr: row.fmt(row.tmplVal),
      diffStr: sign + Math.abs(row.diff).toFixed(row.label === '夏普比率' ? 2 : 1) + (row.label === '夏普比率' ? '' : '%'),
      cls,
    };
  });
});

// --- Deviation table helpers ---

const deviationClass = (deviation: number) => {
  if (deviation > 0.005) return 'dev-over';
  if (deviation < -0.005) return 'dev-under';
  return 'dev-neutral';
};

const formatDeviation = (deviation: number) => {
  const pct = (deviation * 100).toFixed(1);
  return deviation > 0.005 ? `+${pct}%` : `${pct}%`;
};

// --- AI features ---

const runAiMatch = async () => {
  if (store.assets.length === 0) {
    alert('请先在"我的配置"页面添加资产');
    return;
  }

  isAnalyzing.value = true;
  aiMatchResult.value = '';
  showAiResult.value = false;

  try {
    const res = await fetch('/api/ai/profile-match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        portfolio: { total_amount: store.totalAmount, holdings: store.assets }
      })
    });

    const data = await res.json();
    aiMatchResult.value = data.result || data.advice || data.error || '无返回结果';
  } catch (e) {
    aiMatchResult.value = '网络错误，无法连接到后端服务。';
  } finally {
    isAnalyzing.value = false;
  }
};

const runAiMigrate = async () => {
  if (!selectedTemplateId.value) return;

  isMigrating.value = true;
  aiMigrateResult.value = '';
  showMigrateResult.value = false;

  try {
    const res = await fetch('/api/ai/migrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        template_id: selectedTemplateId.value,
        portfolio: { total_amount: store.totalAmount, holdings: store.assets }
      })
    });

    const data = await res.json();
    aiMigrateResult.value = data.result || data.advice || data.error || '无返回结果';
  } catch (e) {
    aiMigrateResult.value = '网络错误，无法连接到后端服务。';
  } finally {
    isMigrating.value = false;
  }
};

const formatMarkdown = (text: string) => {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');
};
</script>
