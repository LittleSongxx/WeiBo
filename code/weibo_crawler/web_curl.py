from tornado import gen
from tornado.curl_httpclient import CurlError
from tornado.httpclient import AsyncHTTPClient, HTTPError
from enum import Enum, unique
import re

import settings
import request_builder
from weibo_curl_error import WeiboCurlError


@unique  # 确保枚举值唯一
class SpiderAim(Enum):
    """枚举全部爬取目标，每个目标的value为对应的RequestBuilder"""
    users_show = request_builder.UserIndexReqBuilder
    users_info = request_builder.UserInfoReqBuilder
    users_weibo_page = request_builder.UserWeiboPageReqBuilder
    weibo_comment = request_builder.WeiboCommentReqBuilder
    hot_comment = request_builder.HotCommentReqBuilder
    mblog_pic_all = request_builder.MblogPicAllReqBuilder
    follow = request_builder.FollowsReqBuilder
    fans = request_builder.FansReqBuilder
    search_weibo = request_builder.SearchWeiboReqBuilder
    search_users = request_builder.SearchUsersReqBuilder

 
# AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

@gen.coroutine
def weibo_web_curl(curl_aim: SpiderAim,
                   retry_time=settings.RETRY_TIME, with_cookie=True, **kwargs):
    """
    根据爬取的目标对相对应的网站发送request请求并获得response
    :param curl_aim: 爬取的目标，其值必须为Aim枚举值
    :param retry_time: 最多尝试发送request的次数
    :param kwargs: 需要转发给RequestBuilder的初始化参数
    :return: 当参数use_bs4为True时返回bs4解析的soup，False时返回etree解析后的selector
    """
    global response
    # 使用 curl httpclient 以支持 proxy_host/proxy_port
    try:
        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    except Exception:
        # 如果环境缺少 pycurl，继续用默认客户端（此时 proxy_host 不可用）
        pass
    client = AsyncHTTPClient()
    # 将 curl_aim 转换成 RequestBuilder 类
    RequestBuilder = curl_aim.value
    # 构建请求并发送
    for epoch in range(retry_time):  # 最多进行retry_time次的请求尝试
        request = RequestBuilder(
            **kwargs).make_request(with_cookie=with_cookie)  # 获得 http request

        try:
            response = yield client.fetch(request)  # 发出请求获取响应
            # print(response.body)

            # 检查是否Cookie失效/跳登录页/验证码页（s.weibo.com 经常返回登录/验证页导致解析报错）
            try:
                ascii_hint = response.body.decode("ascii", errors="ignore")
                charset_pattern = re.compile(r'(?<=charset=").+(?=")')
                charset_match = charset_pattern.search(ascii_hint)
                charset = charset_match.group() if charset_match else "utf-8"

                body_text = response.body.decode(charset, errors="ignore")
                # 更精确的判定：优先用 title / passport 域名特征，避免 s.weibo.com 正常页包含 login 字样被误判
                title_pattern = re.compile(r"<title>\s*(.*?)\s*</title>", re.I | re.S)
                title_match = title_pattern.search(body_text)
                page_title = title_match.group(1).strip() if title_match else ""

                is_passport = "passport.weibo" in body_text
                is_login_title = page_title in ("新浪通行证", "登录 - 新浪微博", "登录", "Login")
                is_verify_title = ("验证" in page_title) or ("验证码" in page_title)

                # 极少数情况下 title 抓不到，再用更窄的中文关键字兜底（避免用 login 误伤）
                is_obvious_login_page = ("请输入验证码" in body_text) or ("帐号登录" in body_text) or ("账号登录" in body_text)

                if is_passport or is_login_title or is_verify_title or is_obvious_login_page:
                    if getattr(settings, "VERBOSE_BLOCK_LOG", False):
                        settings.LOGGING.warning(
                            "疑似登录/验证页，判定 Cookie 失效或被拦截。url=%s, title=%s, cookie_prefix=%s",
                            request.url,
                            page_title,
                            (request.headers.get("Cookie") or "")[:80],
                        )
                    return {"error_code": 3, "errmsg": "Invalid cookie or blocked by verification."}

                # 原有 title 判断保留（更严格）
                if page_title in ("新浪通行证", "登录 - 新浪微博"):
                    if getattr(settings, "VERBOSE_BLOCK_LOG", False):
                        settings.LOGGING.warning(
                            "Cookie错误或失效（title判定）。url=%s, title=%s",
                            request.url,
                            page_title,
                        )
                    return {"error_code": 3, "errmsg": "Invalid cookie."}
            except Exception:
                pass
        except CurlError as e:  # 连接超时
            if epoch < settings.RETRY_TIME:
                continue
            return {'error_code': 5, 'errmsg': str(e)}
        except HTTPError as e:  # 其他HTTP错误
            if epoch < settings.RETRY_TIME:
                continue
            return {'error_code': 1, 'errmsg': str(e)}

        # 根据 http code 返回对应的信息
        http_code = response.code
        if http_code == 200:
            return {'error_code': 0, 'response': response}
        # 非200时进行重试
        if epoch < settings.RETRY_TIME:
            continue
        # 若重试多次仍然错误，就返回报错
        if http_code == 302 or http_code == 403:  # Cookie 失效
            return {'error_code': 3, 'errmsg': 'Invalid cookie: {}'.format(
                request.headers.get('Cookie'))}
        elif http_code == 418:  # ip失效，偶尔产生，需要再次请求
            return {'error_code': 4,
                    'errmsg': 'Please change a proxy and send a request again'}
        else:
            return {'error_code': 1,
                    'errmsg': 'Http status code: {}'.format(http_code)}

    return {'error_code': 5, 'errmsg': ''}


def curl_result_to_api_result(curl_result):
    """
    将 weibo_web_curl 返回的错误结果进行处理获得对应的错误信息
    """
    error_code = curl_result.get('error_code')
    # 将 error_code 转化为 WeiboCurlError 中的错误信息结果
    code_to_res = {
        1: lambda: WeiboCurlError.ABNORMAL_HTTP.copy(),
        2: lambda: WeiboCurlError.REQUEST_ARGS_ERROR.copy(),
        3: lambda: WeiboCurlError.COOKIE_INVALID.copy(),
        4: lambda: WeiboCurlError.IP_INVALID.copy(),
        5: lambda: WeiboCurlError.CONNECT_TIMED_OUT.copy()
    }

    error_res = code_to_res.get(error_code)()
    if error_res is not None:
        error_res['error_msg'] += curl_result.get('errmsg')
    else:
        error_res = WeiboCurlError.UNKNOWN_ERROR.copy()
    return error_res
