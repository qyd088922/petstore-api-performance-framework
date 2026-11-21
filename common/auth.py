# -*- coding: utf-8 -*-
"""认证层：BaseClient -> 认证 -> 业务 API 的中间层。

功能测试与压测共用同一套认证逻辑；需要换鉴权方式时只改这里。
"""
from config.config import API_KEY


class AuthProvider(object):
    """认证基类：把凭证写入请求头。"""

    def apply(self, session):
        raise NotImplementedError


class ApiKeyAuth(AuthProvider):
    """Swagger Petstore 的 api_key 请求头认证。"""

    def __init__(self, api_key=API_KEY, header="api_key"):
        self.api_key = api_key
        self.header = header

    def apply(self, session):
        session.headers.update({self.header: self.api_key})


class BearerAuth(AuthProvider):
    """预留：Bearer Token 认证，便于接入真实业务系统。"""

    def __init__(self, token, header="Authorization"):
        self.token = token
        self.header = header

    def apply(self, session):
        session.headers.update({self.header: "Bearer %s" % self.token})


class NoAuth(AuthProvider):
    def apply(self, session):
        pass
