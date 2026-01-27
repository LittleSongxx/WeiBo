"""
:处理前端tag热度请求
@author: lingzhi
* @date 2021/8/13 14:55
"""

import gopup as gp
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.dto.tag_dto.tag_hot import TagHot


async def update_hot_data(tag_task_id: str, mongo_db: AsyncIOMotorDatabase) -> TagHot:
    """
    当接收到前端热度请求后，获取并更新热度信息
    :param mongo_db: 数据库参数
    :param tag_task_id: tag任务id
    :return:
    """
    try:
        mongo_collection = mongo_db["tag_hot"]
        hot_find = await mongo_collection.find_one({"tag_task_id": tag_task_id})
        print(tag_task_id)
        # 检查hot_find和tag字段是否存在
        if not hot_find or "tag" not in hot_find:
            # 如果数据库中已有热度数据，尝试直接返回（需要转换格式）
            if hot_find and "one_day" in hot_find and "one_month" in hot_find and "three_month" in hot_find:
                # 转换数据库中的字典格式为前端需要的格式
                def convert_dict_to_list_format(data_dict, is_hourly=False):
                    """
                    将 {'time': value} 格式转换为 {'data_time': [], 'data_count': []} 格式
                    前端期望时间格式包含T分隔符
                    """
                    if isinstance(data_dict, dict):
                        if "data_time" in data_dict and "data_count" in data_dict:
                            # 已经是列表格式，确保时间格式正确
                            data_time = []
                            for t in data_dict["data_time"]:
                                t_str = str(t)
                                if "T" not in t_str:
                                    t_str = t_str + "T00:00"
                                data_time.append(t_str)
                            return {"data_time": data_time, "data_count": data_dict["data_count"]}
                        else:
                            # 是字典格式，需要转换
                            data_time = []
                            for t in data_dict.keys():
                                t_str = str(t)
                                if "T" not in t_str:
                                    t_str = t_str + "T00:00"
                                data_time.append(t_str)
                            data_count = list(data_dict.values())
                            return {"data_time": data_time, "data_count": data_count}
                    return {"data_time": [], "data_count": []}

                return TagHot(
                    tag_task_id=tag_task_id,
                    tag=hot_find.get("tag", ""),
                    one_day=convert_dict_to_list_format(hot_find.get("one_day", {}), is_hourly=True),
                    one_month=convert_dict_to_list_format(hot_find.get("one_month", {})),
                    three_month=convert_dict_to_list_format(hot_find.get("three_month", {}))
                )
            # 否则返回空数据
            return TagHot(
                tag_task_id=tag_task_id,
                tag="",
                one_day={"data_time": [], "data_count": []},
                one_month={"data_time": [], "data_count": []},
                three_month={"data_time": [], "data_count": []}
            )
        tag = hot_find["tag"]

        # 尝试从gopup获取数据
        try:
            one_day = gp.weibo_index(word=tag, time_type="1day")
            one_month = gp.weibo_index(word=tag, time_type="1month")
            three_month = gp.weibo_index(word=tag, time_type="3month")
            
            # 检查数据是否获取成功
            if one_day is None or one_month is None or three_month is None:
                raise ValueError("gopup返回None数据")
            
            # 检查数据是否包含tag字段
            one_day_dict_data = one_day.to_dict()
            one_month_dict_data = one_month.to_dict()
            three_month_dict_data = three_month.to_dict()
            
            if tag not in one_day_dict_data or tag not in one_month_dict_data or tag not in three_month_dict_data:
                raise ValueError("数据中不包含tag字段")
            
            one_day_dict = {
                "data_time": [str(t) for t in one_day_dict_data[tag].keys()],
                "data_count": [int(v) if v is not None else 0 for v in one_day_dict_data[tag].values()],
            }
            one_month_dict = {
                "data_time": [str(t) for t in one_month_dict_data[tag].keys()],
                "data_count": [int(v) if v is not None else 0 for v in one_month_dict_data[tag].values()],
            }
            three_month_dict = {
                "data_time": [str(t) for t in three_month_dict_data[tag].keys()],
                "data_count": [int(v) if v is not None else 0 for v in three_month_dict_data[tag].values()],
            }
        except (AttributeError, ValueError, KeyError) as e:
            print(f"从gopup获取数据失败: {e}")
            # 如果gopup获取失败，尝试从数据库返回已有数据（需要转换格式）
            if hot_find and "one_day" in hot_find and "one_month" in hot_find and "three_month" in hot_find:
                # 转换数据库中的字典格式为前端需要的格式
                def convert_dict_to_list_format(data_dict, is_hourly=False):
                    """
                    将 {'time': value} 格式转换为 {'data_time': [], 'data_count': []} 格式
                    前端期望时间格式包含T分隔符，如 "2026-01-26T14:00"
                    """
                    if isinstance(data_dict, dict):
                        if "data_time" in data_dict and "data_count" in data_dict:
                            # 已经是列表格式，确保时间格式正确
                            data_time = []
                            for t in data_dict["data_time"]:
                                t_str = str(t)
                                if "T" not in t_str:
                                    # 添加T分隔符
                                    if is_hourly:
                                        t_str = t_str + "T00:00"
                                    else:
                                        t_str = t_str + "T00:00"
                                data_time.append(t_str)
                            return {"data_time": data_time, "data_count": data_dict["data_count"]}
                        else:
                            # 是字典格式，需要转换
                            data_time = []
                            for t in data_dict.keys():
                                t_str = str(t)
                                if "T" not in t_str:
                                    t_str = t_str + "T00:00"
                                data_time.append(t_str)
                            data_count = list(data_dict.values())
                            return {"data_time": data_time, "data_count": data_count}
                    return {"data_time": [], "data_count": []}

                return TagHot(
                    tag_task_id=tag_task_id,
                    tag=tag,
                    one_day=convert_dict_to_list_format(hot_find.get("one_day", {}), is_hourly=True),
                    one_month=convert_dict_to_list_format(hot_find.get("one_month", {})),
                    three_month=convert_dict_to_list_format(hot_find.get("three_month", {}))
                )
            # 如果数据库也没有数据，返回空数据
            return TagHot(
                tag_task_id=tag_task_id,
                tag=tag,
                one_day={"data_time": [], "data_count": []},
                one_month={"data_time": [], "data_count": []},
                three_month={"data_time": [], "data_count": []}
            )

        update_data = TagHot(
            tag_task_id=tag_task_id,
            tag=tag,
            one_day=one_day_dict,
            one_month=one_month_dict,
            three_month=three_month_dict
        )
        await mongo_collection.update_one(
            {"tag_task_id": tag_task_id},
            {
                "$set": {
                    "one_day": update_data.one_day,
                    "one_month": update_data.one_month,
                    "three_month": update_data.three_month,
                }
            },
        )
        return update_data
    except Exception as e:
        print(f"update_hot_data发生错误: {e}")
        # 返回空数据而不是None
        return TagHot(
            tag_task_id=tag_task_id,
            tag="",
            one_day={"data_time": [], "data_count": []},
            one_month={"data_time": [], "data_count": []},
            three_month={"data_time": [], "data_count": []}
        )
