<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="header-brand">
        <span class="header-logo">&#9678;</span>
        <h1>Anti-FOMO</h1>
      </div>
      <!-- Top-level view navigation -->
      <nav class="view-nav">
        <router-link to="/" class="view-tab" active-class="active">我的配置</router-link>
        <router-link to="/templates" class="view-tab" active-class="active">模板库</router-link>
        <router-link to="/compare" class="view-tab" active-class="active">配置对比</router-link>
      </nav>
      <p class="header-sub">资产配置认知工具</p>
    </header>

    <router-view></router-view>
  </div>
</template>

<script setup lang="ts">
// Main layout component
</script>
