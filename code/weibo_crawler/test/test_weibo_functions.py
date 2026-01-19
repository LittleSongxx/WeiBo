#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微博爬虫单元测试
运行方法: pytest test_weibo_functions.py -v
或: python -m pytest test_weibo_functions.py -v
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
try:
    from web_curl import SpiderAim, curl_result_to_api_result
    from weibo_curl_error import (
        WeiboCurlError,
        CookieInvalidException,
        HTMLParseException,
    )
    import settings
    from utils import report_log
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在weibo_crawler目录下运行测试")


class TestSettings(unittest.TestCase):
    """测试配置模块"""

    def test_port_number(self):
        """测试端口配置"""
        self.assertIsInstance(settings.PORT_NUM, int)
        self.assertGreater(settings.PORT_NUM, 0)
        self.assertLess(settings.PORT_NUM, 65536)

    def test_retry_time(self):
        """测试重试次数配置"""
        self.assertIsInstance(settings.RETRY_TIME, int)
        self.assertGreater(settings.RETRY_TIME, 0)

    def test_headers(self):
        """测试请求头配置"""
        self.assertIn("User-Agent", settings.HEADERS)
        self.assertIsInstance(settings.HEADERS, dict)

    def test_success_format(self):
        """测试成功响应格式"""
        self.assertIn("error_code", settings.SUCCESS)
        self.assertIn("data", settings.SUCCESS)
        self.assertIn("error_msg", settings.SUCCESS)
        self.assertEqual(settings.SUCCESS["error_code"], 0)


class TestWeiboCurlError(unittest.TestCase):
    """测试错误处理模块"""

    def test_error_structure(self):
        """测试错误结构"""
        for attr in dir(WeiboCurlError):
            if not attr.startswith("_"):
                error = getattr(WeiboCurlError, attr)
                if isinstance(error, dict):
                    self.assertIn("error_code", error)
                    self.assertIn("error_msg", error)

    def test_cookie_invalid_exception(self):
        """测试Cookie无效异常"""
        with self.assertRaises(CookieInvalidException):
            raise CookieInvalidException("Test cookie invalid")

    def test_html_parse_exception(self):
        """测试HTML解析异常"""
        with self.assertRaises(HTMLParseException):
            raise HTMLParseException("Test parse error")


class TestSpiderAim(unittest.TestCase):
    """测试爬虫目标枚举"""

    def test_spider_aim_values(self):
        """测试爬虫目标值"""
        # 根据实际的SpiderAim定义进行测试
        self.assertTrue(hasattr(SpiderAim, "__members__"))


class TestCurlResultToApiResult(unittest.TestCase):
    """测试结果转换函数"""

    def test_success_result(self):
        """测试成功结果转换"""
        curl_result = {"error_code": 0, "response": {"data": "test"}}
        api_result = curl_result_to_api_result(curl_result)
        self.assertIsInstance(api_result, dict)

    def test_error_result(self):
        """测试错误结果转换"""
        curl_result = {"error_code": 1001, "error_msg": "Test error"}
        api_result = curl_result_to_api_result(curl_result)
        self.assertIsInstance(api_result, dict)
        self.assertIn("error_code", api_result)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n开始集成测试...")

    def test_import_modules(self):
        """测试模块导入"""
        modules = [
            "web_curl",
            "weibo_curl_error",
            "settings",
            "utils",
            "request_builder",
        ]
        for module_name in modules:
            try:
                __import__(module_name)
                self.assertTrue(True)
            except ImportError:
                self.fail(f"无法导入模块: {module_name}")

    def test_settings_consistency(self):
        """测试配置一致性"""
        # 确保超时时间合理
        self.assertGreater(settings.REQUEST_TIME_OUT, 0)
        self.assertLess(settings.REQUEST_TIME_OUT, 60)

        # 确保重试次数合理
        self.assertGreaterEqual(settings.RETRY_TIME, 1)
        self.assertLessEqual(settings.RETRY_TIME, 10)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSettings))
    suite.addTests(loader.loadTestsFromTestCase(TestWeiboCurlError))
    suite.addTests(loader.loadTestsFromTestCase(TestSpiderAim))
    suite.addTests(loader.loadTestsFromTestCase(TestCurlResultToApiResult))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回是否全部通过
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
