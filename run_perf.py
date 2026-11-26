# -*- coding: utf-8 -*-
"""一键性能压测：WS echo -> Locust -> perf_report -> 历史归档。

默认用 10 用户 / 5 并发爬升 / 20 秒，让命令行参数真正生效；
如果要用自定义负载模型（step/sine/multi），传 --shape 即可，此时 -t 会被 Locust 忽略。

用法：
    python run_perf.py
    python run_perf.py -u 40 -r 5 -t 40s
    python run_perf.py -u 40 -r 5 --shape step
"""
import argparse
import os
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from config.perf_config import WS_HOST, WS_PORT  # noqa: E402

REPORT_DIR = os.path.join(ROOT, "reports")
LOCUST_HTML = os.path.join(REPORT_DIR, "locust_report.html")
LOCUST_CSV = os.path.join(REPORT_DIR, "locust_stats")
LOCUST_LOG = os.path.join(REPORT_DIR, "locust_run.log")


def port_open(host, port, timeout=0.2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_port(host, port, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_open(host, port):
            return True
        time.sleep(0.1)
    return False


def parse_args():
    parser = argparse.ArgumentParser(description="一键运行 Petstore 性能压测")
    parser.add_argument("-u", "--users", default="10", help="最大并发用户数，默认 10")
    parser.add_argument("-r", "--spawn-rate", default="5", help="每秒启动用户数，默认 5")
    parser.add_argument("-t", "--run-time", default="20s", help="压测时长，默认 20s")
    parser.add_argument("--shape", default="none",
                        help="负载模型：none/step/sine/multi，默认 none（让 -t 生效）")
    return parser.parse_args()


def main():
    args = parse_args()
    ws_proc = None
    started_ws = False

    try:
        if port_open(WS_HOST, WS_PORT):
            print("WS echo 已在运行，直接复用：ws://%s:%d/echo" % (WS_HOST, WS_PORT))
        else:
            ws_proc = subprocess.Popen(
                [sys.executable, "-m", "perf.ws_echo_server"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            started_ws = True
            if not wait_port(WS_HOST, WS_PORT):
                raise RuntimeError("WS echo server 启动超时")
            print("WS echo 已启动：ws://%s:%d/echo" % (WS_HOST, WS_PORT))

        env = os.environ.copy()
        env["PERF_SHAPE"] = args.shape
        if args.shape != "none":
            print("提示：--shape=%s 使用自定义负载模型，Locust 会忽略 -t=%s" %
                  (args.shape, args.run_time))

        locust_cmd = [
            sys.executable, "-m", "locust",
            "-f", os.path.join(ROOT, "perf", "locustfile.py"),
            "--headless",
            "-u", str(args.users),
            "-r", str(args.spawn_rate),
            "-t", str(args.run_time),
            "--html", LOCUST_HTML,
            "--csv", LOCUST_CSV,
        ]
        print("运行 Locust：%s 用户 / %s 每秒 / %s" %
              (args.users, args.spawn_rate, args.run_time))
        with open(LOCUST_LOG, "w", encoding="utf-8") as log:
            rc = subprocess.call(locust_cmd, cwd=ROOT, env=env,
                                 stdout=log, stderr=subprocess.STDOUT)
        if rc != 0:
            raise SystemExit("Locust 执行失败，详见 %s" % LOCUST_LOG)

        print("生成性能汇总并归档：")
        rc = subprocess.call([sys.executable, "-m", "report.perf_report"],
                             cwd=ROOT, env=env)
        if rc != 0:
            raise SystemExit("perf_report 生成失败")

        print("完成：")
        print("  Locust 报告：%s" % LOCUST_HTML)
        print("  Locust 日志：%s" % LOCUST_LOG)
        print("  性能汇总：%s" % os.path.join(REPORT_DIR, "perf_report.html"))
        print("  历史归档：%s" % os.path.join(REPORT_DIR, "history", "index.html"))
    finally:
        if started_ws and ws_proc is not None and ws_proc.poll() is None:
            ws_proc.terminate()
            try:
                ws_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ws_proc.kill()
            print("WS echo 已关闭（由本脚本启动）")
        elif started_ws:
            print("WS echo 进程已退出")


if __name__ == "__main__":
    main()
