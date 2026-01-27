#!/usr/bin/env python3
"""
微博Cookie有效性测试程序
测试PC端和移动端Cookie是否有效，以及评论接口是否正常工作
"""

import requests
import json
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试配置
API_BASE = "http://localhost:8001/weibo_curl/api"
TEST_WEIBO_ID = "5258051250555225"  # 从终端日志中获取的微博ID


def load_cookies():
    """加载account.json中的Cookie"""
    account_path = os.path.join(os.path.dirname(__file__), "account", "account.json")
    try:
        with open(account_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "pc": data.get("cookies", []),
                "mobile": data.get("cookies_mobile", [])
            }
    except Exception as e:
        print(f"❌ 加载Cookie失败: {e}")
        return None


def check_cookie_expiry(cookies_str):
    """检查Cookie中的过期时间"""
    import re
    from datetime import datetime
    
    # 查找ALF字段（移动端过期时间戳）
    alf_match = re.search(r'ALF=(\d+)', cookies_str)
    if alf_match:
        alf_timestamp = int(alf_match.group(1))
        expiry_time = datetime.fromtimestamp(alf_timestamp)
        now = datetime.now()
        if expiry_time < now:
            return f"❌ 已过期 (过期时间: {expiry_time})"
        else:
            days_left = (expiry_time - now).days
            return f"✓ 有效 (剩余 {days_left} 天，过期时间: {expiry_time})"
    
    # 查找SUB字段（PC端）
    sub_match = re.search(r'SUB=([^;]+)', cookies_str)
    if sub_match:
        return "⚠ 无法确定过期时间（需要实际测试）"
    
    return "⚠ 未找到关键Cookie字段"


def test_api_endpoint(endpoint, params, description):
    """测试API端点"""
    url = f"{API_BASE}/{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    print(f"参数: {params}")
    print("-" * 60)
    
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, params=params, timeout=30)
        
        print(f"状态码: {response.status_code}")
        
        if response.text:
            try:
                data = response.json()
                error_code = data.get("error_code", -1)
                error_msg = data.get("error_msg", "")
                
                if error_code == 0:
                    result = data.get("data", {}).get("result", {})
                    if isinstance(result, dict):
                        # 微博详情
                        comments = result.get("comments", [])
                        print(f"✓ 成功!")
                        print(f"  - 评论数量: {len(comments)}")
                        if comments:
                            print(f"  - 第一条评论: {comments[0].get('text', '')[:50]}...")
                        return True, len(comments)
                    elif isinstance(result, list):
                        print(f"✓ 成功! 返回 {len(result)} 条数据")
                        return True, len(result)
                    else:
                        print(f"✓ 成功!")
                        return True, 0
                else:
                    print(f"❌ 失败!")
                    print(f"  - 错误码: {error_code}")
                    print(f"  - 错误信息: {error_msg}")
                    return False, error_msg
            except json.JSONDecodeError:
                print(f"❌ JSON解析失败")
                print(f"  - 响应内容: {response.text[:200]}...")
                return False, "JSON解析失败"
        else:
            print(f"❌ 响应为空")
            return False, "空响应"
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败 - 请确保weibo_crawler服务正在运行")
        return False, "连接失败"
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False, "超时"
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False, str(e)


def test_direct_weibo_request():
    """直接测试微博网页请求（不经过API）"""
    print(f"\n{'='*60}")
    print("直接测试微博网页访问（绕过API）")
    print("-" * 60)
    
    cookies = load_cookies()
    if not cookies:
        return
    
    # 测试移动端
    mobile_cookie = cookies["mobile"][0] if cookies["mobile"] else ""
    if mobile_cookie:
        print("\n[移动端Cookie测试]")
        print(f"Cookie过期状态: {check_cookie_expiry(mobile_cookie)}")
        
        # 测试移动端微博页面 (m.weibo.cn)
        try:
            headers = {
                "Cookie": mobile_cookie,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
            url = f"https://m.weibo.cn/detail/{TEST_WEIBO_ID}"
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            
            if response.status_code == 200:
                if "登录" in response.text or "passport" in response.text:
                    print(f"  m.weibo.cn/detail: ❌ Cookie失效（登录页）")
                else:
                    print(f"  m.weibo.cn/detail: ✓ 有效")
            elif response.status_code == 302:
                print(f"  m.weibo.cn/detail: ❌ Cookie失效（302）")
            else:
                print(f"  m.weibo.cn/detail: ⚠ 状态码 {response.status_code}")
        except Exception as e:
            print(f"  m.weibo.cn/detail: ❌ 异常 {e}")
        
        # 测试 weibo.cn 评论页面（这是爬虫实际使用的URL）
        try:
            headers = {
                "Cookie": mobile_cookie,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
            url = f"https://weibo.cn/comment/{TEST_WEIBO_ID}?page=1"
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            
            print(f"\n  [关键] weibo.cn/comment 评论页面测试:")
            print(f"    URL: {url}")
            print(f"    状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 检查是否是登录页
                if "登录" in response.text or "passport" in response.text or "新浪通行证" in response.text:
                    print(f"    结果: ❌ 被重定向到登录页")
                    print(f"    原因: Cookie对weibo.cn评论页面无效")
                elif "验证码" in response.text:
                    print(f"    结果: ❌ 需要验证码")
                    print(f"    原因: 触发了微博反爬机制")
                elif "评论" in response.text or "comment" in response.text.lower():
                    print(f"    结果: ✓ 成功访问评论页面")
                else:
                    print(f"    结果: ⚠ 返回内容未知")
                    print(f"    内容预览: {response.text[:200]}...")
            elif response.status_code == 302:
                print(f"    结果: ❌ 302重定向（Cookie失效）")
                print(f"    重定向到: {response.headers.get('Location', 'unknown')}")
            else:
                print(f"    结果: ⚠ 异常状态码")
        except Exception as e:
            print(f"    结果: ❌ 请求异常: {e}")
        
        # 测试 weibo.cn 用户信息页面
        try:
            headers = {
                "Cookie": mobile_cookie,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
            url = f"https://weibo.cn/2318910945/info"
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            
            if response.status_code == 200:
                if "登录" in response.text or "passport" in response.text:
                    print(f"  weibo.cn/info: ❌ Cookie失效")
                else:
                    print(f"  weibo.cn/info: ✓ 有效")
            else:
                print(f"  weibo.cn/info: ⚠ 状态码 {response.status_code}")
        except Exception as e:
            print(f"  weibo.cn/info: ❌ 异常 {e}")
    
    # 测试PC端
    pc_cookie = cookies["pc"][0] if cookies["pc"] else ""
    if pc_cookie:
        print("\n[PC端Cookie测试]")
        print(f"Cookie过期状态: {check_cookie_expiry(pc_cookie)}")
        
        try:
            headers = {
                "Cookie": pc_cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            url = f"https://weibo.com/ajax/statuses/show?id={TEST_WEIBO_ID}"
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "id" in data or "text" in data:
                        print(f"  weibo.com/ajax: ✓ 有效")
                    else:
                        print(f"  weibo.com/ajax: ⚠ 返回数据异常: {str(data)[:100]}")
                except:
                    if "登录" in response.text or "passport" in response.text:
                        print(f"  weibo.com/ajax: ❌ Cookie失效")
                    else:
                        print(f"  weibo.com/ajax: ⚠ 返回非JSON")
            elif response.status_code == 302:
                print(f"  weibo.com/ajax: ❌ Cookie失效（302）")
            else:
                print(f"  weibo.com/ajax: ⚠ 状态码 {response.status_code}")
        except Exception as e:
            print(f"  weibo.com/ajax: ❌ 异常 {e}")
        
        # 测试PC端搜索（这个通常不需要Cookie）
        try:
            headers = {
                "Cookie": pc_cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            url = f"https://s.weibo.com/weibo?q=test&page=1"
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            
            if response.status_code == 200:
                print(f"  s.weibo.com搜索: ✓ 可访问")
            else:
                print(f"  s.weibo.com搜索: ⚠ 状态码 {response.status_code}")
        except Exception as e:
            print(f"  s.weibo.com搜索: ❌ 异常 {e}")


def test_comment_page_detail():
    """详细测试评论页面返回内容"""
    print(f"\n{'='*60}")
    print("详细分析 weibo.cn/comment 页面返回内容")
    print("-" * 60)
    
    cookies = load_cookies()
    if not cookies:
        return
    
    mobile_cookie = cookies["mobile"][0] if cookies["mobile"] else ""
    if not mobile_cookie:
        print("❌ 没有移动端Cookie")
        return
    
    headers = {
        "Cookie": mobile_cookie,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    url = f"https://weibo.cn/comment/{TEST_WEIBO_ID}?page=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
        
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        # 解析内容
        import re
        body_text = response.text
        
        # 提取title
        title_pattern = re.compile(r"<title>\s*(.*?)\s*</title>", re.I | re.S)
        title_match = title_pattern.search(body_text)
        page_title = title_match.group(1).strip() if title_match else "(无title)"
        
        print(f"页面Title: {page_title}")
        
        # 检查关键字
        checks = {
            "passport.weibo": "passport.weibo" in body_text,
            "新浪通行证": "新浪通行证" in body_text,
            "登录": "登录" in body_text,
            "Login": "Login" in body_text,
            "验证码": "验证码" in body_text,
            "请输入验证码": "请输入验证码" in body_text,
            "帐号登录": "帐号登录" in body_text,
            "账号登录": "账号登录" in body_text,
            "评论": "评论" in body_text,
            "转发": "转发" in body_text,
        }
        
        print("\n关键字检测:")
        for keyword, found in checks.items():
            status = "✓ 存在" if found else "✗ 不存在"
            print(f"  '{keyword}': {status}")
        
        # 判断是否会被误判为登录页
        is_passport = "passport.weibo" in body_text
        is_login_title = page_title in ("新浪通行证", "登录 - 新浪微博", "登录", "Login")
        is_verify_title = ("验证" in page_title) or ("验证码" in page_title)
        is_obvious_login_page = ("请输入验证码" in body_text) or ("帐号登录" in body_text) or ("账号登录" in body_text)
        
        print("\n误判检测（web_curl.py中的逻辑）:")
        print(f"  is_passport: {is_passport}")
        print(f"  is_login_title: {is_login_title}")
        print(f"  is_verify_title: {is_verify_title}")
        print(f"  is_obvious_login_page: {is_obvious_login_page}")
        
        will_be_blocked = is_passport or is_login_title or is_verify_title or is_obvious_login_page
        print(f"\n结论: {'❌ 会被误判为登录页/验证页' if will_be_blocked else '✓ 不会被误判'}")
        
        # 显示内容片段
        print(f"\n内容预览 (前500字符):")
        print("-" * 40)
        print(body_text[:500])
        print("-" * 40)
        
        # 如果有评论内容，尝试提取
        if "评论" in body_text:
            # 尝试找到评论数量
            comment_count_match = re.search(r'评论\[(\d+)\]', body_text)
            if comment_count_match:
                print(f"\n检测到评论数: {comment_count_match.group(1)}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 60)
    print("微博爬虫Cookie有效性测试")
    print("=" * 60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试微博ID: {TEST_WEIBO_ID}")
    
    # 1. 检查Cookie文件
    print("\n" + "=" * 60)
    print("1. 检查Cookie配置")
    print("-" * 60)
    cookies = load_cookies()
    if cookies:
        print(f"PC端Cookie数量: {len(cookies['pc'])}")
        print(f"移动端Cookie数量: {len(cookies['mobile'])}")
        
        if cookies['mobile']:
            print(f"\n移动端Cookie过期检查:")
            for i, c in enumerate(cookies['mobile']):
                print(f"  Cookie {i+1}: {check_cookie_expiry(c)}")
        
        if cookies['pc']:
            print(f"\nPC端Cookie过期检查:")
            for i, c in enumerate(cookies['pc']):
                print(f"  Cookie {i+1}: {check_cookie_expiry(c)}")
    
    # 2. 直接测试微博网页
    test_direct_weibo_request()
    
    # 2.5 详细分析评论页面
    test_comment_page_detail()
    
    # 3. 测试API服务
    print("\n" + "=" * 60)
    print("2. 测试API服务")
    print("-" * 60)
    
    results = {}
    
    # 测试移动端评论接口
    success, data = test_api_endpoint(
        "statuses_show",
        {"weibo_id": TEST_WEIBO_ID},
        "移动端微博详情+评论接口"
    )
    results["移动端评论"] = (success, data)
    
    # 测试PC端评论接口
    success, data = test_api_endpoint(
        "statuses_show_pc",
        {"weibo_id": TEST_WEIBO_ID},
        "PC端微博详情+评论接口"
    )
    results["PC端评论"] = (success, data)
    
    # 测试用户信息接口
    success, data = test_api_endpoint(
        "users_show",
        {"user_id": "2318910945"},  # 新浪热点的用户ID
        "用户信息接口"
    )
    results["用户信息"] = (success, data)
    
    # 测试搜索接口
    success, data = test_api_endpoint(
        "search_tweets",
        {"keyword": "一栗小莎子", "cursor": "1"},
        "微博搜索接口"
    )
    results["微博搜索"] = (success, data)
    
    # 4. 总结
    print("\n" + "=" * 60)
    print("3. 测试结果总结")
    print("=" * 60)
    
    for name, (success, data) in results.items():
        status = "✓ 成功" if success else "❌ 失败"
        if success and isinstance(data, int):
            print(f"{name}: {status} (数据量: {data})")
        else:
            print(f"{name}: {status}")
    
    # 5. 问题诊断
    print("\n" + "=" * 60)
    print("4. 问题诊断")
    print("=" * 60)
    
    comment_success = results.get("移动端评论", (False, None))[0] or results.get("PC端评论", (False, None))[0]
    comment_count = results.get("移动端评论", (False, 0))[1] if isinstance(results.get("移动端评论", (False, 0))[1], int) else 0
    
    if not comment_success:
        print("❌ 评论接口失败 - 这是导致博文详情页数据为空的根本原因")
        print("   可能原因:")
        print("   1. Cookie已过期，需要重新登录获取")
        print("   2. 微博反爬机制触发，需要等待或更换账号")
        print("   3. weibo_crawler服务未启动")
    elif comment_count == 0:
        print("⚠ 评论接口成功但返回0条评论")
        print("   可能原因:")
        print("   1. 该微博确实没有评论")
        print("   2. 评论被微博隐藏或删除")
        print("   3. Cookie权限不足，无法查看评论")
    else:
        print("✓ 评论接口正常工作")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
