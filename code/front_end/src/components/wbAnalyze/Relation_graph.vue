<template>
  <div class="relation_graph">
    <div class="relation_graph_top" @click="ToPersonList">
      <svg class="icon" aria-hidden="true">
        <use xlink:href="#icon-wangluoguanxitu"></use>
      </svg>
      <span>关系图</span>
    </div>
    <div id="show_graph"></div>
  </div>
</template>

<script>
export default {
  name: "relation_graph",
  data() {
    return {
      categories: [
        {
          name: "正常用户",
        },
        // {
        //   name: "水军",
        // },
      ],
    };
  },
  methods: {
    myRelationGraph(id) {
      let option;
      let myChart = this.$echarts.init(document.getElementById("show_graph"));
      myChart.showLoading();
      this.$axios.get("relation_graph?tag_task_id="+id).then((res) => {
        console.log(res.data.data);
        
        if (!res.data || !res.data.data) {
          console.error("获取关系图数据失败: 响应数据为空");
          myChart.hideLoading();
          this.$message({
            message: "获取关系图数据失败，请稍后重试",
            type: "warning"
          });
          return;
        }
        
        const graphData = res.data.data;
        let nodes = graphData.nodes_list || [];
        let links = graphData.links_list || [];
        
        if (!Array.isArray(nodes) || !Array.isArray(links)) {
          console.error("关系图数据格式错误");
          myChart.hideLoading();
          this.$message({
            message: "关系图数据格式错误",
            type: "error"
          });
          return;
        }
        
        if (nodes.length === 0) {
          console.warn("关系图节点数据为空");
          myChart.hideLoading();
          this.$message({
            message: "暂无关系图数据",
            type: "info"
          });
          return;
        }
        
        for (let index in nodes) {
          nodes[index].id = index;
          nodes[index].show = false;
        }
        
        links.forEach((link) => {
          for (let node of nodes) {
            if (link.source == node.name) {
              link.source = node.id;
              node.show = true;
            }
            if (link.target == node.name) {
              link.target = node.id;
              node.show = true;
            }
          }
        });
        
        let newNodes = [];
        for(let n in nodes){
          if(nodes[n].show){
            newNodes.push(nodes[n])
          }
        }
        console.log(newNodes);
        console.log(links);
        
        myChart.hideLoading();
        
        newNodes.forEach(function (node) {
          node.label = {
            show: node.value > 10,
          };
        });
        
        option = {
          title: {
            text: "用户关系图",
            subtext: "Default layout",
            top: "bottom",
            left: "right",
          },
          tooltip: {},
          legend: [
            {
              data: this.categories.map(function (a) {
                return a.name;
              }),
            },
          ],
          animationDuration: 1500,
          animationEasingUpdate: "quinticInOut",
          series: [
            {
              name: "用户关系图",
              type: "graph",
              layout: "force",
              data: newNodes,
              links: links,
              categories: this.categories,
              roam: true,
              label: {
                position: "right",
                formatter: "{b}",
              },
              lineStyle: {
                color: "source",
                curveness: 0.3,
              },
              emphasis: {
                focus: "adjacency",
                lineStyle: {
                  width: 10,
                },
              },
            },
          ],
        };
        myChart.setOption(option);
      }).catch((error) => {
        console.error("获取关系图数据失败:", error);
        myChart.hideLoading();
        this.$message({
          message: "获取关系图数据失败，请稍后重试",
          type: "error"
        });
      });
      option && myChart.setOption(option);
    },
    ToPersonList() {
      this.$router.push({
        path: "/person_list",
        query: {
          tag_task_id: this.tid,
        },
      });
    },
  },
  mounted() {
    let res = Array.from(new Array(5), () => []);
    console.log(res);
    this.$bus.$on("send_tag_task_id", (tag_task_id) => {
      console.log("这里是关系图组件,收到了数据:", tag_task_id);
      this.tid = tag_task_id;
      this.myRelationGraph(tag_task_id);

    });
  },
  beforeDestroy() {
    this.$bus.$off("send_tag_task_id");
  },
};
</script>

<style scpoed>
.relation_graph_top {
  margin-left: 10px;
}
.relation_graph {
  background-color: #fff;
  position: absolute;
  top: 31%;
  width: 100%;
  height: 68%;
}
#show_graph {
  height: 500px;
  width: 400px;
}
</style>