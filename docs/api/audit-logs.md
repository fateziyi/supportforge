# 审计日志接口 Audit-Logs

> 基础路径：`/api/v1/audit-logs`

---

## 1. 审计日志列表

```
GET /api/v1/audit-logs
```

### 查询参数

| 字段 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| user_id | string | 用户筛选 |
| action | string | 行为类型 |
| resource_type | string | 资源类型 |
| start_time | string | 起始时间 |
| end_time | string | 结束时间 |

---

## 2. 审计日志详情

```
GET /api/v1/audit-logs/{log_id}
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 日志 ID |
| tenant_id | string | 租户 ID |
| user_id | string | 用户 ID |
| action | string | 操作行为 |
| resource_type | string | 资源类型 |
| resource_id | string | 资源 ID |
| payload | object | 请求/响应摘要 |
| created_at | string | 时间 |

---

## 3. 审计汇总统计

```
GET /api/v1/audit-logs/summary
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| total_actions | int | 总操作数 |
| ai_calls | int | AI 调用数 |
| avg_latency | float | 平均耗时 |
| error_count | int | 错误数 |