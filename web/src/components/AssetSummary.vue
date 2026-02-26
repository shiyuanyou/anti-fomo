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
        <span class="summary-value">{{ store.totalAmount.toLocaleString() }}</span>
      </div>
      
      <button 
        class="btn btn-save" 
        :disabled="store.isSaving || store.assets.length === 0"
        @click="handleSave"
      >
        {{ store.isSaving ? '保存中...' : (store.mode === 'cloud' ? '保存到浏览器' : '生成配置文件') }}
      </button>
      
      <div v-if="store.saveStatus !== 'idle'" class="save-status" :class="store.saveStatus">
        {{ store.saveStatus === 'success' ? '✓ 保存成功' : '✗ 保存失败' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useConfigStore } from '@/store/configStore';

const store = useConfigStore();

const handleSave = () => {
  store.saveConfig();
};
</script>
