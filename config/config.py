# -*- coding: utf-8 -*-
"""全局配置：切换环境、鉴权信息只需修改本文件。"""

# Swagger Petstore v2 服务地址（对应 https://petstore.swagger.io/#/ 页面接口）
HOST = "https://petstore.swagger.io/v2"

# 单次请求超时（秒）
TIMEOUT = 20

# Petstore 演示接口使用的 api_key
API_KEY = "special-key"

# 测试报告 / 日志输出目录（相对项目根目录）
REPORT_DIR = "reports"

# 每类报告保留的历史归档份数（超出后自动删除最旧的）
HISTORY_KEEP = 10

# 是否在日志中打印完整响应体
VERBOSE_LOG = True
