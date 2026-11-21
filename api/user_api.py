# -*- coding: utf-8 -*-
"""User 用户接口封装（Swagger 中的 /user 分组）。"""
from common.base_client import BaseClient


class UserApi(BaseClient):
    def create_user(self, payload):
        return self.post("/user", payload=payload)

    def create_users_with_list(self, users):
        return self.post("/user/createWithList", payload=users)

    def login(self, username, password):
        return self.get("/user/login", params={"username": username, "password": password})

    def logout(self):
        return self.get("/user/logout")

    def get_user(self, username):
        return self.get("/user/%s" % username)

    def update_user(self, username, payload):
        return self.put("/user/%s" % username, payload=payload)

    def delete_user(self, username):
        return self.delete("/user/%s" % username)
