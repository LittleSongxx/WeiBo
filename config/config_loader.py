"""
统一配置加载器
用于加载和访问 app_config.yaml 中的配置项
"""

import os
import yaml
from typing import Any, Optional
from functools import lru_cache


class ConfigLoader:
    """配置加载器类"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 可能的配置文件路径
        possible_paths = [
            # 相对于当前文件
            os.path.join(os.path.dirname(__file__), 'app_config.yaml'),
            # 项目根目录
            os.path.join(os.path.dirname(__file__), '..', 'config', 'app_config.yaml'),
            # 绝对路径
            '/home/song/code/graduation/Topic_and_user_profile_analysis_system/config/app_config.yaml',
            # 相对于工作目录
            'config/app_config.yaml',
            'Topic_and_user_profile_analysis_system/config/app_config.yaml',
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        self._config = yaml.safe_load(f)
                        print(f"[ConfigLoader] 成功加载配置文件: {abs_path}")
                        return
                except Exception as e:
                    print(f"[ConfigLoader] 加载配置文件失败 {abs_path}: {e}")
                    continue
        
        print("[ConfigLoader] 警告: 未找到配置文件，使用默认配置")
        self._config = {}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key_path: 配置路径，使用点号分隔，如 'crawler.request.timeout'
            default: 默认值
        
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def reload(self):
        """重新加载配置文件"""
        self._config = None
        self._load_config()
    
    @property
    def config(self) -> dict:
        """获取完整配置"""
        return self._config or {}


# 全局配置实例
_config_loader = None


def get_config() -> ConfigLoader:
    """获取配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


# ============================================
# 便捷访问函数
# ============================================

def get_server_config() -> dict:
    """获取服务配置"""
    return get_config().get('server', {})


def get_database_config() -> dict:
    """获取数据库配置"""
    return get_config().get('database', {})


def get_crawler_config() -> dict:
    """获取爬虫配置"""
    return get_config().get('crawler', {})


def get_analysis_config() -> dict:
    """获取分析配置"""
    return get_config().get('analysis', {})


def get_logging_config() -> dict:
    """获取日志配置"""
    return get_config().get('logging', {})


def get_task_config() -> dict:
    """获取任务配置"""
    return get_config().get('task', {})


# ============================================
# 常用配置项快捷访问
# ============================================

def get_mobile_cookies() -> list:
    """获取移动端 Cookie 列表"""
    return get_config().get('crawler.cookies_mobile', [])


def get_pc_cookies() -> list:
    """获取 PC 端 Cookie 列表"""
    return get_config().get('crawler.cookies_pc', [])


def get_request_timeout() -> int:
    """获取请求超时时间"""
    return get_config().get('crawler.request.timeout', 30)


def get_retry_times() -> int:
    """获取重试次数"""
    return get_config().get('crawler.request.retry_times', 3)


def get_user_agent() -> str:
    """获取 User-Agent"""
    return get_config().get(
        'crawler.request.user_agent',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )


def get_delay_range() -> dict:
    """获取请求延迟配置（完整字典）"""
    return {
        'min_interval': get_config().get('crawler.delay.min_interval', 3),
        'max_interval': get_config().get('crawler.delay.max_interval', 15),
        'user_info_delay_min': get_config().get('crawler.delay.user_info_delay_min', 5),
        'user_info_delay_max': get_config().get('crawler.delay.user_info_delay_max', 10),
        'failure_delay_min': get_config().get('crawler.delay.failure_delay_min', 5),
        'failure_delay_max': get_config().get('crawler.delay.failure_delay_max', 10),
    }


def get_page_size() -> int:
    """获取分页大小"""
    return get_config().get('crawler.pagination.page_size', 100)


def get_search_max_pages() -> int:
    """获取搜索最大页数"""
    return get_config().get('crawler.pagination.search_max_pages', 50)


def get_repost_max_pages() -> int:
    """获取转发爬取最大页数"""
    return get_config().get('crawler.pagination.repost_max_pages', 300)


def get_mongodb_config() -> dict:
    """获取 MongoDB 配置"""
    return get_config().get('database.mongodb', {
        'host': '127.0.0.1',
        'port': 27017,
        'db_name': 'public_opinion_analysis_system'
    })


def get_redis_config() -> dict:
    """获取 Redis 配置"""
    return get_config().get('database.redis', {
        'host': '127.0.0.1',
        'port': 6379,
        'broker_db': 0,
        'backend_db': 1
    })


def is_proxy_enabled() -> bool:
    """是否启用代理"""
    return get_config().get('crawler.proxy.enabled', False)


def get_proxies() -> list:
    """获取代理列表"""
    return get_config().get('crawler.proxy.proxies', [])


# ============================================
# 测试
# ============================================

if __name__ == '__main__':
    # 测试配置加载
    config = get_config()
    
    print("\n=== 服务配置 ===")
    print(f"后端端口: {get_server_config().get('backend_port')}")
    print(f"爬虫端口: {get_server_config().get('crawler_port')}")
    
    print("\n=== 爬虫配置 ===")
    print(f"请求超时: {get_request_timeout()}秒")
    print(f"重试次数: {get_retry_times()}")
    print(f"延迟范围: {get_delay_range()}")
    print(f"分页大小: {get_page_size()}")
    print(f"搜索最大页数: {get_search_max_pages()}")
    
    print("\n=== Cookie 配置 ===")
    mobile_cookies = get_mobile_cookies()
    print(f"移动端 Cookie 数量: {len(mobile_cookies)}")
    if mobile_cookies:
        print(f"移动端 Cookie 前50字符: {mobile_cookies[0][:50]}...")
    
    print("\n=== 数据库配置 ===")
    print(f"MongoDB: {get_mongodb_config()}")
    print(f"Redis: {get_redis_config()}")
    
    print("\n=== 代理配置 ===")
    print(f"代理启用: {is_proxy_enabled()}")
