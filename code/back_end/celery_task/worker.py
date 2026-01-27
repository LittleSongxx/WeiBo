"""
:
@author: lingzhi
* @date 2021/8/7 9:48
"""
import time

from celery_task import celeryapp
from celery_task.tag_task.tag_spider_task import spider
from celery import current_task
from celery_task.tag_task.tag_introduce_task import introduce
from celery_task.tag_task.tag_word_cloud_task import word_cloud
from celery_task.tag_task.tag_relaton_task import tag_relation
from celery_task.tag_task.tag_hot_task import hot_task
from celery_task.utils.update_task_status import update_task_status
from celery_task.tag_comment_task.task import start_task
from celery_task.tag_task.tag_user_analysis_task import user_analysis
from celery_task.config import mongo_conf


@celeryapp.task()
def task_schedule(tag_task_id: str, tag: str):
    """
    任务管理函数
    :param tag_task_id: 话题任务id
    :param tag:话题名
    :param task_id_dict:各个任务id组成的字典
    :return:
    """
    import traceback
    
    try:
        print(f'[{tag_task_id}] 开始爬虫任务')
        current_task.update_state(state='PROGRESS',
                                  meta={'current': "爬虫任务", 'task_id': tag_task_id})
        update_task_status(tag_task_id, 'PROGRESS')
        weibo_data, weibo_post_list, user_id_list = spider(tag, tag_task_id)
        print(f'[{tag_task_id}] 爬虫任务完成，获取{len(weibo_post_list)}条博文，{len(user_id_list)}个用户')
    except Exception as e:
        print(f'[{tag_task_id}] 爬虫任务失败: {e}')
        traceback.print_exc()
        update_task_status(tag_task_id, 'FAILURE')
        raise

    try:
        print(f'[{tag_task_id}] 开始构建话题基本信息任务')
        current_task.update_state(state='PROGRESS',
                                  meta={'current': "构建话题基本信息", 'task_id': tag_task_id})
        introduce(weibo_data, tag_task_id)
        print(f'[{tag_task_id}] 话题基本信息任务完成')
    except Exception as e:
        print(f'[{tag_task_id}] 话题基本信息任务失败: {e}')
        traceback.print_exc()

    try:
        print(f'[{tag_task_id}] 开始构建词云任务')
        current_task.update_state(state='PROGRESS',
                                  meta={'current': "构建词云任务", 'task_id': tag_task_id})
        word_cloud(weibo_data, tag_task_id)
        print(f'[{tag_task_id}] 词云任务完成')
    except Exception as e:
        print(f'[{tag_task_id}] 词云任务失败: {e}')
        traceback.print_exc()

    # 开始爬取详细博文任务, 由于分析用户成分任务阻塞时间较长，故而在此处发布博文详细任务的提取
    try:
        print(f'[{tag_task_id}] 启动评论分析任务（异步）')
        start_comment_task.delay(weibo_post_list, tag_task_id)
        print(f'[{tag_task_id}] 评论分析任务已启动')
    except Exception as e:
        print(f'[{tag_task_id}] 启动评论分析任务失败: {e}')
        traceback.print_exc()

    user_mark_data = None
    try:
        print(f'[{tag_task_id}] 分析用户成分任务')
        current_task.update_state(state='PROGRESS',
                                  meta={'current': '分析用户成分任务', 'task_id': tag_task_id})
        user_mark_data = user_analysis(weibo_data, tag_task_id, user_id_list)
        if user_mark_data:
            print(f'[{tag_task_id}] 用户成分任务完成，用户数量: {len(user_mark_data.get("data", []))}')
        else:
            print(f'[{tag_task_id}] 用户成分任务完成，但返回数据为空')
    except Exception as e:
        print(f'[{tag_task_id}] 用户成分任务失败: {e}')
        traceback.print_exc()
        # 创建空的user_mark_data以确保后续任务可以继续
        from celery_task.utils import mongo_client
        from celery_task.config import mongo_conf
        user_mark_data = {"data": [], "categories": 0}
        try:
            mongo_client.db[mongo_conf.USER].update_one(
                {"tag_task_id": tag_task_id}, {"$set": user_mark_data}
            )
        except:
            pass

    try:
        print(f'[{tag_task_id}] 开始构建转发关系任务')
        current_task.update_state(state='PROGRESS',
                                  meta={'current': "构建转发关系任务", 'task_id': tag_task_id})
        if user_mark_data is None:
            user_mark_data = {"data": [], "categories": 0}
        tag_relation(weibo_data, tag_task_id, user_mark_data)
        print(f'[{tag_task_id}] 转发关系任务完成')
    except Exception as e:
        print(f'[{tag_task_id}] 转发关系任务失败: {e}')
        traceback.print_exc()

    try:
        print(f'[{tag_task_id}] 开始挖掘热度数据任务')
        current_task.update_state(state='PROGRESS',
                                  meta={'current': "挖掘热度信息任务", 'task_id': tag_task_id})
        tag_name = weibo_data.get('tag', tag)
        hot_task(tag_name, tag_task_id)
        print(f'[{tag_task_id}] 热度数据任务完成')
    except Exception as e:
        print(f'[{tag_task_id}] 热度数据任务失败: {e}')
        traceback.print_exc()
        # 热度数据失败不影响任务完成

    print(f'[{tag_task_id}] 所有任务完成')
    current_task.update_state(state='SUCCESS',
                              meta={'current': "完成", 'task_id': tag_task_id})
    update_task_status(tag_task_id, 'SUCCESS')


@celeryapp.task()
def start_comment_task(weibo_post_list: list, tag_task_id):
    """
    微博评论分析任务
    :param weibo_post_list: 要分析的博文详细信息
    :param tag_task_id: 任务id
    :return:
    """
    for weibo_post in weibo_post_list:
        start_task(tag_task_id=tag_task_id, weibo_post=weibo_post)
        time.sleep(3)


@celeryapp.task()
def test(content: str):
    while True:
        print(content)

#6616523296
