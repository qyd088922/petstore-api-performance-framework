# -*- coding: utf-8 -*-
"""本地 WebSocket echo 服务，作为压测靶标。

Swagger Petstore 不提供 WebSocket 接口，因此用本地 echo server 承担 WS 压测：
可真实测量连接容量、断连重连、消息端到端延迟、协议层 Ping/Pong RTT。

启动：python -m perf.ws_echo_server
"""
from gevent import monkey

monkey.patch_all()  # noqa: E402 - 必须在导入 WSGI/WebSocket 之前

import gevent  # noqa: E402
from gevent.pywsgi import WSGIServer  # noqa: E402
from geventwebsocket.handler import WebSocketHandler  # noqa: E402

from config.perf_config import WS_PORT  # noqa: E402


def echo_app(environ, start_response):
    """收到什么就回什么，并在回包里带上服务端收到时戳，便于测端到端延迟。"""
    import json
    import time

    ws = environ.get("wsgi.websocket")
    if ws is None:
        start_response("400 Bad Request", [("Content-Type", "text/plain")])
        return [b"WebSocket required"]
    while True:
        message = ws.receive()
        if message is None:
            break
        try:
            payload = json.loads(message)
        except ValueError:
            payload = {"raw": message}
        if isinstance(payload, dict):
            payload["_server_ts"] = time.perf_counter()
            reply = json.dumps(payload)
        else:
            reply = message
        if ws.send(reply) is False:
            break
    return []


def main():
    server = WSGIServer(("0.0.0.0", WS_PORT), echo_app, handler_class=WebSocketHandler)
    print("WS echo server listening on ws://0.0.0.0:%d/echo" % WS_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
