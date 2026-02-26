<template>
  <main class="main view-panel active">
    <!-- Sidebar: Input Area -->
    <aside class="sidebar">
      <AssetEditor />
      <AssetSummary />
    </aside>

    <!-- Display Area -->
    <section class="display">
      <div class="display-header">
        <h2>展示区</h2>
        <div class="dimension-tabs">
          <button 
            v-for="dim in dimensions" 
            :key="dim.value"
            class="tab" 
            :class="{ active: currentDimension === dim.value }"
            @click="currentDimension = dim.value"
          >
            {{ dim.label }}
          </button>
        </div>
      </div>
      
      <div class="treemap-wrapper">
        <AssetTreemap 
          :dimension="currentDimension" 
          @edit="handleEdit" 
        />
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useConfigStore } from '@/store/configStore';
import AssetEditor from '@/components/AssetEditor.vue';
import AssetSummary from '@/components/AssetSummary.vue';
import AssetTreemap from '@/components/AssetTreemap.vue';
import type { Asset } from '@/types';

const store = useConfigStore();

type DimensionType = 'type' | 'region' | 'style';
const currentDimension = ref<DimensionType>('type');

const dimensions: {label: string, value: DimensionType}[] = [
  { label: '类型', value: 'type' },
  { label: '区域', value: 'region' },
  { label: '风格', value: 'style' }
];

const handleEdit = (asset: Asset) => {
  // Simple delete for now as a placeholder for full edit modal
  if (confirm(`确定要删除资产 ${asset.name} 吗？\n(编辑功能将在后续补全)`)) {
    store.removeAsset(asset.id!);
  }
};

onMounted(() => {
  store.loadConfig();
});
</script>
