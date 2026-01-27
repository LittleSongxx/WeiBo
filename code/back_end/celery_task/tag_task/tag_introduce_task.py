"""
:话题基本信息任务构建
@author: lingzhi
* @date 2021/8/8 10:44
"""

from celery_task.config import mongo_conf
from celery_task.utils import mongo_client
from celery_task.utils.gopup_utils import user
import requests
import json
from config import weibo_conf


def introduce(tag_data: dict, tag_task_id: str):
    """

    :param tag_task_id: 话题任务id
    :param tag_data: 话题下的微博数据
    :return:
    """
    data_list = tag_data["data"]
    weibo_count = len(data_list)  # 微博数
    weibo_userid = set()  # 用户集合
    vital_user_id = str()  # 用户id
    hot = 0
    for weibo in data_list:
        weibo_userid.add(weibo["weibo_id"])
        if int(weibo["hot_count"]) > hot:
            vital_user_id = weibo["user_id"]
            hot = int(weibo["hot_count"])
    vital_user = get_user_data(vital_user_id)
    tag_introduce_dict = {
        "tag_task_id": tag_task_id,
        "tag": tag_data["tag"],
        "user_count": len(weibo_userid),
        "weibo_count": weibo_count,
        "vital_user": vital_user,
    }
    query_by_task_id = {"tag_task_id": tag_task_id}
    update_data = {"$set": tag_introduce_dict}
    mongo_client.db[mongo_conf.INTRODUCE].update_one(query_by_task_id, update_data)
    # with Mongo('tag_introduce', 'test') as mongo_db:
    #     mongo_db.collect.update_one(query_by_task_id, update_data)


def get_user_data(user_id) -> json:
    """
    获取user详细信息，优先使用weibo_curl，失败则用gopup兜底
    :param user_id:微博user_id
    :return:
    """
    # 第一步：尝试从weibo_curl API获取
    try:
        url = weibo_conf.BASEPATH + f"/weibo_curl/api/users_show?user_id={user_id}"
        session = requests.Session()
        session.trust_env = False  # 禁用环境代理
        session.proxies = {}  # 显式清除所有代理设置
        response = session.get(url, timeout=10)
        response_dict = json.loads(response.text)
        if response_dict.get("data") and response_dict.get("data").get("result"):
            return response_dict.get("data").get("result")
    except Exception as e:
        print(f"警告: 从weibo_curl获取用户{user_id}失败: {e}，使用gopup兜底")

    # 第二步：使用gopup兜底获取
    try:
        return user(user_id)
    except Exception as gopup_e:
        print(f"错误: gopup获取用户{user_id}也失败: {gopup_e}")
        return None
