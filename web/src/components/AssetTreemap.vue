<template>
  <div class="treemap-container" ref="containerRef" :class="fadingClass">
    <div v-if="!store.assets.length" class="empty-state">
      暂无资产，请在左侧添加
    </div>
    <div v-else class="treemap-area" @mousemove="onMouseMove" @mouseleave="onMouseLeave">
      <div 
        v-for="cell in layoutCells" 
        :key="cell.id"
        class="treemap-block"
        :class="classifySize(cell.w - GAP * 2, cell.h - GAP * 2)"
        :style="{
          left: `${cell.x + GAP}px`,
          top: `${cell.y + GAP}px`,
          width: `${Math.max(0, cell.w - GAP * 2)}px`,
          height: `${Math.max(0, cell.h - GAP * 2)}px`,
          background: `linear-gradient(135deg, ${cell.color.from} 0%, ${cell.color.to} 100%)`,
          borderRadius: '4px',
          animationDelay: `${cell.index * 0.06}s`
        }"
        @click="emit('edit', cell.name)"
        @mouseenter="hoveredBlock = cell"
      >
        <span class="block-name">{{ cell.name }}</span>
        <span class="block-pct">{{ cell.percent }}%</span>
        <span class="block-amount">{{ formatAmount(cell.value) }}</span>
      </div>
    </div>

    <!-- Enhanced Tooltip -->
    <div 
      class="treemap-tooltip" 
      :class="{ visible: showTooltip && hoveredBlock }"
      :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
      ref="tooltipRef"
    >
      <template v-if="hoveredBlock">
        <div class="tip-name">{{ hoveredBlock.name }}</div>
        <div class="tip-row"><span>占比</span><span class="tip-val tip-pct">{{ hoveredBlock.percent }}%</span></div>
        <div class="tip-row"><span>金额</span><span class="tip-val tip-amt">{{ formatAmount(hoveredBlock.value) }}</span></div>
        <div class="tip-row"><span>标的数</span><span class="tip-val tip-cnt">{{ hoveredBlock.items.length }} 项</span></div>
        <div class="tip-items" v-if="hoveredBlock.items.length > 1">
          <div class="tip-items-title">包含标的</div>
          <div v-for="it in hoveredBlock.items" :key="it.id" class="tip-item">
            <span>{{ it.name }}</span>
            <span class="tip-item-val">{{ formatAmount(it.amount) }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useConfigStore } from '@/store/configStore';
import { formatAmount, PALETTE } from '@/utils';
import type { Asset } from '@/types';

const props = defineProps<{
  dimension: 'type' | 'region' | 'style'
}>();

const emit = defineEmits<{
  (e: 'edit', groupName: string): void
}>();

const store = useConfigStore();
const containerRef = ref<HTMLElement | null>(null);
const tooltipRef = ref<HTMLElement | null>(null);
const containerSize = ref({ width: 0, height: 0 });

// Dimension switch fading animation
const fadingClass = ref<string>('');
let isTransitioning = false;

// Tooltip state
const showTooltip = ref(false);
const hoveredBlock = ref<any>(null);
const tooltipX = ref(0);
const tooltipY = ref(0);

const resizeObserver = ref<ResizeObserver | null>(null);

const updateSize = () => {
  // Measure the inner treemap-area for layout; fall back to container
  const el = containerRef.value;
  if (el) {
    containerSize.value = {
      width: el.clientWidth,
      height: el.clientHeight
    };
  }
};

onMounted(() => {
  updateSize();
  
  if (containerRef.value) {
    resizeObserver.value = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === containerRef.value) {
          containerSize.value = {
            width: entry.contentRect.width,
            height: entry.contentRect.height
          };
        }
      }
    });
    
    resizeObserver.value.observe(containerRef.value);
  }
  
  window.addEventListener('resize', updateSize);
});

onUnmounted(() => {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect();
  }
  window.removeEventListener('resize', updateSize);
});

// Fading transition when dimension prop changes
watch(() => props.dimension, async (newVal, oldVal) => {
  if (newVal === oldVal || isTransitioning) return;
  isTransitioning = true;

  fadingClass.value = 'fading-out';
  await new Promise(r => setTimeout(r, 200));

  fadingClass.value = 'fading-in';
  await new Promise(r => setTimeout(r, 350));

  fadingClass.value = '';
  isTransitioning = false;
});

watch(() => store.assets.length, async (newLen, oldLen) => {
  if (oldLen === 0 && newLen > 0) {
    await nextTick();
    updateSize();
    
    if (!resizeObserver.value && containerRef.value) {
       resizeObserver.value = new ResizeObserver((entries) => {
         for (const entry of entries) {
           if (entry.target === containerRef.value) {
             containerSize.value = {
               width: entry.contentRect.width,
               height: entry.contentRect.height
             };
           }
         }
       });
       resizeObserver.value.observe(containerRef.value);
    }
  }
});

const onMouseMove = (e: MouseEvent) => {
  if (!hoveredBlock.value) return;
  
  showTooltip.value = true;
  
  // Need to make sure tooltip is rendered to get its dimensions
  nextTick(() => {
    let tipWidth = 200; // default estimate
    let tipHeight = 150; // default estimate
    
    if (tooltipRef.value) {
      tipWidth = tooltipRef.value.offsetWidth;
      tipHeight = tooltipRef.value.offsetHeight;
    }
    
    tooltipX.value = Math.min(e.clientX + 14, window.innerWidth - tipWidth - 10);
    tooltipY.value = Math.min(e.clientY + 14, window.innerHeight - tipHeight - 10);
  });
};

const onMouseLeave = () => {
  showTooltip.value = false;
  hoveredBlock.value = null;
};

const GAP = 3; // px gap between blocks

function classifySize(w: number, h: number) {
  if (w < 60 || h < 35) return "size-tiny";
  if (w < 110 || h < 65) return "size-small";
  if (w < 160 || h < 90) return "size-medium";
  return "size-large";
}

function worstAspectRatio(row: any[], sideLength: number) {
  if (row.length === 0) return Infinity;
  const rowArea = row.reduce((s, item) => s + item.area, 0);
  const rowSide = rowArea / sideLength;
  let worst = 0;
  for (const item of row) {
    const otherSide = item.area / rowSide;
    const ratio = Math.max(rowSide / otherSide, otherSide / rowSide);
    if (ratio > worst) worst = ratio;
  }
  return worst;
}

function computeTreemap(items: any[], rect: {x: number, y: number, w: number, h: number}) {
  if (items.length === 0) return [];

  const totalValue = items.reduce((s, i) => s + i.value, 0);
  const totalArea = rect.w * rect.h;

  // Sort descending, attach normalized area
  const sorted = items
    .map(item => ({ ...item, area: (item.value / totalValue) * totalArea }))
    .sort((a, b) => b.area - a.area);

  const results: any[] = [];
  let remaining = [...sorted];
  let cur = { ...rect };

  while (remaining.length > 0) {
    if (remaining.length === 1) {
      results.push({ ...remaining[0], x: cur.x, y: cur.y, w: cur.w, h: cur.h });
      break;
    }

    const shortSide = Math.min(cur.w, cur.h);
    const row = [remaining[0]];
    remaining = remaining.slice(1);

    while (remaining.length > 0) {
      const candidate = [...row, remaining[0]];
      if (worstAspectRatio(candidate, shortSide) <= worstAspectRatio(row, shortSide)) {
        row.push(remaining.shift()!);
      } else {
        break;
      }
    }

    // Layout the finalized row
    const rowArea = row.reduce((s, i) => s + i.area, 0);
    const isHorizontal = cur.w >= cur.h;

    if (isHorizontal) {
      const rowW = rowArea / cur.h;
      let y = cur.y;
      for (const item of row) {
        const h = item.area / rowW;
        results.push({ ...item, x: cur.x, y, w: rowW, h });
        y += h;
      }
      cur = { x: cur.x + rowW, y: cur.y, w: cur.w - rowW, h: cur.h };
    } else {
      const rowH = rowArea / cur.w;
      let x = cur.x;
      for (const item of row) {
        const w = item.area / rowH;
        results.push({ ...item, x, y: cur.y, w, h: rowH });
        x += w;
      }
      cur = { x: cur.x, y: cur.y + rowH, w: cur.w, h: cur.h - rowH };
    }
  }

  return results;
}

const layoutCells = computed(() => {
  if (store.assets.length === 0 || store.totalAmount === 0) return [];
  
  // Need valid container size. Since we use `width: 100%; height: 100%;` with flex
  // the container might report 0 size briefly. Force a minimum size if it's too small.
  const rect = {
    x: 0,
    y: 0,
    w: Math.max(containerSize.value.width, 100),
    h: Math.max(containerSize.value.height, 100)
  };

  // 1. Group by dimension
  const groups = new Map<string, any>();
  store.assets.forEach(asset => {
    const key = asset[props.dimension] || '其他';
    if (!groups.has(key)) {
      groups.set(key, { name: key, value: 0, items: [] });
    }
    const group = groups.get(key)!;
    group.value += asset.amount;
    group.items.push(asset);
  });
  
  const groupedItems = Array.from(groups.values());
  const blocks = computeTreemap(groupedItems, rect);
  
  // 3. Format result for template
  return blocks.map((block, i) => {
    const percent = ((block.value / store.totalAmount) * 100).toFixed(1);
    return {
      ...block,
      id: `block-${block.name}-${i}`,
      index: i,
      percent,
      color: PALETTE[i % PALETTE.length]
    };
  });
});
</script>

<style scoped>
.treemap-container {
  width: 100%;
  height: 100%; /* Change to 100% to fill the wrapper correctly */
  min-height: 400px;
  background-color: transparent; 
  border-radius: 8px;
  position: relative;
  /* Don't use overflow: hidden here so tooltip can escape if needed, though tooltip is position:fixed */
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

/* Base block styles — animation handled by global blockIn in style.css */
.treemap-block {
  position: absolute;
  box-sizing: border-box;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  overflow: hidden;
  color: #ffffff;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.treemap-block:hover {
  filter: brightness(1.25);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 24px rgba(0, 0, 0, 0.3), inset 0 0 30px rgba(255, 255, 255, 0.03);
  z-index: 10;
}

/* Typography styles based on size classes */
.block-name {
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.block-pct {
  font-weight: 700;
  opacity: 0.95;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.block-amount {
  font-family: 'Courier New', Courier, monospace;
  opacity: 0.8;
  margin-top: auto;
  font-size: 0.85rem;
}

/* Size classes */
.size-large .block-name { font-size: 1.4rem; margin-bottom: 8px; }
.size-large .block-pct { font-size: 1.6rem; }
.size-large .block-amount { font-size: 1rem; }

.size-medium .block-name { font-size: 1.1rem; }
.size-medium .block-pct { font-size: 1.2rem; }

.size-small .block-name { font-size: 0.9rem; margin-bottom: 2px; }
.size-small .block-pct { font-size: 1rem; }
.size-small .block-amount { display: none; }
.size-small { padding: 8px; }

.size-tiny {
  padding: 4px;
  justify-content: center;
  align-items: center;
}
.size-tiny .block-name {
  font-size: 0.8rem;
  margin: 0;
  text-align: center;
}
.size-tiny .block-pct, .size-tiny .block-amount { display: none; }

/* Tooltip styles */
.treemap-tooltip {
    position: fixed;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(8px);
    border: 1px solid var(--border-color);
    padding: 12px 16px;
    border-radius: 8px;
    color: #fff;
    font-size: 12px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s ease;
    z-index: 1000;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    min-width: 180px;
}

.treemap-tooltip.visible {
    opacity: 1;
}

.tip-name {
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
}

.tip-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
    color: var(--text-secondary);
}

.tip-val {
    font-weight: 600;
    font-family: var(--font-mono);
    color: var(--text-primary);
}

.tip-pct { color: var(--accent); }

.tip-items {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.tip-items-title {
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 6px;
    font-weight: 600;
}

.tip-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 3px;
    font-size: 11px;
    color: var(--text-secondary);
}

.tip-item-val {
    font-family: var(--font-mono);
    opacity: 0.8;
}
</style>
