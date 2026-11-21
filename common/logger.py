# -*- coding: utf-8 -*-
"""日志封装：同时输出到控制台和 reports/api.log。"""
import logging
import os
import sys

from config.config import REPORT_DIR, VERBOSE_LOG

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.path.join(_ROOT, REPORT_DIR)
os.makedirs(_LOG_DIR, exist_ok=True)

_FORMAT = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name="petstore"):
    """获取一个带控制台 + 文件双输出的 logger（同名只初始化一次）。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if VERBOSE_LOG else logging.INFO)
    logger.propagate = False

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(_FORMAT)
    logger.addHandler(console)

    file_handler = logging.FileHandler(os.path.join(_LOG_DIR, "api.log"), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_FORMAT)
    logger.addHandler(file_handler)

    return logger
