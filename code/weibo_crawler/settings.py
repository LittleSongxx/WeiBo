import logging

PORT_NUM = 8001  # app运行的端口号


# 发送一个request最多重新尝试的次数
RETRY_TIME = 3

# requests的headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
HEADERS_WITH_COOKIR = HEADERS.copy()

# requests的超时时长限制das
REQUEST_TIME_OUT = 10

# 爬取结果正确时返回结果的格式
SUCCESS = {"error_code": 0, "data": None, "error_msg": None}

# 日志
LOGGING = logging
