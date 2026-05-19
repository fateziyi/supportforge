# 工单接口 Tickets

> 基础路径：`/api/v1/tickets`

---

## 1. 创建工单

```
POST /api/v1/tickets
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subject | string | 是 | 工单标题 |
| description | string | 是 | 工单描述 |
| priority | string | 否 | 优先级 |
| source | string | 否 | 来源：`manual` / `agent` |
| conversation_id | string | 否 | 关联对话 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 工单 ID |
| tenant_id | string | 租户 ID |
| subject | string | 标题 |
| status | string | 状态 |
| priority | string | 优先级 |
| source | string | 来源 |

---

## 2. 工单列表

```
GET /api/v1/tickets
```

### 查询参数

| 字段 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| status | string | 状态筛选 |
| priority | string | 优先级筛选 |
| assignee_id | string | 指派人 |
| keyword | string | 标题关键词 |

---

## 3. 工单详情

```
GET /api/v1/tickets/{ticket_id}
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 工单 ID |
| subject | string | 标题 |
| description | string | 描述 |
| status | string | 状态 |
| priority | string | 优先级 |
| assignee_id | string | 指派人 |
| conversation_id | string | 关联对话 |

---

## 4. 更新工单状态

```
PATCH /api/v1/tickets/{ticket_id}/status
```

### 请求字段

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 新状态 |

---

## 5. 指派工单

```
PATCH /api/v1/tickets/{ticket_id}/assign
```

### 请求字段

| 字段 | 类型 | 说明 |
|------|------|------|
| assignee_id | string | 处理人 ID |

---

## 6. 关闭工单

```
POST /api/v1/tickets/{ticket_id}/close
```

---

## 7. 添加工单备注

```
POST /api/v1/tickets/{ticket_id}/comments
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 备注内容 |