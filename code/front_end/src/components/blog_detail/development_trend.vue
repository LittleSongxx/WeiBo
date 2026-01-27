<template>
  <div class="development_trend">
    <div class="development_trend_title">发展趋势</div>
    <div id="development_trend_line"></div>
  </div>
</template>

<script>
export default {
  name: "development_trend",
  data() {
    return {};
  },
  methods: {
    mydevelopmentTrendLine() {
      let option;
      let myChart = this.$echarts.init(
        document.getElementById("development_trend_line")
      );
      let query = this.$route.query;
      this.$axios
        .get("comment/tendency?tag_task_id="+query.tag_task_id+"&weibo_id="+query.weibo_id)
        .then((res) => {
          // 检查数据是否存在
          if (!res.data || !res.data.data || !res.data.data.data) {
            console.log("发展趋势数据为空");
            return;
          }
          let trend = res.data.data.data;
          console.log("发展趋势数据:", trend);

          // 检查数据是否有效
          if (!trend.data_time || !trend.data_count || trend.data_time.length === 0) {
            console.log("发展趋势数据无效");
            return;
          }

          option = {
            tooltip: {
              trigger: "axis",
              position: "center",
              axisPointer: {
                type: "cross",
                label: {
                  backgroundColor: "#6a7985",
                },
              },
            },
            xAxis: {
              type: "category",
              data: trend.data_time,
            },
            yAxis: {
              type: "value",
            },
            series: [
              {
                data: trend.data_count,
                type: "line",
              },
            ],
          };
          myChart.setOption(option);
        })
        .catch((error) => {
          console.error("获取发展趋势数据失败:", error);
        });
      option && myChart.setOption(option);
    },
  },
  mounted() {
    this.mydevelopmentTrendLine();
  },
};
</script>

<style scoped>
.development_trend {
  position: absolute;
  margin-left: 5px;
  top: 37%;
  height: 20%;
  width: 100%;
  background-color: #fff;
}
.development_trend_title {
  margin: 10px 20px;
  padding: 5px;
  font-weight: 600;
  letter-spacing: 1px;
}
#development_trend_line {
  width: 450px;
  height: 200px;
  top: -55px;
}
</style>