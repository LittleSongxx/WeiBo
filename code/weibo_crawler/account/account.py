"""
账号管理模块
优先从统一配置文件读取 Cookie 和代理配置
"""

from settings import LOGGING
import json
import os
import sys
from urllib.parse import urlparse

# 添加配置模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 尝试加载统一配置
try:
    from config import get_mobile_cookies, get_pc_cookies, get_proxies, is_proxy_enabled
    USE_UNIFIED_CONFIG = True
except ImportError:
    USE_UNIFIED_CONFIG = False


class Account:
    """一个账号，包含cookie和proxy"""

    def __init__(self, cookie, proxy):
        self.cookie = cookie
        self.proxy = proxy  # proxy[0]为proxy_host， proxy[1]为proxy_port

    def __repr__(self):
        return "proxy: {}, cookie: {}".format(self.proxy, self.cookie)


class AccountPool:
    """账号池，管理cookie和ip"""

    def __init__(self, cookies, proxies):
        if not cookies or not proxies:
            raise ValueError
        if type(cookies) is not list or type(proxies) is not list:
            raise TypeError

        self.__cookies = cookies
        self.__proxies = proxies
        self.accounts = list()
        self.__count = 0
        self._compound_accounts()

    def __repr__(self):
        return "\n".join(str(acc) for acc in self.accounts)

    def _compound_accounts(self):
        """根据cookies和proxies合成所有Account对象"""
        cookies_len = len(self.__cookies)
        proxies_len = len(self.__proxies)
        max_len = max(cookies_len, proxies_len)

        self.accounts.clear()
        for i in range(max_len):
            account = Account(
                self.__cookies[i % cookies_len], self.__proxies[i % proxies_len]
            )
            self.accounts.append(account)

    def update(self, new_cookies=None, new_proxies=None):
        """对信息进行更新"""

        # 检查new_cookies和new_proxies是否为list或None
        if not isinstance(new_cookies, list) and new_cookies is not None:
            raise ValueError
        if not isinstance(new_proxies, list) and new_proxies is not None:
            raise ValueError
        # 分别进行更新
        if new_cookies:  # 如果new_cookies不是None就进行更新
            self.__cookies = new_cookies
        if new_proxies:
            self.accounts = new_proxies
        # 将更新后的cookie和proxy进行配对复合成多个account
        self._compound_accounts()

    def update_one_cookie(self, seq_num, new_cookie):
        try:
            self.accounts[seq_num].cookie = new_cookie
        except IndexError:
            LOGGING.warning(
                "update fail because seq_num {} over the max account number {}.".format(
                    seq_num, len(self.accounts)
                )
            )

    def update_one_proxy(self, seq_num, new_proxy):
        try:
            self.accounts[seq_num].proxy = new_proxy
        except IndexError:
            LOGGING.warning(
                "update fail because seq_num {} over the max account number {}.".format(
                    seq_num, len(self.accounts)
                )
            )

    def delete_one_proxy(self, seq_num):
        try:
            del self.accounts[seq_num]
        except IndexError:
            LOGGING.warning(
                "delete fail because seq_num {} over the max account number {}.".format(
                    seq_num, len(self.accounts)
                )
            )

    def fetch(self):
        """获取一个账号的cookie和代理"""
        self.__count += 1
        self.__count = self.__count % len(self.accounts)
        account = self.accounts[self.__count]
        return account.cookie, account.proxy


def _load_from_unified_config():
    """从统一配置文件加载 Cookie 和代理"""
    if not USE_UNIFIED_CONFIG:
        return None, None
    
    try:
        cookies = get_mobile_cookies()
        proxies = get_proxies()
        
        if cookies and proxies:
            LOGGING.info("成功从统一配置文件加载 Cookie 和代理")
            return cookies, proxies
    except Exception as e:
        LOGGING.warning(f"从统一配置加载失败: {e}")
    
    return None, None


def _load_account_json():
    """从 account.json 加载配置"""
    # 可能的路径
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'account.json'),
        'account/account.json',
        os.path.join(os.path.dirname(__file__), '..', 'account', 'account.json'),
    ]
    
    for path in possible_paths:
        try:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as json_file:
                    return json.load(json_file)
        except Exception as e:
            continue
    
    # 返回空配置
    return {"cookies": [], "cookies_mobile": [], "proxies": [["", 0]]}


def _get_cookie_list(account_json: dict, key: str):
    cookies = account_json.get(key)
    return cookies if isinstance(cookies, list) else []


def _get_proxy_list(account_json: dict):
    proxies = account_json.get("proxies")
    return proxies if isinstance(proxies, list) else []


def _build_pool(cookies: list, proxies: list):
    # AccountPool 原实现要求 cookies/proxies 都非空；这里做降级：若缺少则返回 None
    if not cookies or not proxies:
        return None
    try:
        return AccountPool(cookies, proxies)
    except Exception as e:
        LOGGING.error("init AccountPool failed: %s", e)
        return None


# ============================================
# 初始化账号池
# ============================================

# 优先从统一配置加载
_unified_cookies, _unified_proxies = _load_from_unified_config()

if _unified_cookies and _unified_proxies:
    # 使用统一配置
    _cookies_mobile = _unified_cookies
    _proxies = _unified_proxies
else:
    # 回退到 account.json
    account_json = _load_account_json()
    _proxies = _get_proxy_list(account_json)
    _cookies_legacy = _get_cookie_list(account_json, "cookies")
    _cookies_mobile = _get_cookie_list(account_json, "cookies_mobile") or _cookies_legacy

account_pool_mobile = _build_pool(_cookies_mobile, _proxies)


def fetch_by_url(url: str):
    """
    获取移动端 cookie（统一使用移动端，兼容所有微博域名）
    """
    if account_pool_mobile:
        return account_pool_mobile.fetch()
    raise ValueError("No valid cookie/proxy config found")


def update_pools(new_cookies_mobile=None, new_proxies=None):
    """
    运行时热更新账号池（供 account_update 接口调用）
    """
    global account_pool_mobile, _proxies

    if new_proxies is not None:
        if not isinstance(new_proxies, list):
            raise ValueError
        _proxies = new_proxies

    if new_cookies_mobile is not None:
        if not isinstance(new_cookies_mobile, list):
            raise ValueError
        account_pool_mobile = _build_pool(new_cookies_mobile, _proxies)


def reload_from_config():
    """
    从配置文件重新加载账号池
    """
    global account_pool_mobile, _proxies, _cookies_mobile
    
    # 优先从统一配置加载
    unified_cookies, unified_proxies = _load_from_unified_config()
    
    if unified_cookies and unified_proxies:
        _cookies_mobile = unified_cookies
        _proxies = unified_proxies
    else:
        # 回退到 account.json
        account_json = _load_account_json()
        _proxies = _get_proxy_list(account_json)
        _cookies_legacy = _get_cookie_list(account_json, "cookies")
        _cookies_mobile = _get_cookie_list(account_json, "cookies_mobile") or _cookies_legacy
    
    account_pool_mobile = _build_pool(_cookies_mobile, _proxies)
    return account_pool_mobile is not None
