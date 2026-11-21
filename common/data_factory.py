# -*- coding: utf-8 -*-
"""测试数据工厂：统一构造动态数据，避免多次执行时数据冲突。"""
import os
import tempfile
import time


class DataFactory(object):
    """所有测试数据的生成入口。"""

    @staticmethod
    def unique_id():
        """基于毫秒时间戳生成唯一 ID（Petstore 使用 int64 类型的 id）。"""
        return int(time.time() * 1000) % 1000000000

    @staticmethod
    def pet_payload(pet_id=None, name=None, status="available"):
        pet_id = pet_id if pet_id is not None else DataFactory.unique_id()
        return {
            "id": pet_id,
            "name": name or ("auto_pet_%s" % pet_id),
            "photoUrls": ["https://example.com/pet.png"],
            "tags": [{"id": 1, "name": "automation"}],
            "status": status,
        }

    @staticmethod
    def order_payload(order_id=None, pet_id=1, quantity=1, status="placed"):
        order_id = order_id if order_id is not None else DataFactory.unique_id()
        return {
            "id": order_id,
            "petId": pet_id,
            "quantity": quantity,
            "shipDate": "2026-01-01T00:00:00.000Z",
            "status": status,
            "complete": False,
        }

    @staticmethod
    def user_payload(user_id=None, username=None, email=None):
        user_id = user_id if user_id is not None else DataFactory.unique_id()
        return {
            "id": user_id,
            "username": username or ("autouser%s" % user_id),
            "firstName": "Auto",
            "lastName": "Test",
            "email": email or ("auto%s@example.com" % user_id),
            "password": "123456",
            "phone": "13800000000",
            "userStatus": 1,
        }

    @staticmethod
    def temp_image():
        """生成用于上传测试的临时 PNG 文件，返回绝对路径。"""
        path = os.path.join(
            tempfile.gettempdir(), "petstore_auto_%s.png" % DataFactory.unique_id())
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        return path
