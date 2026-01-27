"""
:用户分析任务
@author: lingzhi
* @date 2021/10/23 23:26
"""

from celery_task.utils.gopup_utils import tendency
from celery_task.utils.my_db import Mongo
import requests
import json
from celery_task.utils.themeCluster.Single_Pass.single_pass_cluster import (
    SinglePassCluster,
)
from celery_task.utils.gopup_utils import user
import random
import time
from config import weibo_conf

# 尝试从统一配置加载延迟参数
try:
    from config import get_delay_range
    delay_config = get_delay_range()
    USER_INFO_DELAY_MIN = delay_config.get('user_info_delay_min', 5)
    USER_INFO_DELAY_MAX = delay_config.get('user_info_delay_max', 10)
    FAILURE_DELAY_MIN = delay_config.get('failure_delay_min', 5)
    FAILURE_DELAY_MAX = delay_config.get('failure_delay_max', 10)
except ImportError:
    USER_INFO_DELAY_MIN = 5
    USER_INFO_DELAY_MAX = 10
    FAILURE_DELAY_MIN = 5
    FAILURE_DELAY_MAX = 10


def user_analysis(weibo_blog_data: dict, tag_task_id: str, user_id_list: list):
    user_list = list()
    blog_data = weibo_blog_data.get("data", [])
    session = requests.Session()
    session.trust_env = False  # 禁用环境代理
    session.proxies = {}  # 显式清除所有代理设置

    continuous_failures = 0  # 连续失败计数器
    max_consecutive_failures = 5  # 连续失败5次后停止爬取

    # 检查数据是否存在
    if not blog_data or not isinstance(blog_data, list) or len(blog_data) == 0:
        print(f"警告: 博文数据为空或格式错误")
        # 返回空数据而不是None
        from celery_task.utils import mongo_client
        from celery_task.config import mongo_conf

        empty_data = {"data": [], "categories": 0}
        mongo_client.db[mongo_conf.USER].update_one(
            {"tag_task_id": tag_task_id}, {"$set": empty_data}
        )
        return empty_data

    for idx, user_id in enumerate(user_id_list, 1):
        # 检查是否已达到连续失败阈值
        if continuous_failures >= max_consecutive_failures:
            print(f"⚠️ 连续失败{continuous_failures}次，停止用户信息爬取，继续后续流程")
            break

        print(
            f"[用户分析] 正在获取用户信息: {idx}/{len(user_id_list)} (用户ID: {user_id})"
        )
        user_info = None

        # 第一阶段：尝试从 weibo_curl API 获取（如果服务可用且 Cookie 有效）
        try:
            user_url = (
                weibo_conf.BASEPATH
                + "/weibo_curl/api/users_show?user_id={user_id}".format(user_id=user_id)
            )
            print(f"爬取:{user_id}用户(weibo_curl)")
            response = session.get(user_url, timeout=30)
            response.raise_for_status()

            # 检查响应是否为空
            if response.text and response.text.strip() != "":
                try:
                    user_dict = json.loads(response.text)
                    if (
                        user_dict.get("error_code") == 0
                        and user_dict.get("data")
                        and user_dict.get("data").get("result")
                    ):
                        user_info = user_dict.get("data").get("result")
                        user_list.append(user_info)
                        print(f"✓ 成功从weibo_curl获取用户{user_id}信息")
                        continuous_failures = 0  # 重置失败计数器
                        time.sleep(random.uniform(USER_INFO_DELAY_MIN, USER_INFO_DELAY_MAX))  # 使用配置的延迟防止反爬
                        continue
                except json.JSONDecodeError as je:
                    print(f"警告: 用户{user_id}JSON解析失败: {je}，转用gopup")
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            print(
                f"警告: 用户{user_id}从weibo_curl获取失败({type(e).__name__})，转用gopup"
            )
            time.sleep(random.uniform(FAILURE_DELAY_MIN, FAILURE_DELAY_MAX))  # 失败后使用配置的延迟
        except Exception as e:
            print(f"警告: 用户{user_id}从weibo_curl获取异常: {e}，转用gopup")
            time.sleep(random.uniform(FAILURE_DELAY_MIN, FAILURE_DELAY_MAX))

        # 第二阶段：使用 gopup 库兜底获取用户信息
        if user_info is None:
            try:
                print(f"使用gopup获取用户{user_id}信息...")
                gopup_result = user(user_id)
                if gopup_result and "error" not in gopup_result:
                    user_list.append(gopup_result)
                    print(f"✓ 成功从gopup获取用户{user_id}信息")
                    continuous_failures = 0  # 重置失败计数器
                else:
                    print(f"✗ 用户{user_id}信息获取失败(gopup返回错误)，跳过此用户")
                    continuous_failures += 1  # 增加失败计数
            except Exception as gopup_e:
                print(f"✗ gopup获取用户{user_id}失败: {gopup_e}，跳过此用户")
                continuous_failures += 1  # 增加失败计数
            time.sleep(random.uniform(FAILURE_DELAY_MIN, FAILURE_DELAY_MAX))  # 使用配置的延迟
        else:
            # 仅在第一阶段成功时延迟已在上面处理，这里只针对gopup的情况
            pass

    # 如果没有获取到用户数据，返回空数据
    if len(user_list) == 0:
        print(f"警告: 没有获取到任何用户数据")
        from celery_task.utils import mongo_client
        from celery_task.config import mongo_conf

        empty_data = {"data": [], "categories": 0}
        mongo_client.db[mongo_conf.USER].update_one(
            {"tag_task_id": tag_task_id}, {"$set": empty_data}
        )
        return empty_data

    try:
        user_mark = SinglePassCluster(
            tag_task_id=tag_task_id,
            blog_data=blog_data,
            user_list=user_list,
        )
        user_mark_data = user_mark.single_pass()
        return user_mark_data
    except Exception as e:
        print(f"用户分析任务失败: {e}")
        import traceback

        traceback.print_exc()
        # 返回空数据而不是None
        from celery_task.utils import mongo_client
        from celery_task.config import mongo_conf

        empty_data = {"data": [], "categories": 0}
        mongo_client.db[mongo_conf.USER].update_one(
            {"tag_task_id": tag_task_id}, {"$set": empty_data}
        )
        return empty_data
