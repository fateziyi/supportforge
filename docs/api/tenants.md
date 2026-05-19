# 租户接口 Tenants

> 基础路径：`/api/v1/tenants`

---

## 1. 创建租户

```
POST /api/v1/tenants
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 租户名称 |
| status | string | 否 | 状态，默认 `active` |
| plan | string | 否 | 套餐类型 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 租户 ID |
| name | string | 租户名称 |
| status | string | 状态 |
| plan | string | 套餐类型 |
| created_at | string | 创建时间 |

---

## 2. 租户列表

```
GET /api/v1/tenants
```

### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| status | string | 否 | 状态筛选 |
| keyword | string | 否 | 名称关键词 |

### 响应字段

返回分页结构 `items + total + page + page_size`

---

## 3. 租户详情

```
GET /api/v1/tenants/{tenant_id}
```

### 路径参数

| 字段 | 类型 | 说明 |
|------|------|------|
| tenant_id | string | 租户 ID |

---

## 4. 更新租户

```
PUT /api/v1/tenants/{tenant_id}
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 租户名称 |
| status | string | 否 | 状态 |
| plan | string | 否 | 套餐类型 |

---

## 5. 禁用租户

```
POST /api/v1/tenants/{tenant_id}/disable
```

---

## 6. 启用租户

```
POST /api/v1/tenants/{tenant_id}/enable
```