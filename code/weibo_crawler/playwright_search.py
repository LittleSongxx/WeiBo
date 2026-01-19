#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Playwright渲染微博搜索页面，解决SPA问题
"""

import asyncio
import json
import re
from urllib.parse import quote
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


def log(msg):
    """简单的日志函数"""
    print(f"[Playwright] {msg}")


class WeiboPlaywrightSearcher:
    """使用Playwright渲染和爬取微博搜索结果"""

    def __init__(self, cookie):
        self.cookie = cookie
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.playwright = await async_playwright().start()
        # 使用chromium，无头模式
        self.browser = await self.playwright.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        # 创建浏览器上下文
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        # 设置Cookie
        if self.cookie:
            cookies = self._parse_cookie_string(self.cookie)
            await self.context.add_cookies(cookies)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _parse_cookie_string(self, cookie_str):
        """解析Cookie字符串为Playwright格式"""
        cookies = []
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                name, value = item.split("=", 1)
                cookies.append(
                    {
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".weibo.com",
                        "path": "/",
                    }
                )
        return cookies

    async def search_weibo(self, keyword, page=1, is_hot=False):
        """
        搜索微博
        :param keyword: 搜索关键词
        :param page: 页码
        :param is_hot: 是否只看热门
        :return: 微博列表
        """
        # 构建URL
        search_type = "&xsort=hot" if is_hot else ""
        url = f"https://s.weibo.com/weibo?q={quote(keyword)}&typeall=1&suball=1&page={page}{search_type}"

        log(f"正在访问: {url}")

        # 创建新页面
        page_obj = await self.context.new_page()

        try:
            # 访问搜索页面
            await page_obj.goto(url, wait_until="networkidle", timeout=30000)

            # 等待内容加载（等待微博卡片出现）
            try:
                await page_obj.wait_for_selector(".card-wrap", timeout=10000)
            except PlaywrightTimeout:
                log("未找到微博内容，可能需要登录或页面结构变化")
                # 保存页面截图用于调试
                await page_obj.screenshot(path="debug_screenshot.png")
                return []

            # 额外等待一下确保数据完全加载
            await asyncio.sleep(2)

            # 提取页面中的JSON数据
            weibo_list = await self._extract_weibo_from_page(page_obj)

            log(f"成功提取 {len(weibo_list)} 条微博")
            return weibo_list

        except Exception as e:
            log(f"搜索失败: {e}")
            # 保存页面用于调试
            try:
                await page_obj.screenshot(path="error_screenshot.png")
                html_content = await page_obj.content()
                with open("error_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
            except:
                pass
            raise
        finally:
            await page_obj.close()

    async def _extract_weibo_from_page(self, page):
        """从渲染后的页面提取微博数据"""
        weibo_list = []

        # 获取所有微博卡片
        cards = await page.query_selector_all(".card-wrap")
        log(f"找到 {len(cards)} 个卡片")

        for card in cards:
            try:
                weibo = await self._parse_card(card)
                if weibo:
                    weibo_list.append(weibo)
            except Exception as e:
                log(f"解析卡片失败: {e}")
                continue

        return weibo_list

    async def _parse_card(self, card):
        """解析单个微博卡片"""
        weibo = {}

        # 检查是否是微博内容（排除广告等）
        content_div = await card.query_selector(".card-feed .content")
        if not content_div:
            return None

        # 微博ID（从data-mid属性或链接中提取）
        mid_attr = await card.get_attribute("mid")
        if mid_attr:
            weibo["weibo_id"] = mid_attr
        else:
            # 尝试从链接提取
            from_link = await card.query_selector(".from a")
            if from_link:
                href = await from_link.get_attribute("href")
                if href:
                    match = re.search(r"/(\w+)\?", href)
                    if match:
                        weibo["weibo_id"] = match.group(1)

        if not weibo.get("weibo_id"):
            return None

        # 用户信息
        user_link = await content_div.query_selector(".info .name")
        if user_link:
            weibo["screen_name"] = await user_link.inner_text()
            user_href = await user_link.get_attribute("href")
            if user_href:
                weibo["user_id"] = user_href.strip("/").split("/")[-1].split("?")[0]
        else:
            weibo["screen_name"] = ""
            weibo["user_id"] = ""

        # 头像
        avatar = await card.query_selector(".avator img")
        if avatar:
            weibo["head"] = await avatar.get_attribute("src")
        else:
            weibo["head"] = ""

        # 微博内容
        text_elem = await content_div.query_selector(".txt")
        if text_elem:
            weibo["text"] = await text_elem.inner_text()
            weibo["text"] = weibo["text"].strip()
        else:
            weibo["text"] = ""

        # 发布时间和来源
        from_elem = await card.query_selector(".from")
        if from_elem:
            from_text = await from_elem.inner_text()
            # 解析时间
            parts = from_text.split("\xa0")
            if len(parts) >= 1:
                weibo["created_at"] = parts[0].strip()
                try:
                    weibo["created_at"] = str(weibo["created_at"])
                except:
                    pass
            if len(parts) >= 2:
                weibo["source"] = parts[1].strip()
            else:
                weibo["source"] = ""
        else:
            weibo["created_at"] = ""
            weibo["source"] = ""

        # 互动数据（转发、评论、点赞）
        weibo["reposts_count"] = await self._extract_count(
            card, ".card-act ul li:nth-child(2)"
        )
        weibo["comments_count"] = await self._extract_count(
            card, ".card-act ul li:nth-child(3)"
        )
        weibo["attitudes_count"] = await self._extract_count(
            card, ".card-act ul li:nth-child(4)"
        )

        # 图片
        pics = []
        pic_elements = await card.query_selector_all(".media-box img")
        for pic in pic_elements:
            src = await pic.get_attribute("src")
            if src and "jpg" in src:
                # 将缩略图转为大图
                pics.append(src.replace("thumbnail", "large"))
        weibo["pics"] = pics

        # 视频
        video_elem = await card.query_selector("video")
        if video_elem:
            video_src = await video_elem.get_attribute("src")
            weibo["video_url"] = video_src or ""
        else:
            weibo["video_url"] = ""

        return weibo

    async def _extract_count(self, card, selector):
        """提取互动数量"""
        elem = await card.query_selector(selector)
        if elem:
            text = await elem.inner_text()
            # 提取数字
            match = re.search(r"(\d+)", text)
            if match:
                return match.group(1)
        return "0"


def sync_search_weibo(keyword, page=1, is_hot=False, cookie=""):
    """
    同步包装器，用于在Tornado中调用
    :param keyword: 搜索关键词
    :param page: 页码
    :param is_hot: 是否只看热门
    :param cookie: Cookie字符串
    :return: 微博列表
    """
    import nest_asyncio

    nest_asyncio.apply()

    async def _async_search():
        async with WeiboPlaywrightSearcher(cookie) as searcher:
            return await searcher.search_weibo(keyword, page, is_hot)

    # 获取或创建事件循环
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_search())


# 测试代码
if __name__ == "__main__":
    from account.account import account_pool

    # 获取Cookie
    cookie, _ = account_pool.fetch()

    # 测试搜索
    print("开始测试Playwright搜索...")
    results = sync_search_weibo("春节", page=1, cookie=cookie)

    print(f"\n成功获取 {len(results)} 条微博")
    if results:
        print("\n第一条微博:")
        first = results[0]
        for key, value in first.items():
            if key == "text":
                print(f"  {key}: {value[:50]}...")
            elif key == "pics":
                print(f"  {key}: {len(value)} 张图片")
            else:
                print(f"  {key}: {value}")
