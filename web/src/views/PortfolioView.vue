<template>
  <main class="main view-panel active">
    <!-- Sidebar: Input Area -->
    <aside class="sidebar">
      <AssetEditor />
      <AssetSummary :currentDimensionLabel="currentDimensionLabel" />
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
            <span class="tab-badge">{{ getGroupCount(dim.value) }}</span>
          </button>
        </div>
      </div>
      
      <div class="treemap-wrapper">
        <AssetTreemap 
          :dimension="currentDimension" 
          @edit="handleEdit" 
        />
      </div>
      
      <AssetDetailBar :dimension="currentDimension" />
    </section>
    
    <AssetModal 
      v-model:show="showModal" 
      :groupName="modalGroupName" 
      :dimensionKey="currentDimension" 
    />
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useConfigStore } from '@/store/configStore';
import AssetEditor from '@/components/AssetEditor.vue';
import AssetSummary from '@/components/AssetSummary.vue';
import AssetTreemap from '@/components/AssetTreemap.vue';
import AssetDetailBar from '@/components/AssetDetailBar.vue';
import AssetModal from '@/components/AssetModal.vue';

const store = useConfigStore();

type DimensionType = 'type' | 'region' | 'style';
const currentDimension = ref<DimensionType>('type');

const dimensions: {label: string, value: DimensionType}[] = [
  { label: '类型', value: 'type' },
  { label: '区域', value: 'region' },
  { label: '风格', value: 'style' }
];

const currentDimensionLabel = computed(() => {
  return dimensions.find(d => d.value === currentDimension.value)?.label || '类型';
});

const getGroupCount = (dim: DimensionType) => {
  const groups = new Set<string>();
  store.assets.forEach(asset => {
    groups.add(asset[dim] || '其他');
  });
  return groups.size;
};

const showModal = ref(false);
const modalGroupName = ref('');

const handleEdit = (groupName: string) => {
  modalGroupName.value = groupName;
  showModal.value = true;
};

onMounted(() => {
  store.loadConfig();
});
</script>

<style scoped>
/* Component styles inherited from globals */
</style>
