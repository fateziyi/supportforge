# 对话接口 Conversations

> 基础路径：`/api/v1/conversations`

---

## 1. 创建对话

```
POST /api/v1/conversations
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 对话标题 |
| knowledge_base_id | string | 否 | 默认知识库 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 对话 ID |
| tenant_id | string | 租户 ID |
| title | string | 标题 |
| status | string | 状态 |

---

## 2. 对话列表

```
GET /api/v1/conversations
```

### 查询参数

| 字段 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| status | string | 状态筛选 |
| keyword | string | 标题关键词 |

---

## 3. 对话详情

```
GET /api/v1/conversations/{conversation_id}
```

---

## 4. 发送消息并触发 Agent

```
POST /api/v1/conversations/{conversation_id}/messages
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 用户消息 |
| knowledge_base_id | string | 否 | 本次检索知识库 |
| stream | boolean | 否 | 是否流式返回 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| message_id | string | 消息 ID |
| conversation_id | string | 对话 ID |
| role | string | 角色：`assistant` / `user` |
| content | string | 回复内容 |
| category | string | 问题分类 |
| sources | array | 引用来源 |
| ticket_created | boolean | 是否已转工单 |

### `sources` 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| document_id | string | 来源文档 ID |
| chunk_id | string | 来源分片 ID |
| text | string | 引用文本 |
| score | float | 相似度分数 |

---

## 5. 获取消息列表

```
GET /api/v1/conversations/{conversation_id}/messages
```

### 响应字段

返回消息数组，每条消息包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息 ID |
| role | string | `user` / `assistant` / `system` |
| content | string | 内容 |
| created_at | string | 创建时间 |

---

## 6. 结束对话

```
POST /api/v1/conversations/{conversation_id}/close
```