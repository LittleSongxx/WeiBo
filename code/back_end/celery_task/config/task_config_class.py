"""
:配置类
@author: lingzhi
* @date 2021/8/12 20:29
"""

import os
from pydantic import BaseSettings


class CeleryConfig(BaseSettings):
    """
    celery 启动的相关配置
    """

    @property
    def BROKER(self):
        redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        redis_port = os.getenv("REDIS_PORT", "6379")
        return f"redis://{redis_host}:{redis_port}/0"

    @property
    def BACKEND(self):
        redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        redis_port = os.getenv("REDIS_PORT", "6379")
        return f"redis://{redis_host}:{redis_port}/1"


class MongoConfig(BaseSettings):
    """
    Mongo的相关配置
    """

    HOST: str = os.getenv("MONGO_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("MONGO_PORT", "27017"))
    DB_NAME: str = "test"

    # 话题任务数据库名称
    TASK: str = "tag_task"
    BLOG: str = "blog"
    CHARACTER: str = "character_category"
    EVOLVE: str = "tag_evolve"
    HOT: str = "tag_hot"
    INTRODUCE: str = "tag_introduce"
    RELATION: str = "tag_relation_graph"
    RETWEET: str = "tag_weibo_task"
    CLOUD: str = "tag_word_cloud"
    USER: str = "tag_user"

    # 评论任务数据库名称
    COMMENT_TASK = "comment_task"
    COMMENT_REPOSTS = "comment_reposts"
    COMMENT_CLOUD = "comment_cloud"
    COMMENT_CLUSTER = "comment_cluster"
    COMMENT_NODE = "comment_node"
    COMMENT_TENDENCY = "comment_tendency"
    COMMENT_TOPIC = "comment_topic"
    COMMENT_TREE = "comment_tree"


class ElasticSearchConfig(BaseSettings):
    """
    ES配置
    """

    ES_HOST = os.getenv("ES_HOST", "127.0.0.1:9200")
    ES_SEARCH_INDEX = "weibo"
    ES_TIMEOUT = 60
    LANG_TYPE = ["zh", "en"]
