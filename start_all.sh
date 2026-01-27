#!/usr/bin/env bash

# 一键启动 Topic_and_user_profile_analysis_system 的主要服务
# 用法：
#   cd ~/code/graduation/Topic_and_user_profile_analysis_system
#   chmod +x start_all.sh
#   ./start_all.sh
#
# 说明：
# - 默认使用 conda 环境 graduation
# - 后端、Celery、爬虫、前端分别后台启动，日志写入 /tmp

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/code/back_end"
CRAWLER_DIR="${PROJECT_ROOT}/code/weibo_crawler"
FRONTEND_DIR="${PROJECT_ROOT}/code/front_end"
CONDA_INIT="${HOME}/miniconda3/etc/profile.d/conda.sh"
ENV_NAME="graduation"

log() { echo "[$(date '+%F %T')] $*"; }

# 1) 激活 conda 环境
if [[ -f "${CONDA_INIT}" ]]; then
  source "${CONDA_INIT}"
  conda activate "${ENV_NAME}"
else
  log "未找到 conda 初始化脚本：${CONDA_INIT}"
  exit 1
fi

# 2) 启动后端 API
log "启动后端 API (main.py)..."
cd "${BACKEND_DIR}"
nohup python main.py > /tmp/topic_backend.log 2>&1 &
log "  后端日志: /tmp/topic_backend.log"

# 3) 启动 Celery Worker
log "启动 Celery Worker..."
nohup celery -A celery_task.worker worker --loglevel=info -P threads > /tmp/topic_celery.log 2>&1 &
log "  Celery 日志: /tmp/topic_celery.log"

# 4) 启动 weibo 爬虫 API
log "启动 weibo_curl_api..."
cd "${CRAWLER_DIR}"
nohup python weibo_curl_api.py > /tmp/topic_crawler.log 2>&1 &
log "  爬虫日志: /tmp/topic_crawler.log"

# 5) 启动前端
log "启动前端 npm run serve..."
cd "${FRONTEND_DIR}"
nohup npm run serve > /tmp/topic_frontend.log 2>&1 &
log "  前端日志: /tmp/topic_frontend.log"

log "全部启动完成。"
log "访问：前端 http://localhost:8080  后端 http://127.0.0.1:8181/docs  爬虫 http://127.0.0.1:8001"

