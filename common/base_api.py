# -*- coding: utf-8 -*-
"""HTTP 请求统一封装层。

所有业务接口均继承 BaseApi，只关心"调用哪个路径、传什么参数"，
host、超时、鉴权、日志、响应解析等公共逻辑在这里统一处理。
"""
import time

import requests

from common.logger import get_logger
from config.config import API_KEY, HOST, TIMEOUT, VERBOSE_LOG

log = get_logger("petstore.api")


class ApiResponse(object):
    """对 requests.Response 的轻封装，提供统一、易断言的读取接口。"""

    def __init__(self, response):
        self.raw = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.text = response.text
        try:
            self.body = response.json()
        except ValueError:
            self.body = None

    @property
    def ok(self):
        """2xx 即成功。"""
        return 200 <= self.status_code < 300

    def get(self, key, default=None):
        """安全读取 JSON 字典字段。"""
        if isinstance(self.body, dict):
            return self.body.get(key, default)
        return default

    def __repr__(self):
        return "<ApiResponse %s %s>" % (self.status_code, str(self.body)[:160])


class BaseApi(object):
    """所有接口类的基类：封装 session、请求发送与响应处理。"""

    def __init__(self, host=HOST, timeout=TIMEOUT, api_key=API_KEY):
        self.host = host.rstrip("/")
        self.timeout = timeout
        # 复用连接，提升批量执行速度
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if api_key:
            self.session.headers.update({"api_key": api_key})

    def request(self, method, path, params=None, payload=None,
                data=None, files=None, headers=None):
        """统一请求入口，返回 ApiResponse。

        :param method: HTTP 方法
        :param path: 接口路径（也支持完整 URL）
        :param params: URL 查询参数
        :param payload: JSON 请求体
        :param data: 表单请求体
        :param files: 上传文件（multipart）
        :param headers: 本次请求额外请求头
        """
        url = path if path.startswith("http") else self.host + path
        log.info(">>> %s %s | params=%s | body=%s",
                 method.upper(), url, params,
                 payload if payload is not None else data)

        start = time.time()
        try:
            raw = self.session.request(
                method=method.upper(), url=url, params=params, json=payload,
                data=data, files=files, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            log.error("!!! 请求异常 %s %s : %s", method.upper(), url, exc)
            raise

        cost_ms = (time.time() - start) * 1000
        result = ApiResponse(raw)
        log.info("<<< %s %s | %.0fms | status=%s | body=%s",
                 method.upper(), url, cost_ms, result.status_code,
                 result.text[:500] if VERBOSE_LOG else "<已省略>")
        return result

    # ---- HTTP 动词快捷方法 ----
    def get(self, path, params=None, headers=None):
        return self.request("GET", path, params=params, headers=headers)

    def post(self, path, payload=None, data=None, files=None, headers=None):
        return self.request("POST", path, payload=payload, data=data,
                            files=files, headers=headers)

    def put(self, path, payload=None, data=None, headers=None):
        return self.request("PUT", path, payload=payload, data=data, headers=headers)

    def delete(self, path, params=None, headers=None):
        return self.request("DELETE", path, params=params, headers=headers)
