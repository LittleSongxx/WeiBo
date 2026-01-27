<template>
  <div class="task-monitor">
    <div class="monitor-header">
      <h2>评论分析任务监控</h2>
      <div class="header-actions">
        <el-input
          v-model="filterTagTaskId"
          placeholder="按话题任务ID过滤（可选）"
          style="width: 300px; margin-right: 10px;"
          clearable
        />
        <el-button type="primary" @click="loadTasks">刷新</el-button>
        <el-button @click="autoRefresh = !autoRefresh">
          {{ autoRefresh ? '停止自动刷新' : '开启自动刷新' }}
        </el-button>
      </div>
    </div>

    <div class="stats-bar">
      <el-card class="stat-card">
        <div class="stat-label">总任务数</div>
        <div class="stat-value">{{ total }}</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-label">已完成</div>
        <div class="stat-value success">{{ statusCounts.SUCCESS || 0 }}</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-label">进行中</div>
        <div class="stat-value progress">{{ statusCounts.PROGRESS || 0 }}</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-label">等待中</div>
        <div class="stat-value pending">{{ statusCounts.PENDING || 0 }}</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-label">失败</div>
        <div class="stat-value failed">{{ statusCounts.FAILURE || 0 }}</div>
      </el-card>
      <el-card class="stat-card" v-if="statusCounts.EXPIRED > 0">
        <div class="stat-label">已过期</div>
        <div class="stat-value expired">{{ statusCounts.EXPIRED || 0 }}</div>
      </el-card>
    </div>

    <el-table
      :data="tasks"
      stripe
      border
      style="width: 100%; margin-top: 20px;"
      v-loading="loading"
    >
      <el-table-column prop="tag_task_id" label="话题任务ID" width="200" />
      <el-table-column prop="weibo_id" label="微博ID" width="150" />
      <el-table-column prop="user_name" label="用户名" width="120" />
      <el-table-column prop="weibo_text" label="微博内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="analysis_status" label="状态" width="150">
        <template slot-scope="scope">
          <el-tag :type="getStatusType(scope.row.analysis_status)">
            {{ formatStatus(scope.row.analysis_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="150" fixed="right">
        <template slot-scope="scope">
            <el-button
            size="mini"
            type="primary"
            @click="viewDetail(scope.row)"
            :disabled="!scope.row.has_detail && scope.row.analysis_status !== 'SUCCESS'"
          >
            查看详情
          </el-button>
          <el-button
            size="mini"
            type="info"
            @click="checkStatus(scope.row)"
            style="margin-left: 5px;"
          >
            查看状态
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="tasks.length === 0 && !loading" class="empty-tips">
      <p>暂无评论分析任务</p>
      <p style="color: #999; font-size: 12px; margin-top: 10px;">
        提示：评论分析任务会在话题分析完成后自动创建
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: "task_monitor",
  data() {
    return {
      tasks: [],
      total: 0,
      loading: false,
      autoRefresh: false,
      refreshInterval: null,
      filterTagTaskId: "",
      statusCounts: {},
    };
  },
  methods: {
    async loadTasks() {
      this.loading = true;
      try {
        const url = this.filterTagTaskId
          ? `comment/task_list?tag_task_id=${this.filterTagTaskId}`
          : "comment/task_list";
        
        const res = await this.$axios.get(url);
        
        if (res.data && res.data.code === 0) {
          this.tasks = res.data.data.tasks || [];
          this.total = res.data.data.total || 0;
          this.calculateStatusCounts();
        } else {
          this.$message.error("获取任务列表失败：" + (res.data?.data || "未知错误"));
          this.tasks = [];
          this.total = 0;
        }
      } catch (error) {
        console.error("loadTasks error:", error);
        this.$message.error("获取任务列表失败：" + (error.message || "网络错误"));
        this.tasks = [];
        this.total = 0;
      } finally {
        this.loading = false;
      }
    },
    calculateStatusCounts() {
      this.statusCounts = {
        SUCCESS: 0,
        PROGRESS: 0,
        PENDING: 0,
        FAILURE: 0,
        EXPIRED: 0,
      };
      
      this.tasks.forEach(task => {
        const status = task.analysis_status;
        if (status === "SUCCESS") {
          this.statusCounts.SUCCESS++;
        } else if (status === "PENDING" || status === "STARTED") {
          this.statusCounts.PENDING++;
        } else if (status === "PROGRESS") {
          this.statusCounts.PROGRESS++;
        } else if (status === "FAILURE" || status === "FAILED") {
          this.statusCounts.FAILURE++;
        } else if (status === "EXPIRED") {
          this.statusCounts.EXPIRED++;
        } else {
          // PROGRESS 或其他进行中状态
          this.statusCounts.PROGRESS++;
        }
      });
    },
    getStatusType(status) {
      if (status === "SUCCESS") return "success";
      if (status === "FAILURE" || status === "FAILED") return "danger";
      if (status === "PENDING" || status === "STARTED") return "info";
      if (status === "EXPIRED") return "warning";
      return "warning"; // PROGRESS 或其他进行中状态
    },
    formatStatus(status) {
      const statusMap = {
        "SUCCESS": "已完成",
        "PENDING": "等待中",
        "STARTED": "已启动",
        "FAILURE": "失败",
        "FAILED": "失败",
        "PROGRESS": "进行中",
        "EXPIRED": "已过期",
        "爬虫任务": "爬虫任务",
        "传播树构建任务": "构建传播树",
        "主题挖掘任务": "主题挖掘",
        "词云任务": "生成词云",
        "趋势任务": "分析趋势",
        "关键节点任务": "计算关键节点",
      };
      return statusMap[status] || status;
    },
    viewDetail(task) {
      this.$router.push({
        path: "/blog_detail",
        query: {
          tag_task_id: task.tag_task_id,
          weibo_id: task.weibo_id,
        },
      });
    },
    async checkStatus(task) {
      try {
        const res = await this.$axios.get(
          `comment/task_status?tag_task_id=${task.tag_task_id}&weibo_id=${task.weibo_id}`
        );
        if (res.data && res.data.code === 0) {
          const status = res.data.data;
          let message = `状态: ${this.formatStatus(status.analysis_status)}`;
          if (status.progress) {
            message += `\n当前进度: ${status.progress}`;
          }
          if (status.has_detail) {
            message += `\n详情数据: 已生成`;
          }
          this.$alert(message, "任务状态详情", {
            confirmButtonText: "确定",
          });
        } else {
          this.$message.error("获取任务状态失败");
        }
      } catch (error) {
        console.error("checkStatus error:", error);
        this.$message.error("获取任务状态失败：" + (error.message || "网络错误"));
      }
    },
  },
  watch: {
    autoRefresh(newVal) {
      if (newVal) {
        this.refreshInterval = setInterval(() => {
          this.loadTasks();
        }, 5000); // 每5秒自动刷新
        this.$message.info("已开启自动刷新（每5秒）");
      } else {
        if (this.refreshInterval) {
          clearInterval(this.refreshInterval);
          this.refreshInterval = null;
        }
        this.$message.info("已停止自动刷新");
      }
    },
    filterTagTaskId() {
      // 过滤条件改变时重新加载
      this.loadTasks();
    },
  },
  mounted() {
    this.loadTasks();
  },
  beforeDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },
};
</script>

<style scoped>
.task-monitor {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background-color: #fff;
  padding: 20px;
  border-radius: 4px;
}

.monitor-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
}

.stats-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.progress {
  color: #e6a23c;
}

.stat-value.pending {
  color: #909399;
}

.stat-value.failed {
  color: #f56c6c;
}

.stat-value.expired {
  color: #909399;
}

.empty-tips {
  text-align: center;
  padding: 60px 20px;
  background-color: #fff;
  border-radius: 4px;
  margin-top: 20px;
}

.empty-tips p {
  margin: 0;
  font-size: 16px;
  color: #666;
}
</style>
