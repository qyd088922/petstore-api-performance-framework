# -*- coding: utf-8 -*-
"""测试基类：统一初始化接口对象与通用断言，业务用例只写测试逻辑。"""
import unittest

from api.pet_api import PetApi
from api.store_api import StoreApi
from api.user_api import UserApi
from common.data_factory import DataFactory


class BaseCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pet_api = PetApi()
        cls.store_api = StoreApi()
        cls.user_api = UserApi()
        cls.data = DataFactory()

    def assert_status(self, response, expected=200, msg=None):
        """断言响应状态码，失败时自动带上响应正文便于排查。"""
        self.assertEqual(
            response.status_code, expected,
            msg or ("期望状态码 %s，实际 %s；响应：%s"
                    % (expected, response.status_code, response.text[:500])))

    def assert_body_dict(self, response, msg=None):
        """断言响应体是 JSON 对象。"""
        self.assertIsInstance(
            response.body, dict,
            msg or ("响应体不是 JSON 对象：%s" % response.text[:500]))
