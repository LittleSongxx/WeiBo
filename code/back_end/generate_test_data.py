#!/usr/bin/env python3
"""
生成测试数据脚本
用于验证前端数据展示功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import random
import hashlib
import time

# 连接MongoDB
client = MongoClient('mongodb://127.0.0.1:27017')
db = client['public_opinion_analysis_system']

# 生成唯一的tag_task_id
def generate_tag_task_id(tag):
    timestamp = str(int(time.time() * 1000))
    md5_hash = hashlib.md5(tag.encode()).hexdigest()
    return timestamp + md5_hash[:16]

# 测试话题
TEST_TAG = "测试话题"
TAG_TASK_ID = generate_tag_task_id(TEST_TAG)

print(f"=== 生成测试数据 ===")
print(f"话题: {TEST_TAG}")
print(f"tag_task_id: {TAG_TASK_ID}")

# 1. 生成 tag_task (话题任务管理)
tag_task_data = {
    "tag_task_id": TAG_TASK_ID,
    "tag": TEST_TAG,
    "tag_celery_task_id": f"celery-{TAG_TASK_ID[:16]}",
    "tag_introduce_id": str(ObjectId()),
    "tag_hot_id": str(ObjectId()),
    "tag_word_cloud_id": str(ObjectId()),
    "tag_user_id": str(ObjectId()),
    "tag_relation_id": str(ObjectId()),
    "tag_evolve_id": str(ObjectId()),
    "tag_weibo_task_id": str(ObjectId()),
    "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "SUCCESS",
    "analysis_status": "SUCCESS"
}

# 删除旧的测试数据
db.tag_task.delete_many({"tag": TEST_TAG})
db.tag_task.insert_one(tag_task_data)
print(f"✓ 创建 tag_task")

# 2. 生成 tag_introduce (话题基本信息)
tag_introduce_data = {
    "tag_task_id": TAG_TASK_ID,
    "tag": TEST_TAG,
    "user_count": 156,
    "weibo_count": 328,
    "vital_user": {
        "user_id": "1234567890",
        "head": "https://tvax1.sinaimg.cn/crop.0.0.996.996.180/006Fd7ably8gp0yp0r0xyj30ro0ro0ue.jpg",
        "nickname": "测试大V用户",
        "gender": "男",
        "location": "北京",
        "birthday": "1990-01-01",
        "description": "这是一个测试用户的简介",
        "verified_reason": "知名博主",
        "education": "清华大学",
        "work": "某科技公司",
        "weibo_num": 5000,
        "following": 500,
        "followers": 1000000,
        "max_page": 100
    }
}
db.tag_introduce.delete_many({"tag_task_id": TAG_TASK_ID})
db.tag_introduce.insert_one(tag_introduce_data)
print(f"✓ 创建 tag_introduce")

# 3. 生成 tag_hot (话题热度)
# 前端期望格式: {"data_time": [...], "data_count": [...]}
def generate_hot_data_hours(hours):
    """生成小时级热度数据（一天内）"""
    data_time = []
    data_count = []
    base_date = datetime.now()
    for i in range(hours):
        date = base_date - timedelta(hours=hours-i-1)
        # 生成波动的热度值
        base_value = 500 + i * 10
        value = base_value + random.randint(-100, 200)
        # 前端期望格式包含T分隔符，如 "2026-01-25T14:00"
        data_time.append(date.strftime("%Y-%m-%dT%H:00"))
        data_count.append(max(0, value))
    return {"data_time": data_time, "data_count": data_count}

def generate_hot_data_days(days):
    """生成天级热度数据（一个月/三个月）"""
    data_time = []
    data_count = []
    base_date = datetime.now()
    for i in range(days):
        date = base_date - timedelta(days=days-i-1)
        # 生成波动的热度值
        base_value = 500 + i * 20
        value = base_value + random.randint(-100, 200)
        # 前端期望格式包含T分隔符
        data_time.append(date.strftime("%Y-%m-%dT00:00"))
        data_count.append(max(0, value))
    return {"data_time": data_time, "data_count": data_count}

tag_hot_data = {
    "tag_task_id": TAG_TASK_ID,
    "tag": TEST_TAG,
    "one_day": generate_hot_data_hours(24),  # 24小时数据
    "one_month": generate_hot_data_days(30),  # 30天数据
    "three_month": generate_hot_data_days(90)  # 90天数据
}
db.tag_hot.delete_many({"tag_task_id": TAG_TASK_ID})
db.tag_hot.insert_one(tag_hot_data)
print(f"✓ 创建 tag_hot (热度数据)")

# 4. 生成 tag_word_cloud (词云)
# 前端 echarts wordCloud 期望格式: [{"name": "关键字", "value": 出现次数}]
word_cloud_words = [
    ("测试", 150), ("数据", 120), ("分析", 100), ("系统", 95),
    ("功能", 85), ("展示", 80), ("验证", 75), ("前端", 70),
    ("后端", 65), ("数据库", 60), ("接口", 55), ("用户", 50),
    ("话题", 48), ("热度", 45), ("词云", 42), ("关系图", 40),
    ("传播", 38), ("趋势", 35), ("聚类", 32), ("主题", 30),
    ("评论", 28), ("转发", 25), ("点赞", 22), ("微博", 20),
    ("社交", 18), ("网络", 16), ("媒体", 14), ("信息", 12)
]

tag_word_cloud_data = {
    "tag_task_id": TAG_TASK_ID,
    "data": [{"name": word, "value": count} for word, count in word_cloud_words]
}
db.tag_word_cloud.delete_many({"tag_task_id": TAG_TASK_ID})
db.tag_word_cloud.insert_one(tag_word_cloud_data)
print(f"✓ 创建 tag_word_cloud (词云)")

# 5. 生成 tag_relation_graph (关系图)
users = [
    ("测试大V", 3, 100),
    ("普通用户A", 2, 30),
    ("普通用户B", 2, 25),
    ("普通用户C", 2, 20),
    ("活跃用户D", 2, 45),
    ("活跃用户E", 2, 40),
    ("新用户F", 2, 10),
    ("新用户G", 2, 8),
    ("意见领袖H", 3, 80),
    ("水军账号I", 1, 5),
]

nodes_list = [
    {"category": cat, "name": name, "value": val}
    for name, cat, val in users
]

links_list = [
    {"source": "测试大V", "target": "普通用户A", "weight": 5},
    {"source": "测试大V", "target": "普通用户B", "weight": 3},
    {"source": "测试大V", "target": "活跃用户D", "weight": 8},
    {"source": "意见领袖H", "target": "普通用户C", "weight": 4},
    {"source": "意见领袖H", "target": "活跃用户E", "weight": 6},
    {"source": "活跃用户D", "target": "新用户F", "weight": 2},
    {"source": "活跃用户E", "target": "新用户G", "weight": 2},
    {"source": "普通用户A", "target": "水军账号I", "weight": 1},
]

tag_relation_data = {
    "tag_task_id": TAG_TASK_ID,
    "nodes_list": nodes_list,
    "links_list": links_list
}
db.tag_relation_graph.delete_many({"tag_task_id": TAG_TASK_ID})
db.tag_relation_graph.insert_one(tag_relation_data)
print(f"✓ 创建 tag_relation_graph (关系图)")

# 6. 生成 tag_user (用户分析)
user_categories = ["推手", "水军", "普通用户", "意见领袖"]
user_list = []
for i in range(20):
    user_list.append({
        "user_id": str(1000000000 + i),
        "nickname": f"测试用户{i+1}",
        "gender": random.choice(["男", "女"]),
        "location": random.choice(["北京", "上海", "广州", "深圳", "杭州"]),
        "followers": random.randint(100, 100000),
        "following": random.randint(50, 500),
        "weibo_num": random.randint(10, 1000),
        "category": random.randint(0, 3),
        "category_name": user_categories[random.randint(0, 3)]
    })

tag_user_data = {
    "tag_task_id": TAG_TASK_ID,
    "data": user_list,
    "categories": 4
}
db.tag_user.delete_many({"tag_task_id": TAG_TASK_ID})
db.tag_user.insert_one(tag_user_data)
print(f"✓ 创建 tag_user (用户分析)")

# 7. 生成 blog (博文数据)
blog_list = []
for i in range(15):
    weibo_id = str(5000000000000000 + i)
    hot_count = random.randint(100, 1000)
    blog_list.append({
        "head": f"https://tvax1.sinaimg.cn/default/images/default_avatar_male_180.gif",
        "weibo_id": weibo_id,
        "user_id": str(1000000000 + i % 10),
        "screen_name": f"测试用户{i % 10 + 1}",
        "text": f"这是第{i+1}条测试微博内容，用于验证博文热度前十的展示功能。#{TEST_TAG}#",
        "article_url": "",
        "location": random.choice(["北京", "上海", "广州", ""]),
        "at_users": [],
        "topics": TEST_TAG,
        "created_at": (datetime.now() - timedelta(hours=i*2)).strftime("%Y-%m-%d %H:%M"),
        "source": random.choice(["iPhone客户端", "Android客户端", "微博网页版"]),
        "pics": [],
        "video_url": "",
        "retweet_id": "",
        "tid": weibo_id,
        "text_token": f"测试 微博 内容 验证 博文 热度 展示 功能",
        "retweet_count": str(random.randint(0, 100)),
        "favorite_count": str(random.randint(0, 500)),
        "comment_count": str(random.randint(10, 300)),
        "tweet_type": "article",
        "data_source": "weibo",
        "hot_count": hot_count,
        "create_time": int(time.time() * 1000) - i * 3600000
    })

# 按热度排序
blog_list.sort(key=lambda x: x["hot_count"], reverse=True)

blog_data = {
    "tag_task_id": TAG_TASK_ID,
    "tag": TEST_TAG,
    "data": blog_list
}
db.blog.delete_many({"tag_task_id": TAG_TASK_ID})
db.blog.insert_one(blog_data)
print(f"✓ 创建 blog (博文数据，共{len(blog_list)}条)")

# 8. 生成博文详情相关数据 - 使用正确的数据格式
def generate_tree_node(user_name, content, user_id, depth=0, max_depth=3):
    """生成树节点，使用正确的格式"""
    children = {}
    if depth < max_depth:
        num_children = random.randint(0, 3) if depth < 2 else random.randint(0, 1)
        for j in range(num_children):
            child_id = f"{user_id}_{j}"
            child_name = f"回复用户{depth}_{j}"
            children[child_id] = generate_tree_node(
                child_name, 
                f"这是{child_name}的回复内容", 
                child_id, 
                depth + 1, 
                max_depth
            )
    return {
        "user_name": user_name,
        "content": content,
        "user_id": user_id,
        "children": children
    }

for i, blog in enumerate(blog_list[:10]):  # 为前10条创建详细任务
    weibo_task_id = f"{int(time.time()*1000)}{blog['weibo_id']}"

    # 创建博文详情数据 - 前端期望的字段格式
    # blog_info.vue 期望: user_head, user_name, created_at, weibo_content, topics, original_pics
    detail_data = {
        "user_head": blog["head"],
        "user_name": blog["screen_name"],
        "created_at": blog["created_at"],
        "weibo_content": blog["text"],
        "topics": [TEST_TAG],  # 话题列表
        "original_pics": [blog["head"]],  # 图片列表
        "weibo_id": blog["weibo_id"],
        "user_id": blog["user_id"],
        "retweet_count": blog["retweet_count"],
        "favorite_count": blog["favorite_count"],
        "comment_count": blog["comment_count"],
    }

    # 创建评论任务数据
    comment_task_data = {
        "tag_task_id": TAG_TASK_ID,
        "weibo_id": blog["weibo_id"],
        "tag_comment_task_id": weibo_task_id,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tree_id": str(ObjectId()),
        "cluster_id": str(ObjectId()),
        "cloud_id": str(ObjectId()),
        "tendency_id": str(ObjectId()),
        "key_node_id": str(ObjectId()),
        "celery_id": f"celery-{weibo_task_id[:16]}",
        "detail": detail_data,
        "analysis_status": "SUCCESS"
    }
    db.comment_task.delete_many({"weibo_id": blog["weibo_id"]})
    db.comment_task.insert_one(comment_task_data)
    
    # 创建评论树数据 - 使用正确的格式
    tree_data = generate_tree_node(
        blog["screen_name"],
        blog["text"],
        blog["user_id"]
    )
    # 添加更多子节点
    for j in range(random.randint(3, 8)):
        child_id = f"comment_{j}"
        tree_data["children"][child_id] = generate_tree_node(
            f"评论用户{j+1}",
            f"这是评论用户{j+1}的评论内容，很有见地！",
            child_id,
            1,
            3
        )
    
    comment_tree_data = {
        "tag_comment_task_id": weibo_task_id,
        "data": tree_data
    }
    db.comment_tree.delete_many({"tag_comment_task_id": weibo_task_id})
    db.comment_tree.insert_one(comment_tree_data)
    
    # 创建评论词云数据 - 使用正确的格式
    # echarts wordCloud 期望 name 和 value 字段
    cloud_words = ["好评", "支持", "赞同", "不错", "厉害", "学习", "感谢", "分享", "精彩", "有道理"]
    comment_cloud_data = {
        "tag_comment_task_id": weibo_task_id,
        "data": [
            {"name": word, "value": random.randint(5, 50)}
            for word in cloud_words
        ]
    }
    db.comment_cloud.delete_many({"tag_comment_task_id": weibo_task_id})
    db.comment_cloud.insert_one(comment_cloud_data)
    
    # 创建评论聚类数据 - 使用正确的格式 (字典格式)
    cluster_data = {}
    cluster_names = ["正面评价", "中性讨论", "负面评价", "疑问咨询"]
    for idx, name in enumerate(cluster_names):
        cluster_data[str(idx)] = {
            "key": name,
            "id": [f"comment_{k}" for k in range(random.randint(5, 20))]
        }
    
    comment_cluster_data = {
        "tag_comment_task_id": weibo_task_id,
        "data": cluster_data
    }
    db.comment_cluster.delete_many({"tag_comment_task_id": weibo_task_id})
    db.comment_cluster.insert_one(comment_cluster_data)
    
    # 创建评论趋势数据 - 使用正确的格式 (key, doc_count)
    tendency_data = []
    for h in range(24, 0, -1):
        tendency_data.append({
            "key": (datetime.now() - timedelta(hours=h)).strftime("%Y-%m-%d %H:00"),
            "doc_count": random.randint(5, 30)
        })
    
    comment_tendency_data = {
        "tag_comment_task_id": weibo_task_id,
        "data": tendency_data
    }
    db.comment_tendency.delete_many({"tag_comment_task_id": weibo_task_id})
    db.comment_tendency.insert_one(comment_tendency_data)
    
    # 创建关键节点数据
    # essential_node.vue 期望 res.data.data，每项有 name 字段
    # hot_point.vue 期望 res.data.comments，每项有 content 字段
    # 后端 getKeyNode 返回 item["data"]，所以需要在 comment_node 中存储正确格式
    key_nodes = []
    hot_comments = []
    for k in range(random.randint(3, 6)):
        key_nodes.append({
            "name": f"关键用户{k+1}",
            "user_id": f"key_user_{k}",
            "user_name": f"关键用户{k+1}",
            "influence": random.randint(50, 200),
            "comment_count": random.randint(10, 50)
        })
        hot_comments.append({
            "content": f"这是关键用户{k+1}的热门评论内容，非常有见地！",
            "user_name": f"关键用户{k+1}",
            "user_id": f"key_user_{k}",
        })

    comment_node_data = {
        "tag_comment_task_id": weibo_task_id,
        "data": key_nodes,
        "comments": hot_comments
    }
    db.comment_node.delete_many({"tag_comment_task_id": weibo_task_id})
    db.comment_node.insert_one(comment_node_data)
    
    # 创建转发数据 - 每条转发是独立的文档，包含 tag_comment_task_id 和 created_at 字段
    # 这是 spreadTendency 函数期望的格式
    db.comment_reposts.delete_many({"tag_comment_task_id": weibo_task_id})
    reposts_docs = []
    for r in range(random.randint(20, 50)):
        # 生成不同日期的转发，以便趋势图有多个数据点
        hours_ago = random.randint(1, 72)
        created_time = datetime.now() - timedelta(hours=hours_ago)
        reposts_docs.append({
            "tag_comment_task_id": weibo_task_id,
            "tag_task_id": TAG_TASK_ID,
            "weibo_id": blog["weibo_id"],
            "user_id": f"repost_user_{r}",
            "user_name": f"转发用户{r+1}",
            "content": f"转发理由{r+1}：这条微博很有意思！值得关注。",
            "pre_content": f"转发理由{r+1}：这条微博很有意思！值得关注。",
            "created_at": created_time.strftime("%Y-%m-%d %H:%M"),
            "like_counts": random.randint(0, 100),
            "source": "test",
            "data_type": "repost"
        })
    if reposts_docs:
        db.comment_reposts.insert_many(reposts_docs)

print(f"✓ 创建 comment_task, comment_tree, comment_cloud, comment_cluster, comment_tendency, comment_node, comment_reposts (博文详情数据)")

# 9. 生成 tag_evolve (话题演变)
tag_evolve_data = {
    "tag_task_id": TAG_TASK_ID,
    "time_list": [
        {
            "time": (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d"),
            "cluster_list": [
                {
                    "cluster_name": f"主题{c+1}",
                    "weibo_list": [
                        {"weibo_id": str(5000000000000000 + d*10 + c), "content": f"第{d+1}天主题{c+1}的微博内容"}
                        for _ in range(random.randint(2, 5))
                    ]
                }
                for c in range(random.randint(2, 4))
            ]
        }
        for d in range(7)
    ]
}
db.tag_evolve.delete_many({"tag_task_id": TAG_TASK_ID})
db.tag_evolve.insert_one(tag_evolve_data)
print(f"✓ 创建 tag_evolve (话题演变)")

print(f"\n=== 测试数据生成完成 ===")
print(f"话题名称: {TEST_TAG}")
print(f"tag_task_id: {TAG_TASK_ID}")
print(f"\n请在前端搜索 '{TEST_TAG}' 来测试数据展示功能")
print(f"或者直接访问已有的话题任务列表查看")

# 列出所有集合的数据量
print(f"\n=== 数据库集合统计 ===")
for coll_name in db.list_collection_names():
    count = db[coll_name].count_documents({})
    print(f"  {coll_name}: {count} 条记录")
