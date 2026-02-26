<template>
  <main class="main view-panel active">
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
        
        <div v-for="t in templates" :key="t.id" class="template-card" @click="openTemplate(t)">
          <div class="template-header">
            <h3>{{ t.name }}</h3>
            <div class="tags">
              <span v-for="tag in t.personality_tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
          
          <p class="template-desc">{{ t.description }}</p>
          
          <div class="metrics">
            <div class="metric">
              <span class="metric-val">{{ t.metrics.expected_return.toFixed(1) }}%</span>
              <span class="metric-lbl">预期年化</span>
            </div>
            <div class="metric">
              <span class="metric-val">{{ t.metrics.volatility.toFixed(1) }}%</span>
              <span class="metric-lbl">波动率</span>
            </div>
            <div class="metric">
              <span class="metric-val">{{ t.metrics.max_drawdown.toFixed(1) }}%</span>
              <span class="metric-lbl">最大回撤</span>
            </div>
          </div>
          
          <div class="template-footer">
            <span class="view-details">查看详情 &rarr;</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Template Modal (Simple Implementation) -->
    <div v-if="selectedTemplate" class="modal-overlay" @click="closeTemplate">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedTemplate.name }}</h2>
          <button class="modal-close" @click="closeTemplate">&times;</button>
        </div>
        <div class="modal-body">
          <p>{{ selectedTemplate.description }}</p>
          
          <div class="template-detail-grid">
            <div class="template-chart-box">
              <h3>资产配置比例</h3>
              <ChartPie :data="getPieData(selectedTemplate.allocation)" />
            </div>
          </div>
          
          <div class="template-actions">
            <button class="btn btn-primary" @click="copyTemplate(selectedTemplate)">
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
import type { Template } from '@/types';
import ChartPie from '@/components/ChartPie.vue';

const router = useRouter();
const store = useConfigStore();

const templates = ref<Template[]>([]);
const loading = ref(true);
const selectedTemplate = ref<Template | null>(null);

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
  '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6'
];

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

const openTemplate = (t: Template) => {
  selectedTemplate.value = t;
};

const closeTemplate = () => {
  selectedTemplate.value = null;
};

const getPieData = (allocation: Record<string, number>) => {
  const labels = Object.keys(allocation);
  return {
    labels,
    datasets: [{
      data: Object.values(allocation),
      backgroundColor: labels.map((_, i) => COLORS[i % COLORS.length]),
      borderWidth: 0
    }]
  };
};

const copyTemplate = (t: Template) => {
  if (confirm(`这将会覆盖你当前的配置。\n确定要复制【${t.name}】吗？`)) {
    // Generate simple assets from allocation
    const newAssets = Object.entries(t.allocation).map(([type, ratio], index) => {
      // Create a deterministic amount based on a 100k total
      const amount = (ratio / 100) * 100000;
      return {
        name: `${type}资产`,
        code: '',
        amount,
        type,
        region: '全球',
        style: '无'
      };
    });
    
    store.setAssets(newAssets);
    
    // Auto save if in cloud mode
    if (store.mode === 'cloud') {
      store.saveConfig();
    }
    
    closeTemplate();
    router.push('/');
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background-color: var(--panel-bg);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #fff;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-close:hover {
  color: #fff;
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  color: var(--text-color);
  margin-bottom: 24px;
  line-height: 1.6;
}

.template-detail-grid {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.template-chart-box h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 1rem;
  color: #e5e7eb;
  text-align: center;
}

.template-actions {
  display: flex;
  justify-content: center;
}

.btn-primary {
  width: 100%;
  max-width: 300px;
  padding: 12px;
  font-size: 1rem;
}
</style>
