# -*- coding: utf-8 -*-
"""轻量测试报告封装：基于 unittest.TestResult 收集结果并输出 HTML 报告。"""
import html
import os
import time
import traceback
import unittest
from datetime import datetime

from config.config import HOST, REPORT_DIR

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CSS = """
* { box-sizing: border-box; }
body { margin: 0; padding: 32px; background: #f6f8fa; color: #1f2328;
       font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; }
.card { max-width: 1080px; margin: 0 auto; background: #fff; border: 1px solid #d0d7de;
        border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,.04); }
.head { padding: 24px 28px; border-bottom: 1px solid #d0d7de; }
h1 { margin: 0 0 8px; font-size: 22px; }
.meta { color: #656d76; font-size: 13px; line-height: 1.8; }
.stats { display: flex; gap: 14px; padding: 20px 28px; }
.stat { flex: 1; padding: 14px 16px; border: 1px solid #d0d7de; border-radius: 8px; }
.stat .n { font-size: 26px; font-weight: 700; }
.stat .l { font-size: 12px; color: #656d76; margin-top: 4px; }
.pass .n { color: #1a7f37; } .fail .n { color: #cf222e; }
.err .n { color: #9a6700; } .skip .n { color: #57606a; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 14px; border-top: 1px solid #d8dee4; vertical-align: top; }
th { background: #f6f8fa; color: #656d76; font-weight: 600; }
tr:hover td { background: #fafbfc; }
.tag { display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: 12px; }
.tag-ok { background: #dafbe1; color: #1a7f37; }
.tag-fail { background: #ffebe9; color: #cf222e; }
.tag-err { background: #fff8c5; color: #9a6700; }
.tag-skip { background: #eaeef2; color: #57606a; }
pre { margin: 0; white-space: pre-wrap; word-break: break-all; color: #cf222e; font-size: 11px; }
"""


class CollectingResult(unittest.TextTestResult):
    """在标准控制台输出之外，额外收集每条用例的执行结果。"""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.records = []
        self._started = {}

    def startTest(self, test):
        super().startTest(test)
        self._started[test.id()] = time.time()

    def _cost(self, test):
        return time.time() - self._started.pop(test.id(), time.time())

    def _record(self, test, status, err=None, reason=None):
        detail = ""
        if err:
            detail = "".join(traceback.format_exception(*err))
        elif reason:
            detail = str(reason)
        self.records.append({
            "name": test.id(), "status": status,
            "detail": detail, "cost": self._cost(test),
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "通过")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "失败", err=err)

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "错误", err=err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "跳过", reason=reason)


def write_report(result, elapsed):
    """生成 HTML 报告，返回报告文件绝对路径。"""
    records = getattr(result, "records", [])
    total = len(records)
    passed = sum(1 for r in records if r["status"] == "通过")
    failed = sum(1 for r in records if r["status"] == "失败")
    errors = sum(1 for r in records if r["status"] == "错误")
    skipped = sum(1 for r in records if r["status"] == "跳过")
    rate = (passed / total * 100) if total else 0

    cls_map = {"通过": "ok", "失败": "fail", "错误": "err", "跳过": "skip"}
    rows = []
    for item in records:
        tag = cls_map.get(item["status"], "skip")
        detail = ("<pre>%s</pre>" % html.escape(item["detail"])) if item["detail"] else "-"
        rows.append(
            "<tr><td>%s</td><td><span class='tag tag-%s'>%s</span></td>"
            "<td>%.2f s</td><td>%s</td></tr>"
            % (html.escape(item["name"]), tag, item["status"], item["cost"], detail))

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Swagger Petstore 接口自动化测试报告</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
  <div class="head">
    <h1>Swagger Petstore 接口自动化测试报告</h1>
    <div class="meta">
      被测服务：{html.escape(HOST)}<br>
      执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ｜
      总耗时：{elapsed:.2f} s ｜ 通过率：{rate:.1f}%
    </div>
  </div>
  <div class="stats">
    <div class="stat"><div class="n">{total}</div><div class="l">用例总数</div></div>
    <div class="stat pass"><div class="n">{passed}</div><div class="l">通过</div></div>
    <div class="stat fail"><div class="n">{failed}</div><div class="l">失败</div></div>
    <div class="stat err"><div class="n">{errors}</div><div class="l">错误</div></div>
    <div class="stat skip"><div class="n">{skipped}</div><div class="l">跳过</div></div>
  </div>
  <table>
    <thead><tr><th>用例</th><th>结果</th><th>耗时</th><th>详情</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>
</body>
</html>"""

    report_dir = os.path.join(_ROOT, REPORT_DIR)
    os.makedirs(report_dir, exist_ok=True)
    path = os.path.join(report_dir, "report.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path
