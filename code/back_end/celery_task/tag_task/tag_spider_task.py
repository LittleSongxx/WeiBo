"""
:话题爬虫任务
@author: lingzhi
* @date 2021/7/22 16:24
"""

import requests
import json
from celery_task.utils import mongo_client
from celery_task.utils.my_cloud import MyCloud
from celery_task.config import mongo_conf
from celery_task.utils.gopup_utils import user
from config import weibo_conf
import time as time_module
from datetime import datetime, timedelta

# 加载任务配置
try:
    from config.config_class import TaskConfig
    task_config = TaskConfig()
    MAX_USER_ANALYSIS = task_config.MAX_USER_ANALYSIS
    MAX_SPIDER_PAGES = task_config.MAX_SPIDER_PAGES
except ImportError:
    MAX_USER_ANALYSIS = 30
    MAX_SPIDER_PAGES = 24


def convert_created_at_to_timestamp(created_at_str):
    """
    将微博API返回的created_at字符串转换为时间戳（毫秒）
    支持格式: "刚刚", "几秒前", "几分钟前", "几小时前", "今天 HH:MM", "MM-DD", "YYYY-MM-DD"
    """
    try:
        if not created_at_str:
            return int(time_module.time() * 1000)

        created_at_str = str(created_at_str).strip()
        now = datetime.now()

        if "刚刚" in created_at_str or "秒" in created_at_str:
            return int(time_module.time() * 1000)
        elif "分钟" in created_at_str:
            try:
                minute = int(created_at_str.split("分钟")[0])
                target_time = now - timedelta(minutes=minute)
                return int(target_time.timestamp() * 1000)
            except:
                return int(time_module.time() * 1000)
        elif "小时" in created_at_str:
            try:
                hour = int(created_at_str.split("小时")[0])
                target_time = now - timedelta(hours=hour)
                return int(target_time.timestamp() * 1000)
            except:
                return int(time_module.time() * 1000)
        elif "今天" in created_at_str:
            try:
                time_part = created_at_str.split("今天")[1].strip()
                date_str = now.strftime("%Y-%m-%d") + " " + time_part
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                return int(dt.timestamp() * 1000)
            except:
                return int(time_module.time() * 1000)
        elif "-" in created_at_str:
            try:
                if len(created_at_str) == 5:
                    date_str = now.strftime("%Y-") + created_at_str
                else:
                    date_str = created_at_str
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return int(dt.timestamp() * 1000)
            except:
                return int(time_module.time() * 1000)
        else:
            try:
                ts = float(created_at_str)
                return int(ts * 1000) if ts < 1e10 else int(ts)
            except:
                return int(time_module.time() * 1000)
    except Exception as e:
        print(f"[爬虫] 时间转换失败: {e}, 原始值: {created_at_str}")
        return int(time_module.time() * 1000)


def spider(tag: str, tag_task_id: str):
    """
    tag微博数据的爬取与储存
    :param tag_task_id: 任务id
    :param tag: 话题
    :return:
    """
    result_data_list = list()
    user_set = set()
    false_count = 0  # 无效请求次数
    empty_response_count = 0  # 空响应次数
    session = requests.Session()
    session.trust_env = False
    for i in range(1, MAX_SPIDER_PAGES + 1, 1):
        if false_count >= 5:
            break  # 无效请求大于等于5时,认为无法得到相关数据，停止请求
        if empty_response_count >= 3:
            print(
                f"警告: 连续{empty_response_count}次空响应，可能Cookie已失效，停止爬取"
            )
            break
        url = (
            weibo_conf.BASEPATH
            + "/weibo_curl/api/search_tweets?keyword={keyword}&cursor={cursor}&is_hot=1".format(
                keyword=tag, cursor=i
            )
        )
        try:
            response = session.get(url, timeout=30)
            print(url)
            print("false_count: %s" % false_count)

            # 检查响应是否为空
            if not response.text or response.text.strip() == "":
                print(f"警告: 搜索第{i}页返回空响应")
                empty_response_count += 1
                false_count += 1
                continue

            try:
                weibo_dict = json.loads(response.text)
            except json.JSONDecodeError as je:
                print(f"警告: 搜索第{i}页JSON解析失败: {je}")
                empty_response_count += 1
                false_count += 1
                continue

            # 重置空响应计数
            empty_response_count = 0

        except requests.exceptions.Timeout:
            print(f"警告: 搜索第{i}页请求超时")
            false_count += 1
            continue
        except requests.exceptions.RequestException as re:
            print(f"警告: 搜索第{i}页网络错误: {re}")
            false_count += 1
            continue
        except Exception as e:
            print(f"警告: 搜索第{i}页发生异常: {e}")
            false_count += 1
            continue

        if weibo_dict.get("error_code") == 0:
            false_count = 0
            weibo_list = weibo_dict.get("data", {}).get("result", [])
            new_weibo_list = list()
            for weibo in weibo_list:
                weibo["text"] = weibo["text"] + " "
                weibo["tid"] = weibo["weibo_id"]
                weibo["text_token"] = MyCloud(weibo["text"].split(" ")).GetKeyWord()
                weibo["retweet_count"] = weibo.pop("reposts_count")
                weibo["favorite_count"] = weibo.pop("attitudes_count")
                weibo["comment_count"] = weibo.pop("comments_count")
                weibo["tweet_type"] = "article"
                weibo["data_source"] = "weibo"
                weibo["hot_count"] = (
                    int(weibo["retweet_count"])
                    + int(weibo["favorite_count"])
                    + int(weibo["comment_count"])
                )

                # 添加 create_time 字段（转换created_at）
                if "created_at" in weibo:
                    weibo["create_time"] = convert_created_at_to_timestamp(
                        weibo.get("created_at")
                    )
                elif "create_time" not in weibo:
                    # 如果没有时间信息，使用当前时间
                    weibo["create_time"] = int(time_module.time() * 1000)

                user_set.add(weibo["user_id"])
                new_weibo_list.append(weibo)
            result_data_list.extend(new_weibo_list)
        else:
            false_count += 1
    result_data_list.sort(key=lambda x: int(x["hot_count"]), reverse=True)
    result_data_dict = dict()
    result_data_dict["data"] = result_data_list
    result_data_dict["tag"] = tag
    result_data_dict["tag_task_id"] = tag_task_id
    weibo_id_set = set()  # 热度排名前十的weibo_id
    weibo_post_list = list()
    for i in range(0, len(result_data_dict["data"]), 1):
        if result_data_dict["data"][i]["weibo_id"] not in weibo_id_set:
            weibo_post_list.append(result_data_dict["data"][i])
            weibo_id_set.add(result_data_dict["data"][i]["weibo_id"])
        if len(weibo_id_set) >= 10:
            break
    mongo_client.db[mongo_conf.BLOG].insert_one(result_data_dict)

    # 限制用户分析数量，避免测试周期过长
    # 优先选择热门博文的发布者（按热度排序后的前N个用户）
    user_list = list(user_set)
    if MAX_USER_ANALYSIS > 0 and len(user_list) > MAX_USER_ANALYSIS:
        # 按博文热度排序，优先分析热门博文的发布者
        user_hot_map = {}
        for weibo in result_data_list:
            uid = weibo.get("user_id")
            if uid:
                user_hot_map[uid] = max(user_hot_map.get(uid, 0), weibo.get("hot_count", 0))
        # 按热度排序
        user_list = sorted(user_list, key=lambda x: user_hot_map.get(x, 0), reverse=True)[:MAX_USER_ANALYSIS]
        print(f"[爬虫] 用户数量从 {len(user_set)} 限制为 {len(user_list)} 个（按热度排序）")

    return result_data_dict, list(weibo_post_list), user_list
