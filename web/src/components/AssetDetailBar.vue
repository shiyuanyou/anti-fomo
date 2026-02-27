<template>
  <div class="detail-bar">
    <div 
      v-for="(item, i) in detailItems" 
      :key="item.name"
      class="detail-chip"
      :style="{ animationDelay: `${i * 0.04}s` }"
    >
      <span class="detail-dot" :style="{ background: item.color }"></span>
      <span class="detail-name">{{ item.name }}</span>
      <span class="detail-pct">{{ item.percent }}%</span>
      <span class="detail-amt">{{ formatAmount(item.value) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useConfigStore } from '@/store/configStore';

const props = defineProps<{
  dimension: 'type' | 'region' | 'style'
}>();

const store = useConfigStore();

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

function formatAmount(n: number) {
  if (n >= 10000) return (n / 10000).toFixed(1) + "万";
  return n.toLocaleString();
}

const detailItems = computed(() => {
  if (store.assets.length === 0 || store.totalAmount === 0) return [];

  const groups = new Map<string, number>();
  store.assets.forEach(asset => {
    const key = asset[props.dimension] || '其他';
    groups.set(key, (groups.get(key) || 0) + asset.amount);
  });
  
  const sorted = Array.from(groups.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
    
  return sorted.map((item, i) => {
    const percent = ((item.value / store.totalAmount) * 100).toFixed(1);
    return {
      ...item,
      percent,
      color: PALETTE[i % PALETTE.length].from
    };
  });
});
</script>

<style scoped>
/* Inherits from global style.css */
</style>
