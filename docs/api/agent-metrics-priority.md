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