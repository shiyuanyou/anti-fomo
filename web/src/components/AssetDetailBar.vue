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
import { formatAmount, PALETTE } from '@/utils';

const props = defineProps<{
  dimension: 'type' | 'region' | 'style'
}>();

const store = useConfigStore();

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
