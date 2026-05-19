# 知识库接口 Knowledge-Bases

> 基础路径：`/api/v1/knowledge-bases`

---

## 1. 创建知识库

```
POST /api/v1/knowledge-bases
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 知识库名称 |
| description | string | 否 | 描述 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 知识库 ID |
| tenant_id | string | 租户 ID |
| name | string | 名称 |
| description | string | 描述 |
| document_count | int | 文档数 |

---

## 2. 知识库列表

```
GET /api/v1/knowledge-bases
```

### 查询参数

| 字段 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| keyword | string | 名称关键词 |

---

## 3. 知识库详情

```
GET /api/v1/knowledge-bases/{kb_id}
```

---

## 4. 更新知识库

```
PUT /api/v1/knowledge-bases/{kb_id}
```

### 请求字段

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 名称 |
| description | string | 描述 |

---

## 5. 删除知识库

```
DELETE /api/v1/knowledge-bases/{kb_id}
```

---

## 6. 知识库统计

```
GET /api/v1/knowledge-bases/{kb_id}/stats
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| document_count | int | 文档数量 |
| chunk_count | int | 分片数量 |
| vector_count | int | 向量数量 |
| updated_at | string | 最近更新时间 |