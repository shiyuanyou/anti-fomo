<template>
  <div class="chart-container">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Chart from 'chart.js/auto';
import ChartDataLabels from 'chartjs-plugin-datalabels';

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
    indexAxis: 'y',
    scales: {
      x: { 
        stacked: true,
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#9ca3af' }
      },
      y: { 
        stacked: true,
        grid: { display: false },
        ticks: { color: '#9ca3af' }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context: any) => `${context.dataset.label}: ${context.raw.toFixed(1)}%`
        }
      },
      datalabels: {
        color: '#fff',
        formatter: (value: number) => value > 3 ? `${value.toFixed(1)}%` : '',
        font: { size: 11 }
      }
    }
  };

  chartInstance = new Chart(canvasRef.value, {
    type: 'bar',
    plugins: [ChartDataLabels],  // local registration — does not affect other chart instances
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
  height: 250px;
  width: 100%;
}
</style>
