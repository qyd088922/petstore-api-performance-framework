# -*- coding: utf-8 -*-
"""WebSocket 压测客户端：基于 websocket-client 的 WebSocketApp + gevent 协程。

每个 Locust User 持有一个长连接，覆盖四类 WS 场景：
1. 连接容量：connect 成功/失败上报 ws:connect，统计在线连接数。
2. 断连重连：可主动断链并自动重连，重连耗时单独计入指标。
3. 消息端到端延迟：发送带客户端时戳的报文，回包带回服务端时戳，测 RTT+处理耗时。
4. 协议层 Ping/Pong RTT：发 Ping 控制帧，WebSocketApp 的 on_pong 回调结算 RTT。

run_forever 在 gevent greenlet 中运行；monkey.patch_all 已使 socket 协作化，
单机可支撑大量长连接协程。所有场景统一通过 PerfReporter 桥接进 Locust 统计。
"""
import json
import time

import gevent
import websocket  # websocket-client

from common.logger import get_logger
from config.perf_config import WS_URL

log = get_logger("petstore.ws")


class WSClient(object):
    def __init__(self, reporter, url=WS_URL):
        self.reporter = reporter
        self.url = url
        self.app = None
        self._greenlet = None
        self._connected = False
        self._echo_send_ts = {}       # seq -> send_ts
        self._ping_send_ts = {}       # token -> send_ts
        self._seq = 0

    # ---- 回调 ----
    def _on_open(self, ws):
        self._connected = True

    def _on_message(self, ws, message):
        try:
            payload = json.loads(message)
            seq = payload.get("seq")
            send_ts = self._echo_send_ts.pop(seq, None)
            if send_ts is not None:
                elapsed = (time.perf_counter() - send_ts) * 1000
                self.reporter.report("WS_ECHO", "ws:echo_e2e", elapsed,
                                     len(message), exception=None)
        except Exception as err:  # noqa: BLE001
            self.reporter.report("WS_ECHO", "ws:echo_e2e", 0, 0, exception=err)

    def _on_pong(self, ws, data):
        token = data.decode() if isinstance(data, bytes) else str(data)
        send_ts = self._ping_send_ts.pop(token, None)
        if send_ts is not None:
            rtt = (time.perf_counter() - send_ts) * 1000
            self.reporter.report("WS_PING", "ws:pingpong_rtt", rtt, len(data))

    def _on_error(self, ws, error):
        log.debug("WS error: %s", error)

    def _on_close(self, ws, *args):
        self._connected = False

    def _build_app(self):
        return websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_pong=self._on_pong,
            on_error=self._on_error,
            on_close=self._on_close,
        )

    # ---- 连接容量 / 断连重连 ----
    def connect(self):
        """建立长连接并把连接耗时上报为一次 ws:connect 事件。"""
        start = time.perf_counter()
        exc = None
        self.app = self._build_app()
        try:
            self._greenlet = gevent.spawn(
                self.app.run_forever, ping_interval=None, reconnect=0)
            # 等待 on_open 回调置位（最多 5 秒）
            deadline = time.perf_counter() + 5
            while not self._connected and time.perf_counter() < deadline:
                gevent.sleep(0.01)
            if not self._connected:
                exc = Exception("WS connect timeout")
        except Exception as err:  # noqa: BLE001
            exc = err
        self.reporter.report("WS_CONNECT", "ws:connect",
                             (time.perf_counter() - start) * 1000, 0, exception=exc)
        return self._connected

    def reconnect(self):
        """断连后重连，重连耗时单独上报，计入断连重连场景指标。"""
        self.close()
        return self.connect()

    def close(self):
        if self.app is not None:
            try:
                self.app.close()
            except Exception:  # noqa: BLE001
                pass
        if self._greenlet:
            self._greenlet.kill(block=False)
        self.app = None
        self._connected = False
        self._echo_send_ts.clear()
        self._ping_send_ts.clear()

    @property
    def connected(self):
        return self._connected

    # ---- 消息端到端延迟 ----
    def send_echo(self):
        """发送带客户端时戳的报文，由 on_message 回调结算端到端延迟。"""
        if not self.connected:
            self.reporter.report("WS_ECHO", "ws:echo_e2e", 0, 0,
                                 exception=Exception("WS not connected"))
            return
        self._seq += 1
        send_ts = time.perf_counter()
        self._echo_send_ts[self._seq] = send_ts
        try:
            self.app.send(json.dumps({"seq": self._seq, "client_ts": send_ts}))
        except Exception as err:  # noqa: BLE001
            self._echo_send_ts.pop(self._seq, None)
            self.reporter.report("WS_ECHO", "ws:echo_e2e", 0, 0, exception=err)

    # ---- 协议层 Ping/Pong RTT ----
    def send_ping(self):
        """发送 WebSocket Ping 控制帧，由 on_pong 回调结算 RTT。"""
        if not self.connected:
            return
        token = "ping-%d" % int(time.perf_counter() * 1000000)
        self._ping_send_ts[token] = time.perf_counter()
        try:
            self.app.sock.ping(token)
        except Exception as err:  # noqa: BLE001
            self._ping_send_ts.pop(token, None)
            self.reporter.report("WS_PING", "ws:pingpong_rtt", 0, 0, exception=err)
