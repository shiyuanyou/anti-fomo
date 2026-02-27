<template>
  <div class="panel panel-summary">
    <div class="panel-header">
      <span class="panel-indicator"></span>
      配置概览
    </div>
    <div class="panel-body">
      <div class="summary-item">
        <span class="summary-label">资产数量</span>
        <span class="summary-value">{{ store.assets.length }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">总金额</span>
        <span class="summary-value">{{ formatAmount(store.totalAmount) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">当前维度</span>
        <span class="summary-value">{{ currentDimensionLabel }}</span>
      </div>
      
      <button 
        class="btn btn-save" 
        :disabled="store.isSaving || store.assets.length === 0"
        @click="handleSave"
      >
        {{ store.isSaving ? '保存中...' : (store.mode === 'cloud' ? '保存到浏览器' : '生成配置文件') }}
      </button>
      
      <div v-if="store.saveStatus !== 'idle'" class="save-status" :class="saveStatusClass">
        {{ store.saveStatus === 'success' ? 'config.asset.yaml 已生成' : '保存失败，请检查后端连接' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useConfigStore } from '@/store/configStore';
import { formatAmount } from '@/utils';

const props = defineProps<{
  currentDimensionLabel: string
}>();

const store = useConfigStore();

// Map store's semantic status to the CSS class names defined in style.css
const saveStatusClass = computed(() => {
  if (store.saveStatus === 'success') return 'save-ok';
  if (store.saveStatus === 'error') return 'save-err';
  return '';
});

const handleSave = () => {
  store.saveConfig();
};
</script>
