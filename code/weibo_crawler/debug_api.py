#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试工具 - 查看实际的API响应内容
帮助定位HTML解析失败的具体原因
"""
import json
import requests
from datetime import datetime


def load_cookie():
    """加载Cookie"""
    try:
        with open("account/account.json", "r") as f:
            config = json.load(f)
        cookies = config.get("cookies", [])
        if not cookies:
            print("❌ account.json中没有Cookie配置")
            return None
        return cookies[0]
    except Exception as e:
        print(f"❌ 读取Cookie失败: {e}")
        return None


def test_weibo_cn(cookie):
    """测试weibo.cn主页"""
    print("\n" + "=" * 80)
    print(" 测试1: weibo.cn 主页")
    print("=" * 80)

    url = "https://weibo.cn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": cookie,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"实际URL: {response.url}")
        print(f"响应长度: {len(response.text)} 字符")

        html = response.text

        # 检查关键内容
        checks = {
            "包含'我的首页'": "我的首页" in html,
            "包含'退出'": "退出" in html,
            "包含'消息'": "消息" in html,
            "包含'登录'": "登录" in html,
            "包含'验证码'": "验证码" in html or "verify" in html.lower(),
            "被重定向": response.url != url,
        }

        print("\n内容检查:")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")

        # 显示前500字符
        print(f"\n页面内容预览（前500字符）:")
        print("-" * 80)
        print(html[:500])
        print("-" * 80)

        # 判断Cookie状态
        if "我的首页" in html or "退出" in html:
            print("\n✅ Cookie有效！已登录状态")
            return True
        elif "登录" in html:
            print("\n❌ Cookie无效！页面显示未登录")
            return False
        elif "验证码" in html or "verify" in html.lower():
            print("\n❌ 需要验证码！可能触发了安全检测")
            return False
        else:
            print("\n⚠️  无法确定登录状态，请查看页面预览")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_search_api(cookie):
    """测试搜索API（代码实际使用的接口）"""
    print("\n" + "=" * 80)
    print(" 测试2: 搜索API (s.weibo.com)")
    print("=" * 80)

    # 这是代码中实际使用的搜索URL
    keyword = "测试"
    page = 1
    url = f"https://s.weibo.com/weibo?page={page}&q={keyword}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://s.weibo.com/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"实际URL: {response.url}")
        print(f"响应长度: {len(response.text)} 字符")

        html = response.text

        # 检查关键内容
        checks = {
            "包含'搜索'": "搜索" in html,
            "包含微博数据": "card-wrap" in html or "card" in html,
            "包含'登录'": "登录" in html,
            "包含'验证码'": "验证码" in html or "verify" in html.lower(),
            "包含JavaScript": "<script" in html,
            "是否为空页面": len(html.strip()) < 100,
        }

        print("\n内容检查:")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")

        # 显示前800字符
        print(f"\n页面内容预览（前800字符）:")
        print("-" * 80)
        print(html[:800])
        print("-" * 80)

        # 保存到文件供详细查看
        debug_file = "debug_search_response.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n完整响应已保存到: {debug_file}")

        # 判断
        if "card-wrap" in html or ("搜索" in html and len(html) > 5000):
            print("\n✅ 搜索API返回正常数据")
            return True
        elif "登录" in html:
            print("\n❌ 需要登录！Cookie可能无效")
            return False
        elif "验证码" in html or "verify" in html.lower():
            print("\n❌ 需要验证码！")
            return False
        else:
            print("\n⚠️  返回了异常内容，请查看 debug_search_response.html")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_mobile_search(cookie):
    """测试移动端搜索API"""
    print("\n" + "=" * 80)
    print(" 测试3: 移动端搜索API (m.weibo.cn)")
    print("=" * 80)

    url = "https://m.weibo.cn/api/container/getIndex"
    params = {"containerid": "100103type=1&q=测试", "page_type": "searchall"}

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Cookie": cookie,
        "Referer": "https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D测试",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"URL: {url}")
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)} 字符")

        # 尝试解析JSON
        try:
            data = response.json()
            print("\n✅ 返回的是JSON格式")
            print(
                f"JSON结构: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}..."
            )

            if data.get("ok") == 1:
                print("\n✅ API返回成功！")
                if "data" in data and "cards" in data["data"]:
                    print(f"   返回了 {len(data['data']['cards'])} 个数据卡片")
                return True
            else:
                print(f"\n❌ API返回错误: {data.get('msg', '未知错误')}")
                return False

        except json.JSONDecodeError:
            print("\n❌ 返回的不是JSON格式")
            print(f"内容预览: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def analyze_cookie(cookie):
    """分析Cookie内容"""
    print("\n" + "=" * 80)
    print(" Cookie分析")
    print("=" * 80)

    print(f"Cookie长度: {len(cookie)} 字符")

    # 解析字段
    fields = {}
    for item in cookie.split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key.strip()] = value.strip()

    print(f"字段数量: {len(fields)}")

    # 检查关键字段
    required = ["SUB", "SUBP"]
    recommended = ["SCF", "_T_WM", "XSRF-TOKEN"]

    print("\n关键字段检查:")
    for field in required:
        if field in fields:
            print(f"  ✅ {field}: {fields[field][:40]}...")
        else:
            print(f"  ❌ {field}: 缺失")

    print("\n推荐字段:")
    for field in recommended:
        if field in fields:
            print(f"  ✅ {field}")
        else:
            print(f"  ⚠️  {field}: 缺失")

    # 检查Cookie来源
    print("\n可能的Cookie来源判断:")
    if "WEIBOCN_FROM" in fields or "M_WEIBOCN_PARAMS" in fields:
        print("  ✅ 可能来自 weibo.cn 或 m.weibo.cn（移动版）")
    elif "UOR" in fields or "login_sid_t" in fields:
        print("  ⚠️  可能来自 weibo.com（桌面版）- 可能不兼容！")
    else:
        print("  ？ 无法确定来源")


def main():
    """主函数"""
    print("=" * 80)
    print(" 微博爬虫调试工具")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 加载Cookie
    cookie = load_cookie()
    if not cookie:
        return

    # 分析Cookie
    analyze_cookie(cookie)

    # 测试各个接口
    test1 = test_weibo_cn(cookie)
    test2 = test_search_api(cookie)
    test3 = test_mobile_search(cookie)

    # 总结
    print("\n" + "=" * 80)
    print(" 诊断总结")
    print("=" * 80)

    results = {
        "weibo.cn主页": test1,
        "搜索API (s.weibo.com)": test2,
        "移动API (m.weibo.cn)": test3,
    }

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {test_name}")

    print()

    if not any(results.values()):
        print("🔴 所有测试都失败了！")
        print("\n可能的原因:")
        print("1. Cookie已过期 - 需要重新登录获取")
        print("2. Cookie来源错误 - 必须从 weibo.cn 获取")
        print("3. Cookie格式错误 - 检查是否完整")
        print("4. 网络问题 - 检查能否访问微博")
        print("5. IP被封 - 可能需要配置代理")
        print("\n建议操作:")
        print("1. 重新从 https://weibo.cn 登录并获取Cookie")
        print("2. 运行: python check_cookie_format.py 验证格式")
        print("3. 更新 account/account.json")
        print("4. 重新测试: python test_crawler.py --mode quick")
    elif test1 and not test2:
        print("🟡 主页正常但搜索失败")
        print("\n可能的原因:")
        print("1. s.weibo.com 的Cookie域名问题")
        print("2. 搜索接口需要额外的验证")
        print("3. 选择器解析器需要更新")
        print("\n查看详细内容: debug_search_response.html")
    elif all(results.values()):
        print("🟢 所有测试通过！")
        print("\n如果爬虫还是失败，可能是:")
        print("1. 选择器解析器与页面结构不匹配")
        print("2. 需要等待JavaScript加载")
        print("3. 查看 debug_search_response.html 了解实际返回内容")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback

        traceback.print_exc()
