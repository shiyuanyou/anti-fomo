<template>
  <div class="chart-container">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps<{
  data: any,
  options?: any
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
let chartInstance: Chart | null = null;

const renderChart = () => {
  if (!canvasRef.value) return;
  
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: { color: '#9ca3af', font: { size: 12 } },
        ticks: { display: false }
      }
    },
    plugins: {
      legend: { position: 'bottom', labels: { color: '#e5e7eb' } }
    }
  };

  chartInstance = new Chart(canvasRef.value, {
    type: 'radar',
    data: props.data,
    options: props.options || defaultOptions
  });
};

watch(() => props.data, renderChart, { deep: true });

onMounted(renderChart);

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
}
</style>
