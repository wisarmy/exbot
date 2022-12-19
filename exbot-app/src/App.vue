<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import KLine from "./components/KLine.vue";
</script>

<template>
  <div class="container">
    <KLine />
  </div>
</template>
<style>
body {
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f2f3f5;
}
div,
p {
  box-sizing: border-box;
}
p {
  margin: 0;
}
.k-line-chart-container {
  display: flex;
  flex-direction: column;
  border-radius: 2px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  background-color: #ffffff;
  width: 100%;
  height: calc(100vh);
  padding: 16px 6px 16px 16px;
}
.k-line-chart-title {
  margin: 0;
  color: #252525;
  padding-bottom: 10px;
}
.k-line-chart {
  display: flex;
  flex: 1;
}
.k-line-chart-menu-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 10px;
  font-size: 12px;
  color: #606060;
}
.k-line-chart-menu-container button {
  cursor: pointer;
  background-color: #2196f3;
  border-radius: 2px;
  margin-right: 8px;
  height: 24px;
  line-height: 26px;
  padding: 0 6px;
  font-size: 12px;
  color: #fff;
  border: none;
  outline: none;
}
</style>
