#!/usr/bin/env bash

# 一键停止 Topic_and_user_profile_analysis_system 相关进程
# 用法：
#   cd ~/code/graduation/Topic_and_user_profile_analysis_system
#   chmod +x stop_all.sh
#   ./stop_all.sh

set -euo pipefail

echo "开始停止相关进程..."

kill_by_pattern() {
  local pattern="$1"
  local name="$2"

  local pids
  pids=$(pgrep -f "${pattern}" 2>/dev/null || true)

  if [[ -z "${pids}" ]]; then
    echo "  - 未找到 ${name}"
    return
  fi

  echo "  - 停止 ${name}: ${pids}"
  kill ${pids} 2>/dev/null || true
  sleep 1

  # 检查是否还有残留进程
  local still
  still=$(pgrep -f "${pattern}" 2>/dev/null || true)
  if [[ -n "${still}" ]]; then
    echo "    - 强制停止: ${still}"
    kill -9 ${still} 2>/dev/null || true
  fi
}

# 后端 FastAPI (匹配 back_end 目录下的 main.py)
kill_by_pattern "python.*back_end.*main\.py" "后端 API(main.py)"

# Celery worker (更宽松的匹配)
kill_by_pattern "celery.*worker" "Celery Worker"

# weibo 爬虫 API (更宽松的匹配)
kill_by_pattern "weibo_curl_api\.py" "weibo_curl_api"

# 前端 dev server
kill_by_pattern "npm.*serve" "前端 npm serve"
kill_by_pattern "webpack.*dev.*server" "前端 webpack-dev-server"
kill_by_pattern "vue-cli-service.*serve" "前端 vue-cli-service"

# 额外清理：通过端口杀进程（更可靠）
echo ""
echo "检查端口占用..."

kill_by_port() {
  local port="$1"
  local name="$2"
  local pid
  pid=$(lsof -ti:${port} 2>/dev/null || true)
  if [[ -n "${pid}" ]]; then
    echo "  - 停止 ${name} (端口 ${port}): PID ${pid}"
    kill ${pid} 2>/dev/null || true
    sleep 0.5
    # 强制杀死
    pid=$(lsof -ti:${port} 2>/dev/null || true)
    if [[ -n "${pid}" ]]; then
      kill -9 ${pid} 2>/dev/null || true
    fi
  else
    echo "  - 端口 ${port} (${name}) 未被占用"
  fi
}

# 按端口停止服务
kill_by_port 8181 "后端 API"
kill_by_port 8001 "爬虫服务"
kill_by_port 8080 "前端服务"

echo ""
echo "完成。"
echo "如需关闭 Docker(redis/mongo/es)：docker-compose down"
