# -*- coding: utf-8 -*-
"""从 Allure 结果 JSON 生成离线 HTML 报告（无需 Java/Allure CLI）。

CI 中推荐直接用 allure generate；本地无 Java 时用本脚本兜底，
保证 pytest 功能测试结果同样有可视化报告。
"""
import glob
import html
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "reports", "allure-results")
OUT = os.path.join(ROOT, "reports", "pytest_report.html")

_CSS = """
body{margin:0;padding:32px;background:#f6f8fa;color:#1f2328;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.card{max-width:1080px;margin:0 auto;background:#fff;border:1px solid #d0d7de;border-radius:10px;overflow:hidden}
.head{padding:24px 28px;border-bottom:1px solid #d0d7de}
h1{margin:0 0 8px;font-size:22px}.meta{color:#656d76;font-size:13px;line-height:1.8}
.stats{display:flex;gap:14px;padding:20px 28px}.stat{flex:1;padding:14px 16px;border:1px solid #d0d7de;border-radius:8px}
.stat .n{font-size:26px;font-weight:700}.stat .l{font-size:12px;color:#656d76;margin-top:4px}
.pass .n{color:#1a7f37}.fail .n{color:#cf222e}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:10px 14px;border-top:1px solid #d8dee4}
th{background:#f6f8fa;color:#656d76;font-weight:600}
.tag{display:inline-block;padding:2px 9px;border-radius:12px;font-size:12px}
.ok{background:#dafbe1;color:#1a7f37}.no{background:#ffebe9;color:#cf222e}
pre{margin:0;white-space:pre-wrap;color:#cf222e;font-size:11px}
"""


def main():
    results = []
    for path in glob.glob(os.path.join(RESULTS_DIR, "*-result.json")):
        with open(path, encoding="utf-8") as fh:
            results.append(json.load(fh))

    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = len(results) - passed
    rows = []
    for r in sorted(results, key=lambda x: x.get("name", "")):
        ok = r.get("status") == "passed"
        labels = ", ".join(l.get("name", "") for l in r.get("labels", [])
                           if l.get("name") in ("feature", "story"))
        msg = r.get("statusDetails", {}).get("message", "")
        detail = "<pre>%s</pre>" % html.escape(msg) if msg else "-"
        rows.append(
            "<tr><td>%s</td><td>%s</td><td><span class='tag %s'>%s</span></td>"
            "<td>%.0f ms</td><td>%s</td></tr>"
            % (html.escape(labels), html.escape(r.get("name", "")),
               "ok" if ok else "no", "通过" if ok else "失败",
               r.get("stop", 0) - r.get("start", 0), detail))

    page = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>pytest 功能测试报告</title><style>{_CSS}</style></head><body>
<div class="card"><div class="head"><h1>pytest 功能测试报告（Allure 数据源）</h1>
<div class="meta">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ｜
数据来源：reports/allure-results/*.json ｜ 职责：功能测试（压测由 Locust 承担）</div></div>
<div class="stats">
<div class="stat"><div class="n">{len(results)}</div><div class="l">用例总数</div></div>
<div class="stat pass"><div class="n">{passed}</div><div class="l">通过</div></div>
<div class="stat fail"><div class="n">{failed}</div><div class="l">失败</div></div>
</div><table><thead><tr><th>模块</th><th>用例</th><th>结果</th><th>耗时</th><th>详情</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></body></html>"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("pytest HTML 报告:", OUT)


if __name__ == "__main__":
    main()
