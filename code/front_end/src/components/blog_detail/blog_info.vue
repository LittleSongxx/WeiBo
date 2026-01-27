<template>
  <div class="blog_info">
    <div class="blog_info_title">博文详情</div>
    <div class="user_info">
      <div
        class="user_head"
        :style="{ backgroundImage: 'url(' + blog_info.user_head + ')' }"
      ></div>
      <div class="other_info">
        <div class="user_name">
          {{ blog_info.user_name }}(@{{ blog_info.user_name }})
        </div>
        <div class="blog_time">{{ blog_info.created_at }}</div>
      </div>
    </div>
    <div class="blog_content">
      <span v-if="!show_detail">{{ weibo_content }}...</span>
      <span v-if="show_detail">{{ weibo_content_total }}</span>
      <div
        v-if="!show_detail"
        class="blog_info_show_detail"
        @click="showDetail"
      >
        详情
      </div>
      <div v-if="show_detail" class="blog_info_show_detail" @click="hideDetail">
        收起
      </div>
      <span v-html="'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'"></span>
      <span v-for="topic in blog_info.topics" :key="topic.index"
        >#{{ topic }}#</span
      >
    </div>
    <div class="follow_info">转发({{ blog_info.retweet_count || 0 }}) 点赞({{ blog_info.favorite_count || 0 }}) 评论({{ blog_info.comment_count || 0 }})</div>
  </div>
</template>

<script>
export default {
  name: "blog_info",
  data() {
    return {
      blog_info: {},
      show_detail: true,
      weibo_content: "",
      weibo_content_total: "",
      retry_count: 0,
      max_retries: 10,  // 最多重试10次（约30-50秒）
    };
  },
  filters: {
    snippet(value) {
      if (value.length > 150) value = value.slice(0, 150) + "...";
      return value;
    },
  },
  methods: {
    getBlogInfo() {
      let query = this.$route.query;
      this.$axios
        .get("comment/post_detail?tag_task_id="+query.tag_task_id+"&weibo_id="+query.weibo_id)
        .then((res) => {
          console.log("getBlogInfo response:", res);
          if (!res.data || !res.data.data) {
            this.$message({
              message: "获取博文详情失败：数据为空",
              type: "warning"
            });
            return;
          }
          
          const data = res.data.data;
          // 检查是否是状态信息（任务未完成）
          if (data.status) {
            if (this.retry_count >= this.max_retries) {
              this.$message({
                message: "等待超时，请稍后手动刷新页面",
                type: "warning"
              });
              return;
            }
            
            if (data.status === "processing") {
              this.retry_count++;
              this.$message({
                message: `分析任务进行中，请稍候... (${this.retry_count}/${this.max_retries})`,
                type: "info",
                duration: 2000
              });
              // 3秒后重试
              setTimeout(() => this.getBlogInfo(), 3000);
              return;
            } else if (data.status === "not_found") {
              this.retry_count++;
              this.$message({
                message: `该微博的分析任务尚未创建，等待中... (${this.retry_count}/${this.max_retries})`,
                type: "info",
                duration: 2000
              });
              // 5秒后重试
              setTimeout(() => this.getBlogInfo(), 5000);
              return;
            } else if (data.status === "failed") {
              this.$message({
                message: "分析任务失败：" + (data.message || "未知错误"),
                type: "error"
              });
              return;
            }
          }
          
          // 成功获取数据，重置重试计数
          this.retry_count = 0;

          // 正常数据 - data 包含 user_head, user_name, created_at, weibo_content, topics 等字段
          this.blog_info = data;
          if (data.original_pics && data.original_pics.length > 0) {
            this.blog_info.user_head = data.original_pics[0];
          }
          if (data.weibo_content) {
            this.weibo_content = data.weibo_content.slice(0, 150);
            this.weibo_content_total = data.weibo_content;
          if (this.weibo_content_total != this.weibo_content) {
            this.show_detail = false;
          }
          }
        })
        .catch((error) => {
          console.error("getBlogInfo error:", error);
          this.$message({
            message: "获取博文详情失败：" + (error.message || "网络错误"),
            type: "error"
          });
        });
    },
    showDetail() {
      this.show_detail = true;
    },
    hideDetail() {
      this.show_detail = false;
    },
  },
  mounted() {
    this.getBlogInfo();
  },
};
</script>

<style scoped>
.blog_info {
  top: 1%;
  position: absolute;
  height: 35%;
  margin-left: 5px;
  width: 100%;
  background-color: #fff;
}
.blog_info_title {
  margin: 10px 20px;
  padding: 5px;
  font-weight: 600;
  letter-spacing: 1px;
}
.user_info {
  margin-left: 20px;
}
.user_head {
  width: 30px;
  height: 30px;
  background-size: cover;
}
.other_info {
  display: inline-block;
  margin-left: 20px;
}
.blog_time {
  color: #aaa;
}
.blog_content {
  font-size: 14px;
  margin: 5px 20px;
}
.follow_info {
  margin: 10px 20px;
  font-size: 13px;
  color: #aaa;
  padding-bottom: 10px;
}
.blog_info_show_detail {
  display: inline-block;
  color: skyblue;
  cursor: default;
}
.blog_info_show_detail:hover {
  font-weight: 600;
}
</style>