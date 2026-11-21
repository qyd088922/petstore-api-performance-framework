# -*- coding: utf-8 -*-
"""pytest 功能用例：Store 与 User 模块（Allure 注解）。"""
import allure

from common.data_factory import DataFactory


@allure.feature("Store 商店模块")
class TestStoreApi:

    @allure.story("库存查询")
    def test_get_inventory(self, store_api):
        resp = store_api.get_inventory()
        assert resp.status_code == 200
        assert isinstance(resp.body, dict)
        assert len(resp.body) > 0

    @allure.story("下单与回查")
    def test_place_and_get_order(self, store_api):
        oid = DataFactory.unique_id()
        payload = DataFactory.order_payload(oid, quantity=2)
        store_api.place_order(payload)
        try:
            resp = store_api.get_order(oid)
            assert resp.status_code == 200
            assert resp.body["quantity"] == 2
        finally:
            store_api.delete_order(oid)


@allure.feature("User 用户模块")
class TestUserApi:

    @allure.story("登录")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login(self, user_api):
        resp = user_api.login("foo", "bar")
        assert resp.status_code == 200
        assert "logged in" in resp.body["message"]

    @allure.story("创建与删除")
    def test_create_and_delete(self, user_api):
        payload = DataFactory.user_payload()
        user_api.create_user(payload)
        resp = user_api.delete_user(payload["username"])
        assert resp.status_code == 200
        assert resp.body["message"] == payload["username"]
