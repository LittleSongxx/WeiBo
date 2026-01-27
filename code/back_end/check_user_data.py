#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细检查用户标签数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from celery_task.utils import mongo_client
from celery_task.config import mongo_conf

tag_task_id = "57df593f1cf3c2256eab26553e6ccabd"

print("="*60)
print("详细检查用户标签数据")
print("="*60)

# 1. 检查tag_user集合
print("\n1. 检查tag_user集合:")
user_doc = mongo_client.db[mongo_conf.USER].find_one({"tag_task_id": tag_task_id})
if user_doc:
    print(f"   ✓ 找到文档")
    print(f"   字段: {list(user_doc.keys())}")
    print(f"   data字段存在: {'data' in user_doc}")
    if 'data' in user_doc:
        data = user_doc['data']
        print(f"   data类型: {type(data)}")
        if isinstance(data, list):
            print(f"   data长度: {len(data)}")
            if len(data) > 0:
                print(f"   示例: {data[0]}")
        else:
            print(f"   data内容: {data}")
    print(f"   categories字段: {user_doc.get('categories', 'N/A')}")
else:
    print("   ❌ 没有找到文档")

# 2. 检查博文数据中的user_id
print("\n2. 检查博文数据中的user_id:")
blog = mongo_client.db[mongo_conf.BLOG].find_one({"tag_task_id": tag_task_id})
if blog:
    blog_data = blog.get('data', [])
    if isinstance(blog_data, list) and len(blog_data) > 0:
        user_ids = set()
        for item in blog_data[:10]:  # 只检查前10条
            if 'user_id' in item:
                user_ids.add(item['user_id'])
        print(f"   前10条博文中的user_id数量: {len(user_ids)}")
        print(f"   示例user_id: {list(user_ids)[:5]}")

# 3. 检查关系图数据中的节点（包含user_id）
print("\n3. 检查关系图数据中的节点:")
relation = mongo_client.db[mongo_conf.RELATION].find_one({"tag_task_id": tag_task_id})
if relation:
    nodes_list = relation.get('nodes_list', [])
    if isinstance(nodes_list, list):
        print(f"   节点数量: {len(nodes_list)}")
        # 统计有user_id的节点
        nodes_with_user_id = [n for n in nodes_list if n.get('userId')]
        print(f"   有userId的节点数量: {len(nodes_with_user_id)}")
        if nodes_with_user_id:
            print(f"   示例节点: {nodes_with_user_id[0]}")

# 4. 检查at_users字段
print("\n4. 检查博文数据中的at_users字段:")
if blog:
    blog_data = blog.get('data', [])
    if isinstance(blog_data, list):
        has_at_users = 0
        total_at_users = 0
        for item in blog_data[:50]:  # 检查前50条
            at_users = item.get('at_users', [])
            if at_users:
                has_at_users += 1
                total_at_users += len(at_users) if isinstance(at_users, list) else 1
        print(f"   前50条博文中有at_users的: {has_at_users}")
        print(f"   总at_users数量: {total_at_users}")

print("\n" + "="*60)
