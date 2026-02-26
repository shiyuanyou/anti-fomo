<template>
  <div class="panel">
    <div class="panel-header">
      <span class="panel-indicator"></span>
      输入区
    </div>
    <div class="panel-body">
      <form @submit.prevent="handleAdd">
        <div class="form-group">
          <label>资产名</label>
          <input type="text" v-model="form.name" placeholder="e.g. 中证A500" required>
        </div>
        <div class="form-group">
          <label>金额</label>
          <input type="number" v-model.number="form.amount" placeholder="e.g. 50000" min="1" required>
        </div>
        <div class="form-group">
          <label>股票代码 (可选)</label>
          <input type="text" v-model="form.code" placeholder="e.g. 000510">
        </div>
        
        <div class="form-group">
          <label>类型</label>
          <select v-model="form.type" required>
            <option value="" disabled>选择类型</option>
            <option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>区域</label>
          <select v-model="form.region" required>
            <option value="" disabled>选择区域</option>
            <option v-for="r in regionOptions" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>风格</label>
          <select v-model="form.style" required>
            <option value="" disabled>选择风格</option>
            <option v-for="s in styleOptions" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        
        <button type="submit" class="btn btn-primary">
          <span class="btn-icon">+</span> 添加资产
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useConfigStore } from '@/store/configStore';
import type { Asset } from '@/types';

const store = useConfigStore();

const typeOptions = ['股票', '大宗商品', '债券', '货币基金', '现金', '其他'];
const regionOptions = ['中国大陆', '中国香港', '美国', '欧洲', '印度', '全球', '无'];
const styleOptions = ['大盘价值', '大盘成长', '中小盘', '商品对冲', '防御型', '新兴市场', '无'];

const defaultForm = {
  name: '',
  code: '',
  amount: '' as unknown as number,
  type: '',
  region: '',
  style: ''
};

const form = reactive({ ...defaultForm });

const handleAdd = () => {
  store.addAsset({
    name: form.name,
    code: form.code || '',
    amount: form.amount,
    type: form.type,
    region: form.region,
    style: form.style
  });
  
  // Reset form but keep last selections for convenience
  form.name = '';
  form.code = '';
  form.amount = '' as unknown as number;
};
</script>
