<template>
  <div class="treemap-container">
    <div v-if="!store.assets.length" class="empty-state">
      暂无资产，请在左侧添加
    </div>
    <div v-else class="treemap-area" ref="containerRef">
      <div 
        v-for="cell in cells" 
        :key="cell.id"
        class="treemap-cell"
        :style="{
          left: `${cell.x}%`,
          top: `${cell.y}%`,
          width: `${cell.width}%`,
          height: `${cell.height}%`,
          backgroundColor: cell.color
        }"
        @click="emit('edit', cell.originalAsset)"
      >
        <div class="cell-content">
          <div class="cell-name">{{ cell.name }}</div>
          <div class="cell-percent">{{ cell.percent }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useConfigStore } from '@/store/configStore';
import type { Asset } from '@/types';

const props = defineProps<{
  dimension: 'type' | 'region' | 'style'
}>();

const emit = defineEmits<{
  (e: 'edit', asset: Asset): void
}>();

const store = useConfigStore();
const containerRef = ref<HTMLElement | null>(null);

// Colors matching old Vanilla JS implementation
const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
  '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6', 
  '#f97316', '#6366f1'
];

interface TreeMapNode {
  name: string;
  value: number;
  assets: Asset[];
}

// Simple squarified treemap layout generator
const cells = computed(() => {
  if (store.assets.length === 0 || store.totalAmount === 0) return [];

  // Group by dimension
  const groups = new Map<string, TreeMapNode>();
  store.assets.forEach(asset => {
    const key = asset[props.dimension] || '其他';
    if (!groups.has(key)) {
      groups.set(key, { name: key, value: 0, assets: [] });
    }
    const group = groups.get(key)!;
    group.value += asset.amount;
    group.assets.push(asset);
  });

  // Sort groups by value descending
  const sortedGroups = Array.from(groups.values()).sort((a, b) => b.value - a.value);

  // Map to color and percentage
  const colorMap = new Map<string, string>();
  sortedGroups.forEach((g, i) => colorMap.set(g.name, COLORS[i % COLORS.length]));

  // Flatten into cells
  const allCells: any[] = [];
  
  // A very simplified layout for horizontal stacking (MVP replacement for complex squarified math)
  // We'll calculate a simple flow layout first to make sure it works in Vue
  let currentX = 0;
  
  store.assets.forEach(asset => {
    const percent = (asset.amount / store.totalAmount) * 100;
    const groupName = asset[props.dimension] || '其他';
    
    // In a real implementation we would do full squarify.
    // For now we do a simple vertical strip layout for MVP demonstration
    allCells.push({
      id: asset.id,
      name: asset.name,
      amount: asset.amount,
      percent: percent.toFixed(1),
      color: colorMap.get(groupName),
      originalAsset: asset,
      // Fake layout metrics for now until we import full squarify algo
      x: currentX,
      y: 0,
      width: percent,
      height: 100
    });
    
    currentX += percent;
  });

  return allCells;
});
</script>

<style scoped>
.treemap-container {
  width: 100%;
  height: 400px;
  background-color: var(--bg-color);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}
.treemap-area {
  width: 100%;
  height: 100%;
  position: relative;
}
.treemap-cell {
  position: absolute;
  border: 1px solid var(--border-color);
  box-sizing: border-box;
  padding: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}
.treemap-cell:hover {
  opacity: 0.8;
}
.cell-content {
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  font-size: 0.85rem;
}
.cell-name {
  font-weight: 500;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.cell-percent {
  opacity: 0.9;
  font-size: 0.75rem;
}
</style>
