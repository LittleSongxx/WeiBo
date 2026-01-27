#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本：检查数据库中的数据完整性
用于排查前端数据显示不完整的问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from celery_task.utils import mongo_client
from celery_task.config import mongo_conf

def check_task_data(tag_task_id):
    """检查指定任务的数据完整性"""
    print(f"\n{'='*60}")
    print(f"检查任务ID: {tag_task_id}")
    print(f"{'='*60}\n")
    
    # 1. 检查任务基本信息
    print("1. 任务基本信息:")
    task = mongo_client.db[mongo_conf.TASK].find_one({"tag_task_id": tag_task_id})
    if task:
        print(f"   任务状态: {task.get('status', 'N/A')}")
        print(f"   话题名称: {task.get('tag', 'N/A')}")
        print(f"   Celery任务ID: {task.get('tag_celery_task_id', 'N/A')}")
    else:
        print("   ❌ 任务不存在")
        return
    
    # 2. 检查话题基本信息
    print("\n2. 话题基本信息:")
    introduce = mongo_client.db[mongo_conf.INTRODUCE].find_one({"tag_task_id": tag_task_id})
    if introduce:
        print(f"   ✓ 话题: {introduce.get('tag', 'N/A')}")
        print(f"   用户数量: {introduce.get('user_count', 0)}")
        print(f"   博文数量: {introduce.get('weibo_count', 0)}")
        print(f"   重要用户: {'✓' if introduce.get('vital_user') else '✗'}")
    else:
        print("   ❌ 话题基本信息不存在")
    
    # 3. 检查博文数据
    print("\n3. 博文数据:")
    blog = mongo_client.db[mongo_conf.BLOG].find_one({"tag_task_id": tag_task_id})
    if blog:
        blog_data = blog.get('data', [])
        print(f"   ✓ 博文数据存在，数量: {len(blog_data) if isinstance(blog_data, list) else 0}")
    else:
        print("   ❌ 博文数据不存在")
    
    # 4. 检查热度数据
    print("\n4. 话题热度数据:")
    hot = mongo_client.db[mongo_conf.HOT].find_one({"tag_task_id": tag_task_id})
    if hot:
        has_one_day = bool(hot.get('one_day'))
        has_one_month = bool(hot.get('one_month'))
        has_three_month = bool(hot.get('three_month'))
        print(f"   一天数据: {'✓' if has_one_day else '✗'}")
        print(f"   一个月数据: {'✓' if has_one_month else '✗'}")
        print(f"   三个月数据: {'✓' if has_three_month else '✗'}")
        if hot.get('error'):
            print(f"   ⚠️  错误信息: {hot.get('error')}")
    else:
        print("   ❌ 热度数据不存在")
    
    # 5. 检查词云数据
    print("\n5. 词云数据:")
    word_cloud = mongo_client.db[mongo_conf.CLOUD].find_one({"tag_task_id": tag_task_id})
    if word_cloud:
        cloud_data = word_cloud.get('data', [])
        if isinstance(cloud_data, list):
            print(f"   ✓ 词云数据存在，关键词数量: {len(cloud_data)}")
            if len(cloud_data) > 0:
                print(f"   示例: {cloud_data[0] if cloud_data else 'N/A'}")
        elif isinstance(cloud_data, dict):
            print(f"   ⚠️  词云数据格式为字典（应为列表），关键词数量: {len(cloud_data)}")
        else:
            print(f"   ⚠️  词云数据格式异常: {type(cloud_data)}")
    else:
        print("   ❌ 词云数据不存在")
    
    # 6. 检查关系图数据
    print("\n6. 关系图数据:")
    relation = mongo_client.db[mongo_conf.RELATION].find_one({"tag_task_id": tag_task_id})
    if relation:
        nodes_list = relation.get('nodes_list', [])
        links_list = relation.get('links_list', [])
        print(f"   节点数量: {len(nodes_list) if isinstance(nodes_list, list) else 0}")
        print(f"   链接数量: {len(links_list) if isinstance(links_list, list) else 0}")
        if nodes_list and links_list:
            print("   ✓ 关系图数据完整")
        else:
            print("   ⚠️  关系图数据不完整")
    else:
        print("   ❌ 关系图数据不存在")
    
    # 7. 检查用户标签数据
    print("\n7. 用户标签数据:")
    user_mark = mongo_client.db[mongo_conf.USER].find_one({"tag_task_id": tag_task_id})
    if user_mark:
        user_data = user_mark.get('data', [])
        print(f"   ✓ 用户标签数据存在，用户数量: {len(user_data) if isinstance(user_data, list) else 0}")
    else:
        print("   ❌ 用户标签数据不存在")
    
    print(f"\n{'='*60}\n")

def list_all_tasks():
    """列出所有任务"""
    print("\n所有任务列表:")
    tasks = list(mongo_client.db[mongo_conf.TASK].find({}, {"tag_task_id": 1, "tag": 1, "status": 1}))
    if tasks:
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task.get('tag', 'N/A')} - {task.get('tag_task_id', 'N/A')} - {task.get('status', 'N/A')}")
        return [task.get('tag_task_id') for task in tasks]
    else:
        print("   没有找到任何任务")
        return []

if __name__ == "__main__":
    print("="*60)
    print("数据完整性检查工具")
    print("="*60)
    
    # 列出所有任务
    task_ids = list_all_tasks()
    
    if task_ids:
        print(f"\n找到 {len(task_ids)} 个任务")
        # 检查第一个任务
        if task_ids:
            check_task_data(task_ids[0])
            print("\n提示: 可以修改脚本检查其他任务ID")
    else:
        print("\n提示: 没有找到任务，请先创建分析任务")
