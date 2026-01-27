<template>
  <div class="topic_analysis">
    <div class="topic_analysis_title">主题分析</div>
    <div id="topic_analysis_graph"></div>
  </div>
</template>

<script>
export default {
  name: "topic_analysis",
  data() {
    return {
      topic_analysis: [],
    };
  },
  methods: {
    myTopicAnalysis() {
      let myChart = this.$echarts.init(
        document.getElementById("topic_analysis_graph")
      );
      let option;
      let query = this.$route.query;
      this.$axios
        .get(
            "comment/cluster/type?tag_task_id="+query.tag_task_id+"&weibo_id="+query.weibo_id
        )
        .then((res) => {
          console.log("主题分析数据:", res)
          // 重置数组，避免数据残留
          this.topic_analysis = [];
          if (res.data && res.data.data && Array.isArray(res.data.data)) {
            // 使用新数组存储转换后的数据
            this.topic_analysis = res.data.data.map(item => ({
              name: item.key || '未知',
              value: item.doc_count || 0,
              key: item.key,
              doc_count: item.doc_count
            }));
          }

          // 如果没有数据，不渲染图表
          if (this.topic_analysis.length === 0) {
            console.log("主题分析数据为空");
            return;
          }

          option = {
            legend: {
              orient: "vertical",
              right: "right",
            },
            tooltip: {
              trigger: "item",
            },
            series: [
              {
                name: "主题分析",
                type: "pie",
                radius: "50%",
                data: this.topic_analysis,
                emphasis: {
                  itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: "rgba(0, 0, 0, 0.5)",
                  },
                },
              },
            ],
          };
          myChart.setOption(option);
        })
        .catch((error) => {
          console.error("获取主题分析数据失败:", error);
        });
      option && myChart.setOption(option);
    },
  },
  mounted() {
    this.myTopicAnalysis();
  },
};
</script>

<style scoped>
.topic_analysis {
  position: absolute;
  width: 100%;
  height: 25%;
  top: 20%;
  background-color: #fff;
}
.topic_analysis_title {
  margin: 10px 20px;
  padding: 5px;
  font-weight: 600;
  letter-spacing: 1px;
}
#topic_analysis_graph {
  width: 450px;
  height: 220px;
  position: relative;
  top: -45px;
  left: -20px;
}
</style>