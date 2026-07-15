# Agent 接口 & 统计接口 & 开发优先级

---

## Agent 接口

> 基础路径：`/api/v1/agent`

### 1. 运行 Agent

```
POST /api/v1/agent/run
```

#### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 输入问题 |
| conversation_id | string | 否 | 对话 ID |
| knowledge_base_id | string | 否 | 知识库 ID |
| stream | boolean | 否 | 是否流式 |

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | string | 执行 ID |
| category | string | 分类结果 |
| answer | string | 最终回答 |
| sources | array | 引用来源 |
| ticket_created | boolean | 是否创建工单 |
| status | string | `completed`、`interrupted`、`failed` 之一 |
| confidence | float | 本次回答的置信度或路由评分 |
| trace_id | string | 用于关联 API、模型调用、异步任务和审计日志的链路 ID |

---

### 2. 获取工作流图

```
GET /api/v1/agent/graph
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| nodes | array | 节点列表 |
| edges | array | 边列表 |

---

### 3. 获取 Agent 执行记录

```
GET /api/v1/agent/runs
```

---

### 4. 执行详情

```
GET /api/v1/agent/runs/{run_id}
```

### 5. 审核后恢复工作流

```
POST /api/v1/agent/runs/{run_id}/resume
```

> 仅租户内有权限的坐席或管理员可调用。服务端从持久化 checkpoint 恢复状态，绝不接受前端传入的 `tenant_id` 或任意工作流状态。

#### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| decision | string | 是 | `approve`、`reject`、`provide_answer` 之一 |
| operator_note | string | 否 | 人工处理意见，会写入工单和审计日志 |
| answer | string | 否 | 当 `decision=provide_answer` 时的人工回复 |

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | string | 原执行 ID |
| status | string | 恢复后的执行状态 |
| answer | string | 恢复流程产生的最终回复（如有） |
| ticket_id | string | 关联工单 ID（如有） |

---

## 统计接口 Metrics

> 基础路径：`/api/v1/metrics`

### 1. 仪表盘统计

```
GET /api/v1/metrics/dashboard
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| today_conversations | int | 今日对话数 |
| today_tickets | int | 今日工单数 |
| document_count | int | 文档总数 |
| avg_response_latency | float | 平均响应耗时 |
| answer_hit_rate | float | 命中率 |
| p95_response_latency | float | P95 响应耗时，单位毫秒 |
| total_token_usage | int | 统计周期内模型 Token 消耗 |
| estimated_model_cost | float | 按模型单价估算的调用成本 |
| handoff_rate | float | 转人工工单占比 |
| failed_run_rate | float | Agent 失败执行占比 |

---

### 2. 租户统计

```
GET /api/v1/metrics/tenants/{tenant_id}
```

---

## 接口开发优先级

### 第一批 — 必须先做

| # | 接口 | 说明 |
|---|------|------|
| 1 | `POST /auth/login` | 登录认证 |
| 2 | `GET /auth/me` | 当前用户 |
| 3 | `POST /knowledge-bases` | 创建知识库 |
| 4 | `POST /documents/upload` | 上传文档 |
| 5 | `POST /conversations/{id}/messages` | 发送消息 |
| 6 | `POST /tickets` | 创建工单 |
| 7 | `GET /audit-logs` | 审计日志列表 |

### 第二批 — 补齐功能

| # | 接口 | 说明 |
|---|------|------|
| 8 | `GET /documents` | 文档列表 |
| 9 | `GET /tickets` | 工单列表 |
| 10 | `PATCH /tickets/{id}/status` | 工单状态更新 |
| 11 | `GET /metrics/dashboard` | 仪表盘统计 |

### 第三批 — 增强能力

| # | 接口 | 说明 |
|---|------|------|
| 12 | `POST /agent/run` | Agent 运行 |
| 13 | `GET /agent/graph` | 工作流图 |
| 14 | `GET /audit-logs/summary` | 审计汇总 |
| 15 | `GET /knowledge-bases/{id}/stats` | 知识库统计 |
| 16 | `POST /agent/runs/{run_id}/resume` | 人工审核后恢复工作流 |
| 17 | `GET /agent/runs/{run_id}` | 展示路由、引用、耗时、Token 与失败原因 |

---

## 校招演示与验证接口约定

### 固定演示场景

每次演示至少覆盖下列场景，并在 `agent_runs`、工单与审计日志中保留可追溯记录：

| 场景 | 预期结果 |
|------|----------|
| 知识库已覆盖的 FAQ | 返回带文档引用的回答，不创建工单 |
| 检索低置信度或知识库无命中 | 不编造回答，状态为 `interrupted` 或创建工单 |
| 用户明确要求人工 | 跳过自动回复或仅给出确认信息，创建工单 |
| 敏感业务问题 | 进入人工审核节点，等待 `resume` 接口处理 |
| 文档解析/模型调用失败 | 返回统一错误，记录重试次数、失败原因与 `trace_id` |
| 跨租户访问或跨租户检索 | 返回标准无权限错误，并创建越权访问审计事件 |

### 指标口径

- `answer_hit_rate`：在评测集或人工标注样本中，回答引用包含期望来源且最终路由正确的比例；不能仅以“模型返回了文本”计算。
- `handoff_rate`：统计周期内创建人工工单的 Agent 执行数 / 全部 Agent 执行数。
- `failed_run_rate`：执行状态为 `failed` 的运行数 / 全部 Agent 执行数；人工中断不计为失败。
- 成本按模型实际返回的 Token 使用量计算；若供应商未返回 usage 数据，必须标记为“未统计”，不能伪造精确成本。
