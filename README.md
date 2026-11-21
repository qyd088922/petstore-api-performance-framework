# 多协议性能测试框架（Petstore 靶场）

基于 Python 的分层式接口自动化 + 性能压测框架，以 Swagger Petstore 公开靶场为被测对象，
覆盖 **HTTP / WebSocket 双协议**，功能测试与性能压测**共用同一套业务 API 代码路径**。

技术栈：Python 3.13 · requests · pytest · Locust · gevent · websocket-client · Allure

---

## 一、框架分层

```
配置层    config/        host、超时、鉴权、压测参数（环境变量 + 默认值，换环境不改代码）
公共层    common/        BaseApi（HTTP 传输）→ BaseClient（统一服务层）→ AuthProvider（认证策略）
业务层    api/           PetApi / StoreApi / UserApi，只暴露业务语义方法
功能测试  testcases/     unittest 用例（13 条）
          pytest_tests/  pytest + Allure 用例（7 条）
负载层    perf/          Locust User、LoadTestShape、WebSocket 客户端与 echo 靶标、设备数据治理
报告层    report/        Allure / 性能 HTML 报告生成（无 Java 环境离线兜底）
入口      run.py         unittest 一键执行
          run_all.py     pytest + 报告汇总编排
```

三层职责严格解耦：**Locust 负责负载、pytest 负责功能、Allure/HTML 负责报告**。

## 二、核心设计

### 1. 功能与压测共用一条代码路径

`PetApi / StoreApi / UserApi` 只换父类（`BaseApi` → `BaseClient`），业务方法签名不变。
差异只在构造时注入的 reporter：

- 功能测试：`PetApi()` —— 计时/埋点静默，专注断言
- 性能压测：`PetApi(reporter=PerfReporter(environment))` —— 耗时自动桥接进 Locust 统计

接口变更只需改一处，杜绝"压测压的是旧接口"。

### 2. 认证可插拔（策略模式）

`common/auth.py` 定义统一接口 `apply(session)`，提供三种实现：

- `ApiKeyAuth` —— Petstore 演示用 `api_key: special-key`（公开演示值，服务端不强制校验）
- `BearerAuth` —— 预留给真实业务系统的 `Authorization: Bearer <token>`
- `NoAuth` —— 无需鉴权的场景

构造客户端时刷一次卡，后续所有请求自动携带凭证。

### 3. 指标闭环

`perf_counter` 埋点 → 路径归一化（`/pet/1` → `GET /pet/{id}`）→ `events.request.fire` → Locust 统计。
以**业务码**判定失败（HTTP 200 不代表业务成功），**压测禁用重试**（避免失败率失真），
因此 P99 可精确定位到接口级。

### 4. 多协议与负载模型

- WebSocket：自建本地 echo 靶标（Petstore 无 WS 接口），`WebSocketApp` 跑在 gevent 协程上，
  覆盖连接容量、断连重连、消息端到端延迟、Ping/Pong RTT。
- `LoadTestShape` 三种波形：`step` 阶梯（找容量拐点）、`sine` 正弦（潮汐流量）、`multi` 多波叠加。

### 5. 设备数据治理

`DeviceGovernance` 用上下文管理器实现批量激活 + 自动解绑，避免压测脏数据累积。

---

## 三、快速开始

```bash
pip install -r requirements.txt
```

**功能测试（unittest，13 条）**

```bash
python run.py
```

**功能测试（pytest + Allure，7 条）**

```bash
python -m pytest
python -m report.allure_report      # 生成离线 HTML（无需 Java）
```

**性能压测（无头模式）**

```bash
# 1. 先起 WebSocket echo 靶标（另开一个终端，保持运行）
python -m perf.ws_echo_server

# 2. 运行 Locust（阶梯模型，40 并发，40 秒）
python -m locust -f perf/locustfile.py --headless -u 40 -r 5 -t 40s \
    --html reports/locust_report.html --csv reports/locust_stats

# 3. 生成接口级 P99 报告
python -m report.perf_report
```

切换负载模型：`PERF_SHAPE=sine|step|multi`；切换被测地址：`PERF_HTTP_HOST` / `PERF_WS_HOST` 环境变量。

**Docker 无头运行**

```bash
docker build -t petstore-perf .
docker run --rm petstore-perf
```

---

## 四、实测结果

阶梯模型、40 并发上限、运行 40 秒（真实调用公开靶场，非编造）：

| 指标 | 值 |
|---|---|
| 接口数 | 7（4 HTTP + 3 WS） |
| 总请求 / 失败 | 28453 / 0 |
| 聚合 RPS | ≈708 |
| `GET /pet/findByStatus` P99 | 1600 ms |
| `ws:echo` / `ws:pingpong` P99 | 4 ms / 4 ms |

> 说明：40 并发是本次验证规模，不是容量结论；WebSocket 长连接高并发属框架设计目标，未做万级实测。

报告产物位于 `reports/`（由测试生成，已加入 `.gitignore`）：
`locust_report.html`（压测总览）、`perf_report.html`（接口级 P99）、
`pytest_report.html`（功能用例）、`locust_stats_*.csv`（原始数据）。

---

## 五、目录说明

| 目录 | 作用 |
|---|---|
| `config/` | 环境配置，环境变量 + 默认值 |
| `common/` | 传输层 / 统一服务层 / 认证 / 埋点桥接 / 数据工厂 / 日志 |
| `api/` | 业务 API 封装 |
| `testcases/` | unittest 功能用例 |
| `pytest_tests/` | pytest + Allure 功能用例 |
| `perf/` | Locust 负载层、波形、WS 客户端与靶标、设备治理 |
| `report/` | 报告生成脚本 |
| `ci/` | CI 流水线配置 |
