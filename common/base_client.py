# -*- coding: utf-8 -*-
"""统一服务层 BaseClient。

    BaseClient  ->  认证(AuthProvider)  ->  业务 API(PetApi/StoreApi/UserApi)

功能测试与压测复用同一个客户端、同一套业务 API 方法：
- 功能测试：构造 PetApi() 或 PetApi(reporter=None)，不 fire Locust 事件，断言响应。
- 压测：Locust User 构造 PetApi(reporter=PerfReporter(environment))，
        同一方法调用自动把 perf_counter 耗时桥接进 Locust 统计。

压测约束：
- 禁用重试（retry 次数为 0），失败立即暴露，失败率与延迟不被重试掩盖。
- 以"业务码"判定失败：HTTP 200 但 body.code 非成功码，同样记为失败。
"""
from requests.adapters import HTTPAdapter

from common.auth import ApiKeyAuth
from common.base_api import ApiResponse, BaseApi
from common.logger import get_logger
from common.perf_bridge import BusinessError, PerfReporter, Timer
from config.config import API_KEY, HOST, TIMEOUT
from config.perf_config import BIZ_CODE_SUCCESS, DISABLE_RETRY

log = get_logger("petstore.client")


class BaseClient(BaseApi):
    """在 BaseApi 的请求能力之上叠加：认证、埋点、业务码判定、重试策略。"""

    def __init__(self, host=HOST, timeout=TIMEOUT, auth=None, reporter=None,
                 disable_retry=None, name_resolver=None):
        super().__init__(host=host, timeout=timeout)
        # 认证层：默认 ApiKeyAuth，功能/压测一致
        self.auth = auth if auth is not None else ApiKeyAuth(API_KEY)
        self.auth.apply(self.session)

        # 重试策略：压测默认关闭，保证数据真实
        self.disable_retry = DISABLE_RETRY if disable_retry is None else disable_retry
        retries = 0 if self.disable_retry else 2
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 指标桥接：功能测试为 PerfReporter.disabled()，压测注入真实 reporter
        self.reporter = reporter if reporter is not None else PerfReporter.disabled()
        if self.reporter.enabled and name_resolver:
            self.reporter.name_resolver = name_resolver

        self._last_elapsed_ms = 0.0

    def request(self, method, path, params=None, payload=None,
                data=None, files=None, headers=None, check_biz=True):
        """统一请求入口：返回 ApiResponse，并上报一次 Locust 指标。"""
        url = path if path.startswith("http") else self.host + path
        exception = None
        result = None

        with Timer() as timer:
            try:
                raw = self.session.request(
                    method=method.upper(), url=url, params=params, json=payload,
                    data=data, files=files, headers=headers, timeout=self.timeout)
                result = ApiResponse(raw)
                if check_biz:
                    self._check_business(result, method, path)
            except Exception as exc:  # noqa: BLE001 - 压测需捕获一切异常记为失败
                exception = exc

        self._last_elapsed_ms = timer.elapsed_ms
        response_length = len(result.raw.content) if result is not None else 0
        self.reporter.report(method, path, self._last_elapsed_ms,
                             response_length, exception=exception, response=result)

        if exception is not None:
            # 网络异常/业务码失败：压测已被记为失败；功能测试期望拿到响应来断言，
            # 因此业务码失败不抛出（响应里有 code 可供断言），仅网络异常抛出。
            if result is None:
                raise exception
        return result

    @staticmethod
    def _check_business(result, method, path):
        """以业务码判定失败：HTTP 2xx 不代表业务成功。"""
        body = result.body
        if isinstance(body, dict) and "code" in body:
            code = body.get("code")
            if code not in BIZ_CODE_SUCCESS:
                raise BusinessError(
                    "业务码异常 code=%s on %s %s" % (code, method, path), body=body)
        if not result.ok:
            raise BusinessError(
                "HTTP 状态码异常 %s on %s %s" % (result.status_code, method, path),
                body=body)
