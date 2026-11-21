# -*- coding: utf-8 -*-
"""Locust 压测入口：HTTP + WebSocket 多协议，统一负载模型。

运行示例（无头）：
    locust -f perf/locustfile.py --headless -u 40 -r 5 -t 30s \
        --html reports/locust_report.html

负载模型通过 PERF_SHAPE 环境变量切换：sine / step / multi（见 perf/shapes.py）。
"""
import gevent  # noqa: F401
from locust import User, task, events

from api.pet_api import PetApi
from api.store_api import StoreApi
from api.user_api import UserApi
from common.perf_bridge import PerfReporter
from config.perf_config import HTTP_HOST, SHAPE
from perf.ws_client import WSClient
from perf.shapes import SineShape, StepShape, MultiWaveShape


def interface_name(method, path):
    """把具体路径归一化为接口级名称，保证 P99 能定位到接口级别。"""
    import re
    name = re.sub(r"/\d+(?=\b|/)", "/{id}", path)
    return "%s %s" % (method.upper(), name)


class PetstoreHttpUser(User):
    """HTTP 压测用户：直接复用功能测试的同一套业务 API 方法。"""

    weight = 3

    def __init__(self, environment):
        super().__init__(environment)
        reporter = PerfReporter(environment, name_resolver=interface_name)
        self.pet = PetApi(host=HTTP_HOST, reporter=reporter)
        self.store = StoreApi(host=HTTP_HOST, reporter=reporter)
        self.user = UserApi(host=HTTP_HOST, reporter=reporter)

    @task(3)
    def find_pets(self):
        self.pet.find_pets_by_status("available")

    @task(2)
    def get_inventory(self):
        self.store.get_inventory()

    @task(1)
    def get_pet_detail(self):
        listed = self.pet.find_pets_by_status("available")
        if listed is not None and isinstance(listed.body, list) and listed.body:
            self.pet.get_pet(listed.body[0]["id"])

    @task(1)
    def login(self):
        self.user.login("foo", "bar")


class WebSocketUser(User):
    """WebSocket 长连接用户：gevent 协程驱动，覆盖连接/重连/延迟/PingPong。"""

    weight = 1

    def __init__(self, environment):
        super().__init__(environment)
        self.reporter = PerfReporter(environment)
        self.client = WSClient(self.reporter)

    def on_start(self):
        self.client.connect()

    def on_stop(self):
        self.client.close()

    @task(4)
    def echo_latency(self):
        self.client.send_echo()

    @task(2)
    def pingpong_rtt(self):
        self.client.send_ping()

    @task(1)
    def reconnect_flow(self):
        # 断连重连场景：低频触发，避免影响主连接容量指标
        self.client.reconnect()


# ---- 根据环境切换负载模型 ----
_SHAPES = {"sine": SineShape, "step": StepShape, "multi": MultiWaveShape}
LoadTestShape = _SHAPES.get(SHAPE, StepShape)
