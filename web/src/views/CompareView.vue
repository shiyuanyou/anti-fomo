<template>
  <main class="main view-panel active">
    <div class="compare-layout">
      <!-- Left: template selector + AI panel -->
      <aside class="compare-sidebar">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-indicator"></span>
            选择对比模板
          </div>
          <div class="panel-body">
            <select class="compare-select" v-model="selectedTemplateId" @change="runCompare">
              <option value="">-- 请选择模板 --</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
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
            <div v-if="aiMatchResult" class="ai-result" v-html="formatMarkdown(aiMatchResult)"></div>
          </div>
        </div>
      </aside>

      <!-- Right: comparison results -->
      <section class="compare-display">
        <div v-if="!compareResult" class="compare-empty">
          <div class="compare-empty-icon">&#9635;</div>
          <p>在左侧选择一个模板，开始与当前配置进行对比</p>
        </div>
        <div v-else class="compare-content">
          <div class="compare-cards">
            <!-- Metrics Card -->
            <div class="compare-card">
              <h3>预期指标对比 (模拟)</h3>
              <div class="metrics-grid">
                <div class="metric-item">
                  <div class="metric-label">年化收益</div>
                  <div class="metric-values">
                    <span class="value-mine">{{ compareResult.metrics_delta.user.expected_return.toFixed(1) }}%</span>
                    <span class="value-vs">vs</span>
                    <span class="value-tmpl">{{ compareResult.metrics_delta.template.expected_return.toFixed(1) }}%</span>
                  </div>
                  <div class="metric-delta" :class="getDeltaClass(compareResult.metrics_delta.delta.expected_return)">
                    {{ formatDelta(compareResult.metrics_delta.delta.expected_return) }}%
                  </div>
                </div>
                
                <div class="metric-item">
                  <div class="metric-label">年化波动率</div>
                  <div class="metric-values">
                    <span class="value-mine">{{ compareResult.metrics_delta.user.volatility.toFixed(1) }}%</span>
                    <span class="value-vs">vs</span>
                    <span class="value-tmpl">{{ compareResult.metrics_delta.template.volatility.toFixed(1) }}%</span>
                  </div>
                  <div class="metric-delta" :class="getDeltaClass(-compareResult.metrics_delta.delta.volatility)">
                    {{ formatDelta(compareResult.metrics_delta.delta.volatility) }}%
                  </div>
                </div>
                
                <div class="metric-item">
                  <div class="metric-label">最大回撤</div>
                  <div class="metric-values">
                    <span class="value-mine">{{ compareResult.metrics_delta.user.max_drawdown.toFixed(1) }}%</span>
                    <span class="value-vs">vs</span>
                    <span class="value-tmpl">{{ compareResult.metrics_delta.template.max_drawdown.toFixed(1) }}%</span>
                  </div>
                  <div class="metric-delta" :class="getDeltaClass(compareResult.metrics_delta.delta.max_drawdown)">
                    {{ formatDelta(compareResult.metrics_delta.delta.max_drawdown) }}%
                  </div>
                </div>
              </div>
            </div>

            <!-- Radar Chart Card -->
            <div class="compare-card">
              <h3>配置倾向 (资产大类)</h3>
              <ChartRadar :data="radarData" />
            </div>

            <!-- Bar Chart Card -->
            <div class="compare-card full-width">
              <h3>大类配置差异</h3>
              <ChartBar :data="barData" />
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useConfigStore } from '@/store/configStore';
import type { Template } from '@/types';
import ChartRadar from '@/components/ChartRadar.vue';
import ChartBar from '@/components/ChartBar.vue';

const store = useConfigStore();
const templates = ref<Template[]>([]);
const selectedTemplateId = ref('');
const compareResult = ref<any>(null);

const isAnalyzing = ref(false);
const aiMatchResult = ref('');

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
  '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6'
];

onMounted(async () => {
  store.loadConfig(); // Ensure we have the latest config
  
  try {
    const res = await fetch('/api/templates');
    if (res.ok) {
      templates.value = await res.json();
    }
  } catch (e) {
    console.error('Failed to load templates', e);
  }
});

const runCompare = async () => {
  if (!selectedTemplateId.value) {
    compareResult.value = null;
    return;
  }
  
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
    }
  } catch (e) {
    console.error('Failed to compare', e);
  }
};

// Computed chart data
const radarData = computed(() => {
  if (!compareResult.value) return null;
  
  const dimData = compareResult.value.dimensions.type;
  const labels = Object.keys(dimData);
  
  return {
    labels,
    datasets: [
      {
        label: '当前配置',
        data: labels.map(l => dimData[l].user_ratio),
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        pointBackgroundColor: '#3b82f6',
        borderWidth: 2,
      },
      {
        label: '对比模板',
        data: labels.map(l => dimData[l].template_ratio),
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        borderColor: '#10b981',
        pointBackgroundColor: '#10b981',
        borderWidth: 2,
      }
    ]
  };
});

const barData = computed(() => {
  if (!compareResult.value) return null;
  
  const dimData = compareResult.value.dimensions.type;
  const labels = Object.keys(dimData);
  
  return {
    labels: ['当前配置', '对比模板'],
    datasets: labels.map((label, i) => ({
      label,
      data: [dimData[label].user_ratio, dimData[label].template_ratio],
      backgroundColor: COLORS[i % COLORS.length]
    }))
  };
});

// Helpers
const getDeltaClass = (val: number) => {
  if (Math.abs(val) < 0.1) return 'neutral';
  return val > 0 ? 'positive' : 'negative';
};

const formatDelta = (val: number) => {
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(1)}`;
};

// AI Match logic (same as before)
const runAiMatch = async () => {
  if (store.assets.length === 0) {
    alert('请先在"我的配置"页面添加资产');
    return;
  }
  
  isAnalyzing.value = true;
  aiMatchResult.value = '';
  
  try {
    const res = await fetch('/api/ai/profile-match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        portfolio: { total_amount: store.totalAmount, holdings: store.assets }
      })
    });
    
    if (res.ok) {
      const data = await res.json();
      aiMatchResult.value = data.advice;
    } else {
      aiMatchResult.value = '分析失败，请检查后端 AI 配置。';
    }
  } catch (e) {
    console.error('Failed to run AI match', e);
    aiMatchResult.value = '网络错误，无法连接到后端服务。';
  } finally {
    isAnalyzing.value = false;
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
