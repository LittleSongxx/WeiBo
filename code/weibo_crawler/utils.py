from datetime import datetime, timedelta
import sys
from settings import LOGGING
import traceback
import re


# Base62 字符表，用于微博ID转换
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def mid_to_base62(mid):
    """
    将微博的数字ID (mid) 转换为 Base62 编码的 ID
    微博的 mid 是一个大整数，需要分段转换：
    - 将 mid 从右往左每7位分成一组
    - 每组转换为 Base62
    - 拼接结果（第一组可能不足4位，其他组补齐4位）

    :param mid: 数字格式的微博ID，如 "5257648623851219"
    :return: Base62格式的ID，如 "QoNgcBEJA"
    """
    mid = str(mid)
    # 从右往左每7位分一组
    groups = []
    while mid:
        groups.append(mid[-7:])
        mid = mid[:-7]
    groups.reverse()

    result = []
    for i, group in enumerate(groups):
        num = int(group)
        base62_str = _int_to_base62(num)
        # 除了第一组，其他组需要补齐到4位
        if i > 0:
            base62_str = base62_str.zfill(4)
        result.append(base62_str)

    return ''.join(result)


def base62_to_mid(base62_id):
    """
    将 Base62 编码的微博 ID 转换为数字 ID (mid)

    :param base62_id: Base62格式的ID，如 "QoNgcBEJA"
    :return: 数字格式的微博ID，如 "5257648623851219"
    """
    # 从右往左每4位分一组
    groups = []
    while base62_id:
        groups.append(base62_id[-4:])
        base62_id = base62_id[:-4]
    groups.reverse()

    result = []
    for i, group in enumerate(groups):
        num = _base62_to_int(group)
        num_str = str(num)
        # 除了第一组，其他组需要补齐到7位
        if i > 0:
            num_str = num_str.zfill(7)
        result.append(num_str)

    return ''.join(result)


def _int_to_base62(num):
    """将整数转换为 Base62 字符串"""
    if num == 0:
        return BASE62_ALPHABET[0]

    result = []
    while num:
        result.append(BASE62_ALPHABET[num % 62])
        num //= 62
    return ''.join(reversed(result))


def _base62_to_int(base62_str):
    """将 Base62 字符串转换为整数"""
    result = 0
    for char in base62_str:
        result = result * 62 + BASE62_ALPHABET.index(char)
    return result


def is_numeric_mid(weibo_id):
    """判断微博ID是否为数字格式的mid"""
    return str(weibo_id).isdigit()


def ensure_base62_id(weibo_id):
    """
    确保返回 Base62 格式的微博ID
    如果输入是数字格式，则转换；否则直接返回
    """
    weibo_id = str(weibo_id)
    if is_numeric_mid(weibo_id):
        return mid_to_base62(weibo_id)
    return weibo_id


def report_log(exception: Exception):
    """
    将错误报告给日志
    :param exception: 产生的异常
    """
    LOGGING.warning(
        '{} occur a exception {}:\n{}\n==========\n{}'
        .format(datetime.now(), exception.__class__.__name__, exception.args, traceback.format_exc())
    )


def handle_garbled(info):
    """处理乱码"""
    try:
        _info = (' '.join(info.xpath('.//text()')).replace(u'\u200b', '').encode(
            sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
        return _info
    except Exception as e:
        LOGGING.exception(e)


def extract_from_one_table_node(table_node):
    """处理关注者或粉丝列表页中的一个table"""
    table_node = table_node.xpath('.//td')[1]
    follow_user = table_node.xpath('./a')[0]
    user_name = follow_user.text  # 关注者的昵称
    user_id = follow_user.get('href')  # 关注者的id
    if isinstance(user_id, str):
        user_id = user_id[user_id.rfind(r'/') + 1:]
    fans_num = table_node.xpath('text()')  # 关注者的粉丝数
    if len(fans_num) != 0:
        row_data = re.findall("粉丝(.+?)人", fans_num[0], re.I|re.M)
        fans_num = str2value(row_data[0])
    else:
        fans_num = None
    return dict(user_id=user_id, user_name=user_name, fans_num=fans_num)


def str2value(valueStr):
    """
    微博粉丝、朋友数中万、亿的转换
    """
    valueStr = str(valueStr)
    idxOfYi = valueStr.find('亿')
    idxOfWan = valueStr.find('万')
    if idxOfYi != -1 and idxOfWan != -1:
        return int(float(valueStr[:idxOfYi]) * 1e8 + float(valueStr[idxOfYi + 1:idxOfWan]) * 1e4)
    elif idxOfYi != -1 and idxOfWan == -1:
        return int(float(valueStr[:idxOfYi]) * 1e8)
    elif idxOfYi == -1 and idxOfWan != -1:
        return int(float(valueStr[idxOfYi + 1:idxOfWan]) * 1e4)
    elif idxOfYi == -1 and idxOfWan == -1:
        return int(valueStr)



def standardize_date(created_at):
    """标准化微博发布时间"""
    if not created_at:
        return ''

    if "刚刚" in created_at:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    elif "秒" in created_at:
        second = created_at[:created_at.find(u"秒")]
        second = timedelta(seconds=int(second))
        created_at = (datetime.now() - second).strftime("%Y-%m-%d %H:%M")
    elif "分钟" in created_at:
        minute = created_at[:created_at.find(u"分钟")]
        minute = timedelta(minutes=int(minute))
        created_at = (datetime.now() - minute).strftime("%Y-%m-%d %H:%M")
    elif "小时" in created_at:
        hour = created_at[:created_at.find(u"小时")]
        hour = timedelta(hours=int(hour))
        created_at = (datetime.now() - hour).strftime("%Y-%m-%d %H:%M")
    elif "今天" in created_at:
        today = datetime.now().strftime('%Y-%m-%d')
        created_at = today + ' ' + created_at[2:]
    elif "昨天" in created_at:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        created_at = yesterday + ' ' + created_at[2:]
    elif '年' in created_at and '月' in created_at and '日' in created_at:
        # 处理 "2025年03月31日09:49" 格式（带年份的完整格式）
        year_idx = created_at.find('年')
        year = created_at[:year_idx]
        month_idx = created_at.find('月')
        month = created_at[year_idx + 1:month_idx].zfill(2)
        day_idx = created_at.find('日')
        day = created_at[month_idx + 1:day_idx].zfill(2)
        time_str = created_at[day_idx + 1:].strip()
        if time_str:
            created_at = f"{year}-{month}-{day} {time_str}"
        else:
            created_at = f"{year}-{month}-{day}"
    elif '月' in created_at and '日' in created_at:
        # 处理 "01月25日06:49" 或 "01月25日 06:49" 格式（不带年份）
        year = datetime.now().strftime("%Y")
        month_idx = created_at.find('月')
        month = created_at[:month_idx].zfill(2)
        day_start = month_idx + 1
        day_idx = created_at.find('日')
        day = created_at[day_start:day_idx].zfill(2)
        time_str = created_at[day_idx + 1:].strip()
        if time_str:
            created_at = f"{year}-{month}-{day} {time_str}"
        else:
            created_at = f"{year}-{month}-{day}"
    elif re.match(r'^\d{4}-\d{1,2}-\d{1,2}', created_at):
        # 处理 "YYYY-MM-DD HH:MM" 格式（已经是标准格式）
        pass
    elif '年' not in created_at and '-' in created_at:
        # 处理 "MM-DD HH:MM" 格式
        year = datetime.now().strftime("%Y")
        month = created_at[:2]
        day = created_at[3:5]
        time_str = created_at[6:] if len(created_at) > 5 else ''
        if time_str:
            created_at = year + '-' + month + '-' + day + ' ' + time_str
        else:
            created_at = year + '-' + month + '-' + day
    elif '年' in created_at:
        year = created_at[:4]
        month = created_at[5:7]
        day = created_at[8:10]
        time_str = created_at[11:]
        created_at = year + '-' + month + '-' + day + ' ' + time_str
    return created_at
