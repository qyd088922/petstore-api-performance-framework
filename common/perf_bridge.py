# -*- coding: utf-8 -*-
"""指标桥接层：把业务请求耗时接入 Locust 统计。

关键设计：
- 用 time.perf_counter（单调时钟）做客户端耗时埋点，覆盖"请求发出 -> 响应解析完"的完整时间。
- 只有压测模式下才 fire(events.request)，功能测试模式 reporter=None，完全静默。
- 失败判定以"业务码"为准，而不只看 HTTP 状态码；压测禁用重试，保证失败率与 P99 真实。
"""
import time

from common.logger import get_logger

log = get_logger("petstore.perf")


class BusinessError(Exception):
    """业务码非成功时抛出，供 Locust 记为失败。"""

    def __init__(self, message, body=None):
        super().__init__(message)
        self.body = body


class PerfReporter(object):
    """把一次请求结果投递给 Locust 的 events.request。

    :param environment: Locust Environment 实例（压测时有，功能测试时 None）
    :param name_resolver: 可选 callable(method, path) -> 统计名称，用于接口级聚合
    """

    def __init__(self, environment, name_resolver=None):
        self.environment = environment
        self.name_resolver = name_resolver

    @classmethod
    def disabled(cls):
        return cls(environment=None)

    @property
    def enabled(self):
        return self.environment is not None

    def report(self, method, path, response_time_ms, response_length,
               exception=None, response=None):
        if not self.enabled:
            return
        name = self.name_resolver(method, path) if self.name_resolver else path
        self.environment.events.request.fire(
            request_type=method.upper(),
            name=name,
            response_time=response_time_ms,
            response_length=response_length,
            exception=exception,
            response=response,
        )


class Timer(object):
    """perf_counter 计时上下文，退出时得到毫秒耗时。"""

    def __init__(self):
        self.elapsed_ms = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        return False
