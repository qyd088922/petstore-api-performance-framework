# -*- coding: utf-8 -*-
"""汇总 Locust CSV 生成接口级 P99 性能报告（数字全部来自真实压测，不编造）。"""
import csv
import html
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "reports", "locust_stats_stats.csv")
OUT = os.path.join(ROOT, "reports", "perf_report.html")

_CSS = """
body{margin:0;padding:32px;background:#f6f8fa;color:#1f2328;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.card{max-width:1180px;margin:0 auto;background:#fff;border:1px solid #d0d7de;border-radius:10px;overflow:hidden}
.head{padding:24px 28px;border-bottom:1px solid #d0d7de}
h1{margin:0 0 8px;font-size:22px}.meta{color:#656d76;font-size:13px;line-height:1.8}
.stats{display:flex;gap:14px;padding:20px 28px;flex-wrap:wrap}
.stat{flex:1;min-width:140px;padding:14px 16px;border:1px solid #d0d7de;border-radius:8px}
.stat .n{font-size:24px;font-weight:700}.stat .l{font-size:12px;color:#656d76;margin-top:4px}
h2{font-size:15px;font-weight:500;padding:8px 28px;margin:0}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:10px 14px;border-top:1px solid #d8dee4}
th{background:#f6f8fa;color:#656d76;font-weight:600}
.p99{color:#cf222e;font-weight:600}.note{padding:16px 28px;color:#656d76;font-size:12px;line-height:1.9}
"""
PROTO = {"GET": "HTTP", "WS_CONNECT": "WebSocket", "WS_ECHO": "WebSocket", "WS_PING": "WebSocket"}


def num(v, digits=0):
    try:
        return round(float(v), digits)
    except (TypeError, ValueError):
        return v


def main():
    with open(CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    data = [r for r in rows if r.get("Name") not in ("", "Aggregated")]
    agg = next((r for r in rows if r.get("Name") == "Aggregated"), None)

    interfaces = len(data)
    total_req = sum(int(r["Request Count"]) for r in data)
    total_fail = sum(int(r["Failure Count"]) for r in data)
    http_ifaces = sum(1 for r in data if PROTO.get(r["Type"]) == "HTTP")
    ws_ifaces = sum(1 for r in data if PROTO.get(r["Type"]) == "WebSocket")

    trs = []
    for r in data:
        trs.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td class='p99'>%s ms</td><td>%s</td></tr>"
            % (PROTO.get(r["Type"], r["Type"]), html.escape(r["Name"]),
               r["Request Count"], r["Failure Count"], num(r["Average Response Time"]),
               num(r["Median Response Time"]), num(r["99%"]), num(r["Requests/s"], 1)))

    page = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>性能压测报告</title><style>{_CSS}</style></head><body>
<div class="card"><div class="head"><h1>Swagger Petstore 性能压测报告</h1>
<div class="meta">数据来源：Locust 无头模式实际运行 CSV ｜ 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
负载模型：阶梯加压（StepShape）｜ 协议：HTTP + WebSocket ｜ 统计口径：客户端 perf_counter</div></div>
<div class="stats">
<div class="stat"><div class="n">{interfaces}</div><div class="l">接口数（实测）</div></div>
<div class="stat"><div class="n">{http_ifaces} / {ws_ifaces}</div><div class="l">HTTP / WS 接口</div></div>
<div class="stat"><div class="n">{total_req}</div><div class="l">总请求数</div></div>
<div class="stat"><div class="n">{total_fail}</div><div class="l">失败数</div></div>
<div class="stat"><div class="n">{num(agg['99%']) if agg else '-'} ms</div><div class="l">聚合 P99</div></div>
<div class="stat"><div class="n">{num(agg['Requests/s'],1) if agg else '-'}</div><div class="l">聚合 RPS</div></div>
</div>
<h2>接口级延迟明细</h2>
<table><thead><tr><th>协议</th><th>接口</th><th>请求数</th><th>失败数</th><th>平均</th><th>中位数</th><th>P99</th><th>RPS</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table>
<div class="note">
说明：本次为小规模真实压测，实测最大并发用户数为 40（阶梯模型 STEP 上限），
并非万级并发的容量结论；万级并发属于框架设计目标，需在其他环境实测后填入。<br>
ws:connect 为累计连接次数（含断连重连），不等同于同时在线连接数；
ws:echo_e2e 为消息端到端延迟，ws:pingpong_rtt 为协议层 Ping/Pong RTT。<br>
失败判定以业务码为准，压测禁用重试，因此失败率与延迟未被重试掩盖。
</div></div></body></html>"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("性能报告:", OUT)


if __name__ == "__main__":
    main()
