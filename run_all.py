# -*- coding: utf-8 -*-
"""一键编排：功能测试 -> 功能报告 -> 性能报告汇总。

压测本体由 run_perf.sh / CI 以 locust --headless 执行（见 Dockerfile、ci）。
本脚本负责把各层结果汇总为可查看的 HTML 报告。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd, cwd=ROOT):
    print("\n>>>", " ".join(cmd))
    return subprocess.call(cmd, cwd=cwd)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode in ("func", "all"):
        run([sys.executable, "-m", "pytest"])
        run([sys.executable, "-m", "report.allure_report"])
    if mode in ("report", "all"):
        if os.path.exists(os.path.join(ROOT, "reports", "locust_stats_stats.csv")):
            run([sys.executable, "-m", "report.perf_report"])
        else:
            print("跳过性能报告：未找到 locust CSV，请先执行压测。")
    print("\n报告目录:", os.path.join(ROOT, "reports"))


if __name__ == "__main__":
    main()
