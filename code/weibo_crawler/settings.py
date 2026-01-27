"""
weibo_crawler 配置文件
优先从统一配置文件 (config/app_config.yaml) 读取，若失败则使用默认值
"""

import logging
import sys
import os

# 添加配置模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 尝试加载统一配置
try:
    from config import (
        get_config,
        get_server_config,
        get_crawler_config,
        get_request_timeout,
        get_retry_times,
        get_user_agent,
        get_logging_config,
        is_proxy_enabled,
    )
    USE_UNIFIED_CONFIG = True
except ImportError:
    USE_UNIFIED_CONFIG = False


def _get_port():
    """获取爬虫服务端口"""
    if USE_UNIFIED_CONFIG:
        try:
            return get_server_config().get('crawler_port', 8001)
        except:
            pass
    return 8001


def _get_retry_time():
    """获取重试次数"""
    if USE_UNIFIED_CONFIG:
        try:
            return get_retry_times()
        except:
            pass
    return 3


def _get_timeout():
    """获取请求超时时间"""
    if USE_UNIFIED_CONFIG:
        try:
            return get_request_timeout()
        except:
            pass
    return 30


def _get_user_agent():
    """获取 User-Agent"""
    if USE_UNIFIED_CONFIG:
        try:
            return get_user_agent()
        except:
            pass
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _get_use_proxy():
    """是否启用代理"""
    if USE_UNIFIED_CONFIG:
        try:
            return is_proxy_enabled()
        except:
            pass
    return False


def _get_verbose_block_log():
    """是否输出详细拦截日志"""
    if USE_UNIFIED_CONFIG:
        try:
            return get_logging_config().get('verbose_block_log', False)
        except:
            pass
    return False


def _get_verbose_result_log():
    """是否输出详细结果日志"""
    if USE_UNIFIED_CONFIG:
        try:
            return get_logging_config().get('verbose_result_log', False)
        except:
            pass
    return False


# ============================================
# 导出配置（保持向后兼容）
# ============================================

# app运行的端口号
PORT_NUM = _get_port()

# 发送一个request最多重新尝试的次数
RETRY_TIME = _get_retry_time()

# requests的headers
HEADERS = {
    "User-Agent": _get_user_agent(),
}
HEADERS_WITH_COOKIR = HEADERS.copy()

# requests的超时时长限制
REQUEST_TIME_OUT = _get_timeout()

# 是否启用代理
USE_PROXY = _get_use_proxy()

# 是否支持代理（运行时探测 pycurl/tornado curl 客户端可用性）
PROXY_SUPPORTED = False

# 爬取结果正确时返回结果的格式
SUCCESS = {
    'error_code': 0,
    'data': None,
    'error_msg': None
}

# 日志
LOGGING = logging

# 是否输出"被登录/验证码拦截"的详细诊断日志
VERBOSE_BLOCK_LOG = _get_verbose_block_log()

# 是否在 weibo_curl_api 终端打印接口返回的完整 JSON
VERBOSE_RESULT_LOG = _get_verbose_result_log()


# 打印配置加载状态
if __name__ == '__main__':
    print(f"使用统一配置: {USE_UNIFIED_CONFIG}")
    print(f"端口号: {PORT_NUM}")
    print(f"重试次数: {RETRY_TIME}")
    print(f"超时时间: {REQUEST_TIME_OUT}")
    print(f"User-Agent: {HEADERS['User-Agent'][:50]}...")
    print(f"启用代理: {USE_PROXY}")
    print(f"详细拦截日志: {VERBOSE_BLOCK_LOG}")
    print(f"详细结果日志: {VERBOSE_RESULT_LOG}")
