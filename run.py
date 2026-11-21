# -*- coding: utf-8 -*-
"""统一执行入口：在项目根目录执行  python run.py"""
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from common.html_report import CollectingResult, write_report  # noqa: E402


def main():
    suite = unittest.defaultTestLoader.discover(
        start_dir=os.path.join(ROOT, "testcases"),
        pattern="test_*.py",
        top_level_dir=ROOT,
    )
    print("=" * 64)
    print("Swagger Petstore 接口自动化测试  |  共 %d 条用例" % suite.countTestCases())
    print("被测服务：https://petstore.swagger.io/v2")
    print("=" * 64)

    started = time.time()
    result = unittest.TextTestRunner(verbosity=2, resultclass=CollectingResult).run(suite)
    elapsed = time.time() - started

    report_path = write_report(result, elapsed)
    passed = sum(1 for r in result.records if r["status"] == "通过")
    print("=" * 64)
    print("执行完成：通过 %d / %d，耗时 %.2fs" % (passed, len(result.records), elapsed))
    print("HTML 报告：%s" % report_path)
    print("=" * 64)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
