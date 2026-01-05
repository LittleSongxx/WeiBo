"""
: 任务处理层
@author: lingzhi
@time: 2021/7/19 20:01
"""

import os
from config import *
from celery import Celery, platforms

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

celeryapp = Celery(
    __name__,
    broker=f"redis://{redis_host}:{redis_port}/0",
    backend=f"redis://{redis_host}:{redis_port}/1",
    result_serializer=True,
)
celeryapp.autodiscover_tasks(
    [
        "celery_task.task",
        "celery_task.tag_comment_task.task.task_schedule",
        "celery_task.worker",
        "celery_task.worker.task_schedule",
        "celery_task.worker.start_comment_task",
    ]
)
celeryapp.conf.update(
    result_expires=3600,  # 任务结果一小时内没人取就丢弃
)
platforms.C_FORCE_ROOT = True
