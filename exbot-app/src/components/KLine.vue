<template>
  <div class="k-line-chart-container">
    <h3 class="k-line-chart-title">COMING SOON</h3>
    <div id="k-line" class="k-line-chart" />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { dispose, init } from "klinecharts";
import generatedKLineDataList from "../generatedKLineDataList";

export default defineComponent({
  name: "KLine",
  mounted: function () {
    const kLineChart = init("k-line");
    const updateData = (any: {}) => {
      setTimeout(() => {
        const dataList = kLineChart.getDataList();
        const lastData = dataList[dataList.length - 1];
        const newData = generatedKLineDataList(
          lastData.timestamp,
          lastData.close,
          1
        )[0];
        newData.timestamp += 60 * 1000;
        kLineChart.updateData(newData as klinecharts.KLineData);
        updateData(kLineChart);
      }, 1000);
    };
    kLineChart.applyNewData(
      generatedKLineDataList() as klinecharts.KLineData[]
    );
    updateData({});
  },
  methods: {},
  destroyed: function () {
    dispose("k-line");
  },
});
</script>
