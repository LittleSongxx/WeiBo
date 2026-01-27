"""
task，将模型与数据处理部分分离
计划仅由本文件提供task任务
"""

import time
import json
import pymongo
import requests
from bson import ObjectId

from celery_task.config import mongo_conf
from celery_task.utils import mongo_client
from config import weibo_conf

from celery_task import celeryapp
from celery_task.tag_comment_task.process import get_path_tree_part
from celery_task.utils.gsdmmCluster.cluster_extract import cluster_extract
from celery_task.tag_comment_task.my_cloud import preContent
from celery_task.tag_comment_task.myRank import startRank
from celery_task.tag_comment_task.repost_spider import spider_list
from celery_task.utils.my_db import Mongo


def init_task(tag_comment_task_dict):
    """
    # 微博评论任务id的储存
    :param tag_comment_task_dict:
    :return:
    """
    tree_id = mongo_client.db[mongo_conf.COMMENT_TREE].insert_one(
        {"tag_comment_task_id": tag_comment_task_dict["tag_comment_task_id"]}
    )
    cluster_id = mongo_client.db[mongo_conf.COMMENT_CLUSTER].insert_one(
        {"tag_comment_task_id": tag_comment_task_dict["tag_comment_task_id"]}
    )
    cloud_id = mongo_client.db[mongo_conf.COMMENT_CLOUD].insert_one(
        {"tag_comment_task_id": tag_comment_task_dict["tag_comment_task_id"]}
    )
    tendency_id = mongo_client.db[mongo_conf.COMMENT_TENDENCY].insert_one(
        {"tag_comment_task_id": tag_comment_task_dict["tag_comment_task_id"]}
    )
    key_node_id = mongo_client.db[mongo_conf.COMMENT_NODE].insert_one(
        {"tag_comment_task_id": tag_comment_task_dict["tag_comment_task_id"]}
    )

    tag_comment_task_dict["tree_id"] = str(tree_id.inserted_id)
    tag_comment_task_dict["cluster_id"] = str(cluster_id.inserted_id)
    tag_comment_task_dict["cloud_id"] = str(cloud_id.inserted_id)
    tag_comment_task_dict["tendency_id"] = str(tendency_id.inserted_id)
    tag_comment_task_dict["key_node_id"] = str(key_node_id.inserted_id)

    return tag_comment_task_dict


# 获取微博详细信息（使用PC端接口）
def get_post_detail(weibo_id: str, tag_comment_task_id: str):
    """
    优先使用PC端接口（statuses_show_pc），失败时回退到移动端接口
    PC端接口使用Playwright，只需要PC端Cookie，不需要移动端Cookie
    """
    # 尝试PC端接口
    try:
        print(f"[PC端] 尝试获取微博{weibo_id}详情...")
        session = requests.Session()
        session.trust_env = False
        response = session.get(
            weibo_conf.BASEPATH
            + "/weibo_curl/api/statuses_show_pc?weibo_id={weibo_id}".format(weibo_id=weibo_id),
            timeout=60,  # PC端需要渲染页面，超时时间加长
        )
        
        # 检查响应是否为空
        if not response.text or response.text.strip() == "":
            print(f"[PC端] 微博{weibo_id}返回空响应")
        else:
            try:
                weibo_dict = json.loads(response.text)
                # 检查是否返回错误
                if "error_code" in weibo_dict:
                    if weibo_dict["error_code"] == 0:
                        # 成功
                        if "data" in weibo_dict and "result" in weibo_dict["data"]:
                            print(
                                f"[PC端] 成功获取微博{weibo_id}，评论数: {len(weibo_dict['data']['result'].get('comments', []))}"
                            )
                            mongo_client.db[mongo_conf.COMMENT_TASK].update_one(
                                {"tag_comment_task_id": tag_comment_task_id},
                                {"$set": {"detail": weibo_dict["data"]["result"]}},
                            )
                            return weibo_dict["data"]["result"]
                    else:
                        print(
                            f"[PC端] 微博{weibo_id}爬取失败: {weibo_dict.get('error_msg', '未知错误')}"
                        )
                else:
                    print(f"[PC端] 微博{weibo_id}返回数据格式异常")
            except json.JSONDecodeError as je:
                print(f"[PC端] 微博{weibo_id}JSON解析失败: {je}")

    except requests.exceptions.Timeout:
        print(f"[PC端] 请求微博{weibo_id}超时，PC端渲染较慢")
    except requests.exceptions.RequestException as re:
        print(f"[PC端] 请求微博{weibo_id}网络错误: {re}")
    except Exception as e:
        print(f"[PC端] 获取微博{weibo_id}失败: {e}")

    # PC端失败，尝试移动端接口（保留兼容性）
    try:
        print(f"[移动端] 回退到移动端接口获取微博{weibo_id}...")
        session = requests.Session()
        session.trust_env = False
        response = session.get(
            weibo_conf.BASEPATH
            + "/weibo_curl/api/statuses_show?weibo_id={weibo_id}".format(weibo_id=weibo_id),
            timeout=30,
        )
        
        # 检查响应是否为空
        if not response.text or response.text.strip() == "":
            print(f"[移动端] 微博{weibo_id}返回空响应，可能Cookie已失效")
            return None
            
        try:
            weibo_dict = json.loads(response.text)
            # 检查是否返回错误
            if "error_code" in weibo_dict:
                if (
                    weibo_dict["error_code"] == 0
                    and "data" in weibo_dict
                    and "result" in weibo_dict["data"]
                ):
                    print(f"[移动端] 成功获取微博{weibo_id}")
                    mongo_client.db[mongo_conf.COMMENT_TASK].update_one(
                        {"tag_comment_task_id": tag_comment_task_id},
                        {"$set": {"detail": weibo_dict["data"]["result"]}},
                    )
                    return weibo_dict["data"]["result"]
                else:
                    print(
                        f"[移动端] 微博{weibo_id}爬取失败: {weibo_dict.get('error_msg', 'Cookie invalid')}"
                    )
                    return None
            else:
                print(f"[移动端] 微博{weibo_id}返回数据格式异常")
                return None
        except json.JSONDecodeError as je:
            print(f"[移动端] 微博{weibo_id}JSON解析失败: {je}")
            return None

    except requests.exceptions.Timeout:
        print(f"[移动端] 请求微博{weibo_id}超时")
        return None
    except requests.exceptions.RequestException as re:
        print(f"[移动端] 请求微博{weibo_id}网络错误: {re}")
        return None
    except Exception as e:
        print(f"[移动端] 获取微博{weibo_id}详情时发生异常: {e}")
        return None


# 聚类任务
def run_by_task_id_part(tag_comment_task_id, doc_id):
    post_list = []
    for post in mongo_client.db[mongo_conf.COMMENT_REPOSTS].find(
        {"tag_comment_task_id": tag_comment_task_id}
    ):
        if post["content"].strip() == "" or post["content"].strip() == "转发微博":
            continue
        post_list.append({"_id": post["_id"], "fulltext": post["content"]})

    # 检查是否有有效数据
    if not post_list:
        print(f"警告: 任务 {tag_comment_task_id} 没有有效的评论数据，跳过聚类")
        # 存储空结果
        mongo_client.db[mongo_conf.COMMENT_CLUSTER].update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"data": {}, "warning": "无有效评论数据"}},
        )
        return

    result = cluster_extract(post_list)

    # 检查聚类结果是否为None
    if result is None:
        print(
            f"警告: 任务 {tag_comment_task_id} 聚类失败，post_list长度: {len(post_list)}"
        )
        mongo_client.db[mongo_conf.COMMENT_CLUSTER].update_one(
            {"_id": ObjectId(doc_id)}, {"$set": {"data": {}, "warning": "聚类失败"}}
        )
        return

    mydict = result.to_dict(orient="index")
    key_list = list(mydict.keys())
    for key in key_list:
        mydict[str(key)] = mydict.pop(key)
        while "" in mydict[str(key)]["content"]:
            mydict[str(key)]["content"].remove("")
    mongo_client.db[mongo_conf.COMMENT_CLUSTER].update_one(
        {"_id": ObjectId(doc_id)}, {"$set": {"data": mydict}}
    )


# 调度任务
@celeryapp.task(bind=True)
def comment_task_schedule(self, tag_comment_task_dict):
    print(tag_comment_task_dict)
    # 爬虫任务
    print("开始爬虫任务")
    self.update_state(
        state="PROGRESS",
        meta={
            "current": "爬虫任务",
            "weibo_id": tag_comment_task_dict["weibo_id"],
            "task_id": tag_comment_task_dict["tag_comment_task_id"],
        },
    )

    # 获取微博详情（可能失败）
    detail_result = get_post_detail(
        weibo_id=tag_comment_task_dict["weibo_id"],
        tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"],
    )

    # 检查PC端是否成功获取了评论
    has_pc_comments = False
    if detail_result is not None and "comments" in detail_result:
        comments = detail_result.get("comments", [])
        if len(comments) > 0:
            print(f"[PC端] 发现 {len(comments)} 条评论，转换格式并保存到MongoDB...")
            # 将PC端评论转换为系统格式并保存（兼容移动端字段）
            comment_items = []
            import time

            for comment in comments:
                comment_item = {
                    "tag_comment_task_id": tag_comment_task_dict["tag_comment_task_id"],
                    "tag_task_id": tag_comment_task_dict["tag_task_id"],
                    "weibo_id": tag_comment_task_dict["weibo_id"],
                    "crawl_time": int(time.time()),
                    "page": 1,  # PC端统一标记为第1页
                    # 核心字段：content（必须！聚类和词云都用这个字段）
                    # 爬虫返回的字段是 "content"，不是 "text"
                    "content": (comment.get("content") or comment.get("text") or "").strip(),
                    "pre_content": (comment.get("content") or comment.get("text") or "").strip(),  # 原始内容
                    # 用户信息
                    "user_id": comment.get("user_id", ""),
                    "user_name": comment.get("screen_name") or comment.get("user_name", "Unknown"),
                    "user": comment.get("user", {}),
                    # 互动数据
                    "like_counts": comment.get("like_num") or comment.get("like_counts", 0),
                    "created_at": comment.get("publish_time") or comment.get("created_at", ""),
                    # 转发信息（PC端评论没有转发链，置空）
                    "repost": [],
                    # 标记数据来源
                    "source": "pc",  # PC端
                    "data_type": "comment",  # 评论（不是转发）
                }
                # 过滤空评论
                if comment_item["content"]:
                    comment_items.append(comment_item)

            # 保存到MongoDB
            if comment_items:
                try:
                    mongo_client.db[mongo_conf.COMMENT_REPOSTS].insert_many(
                        comment_items
                    )
                    print(f"[PC端] 成功保存 {len(comment_items)} 条评论到MongoDB")
                    has_pc_comments = True
                except Exception as e:
                    print(f"[PC端] 保存评论失败: {e}")
                    import traceback

                    traceback.print_exc()
            else:
                print(f"[PC端] 过滤后无有效评论")

    # 如果PC端没有获取到评论，尝试移动端爬取
    if not has_pc_comments:
        print(f"[移动端] PC端未获取到评论，尝试移动端爬取转发数据...")
        try:
            spider_list(
                tag_task_id=tag_comment_task_dict["tag_task_id"],
                weibo_id=tag_comment_task_dict["weibo_id"],
                tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"],
            )
        except Exception as e:
            print(f"[移动端] 移动端爬取失败: {e}")
            import traceback

            traceback.print_exc()
            # 不中断任务，继续后续流程
    else:
        if comment_items:
            print(f"[跳过] 已有PC端评论 {len(comment_items)} 条，跳过移动端转发爬取")
        else:
            print(f"[跳过] 已有PC端数据，跳过移动端转发爬取")

    print("爬虫任务结束")
    print("开始传播树构建任务")
    self.update_state(
        state="PROGRESS",
        meta={
            "current": "传播树构建任务",
            "weibo_id": tag_comment_task_dict["weibo_id"],
            "task_id": tag_comment_task_dict["tag_comment_task_id"],
        },
    )
    # 兼容旧任务 / 手动触发任务：缺少 tree_id 时跳过该子任务，而不是直接报错
    tree_id = tag_comment_task_dict.get("tree_id")
    if tree_id:
        get_path_tree_part(
            tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"],
            doc_id=tree_id,
        )
    else:
        print(
            f"[警告] 任务 {tag_comment_task_dict['tag_comment_task_id']} 缺少 tree_id，跳过传播树构建任务"
        )
    print("传播树构建任务结束")
    print("开始主题挖掘任务")
    self.update_state(
        state="PROGRESS",
        meta={
            "current": "传播分析-主题挖掘",
            "weibo_id": tag_comment_task_dict["weibo_id"],
            "task_id": tag_comment_task_dict["tag_comment_task_id"],
        },
    )
    run_by_task_id_part(
        tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"],
        doc_id=tag_comment_task_dict["cluster_id"],
    )
    print("主题挖掘任务结束")
    print("开始传播分析-词云任务")
    self.update_state(
        state="PROGRESS",
        meta={
            "current": "传播分析-词云",
            "weibo_id": tag_comment_task_dict["weibo_id"],
            "task_id": tag_comment_task_dict["tag_comment_task_id"],
        },
    )
    preContent(
        tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"],
        doc_id=tag_comment_task_dict["cloud_id"],
    )
    print("传播分析-词云任务结束")
    print("开始传播分析-趋势任务")
    self.update_state(
        state="PROGRESS",
        meta={
            "current": "传播分析-趋势",
            "weibo_id": tag_comment_task_dict["weibo_id"],
            "task_id": tag_comment_task_dict["tag_comment_task_id"],
        },
    )
    spreadTendency(
        tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"],
        doc_id=tag_comment_task_dict["tendency_id"],
    )
    print("传播分析-趋势任务结束")
    print("开始传播分析-关键节点任务")
    self.update_state(
        state="PROGRESS",
        meta={
            "current": "传播分析-关键节点",
            "weibo_id": tag_comment_task_dict["weibo_id"],
            "task_id": tag_comment_task_dict["tag_comment_task_id"],
        },
    )
    node(tag_comment_task_id=tag_comment_task_dict["tag_comment_task_id"])


# 初始化任务
def start_task(tag_task_id: str, weibo_post=None):
    # todo 错误处理
    # 时间戳->字符串
    time_int = int(time.time())
    time_array = time.localtime(time_int)
    time_style_str = time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    tag_comment_task_id = str(time_int) + weibo_post["weibo_id"]
    task_dict = {
        "tag_task_id": tag_task_id,
        "weibo_id": weibo_post["weibo_id"],
        "tag_comment_task_id": tag_comment_task_id,
        "created_time": time_style_str,
    }

    task_dict = init_task(task_dict)

    task = comment_task_schedule.delay(tag_comment_task_dict=task_dict)
    task_dict["celery_id"] = task.id
    # weibo_detail = get_post_detail(weibo_id=weibo_id)
    task_dict["detail"] = weibo_post
    task_dict["analysis_status"] = "PENDING"
    mongo_client.db[mongo_conf.COMMENT_TASK].insert_one(task_dict)
    task_dict.pop("_id")
    print(task_dict)
    return task_dict


# 刷新任务
def refresh_task():
    mydb = mongo_client.db[mongo_conf.COMMENT_TASK]
    for item in mydb.find():
        try:
            if item["analysis_status"] != "SUCCESS":
                celery_id = item.get("celery_id")
                if not celery_id:
                    continue
                    
                task = celeryapp.AsyncResult(celery_id)
                # 直接使用 task.state 作为状态，不要使用 task.info.get("current")
                # task.state 可能是: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY, REVOKED
                new_status = task.state
                
                # 如果任务状态是 PENDING 且 info 为 None，可能是任务已过期或从未被执行
                # 检查任务创建时间，如果超过1小时，标记为 EXPIRED
                if new_status == "PENDING" and task.info is None:
                    import time
                    created_time_str = item.get("created_time", "")
                    if created_time_str:
                        try:
                            from datetime import datetime
                            created_time = datetime.strptime(created_time_str, "%Y-%m-%d %H:%M:%S")
                            time_diff = time.time() - created_time.timestamp()
                            # 如果任务创建时间超过1小时，标记为 EXPIRED
                            if time_diff > 3600:
                                new_status = "EXPIRED"
                        except:
                            pass
                
                if new_status != item.get("analysis_status"):
                    mydb.update_one(
                        {"_id": item["_id"]}, {"$set": {"analysis_status": new_status}}
                    )
        except Exception as e:
            print(item.get("tag_comment_task_id", "Unknown"), "刷新任务失败:", e)


# 获取任务队列
def getTaskList():
    result = {"error_code": 0, "error_msg": "", "data": []}
    # 获取task库,更新task状态
    mydb = mongo_client.db[mongo_conf.COMMENT_TASK]
    for item in mydb.find():
        try:
            if item["analysis_status"] != "SUCCESS":
                task = celeryapp.AsyncResult(item["celery_id"])
                # 直接使用 task.state 作为状态
                new_status = task.state
                if new_status != item.get("analysis_status"):
                    item["analysis_status"] = new_status
                    mydb.update_one(
                        {"_id": item["_id"]}, {"$set": {"analysis_status": new_status}}
                    )
            item.pop("_id")
            result["data"].append(item)
        except Exception as e:
            print("getTaskList error:", e)
            print(item)
    return result


# 删除任务
def deleteTask(tag_comment_task_id):
    mydb = mongo_client.db[mongo_conf.COMMENT_TASK]
    celeryapp.control.revoke(tag_comment_task_id, terminate=True)
    myquery = {"tag_comment_task_id": tag_comment_task_id}
    mydb.delete_one(myquery)
    mongo_client.db[mongo_conf.COMMENT_TREE].delete_one(myquery)
    mongo_client.db[mongo_conf.COMMENT_CLUSTER].delete_one(myquery)


# 统计每天的转发
def spreadTendency(tag_comment_task_id=None, doc_id=None):
    # if task_id is None or task_id.__len__() == 0:
    #     return {"error_code": 1, "error_msg": "缺少task_id"}
    pipeline = [
        {
            "$project": {
                "day": {"$substr": ["$created_at", 0, 10]},
                "tag_comment_task_id": "$tag_comment_task_id",
            }
        },
        {
            "$group": {
                "_id": {"data": "$day", "tag_comment_task_id": "$tag_comment_task_id"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.data": 1}},
        {"$match": {"_id.tag_comment_task_id": tag_comment_task_id}},
    ]
    result = []
    mydb = mongo_client.db[mongo_conf.COMMENT_REPOSTS]
    for i in mydb.aggregate(pipeline):
        print("reports:", i)
        result.append({"key": i["_id"]["data"], "doc_count": i["count"]})
    mongo_client.db[mongo_conf.COMMENT_TENDENCY].update_one(
        {"tag_comment_task_id": tag_comment_task_id}, {"$set": {"data": result}}
    )


# 以task_id获取 趋势 内容
def getByTendencyId(tag_comment_task_id=None):
    item = mongo_client.db[mongo_conf.COMMENT_TENDENCY].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    item.pop("_id")
    data_time = []
    data_count = []
    for i in item["data"]:
        data_time.append(i["key"])
        data_count.append(i["doc_count"])
    data = {"data_time": data_time, "data_count": data_count}
    item["data"] = data
    print(item)
    return item


# 以task_id获取 词云 内容
def getByCloudId(tag_comment_task_id=None):
    # item = mydb['cloud'].find_one({"_id": ObjectId(doc_id)})
    item = mongo_client.db[mongo_conf.COMMENT_CLOUD].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    item.pop("_id")
    print(item)
    return item


# 以task_id 获取 聚类 内容
def getByClusterId(tag_comment_task_id=None):
    # item = mydb['cluster'].find_one({"tag_comment_task_id": ObjectId(doc_id)})
    item = mongo_client.db[mongo_conf.COMMENT_CLOUD].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    item.pop("_id")
    print(item)
    return item


# 以task_id 获取 聚类 类别
def getTypeByClusterId(tag_comment_task_id=None):
    item = mongo_client.db[mongo_conf.COMMENT_CLUSTER].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    item.pop("_id")
    result = []
    for i in item["data"]:
        key_count = {
            "key": item["data"][i]["key"],
            "doc_count": len(item["data"][i]["id"]),
        }
        result.append(key_count)
    return result


# 以task_id和类别 获取 某一类聚类内容
def getContentByClusterId(tag_comment_task_id=None, content_type=None):
    item = mongo_client.db[mongo_conf.COMMENT_CLUSTER].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    item.pop("_id")
    result = []
    for i in item["data"]:
        if item["data"][i]["key"] == content_type:
            result = item["data"][i]["content"]
    result_sort = []

    for content in result:
        content_sort = {"text": content, "score": len(set(content)) / 8}
        for key in content_type.split(" "):
            if key in content:
                content_sort["score"] += 1
        result_sort.append(content_sort)
    result_sort.sort(key=lambda i: i["score"], reverse=True)
    return result_sort[0:10]


# 以task_id和类别 获取 某一类聚类内容
def getPostById(tag_comment_task_id=None):
    item = mongo_client.db[mongo_conf.COMMENT_TASK].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    result = []
    result.append(item["detail"])
    return result


# 统计关键节点
def statisticsRepost(item, total):
    children_list = [i for i in item["children"].values()]
    total[item["user_name"].strip()] = len(children_list)
    for i in children_list:
        total[item["user_name"].strip()] = total[
            item["user_name"].strip()
        ] + statisticsRepost(i, total)
    return total[item["user_name"].strip()]


# 获取获取关键节点
def getKeyNode(tag_comment_task_id):
    item = mongo_client.db[mongo_conf.COMMENT_NODE].find_one(
        {"tag_comment_task_id": tag_comment_task_id}
    )
    return item["data"]


# 转换tree数据结构-->leader rank 数据结构
def editJson4Graph(item, nodes, edges):
    nodes.add(item["user_name"].strip())
    if item["children"]:
        edges[item["user_name"].strip()] = {}
        children_list = [i for i in item["children"].values()]

        for i in children_list:
            editJson4Graph(i, nodes, edges)
            i.pop("children")
            edges[item["user_name"].strip()][i["user_name"].strip()] = i


# leader rank计算
def node(tag_comment_task_id):
    try:
        nodes = set()
        edges = {}
        re_edges = {}
        data = mongo_client.db[mongo_conf.COMMENT_TREE].find_one(
            {"tag_comment_task_id": tag_comment_task_id}
        )
        if data:
            total = {}
            statisticsRepost(data["data"], total)

            editJson4Graph(data["data"], nodes, edges)
            # 去除G节点和根节点
            result_sorted = startRank(edges, re_edges, list(nodes))[2:]
            result_list = []
            for item in result_sorted:
                try:
                    if total[item[0]] != 0:
                        result = {
                            "name": item[0],
                            "count": total[item[0]],
                            "score": item[1],
                        }
                        result_list.append(result)
                except:
                    # todo
                    pass

            # 获取热点转发内容 - 从 comment_reposts 集合中获取热门评论
            hot_comments = []
            reposts_cursor = mongo_client.db[mongo_conf.COMMENT_REPOSTS].find(
                {"tag_comment_task_id": tag_comment_task_id}
            ).sort("like_counts", -1).limit(10)

            for repost in reposts_cursor:
                content = repost.get("content", "") or repost.get("pre_content", "")
                if content and content.strip() and content.strip() != "转发微博":
                    hot_comments.append({
                        "content": content,
                        "user_name": repost.get("user_name", ""),
                        "user_id": repost.get("user_id", ""),
                        "like_counts": repost.get("like_counts", 0)
                    })

            mongo_client.db[mongo_conf.COMMENT_NODE].update_one(
                {"tag_comment_task_id": tag_comment_task_id},
                {"$set": {"data": result_list, "comments": hot_comments}},
            )
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # mydb['tendency'].insert_one(spreadTendency("1621162456K7okwxcKa"))
    # refresh_task()
    # print(getTaskList())
    # print(node("1622465660KhQes4VMs"))
    run_by_task_id_part("1635758101KDOBs1AO2", "617fb015de0c993aa08e78f0")
