"""
: 博文详细页请求的api
@author: lingzhi
@time: 2021/7/20 15:27
"""
from fastapi import APIRouter, Depends
from models.dto.restful_model import RESTfulModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from dependencise import get_mongo_db
from service.comment_extract import get_tree_data, get_comment_task_id, getByTendencyId, getByCloudId,\
    getTypeByClusterId, getKeyNode, getWeiboById
from celery_task.tag_comment_task.task import getTaskList, refresh_task
from celery_task.config import mongo_conf
from celery_task.utils import mongo_client

comment_router = APIRouter(tags=['微博评论分析api'])


@comment_router.get('/post_detail', response_model=RESTfulModel,
                    description='获取文章详细信息',
                    summary='文章')
async def get_post_detail(tag_task_id: str, weibo_id: str, mongo: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    return RESTfulModel(code=0, data=await getWeiboById(tag_task_id=tag_task_id, weibo_id=weibo_id, mongo_db=mongo))


@comment_router.get('/tree', response_model=RESTfulModel,
                    description='获取微博传播树结果',
                    summary='传播树')
async def get_tree(tag_task_id: str, weibo_id: str, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    comment_task_id = await get_comment_task_id(tag_task_id=tag_task_id, weibo_id=weibo_id, mongo=mongo_db)
    try:
        return RESTfulModel(code=0, data=await get_tree_data(comment_task_id, mongo_db))
    except Exception as e:
        return RESTfulModel(code=1, data=str(e))


@comment_router.get('/tendency', response_model=RESTfulModel,
                    description='获取微博热度趋势数据',
                    summary='热度数据')
async def get_tendency(tag_task_id: str, weibo_id: str, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    comment_task_id = await get_comment_task_id(tag_task_id=tag_task_id, weibo_id=weibo_id, mongo=mongo_db)
    return RESTfulModel(code=0, data=await getByTendencyId(comment_task_id, mongo_db))


@comment_router.get('/cloud', response_model=RESTfulModel,
                    description='获取评论云图数据',
                    summary='云图数据')
async def get_cloud(tag_task_id: str, weibo_id: str, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    comment_task_id = await get_comment_task_id(tag_task_id=tag_task_id, weibo_id=weibo_id, mongo=mongo_db)
    return RESTfulModel(code=0, data=await getByCloudId(comment_task_id, mongo_db))


@comment_router.get('/cluster/type', response_model=RESTfulModel,
                    description='获取评论聚类数据',
                    summary='聚类')
async def get_cluster(tag_task_id: str, weibo_id: str, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    comment_task_id = await get_comment_task_id(tag_task_id=tag_task_id, weibo_id=weibo_id, mongo=mongo_db)
    return RESTfulModel(code=0, data=await getTypeByClusterId(comment_task_id, mongo_db=mongo_db))


@comment_router.get('/key_node', response_model=RESTfulModel,
                    description='获取评论中的关键节点',
                    summary='关键节点')
async def get_key_node(tag_task_id: str, weibo_id: str, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    comment_task_id = await get_comment_task_id(tag_task_id=tag_task_id, weibo_id=weibo_id, mongo=mongo_db)
    return RESTfulModel(code=0, data=await getKeyNode(comment_task_id, mongo_db))


@comment_router.get('/task_list', response_model=RESTfulModel,
                    description='获取评论分析任务列表（支持按tag_task_id过滤）',
                    summary='任务列表')
async def get_comment_task_list(tag_task_id: str = None, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """
    获取所有评论分析任务列表，可选的按tag_task_id过滤
    
    :param tag_task_id: 可选，话题任务ID，如果提供则只返回该话题下的评论任务
    :param mongo_db: MongoDB数据库连接
    :return: 任务列表，每个任务包含：tag_task_id, weibo_id, tag_comment_task_id, analysis_status, created_time等
    """
    # 先刷新任务状态（从Celery获取最新状态）
    refresh_task()
    
    # 获取任务列表（使用异步 MongoDB 查询）
    query = {}
    if tag_task_id:
        query["tag_task_id"] = tag_task_id
    
    tasks = []
    cursor = mongo_db[mongo_conf.COMMENT_TASK].find(query).sort("created_time", -1)
    async for item in cursor:
        item.pop("_id", None)
        # 确保有必要的字段
        task_info = {
            "tag_task_id": item.get("tag_task_id", ""),
            "weibo_id": item.get("weibo_id", ""),
            "tag_comment_task_id": item.get("tag_comment_task_id", ""),
            "analysis_status": item.get("analysis_status", "UNKNOWN"),
            "created_time": item.get("created_time", ""),
            "celery_id": item.get("celery_id", ""),
            "has_detail": False,
        }
        # 如果有detail，添加摘要信息
        if "detail" in item and item["detail"]:
            detail = item["detail"]
            task_info["has_detail"] = True
            if isinstance(detail, dict):
                task_info["weibo_text"] = detail.get("text", "")[:50] + "..." if detail.get("text") else ""
                task_info["user_name"] = detail.get("screen_name", "")
            else:
                # detail 可能是其他格式
                task_info["weibo_text"] = str(detail)[:50] + "..." if detail else ""
        tasks.append(task_info)
    
    return RESTfulModel(code=0, data={
        "tasks": tasks,
        "total": len(tasks),
        "filter": {"tag_task_id": tag_task_id} if tag_task_id else {}
    })


@comment_router.get('/task_status', response_model=RESTfulModel,
                    description='获取单个评论分析任务的状态',
                    summary='任务状态')
async def get_comment_task_status(tag_task_id: str, weibo_id: str, mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """
    获取指定微博的评论分析任务状态
    
    :param tag_task_id: 话题任务ID
    :param weibo_id: 微博ID
    :param mongo_db: MongoDB数据库连接
    :return: 任务状态信息
    """
    task = await mongo_db[mongo_conf.COMMENT_TASK].find_one(
        {"tag_task_id": tag_task_id, "weibo_id": weibo_id}
    )
    
    if not task:
        return RESTfulModel(code=-1, data={
            "status": "not_found",
            "message": "该微博的评论分析任务尚未创建"
        })
    
    # 刷新任务状态
    refresh_task()
    # 重新查询获取最新状态
    task = await mongo_db[mongo_conf.COMMENT_TASK].find_one(
        {"tag_task_id": tag_task_id, "weibo_id": weibo_id}
    )
    
    from celery_task import celeryapp
    celery_task = celeryapp.AsyncResult(task.get("celery_id", ""))
    
    status_info = {
        "tag_task_id": task.get("tag_task_id", ""),
        "weibo_id": task.get("weibo_id", ""),
        "tag_comment_task_id": task.get("tag_comment_task_id", ""),
        "analysis_status": task.get("analysis_status", "UNKNOWN"),
        "celery_state": celery_task.state if celery_task else "UNKNOWN",
        "created_time": task.get("created_time", ""),
        "has_detail": "detail" in task and bool(task.get("detail")),
    }
    
    # 如果任务正在进行中，添加进度信息
    if celery_task and celery_task.state == "PROGRESS":
        status_info["progress"] = celery_task.info.get("current", "")
    
    return RESTfulModel(code=0, data=status_info)


