<template>
  <div class="side">
    <div class="side_background"></div>
    <div class="logo" @click="ToHome"></div>
    <div class="wb" @click="ToWB">
      <svg class="icon" aria-hidden="true">
        <use xlink:href="#icon-weibo-copy"></use>
      </svg>
    </div>
    <div class="task-monitor-icon" @click="ToTaskMonitor" title="任务监控">
      <img
        src="../assets/img/monitor.png"
        alt="任务监控"
        class="monitor-img"
      />
      <span class="monitor-text">监控</span>
    </div>
    <div class="user">
      <svg class="icon" aria-hidden="true">
        <use xlink:href="#icon-yonghu"></use>
      </svg>
    </div>
  </div>
</template>

<script>
export default {
  name: "side_border",
  methods: {
    ToWB() {
      this.$router.push({
        path: "/wb",
      });
    },
    ToHome() {
      this.$router.push({
        path: "/home",
      });
    },
    ToTaskMonitor() {
      // 在新标签页中打开任务监控页面，而不是当前页跳转
      window.open("/task_monitor", "_blank");
    },
  },
};
</script>

<style scoped>
.side {
  width: 100%;
  height: 100%;
}
.side_background {
  background: #2f323a;
  width: 100%;
  height: 100%;
}
.logo {
  position: relative;
  top: -100vh;
  width: 50px;
  height: 50px;
  background: #418de6 url("../assets/img/logo.png") no-repeat center center/40px;
}
.wb {
  position: relative;
  top: -100vh;
}
.task-monitor-icon {
  position: relative;
  top: -100vh;
  margin-top: 60px;
  cursor: pointer;
  text-align: center;
}
.task-monitor-icon:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
.monitor-img {
  width: 32px;
  height: 32px;
  margin-top: 4px;
}
.monitor-text {
  color: #fff;
  font-size: 12px;
  display: block;
  margin-top: 2px;
}
.user{
  position: relative;
  bottom: 22vh;
}
.icon {
  width: 50px;
  height: 50px;
}
</style>