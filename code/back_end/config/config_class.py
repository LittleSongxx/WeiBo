from pydantic import BaseSettings
from typing import Union, List, Dict, Any


class AppConfig(BaseSettings):
    """
    app启动的相关配置
    """

    HOST: str = "127.0.0.1"
    PORT: int = 8181


class WeiBoConfig(BaseSettings):
    """weibo 爬虫api的相关配置"""

    # weibo_crawler 默认端口在 code/weibo_crawler/settings.py 中为 8001
    # 如需覆盖可通过环境变量 BASEPATH 指定（pydantic BaseSettings 行为）
    BASEPATH: str = "http://127.0.0.1:8001"


class TaskConfig(BaseSettings):
    """任务相关配置"""

    # 用户分析最大数量限制（设置为0表示不限制）
    MAX_USER_ANALYSIS: int = 30
    # 爬取微博的最大页数（每页约20条）
    MAX_SPIDER_PAGES: int = 24
