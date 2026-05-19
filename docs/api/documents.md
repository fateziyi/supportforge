# 文档接口 Documents

> 基础路径：`/api/v1/documents`

---

## 1. 上传文档

```
POST /api/v1/documents/upload
```

### 请求类型

`multipart/form-data`

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 文档文件 |
| knowledge_base_id | string | 是 | 所属知识库 ID |
| title | string | 否 | 文档标题 |
| description | string | 否 | 文档描述 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文档 ID |
| knowledge_base_id | string | 知识库 ID |
| filename | string | 文件名 |
| status | string | 状态：`uploaded` / `processing` / `ready` / `failed` |
| created_at | string | 创建时间 |

---

## 2. 文档列表

```
GET /api/v1/documents
```

### 查询参数

| 字段 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| knowledge_base_id | string | 知识库筛选 |
| status | string | 状态筛选 |
| keyword | string | 文件名关键词 |

---

## 3. 文档详情

```
GET /api/v1/documents/{document_id}
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文档 ID |
| knowledge_base_id | string | 知识库 ID |
| filename | string | 文件名 |
| status | string | 状态 |
| file_path | string | 存储路径 |
| chunk_count | int | 分片数 |
| vector_count | int | 向量数 |

---

## 4. 删除文档

```
DELETE /api/v1/documents/{document_id}
```

---

## 5. 重新解析文档

```
POST /api/v1/documents/{document_id}/reparse
```

不需要额外请求字段。

---

## 6. 查询解析状态

```
GET /api/v1/documents/{document_id}/status
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 当前状态 |
| progress | int | 进度百分比 |
| error_message | string | 失败原因 |