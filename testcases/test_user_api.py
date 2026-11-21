# -*- coding: utf-8 -*-
"""User 接口测试用例。"""
from testcases.base_case import BaseCase


class TestUserApi(BaseCase):

    def _create_temp_user(self):
        """创建用户并注册用例结束后的清理动作，返回 (user_id, username, payload)。"""
        payload = self.data.user_payload()
        resp = self.user_api.create_user(payload)
        self.assert_status(resp)
        self.addCleanup(self.user_api.delete_user, payload["username"])
        return payload

    def test_01_create_and_get_user(self):
        """创建用户后按用户名查询"""
        payload = self._create_temp_user()

        resp = self.user_api.get_user(payload["username"])
        self.assert_status(resp)
        self.assert_body_dict(resp)
        self.assertEqual(resp.body["username"], payload["username"])
        self.assertEqual(resp.body["email"], payload["email"])

    def test_02_login_and_logout(self):
        """用户登录与登出"""
        payload = self._create_temp_user()

        login = self.user_api.login(payload["username"], payload["password"])
        self.assert_status(login)
        self.assertIn("logged in user session", login.body.get("message", ""))

        logout = self.user_api.logout()
        self.assert_status(logout)
        self.assertEqual(logout.body.get("message"), "ok")

    def test_03_update_user(self):
        """修改用户信息并验证生效"""
        payload = self._create_temp_user()
        payload["firstName"] = "Changed"

        resp = self.user_api.update_user(payload["username"], payload)
        self.assert_status(resp)

        fetched = self.user_api.get_user(payload["username"])
        self.assert_status(fetched)
        self.assertEqual(fetched.body["firstName"], "Changed")

    def test_04_delete_user(self):
        """删除用户"""
        payload = self.data.user_payload()
        self.assert_status(self.user_api.create_user(payload))

        resp = self.user_api.delete_user(payload["username"])
        self.assert_status(resp)
        self.assertEqual(payload["username"], resp.body.get("message"))
