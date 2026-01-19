from lxml import etree
import json


class BaseParser:
    def __init__(self, response=None):
        """保存response于属性中，同时将response转化成selector"""
        self.response = response
        if response is not None:
            # 如果response是字符串（可能是JSON或HTML）
            if isinstance(response, str):
                # 尝试作为HTML解析（如果失败，子类可以尝试作为JSON）
                try:
                    self.selector = etree.HTML(response)
                except:
                    self.selector = None
            # 如果response是response对象
            elif hasattr(response, "body"):
                try:
                    self.selector = etree.HTML(response.body)
                except:
                    self.selector = None
            else:
                self.selector = None
        else:
            self.selector = None
