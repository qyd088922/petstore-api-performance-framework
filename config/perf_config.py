# -*- coding: utf-8 -*-
"""性能压测配置。功能测试配置见 config/config.py。"""
import os

# ---- HTTP 压测目标（复用功能测试同一 HOST，保证同一代码路径）----
HTTP_HOST = os.environ.get("PERF_HTTP_HOST", "https://petstore.swagger.io/v2")
API_KEY = os.environ.get("PERF_API_KEY", "special-key")

# ---- WebSocket 压测目标（本地 echo server，用于真实测量 RTT / 端到端延迟）----
WS_HOST = os.environ.get("PERF_WS_HOST", "127.0.0.1")
WS_PORT = int(os.environ.get("PERF_WS_PORT", "8765"))
WS_URL = "ws://%s:%d/echo" % (WS_HOST, WS_PORT)

# ---- 负载模型 ----
SHAPE = os.environ.get("PERF_SHAPE", "step").lower()   # sine / step / multi
SHAPE_DURATION = int(os.environ.get("PERF_DURATION", "60"))   # 秒
SHAPE_MAX_USERS = int(os.environ.get("PERF_MAX_USERS", "60"))

# ---- 压测行为 ----
DISABLE_RETRY = True          # 压测禁用重试，保证失败率与延迟真实
BIZ_CODE_SUCCESS = (200,)     # 业务码成功范围（Petstore 用 code=200 表示成功）
