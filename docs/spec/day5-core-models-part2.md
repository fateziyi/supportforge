# Day 5 Spec：核心模型（Part 2）— 对话 + 消息 + 工单 + 审计 + Agent 执行记录

> 目标：在 Day 4 已完成租户、用户、知识库、文档 4 张基础业务表的基础上，补齐剩余 5 张核心业务表：`conversations`、`conversation_messages`、`tickets`、`audit_logs`、`agent_runs`，并通过 Alembic 迁移把全部 9 张核心表真正落到 PostgreSQL 数据库中，为 Week 2 的客服对话、工单流转、审计追踪、Agent 工作流持久化打下数据结构基础。

---

## 1. Day 5 要解决什么问题

Day 4 已经把“租户 + 用户 + 知识库 + 文档”的基础骨架搭起来了，但当前项目仍然缺少真正支撑“智能客服闭环”的业务实体，因此还有 5 个核心缺口：

1. **还没有对话主表**：用户和客服之间的会话没有持久化容器
2. **还没有消息明细表**：一轮轮对话内容无法逐条保存，后续无法做上下文拼接与追溯
3. **还没有工单表**：复杂问题升级为工单后，没有地方记录工单状态、优先级、指派人
4. **还没有审计日志表**：关键操作和 AI 决策缺少可追踪记录
5. **还没有 Agent 执行记录表**：LangGraph / Agent 每次运行的输入、输出、状态、耗时没有持久化落点

Day 5 就是解决这 5 个问题。

---

## 2. Day 5 目标产出

完成后新增 / 修改的核心文件如下：

```text
backend/app/
├── models/
│   ├── __init__.py                         # 补充导入 Day 5 的全部模型
│   ├── conversation.py                     # 对话表模型
│   ├── conversation_message.py             # 对话消息表模型
│   ├── ticket.py                           # 工单表模型
│   ├── audit_log.py                        # 审计日志表模型
│   └── agent_run.py                        # Agent 执行记录表模型
└── db/
    └── migrations/
        └── versions/
            └── <revision>_add_conversation_message_ticket_audit_agent_run.py
```

> 说明：
> - Day 5 只覆盖剩余 5 张业务表
> - Day 5 完成后，数据库里应能看到全部 9 张核心业务表 + `alembic_version`
> - Day 5 依然只做模型与迁移，不进入 repository / service / API 逻辑实现

---

## 3. Day 5 实现边界

### Day 5 要做

| 模块 | 内容 |
|------|------|
| `models/conversation.py` | 定义对话主表 |
| `models/conversation_message.py` | 定义对话消息明细表 |
| `models/ticket.py` | 定义工单表 |
| `models/audit_log.py` | 定义审计日志表 |
| `models/agent_run.py` | 定义 Agent 执行记录表 |
| `models/__init__.py` | 补充导入 Day 5 全部模型，确保 Alembic autogenerate 能识别 |
| Alembic 迁移 | 生成并执行第二批业务表迁移 |
| 验证 | 数据库里能看到 5 张新表，且与 Day 4 的 4 张表关系正确 |

### Day 5 不做

| 不做 | 原因 |
|------|------|
| 登录接口、租户/用户/知识库/工单 CRUD API | Day 6 / Week 2 任务 |
| Repository / Service 层 | 依赖模型完成后再做 |
| 消息发送逻辑、Agent 工作流逻辑 | Week 3/4 任务 |
| Ticket 自动流转规则 | Week 4 任务 |
| 审计日志写入时机与策略 | Week 5 任务 |
| Agent 实时 tracing / LangSmith 集成 | Week 5 任务 |
| 复杂枚举、状态机校验、业务 hooks | 后续逐步补齐 |

---

## 4. 设计总原则（Day 5 必须遵守）

### 4.1 多租户优先原则继续生效

Day 5 的所有表都必须明确租户归属：

| 表 | 是否必须有 `tenant_id` | 原因 |
|----|------------------------|------|
| `conversations` | 是 | 对话属于某个租户 |
| `conversation_messages` | 是 | 消息属于某个租户，方便按租户过滤 |
| `tickets` | 是 | 工单属于某个租户 |
| `audit_logs` | 是 | 审计日志天然有租户边界 |
| `agent_runs` | 是 | Agent 执行记录归属于某个租户 |

### 4.2 先保留核心字段，不一次性做满

Day 5 只追求：
- 主表与从表关系正确
- 多租户字段完整
- 工单 / 审计 / Agent 跑通基础持久化结构
- 能生成迁移并成功落库

不追求：
- 完整业务状态机
- 超细粒度索引优化
- 海量 JSON 字段拆表设计
- 提前做复杂分库分表规划

### 4.3 统一继承与命名风格

所有模型必须遵循 Day 3 / Day 4 已建立的约束：
- 继承 `Base`
- 需要时间戳的表继承 `TimestampMixin`
- 使用 SQLAlchemy 2.0 风格：`Mapped[...]` + `mapped_column(...)`
- 外键与 `__tablename__` 必须与已存在模型精确匹配
- 优先写清晰中文注释，方便你后续复盘和面试表达

---

## 5. 逐文件实现规格

### 5.1 `backend/app/models/conversation.py`

**职责**：
- 定义对话主表，是一轮客户咨询会话的容器
- 后续消息都归属于某个 conversation
- Agent 回答、转工单、人工接管都会挂在 conversation 上下文里

**建议表名**：

```python
__tablename__ = "conversations"
```

**Day 5 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 对话 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `user_id` | `ForeignKey("users.id")` | 发起对话的用户 |
| `status` | `String(20)` | 对话状态，如 `open` / `closed` / `handoff` |
| `last_message_at` | `DateTime(timezone=True)` | 最后一条消息时间 |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |

**推荐关系**：
- `tenant`：多对一
- `user`：多对一
- `messages`：一对多，关联 `ConversationMessage`
- `tickets`：一对多，关联 `Ticket`
- `agent_runs`：一对多，关联 `AgentRun`

**关键约束**：
- `tenant_id`、`user_id` 必须建索引
- `status` 先用字符串，不上 Enum
- `last_message_at` 建议允许为空（刚创建但还没发消息的对话）

---

### 5.2 `backend/app/models/conversation_message.py`

**职责**：
- 定义对话消息明细表，保存每一条用户消息、客服消息、AI 回复消息、系统消息
- 后续做上下文拼接、消息回放、审计排查都依赖这个表

**建议表名**：

```python
__tablename__ = "conversation_messages"
```

**Day 5 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 消息 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `conversation_id` | `ForeignKey("conversations.id")` | 所属对话 |
| `sender_type` | `String(20)` | 发送者类型，如 `user` / `agent` / `human_agent` / `system` |
| `sender_id` | `String(36)` 或 `None` | 发送者 ID，系统消息可为空 |
| `content` | `Text` | 消息正文 |
| `message_type` | `String(20)` | 消息类型，如 `text` / `event` / `tool_result` |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳（与 CLAUDE.md §9 一致，所有表统一继承） |

**推荐关系**：
- `tenant`：多对一
- `conversation`：多对一

**关键约束**：
- `tenant_id`、`conversation_id` 必须建索引
- `content` 建议用 `Text`，不要用 `String(255)` 截断长消息
- 与 CLAUDE.md §9 数据库规范一致：所有表必须包含 `created_at`、`updated_at`，统一继承 `TimestampMixin`
- 消息表虽然业务上 `updated_at ≈ created_at`，但统一继承可以减少代码风格分裂和后续扩展成本

---

### 5.3 `backend/app/models/ticket.py`

**职责**：
- 定义工单表，用于承接 AI 无法闭环解决的问题
- 工单是客服系统与智能体之间的桥梁：简单问题 AI 回答，复杂问题升级工单

**建议表名**：

```python
__tablename__ = "tickets"
```

**Day 5 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 工单 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `conversation_id` | `ForeignKey("conversations.id")` | 来源对话 |
| `subject` | `String(200)` | 工单标题 |
| `status` | `String(20)` | 工单状态，如 `open` / `assigned` / `resolved` / `closed` |
| `priority` | `String(20)` | 优先级，如 `low` / `medium` / `high` / `urgent` |
| `assignee_id` | `ForeignKey("users.id")` 或 `None` | 指派给哪个客服 |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |

**推荐关系**：
- `tenant`：多对一
- `conversation`：多对一
- `assignee`：多对一，指向 `User`

**关键约束**：
- `tenant_id`、`conversation_id`、`assignee_id` 都建议建索引
- `assignee_id` 可以为空，表示还未指派
- 工单创建者不单独设 `created_by_user_id` 字段，默认从 `conversation.user_id` 推导（减少 Day 5 字段冗余，后续如需独立字段可在 Week 2 补）
- Day 5 不必引入 `description`、`resolution`、`closed_at` 等扩展字段，后续再加

---

### 5.4 `backend/app/models/audit_log.py`

**职责**：
- 定义审计日志表，用于记录关键业务操作和 AI 行为
- 后续所有需要追踪的操作都可以统一写入这里，例如：
  - 用户登录
  - 文档上传
  - 工单创建 / 指派 / 关闭
  - Agent 调用模型 / 检索知识库 / 升级工单

**建议表名**：

```python
__tablename__ = "audit_logs"
```

**Day 5 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 审计日志 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `user_id` | `ForeignKey("users.id")` 或 `None` | 操作用户 |
| `action` | `String(100)` | 动作名，如 `ticket_created` / `document_uploaded` |
| `resource_type` | `String(50)` | 资源类型，如 `ticket` / `document` / `conversation` |
| `resource_id` | `String(36)` 或 `None` | 资源 ID |
| `payload` | `JSON` 或 `Text` | 附加详情，建议优先 JSON |
| `created_at` | 时间戳字段 | 操作时间 |

**推荐关系**：
- `tenant`：多对一
- `user`：多对一，可为空

**关键约束**：
- `tenant_id`、`user_id`、`action` 建议建索引
- `payload` 优先用 `JSON`，便于后续做结构化审计查询
- 与 CLAUDE.md §9 一致，`audit_logs` 也继承 `TimestampMixin`（虽然业务上 `updated_at ≈ created_at`，但统一继承可以保持代码风格一致，减少决策维度）

---

### 5.5 `backend/app/models/agent_run.py`

**职责**：
- 定义 Agent 执行记录表，保存每次 LangGraph / Agent 工作流运行的关键信息
- 用于后续问题排查、链路追踪、性能分析、AI 成本分析

**建议表名**：

```python
__tablename__ = "agent_runs"
```

**Day 5 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | Agent 运行 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `conversation_id` | `ForeignKey("conversations.id")` 或 `None` | 来源对话 |
| `trigger_message_id` | `ForeignKey("conversation_messages.id")` 或 `None` | 触发本次 Agent 的消息 |
| `status` | `String(20)` | 执行状态，如 `running` / `success` / `failed` |
| `input_payload` | `JSON` | 输入参数 |
| `output_payload` | `JSON` 或 `None` | 输出结果 |
| `error_message` | `Text` 或 `None` | 失败时的错误信息 |
| `started_at` | `DateTime(timezone=True)` | 开始时间 |
| `finished_at` | `DateTime(timezone=True)` 或 `None` | 结束时间 |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |

**推荐关系**：
- `tenant`：多对一
- `conversation`：多对一，可为空
- `trigger_message`：多对一，可为空

**关键约束**：
- `tenant_id`、`conversation_id`、`status`、`trigger_message_id` 建议建索引
- `input_payload` / `output_payload` 优先用 `JSON`
- `finished_at` 允许为空，表示仍在执行中
- `started_at` 和 `created_at` 都保留是可以接受的：
  - `created_at` 表示记录被创建时间
  - `started_at` 表示 Agent 真正开始执行的时间

---

### 5.6 `backend/app/models/__init__.py`

**职责变化**：
- 在 Day 4 已导入 4 个模型的基础上，继续补充导入 Day 5 的 5 个模型
- 确保 `import app.models` 后，全部 9 张表都注册到 `Base.metadata`

**Day 5 需要追加的导入**：

```python
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.models.ticket import Ticket
from app.models.audit_log import AuditLog
from app.models.agent_run import AgentRun
```

**关键约束**：
- 导入顺序尽量按依赖链组织：`Conversation` → `ConversationMessage` → `Ticket` → `AuditLog` → `AgentRun`
- 如果 `ruff` 对 `__init__.py` 中的导入报 F401，可采用 Day 4 已经使用过的 redundant alias 模式：`from xxx import Foo as Foo`

---

### 5.7 Alembic 迁移生成

**职责**：
- 基于 Day 5 的模型定义自动生成第二批业务表迁移脚本
- 把对话、消息、工单、审计、Agent 执行记录表真正落到 PostgreSQL

**推荐命令**：

```bash
cd backend
poetry run alembic revision --autogenerate -m "add conversation message ticket audit agent run tables"
poetry run alembic upgrade head
```

**预期结果**：
- `app/db/migrations/versions/` 下出现新的 revision 文件
- 新 revision 的 `down_revision` 指向 Day 4 的 `f6c7458fff25`
- 升级成功后，数据库里出现全部 9 张表 + `alembic_version`

**关键约束**：
- migration message 要清晰，后续回看时能快速理解这批变更
- 如果 autogenerate 没发现新表，优先检查 `models/__init__.py` 是否补充导入成功
- 迁移脚本生成后建议人工过一遍，确认外键链路与索引符合预期

---

## 6. Day 5 五张表关系概览

### 6.1 关系总图（逻辑）

```text
Tenant
  ├── Conversation (1:N)
  │     ├── ConversationMessage (1:N)
  │     ├── Ticket (1:N)
  │     └── AgentRun (1:N)
  ├── Ticket (1:N)
  ├── AuditLog (1:N)
  └── AgentRun (1:N)

User
  ├── Conversation (1:N, 发起者)
  ├── Ticket (1:N, assignee)
  └── AuditLog (1:N, 操作者)

ConversationMessage
  └── AgentRun (0..1:N, 作为触发消息)
```

### 6.2 Day 5 表职责总表

| 表名 | 主键 | 关键外键 | 主要作用 |
|------|------|----------|----------|
| `conversations` | `id` | `tenant_id -> tenants.id`, `user_id -> users.id` | 对话会话容器 |
| `conversation_messages` | `id` | `tenant_id -> tenants.id`, `conversation_id -> conversations.id` | 对话消息明细 |
| `tickets` | `id` | `tenant_id -> tenants.id`, `conversation_id -> conversations.id`, `assignee_id -> users.id` | 工单流转基础 |
| `audit_logs` | `id` | `tenant_id -> tenants.id`, `user_id -> users.id` | 审计追踪 |
| `agent_runs` | `id` | `tenant_id -> tenants.id`, `conversation_id -> conversations.id`, `trigger_message_id -> conversation_messages.id` | Agent 执行记录 |

---

## 7. 验证标准

### 7.1 模型导入验证

```bash
cd backend
poetry run python -c "from app.models import Conversation, ConversationMessage, Ticket, AuditLog, AgentRun; print(Conversation, ConversationMessage, Ticket, AuditLog, AgentRun)"
```

预期：
- 5 个模型都能成功导入
- 不出现循环导入、relationship 找不到类、字段定义错误

---

### 7.2 Metadata 识别验证

```bash
cd backend
poetry run python -c "from app.db.base import Base; import app.models; print(sorted(Base.metadata.tables.keys()))"
```

预期：
- 输出中能看到全部 9 张表：
  - `tenants`
  - `users`
  - `knowledge_bases`
  - `documents`
  - `conversations`
  - `conversation_messages`
  - `tickets`
  - `audit_logs`
  - `agent_runs`

---

### 7.3 迁移生成验证

```bash
cd backend
poetry run alembic revision --autogenerate -m "add conversation message ticket audit agent run tables"
```

预期：
- 成功生成新的 revision 文件
- `down_revision` 指向 Day 4 的 `f6c7458fff25`
- 迁移脚本中包含 5 张新表的 `create_table(...)`
- 外键链路与索引定义合理

---

### 7.4 数据库落表验证

```bash
cd backend
poetry run alembic upgrade head
podman exec supportforge-postgres psql -U supportforge -c "\dt"
```

预期：
- PostgreSQL 中能看到：
  - `alembic_version`
  - `tenants`
  - `users`
  - `knowledge_bases`
  - `documents`
  - `conversations`
  - `conversation_messages`
  - `tickets`
  - `audit_logs`
  - `agent_runs`

---

## 8. 与后续开发的衔接关系

Day 5 完成后，以下能力就具备前提了：

| 后续阶段 | 依赖 Day 5 的内容 |
|----------|------------------|
| Day 6 路由骨架 | 可以基于真实模型设计 API 输入输出结构 |
| Week 2 登录与对话接口 | `conversations` / `conversation_messages` 提供持久化基础 |
| Week 4 工单闭环 | `tickets` 表提供流转与指派数据基础 |
| Week 5 审计日志与 tracing | `audit_logs` + `agent_runs` 提供行为追踪与 AI 运行追踪 |
| Repository / Service 层 | 可围绕 9 张核心表封装 CRUD 与业务逻辑 |

---

## 9. Day 5 完成标准（DoD）

完成 Day 5，至少要满足以下检查项：

- [ ] `models/conversation.py` 已创建
- [ ] `models/conversation_message.py` 已创建
- [ ] `models/ticket.py` 已创建
- [ ] `models/audit_log.py` 已创建
- [ ] `models/agent_run.py` 已创建
- [ ] 5 个模型都继承了 `Base`
- [ ] 需要时间戳的模型都继承了 `TimestampMixin`（或有明确不继承的理由）
- [ ] 5 张表都包含 `tenant_id`
- [ ] `conversation_messages` 正确关联 `conversations`
- [ ] `tickets` 正确关联 `conversations` 和 `users`
- [ ] `audit_logs` 正确关联 `users`（可空）
- [ ] `agent_runs` 正确关联 `conversations` 和 `conversation_messages`（可空）
- [ ] `models/__init__.py` 已正确导入全部 9 个模型
- [ ] `Base.metadata.tables.keys()` 能看到全部 9 张表
- [ ] Alembic autogenerate 能生成第二个 revision
- [ ] `alembic upgrade head` 后数据库里能看到全部 9 张业务表
- [ ] 字段命名、角色命名、多租户约束与 CLAUDE.md 保持一致
- [ ] 代码注释清晰，方便你后续讲设计思路

---

## 10. 常见坑与排错建议

### 10.1 `relationship()` 循环导入报错

**常见原因**：
- 模型文件之间互相直接 import，形成循环依赖

**建议**：
- `relationship()` 优先用字符串类名，例如 `relationship("Conversation")`
- 只在 `models/__init__.py` 做集中导入，不在模型文件之间相互 import 具体类

---

### 10.2 外键链路写错

**典型错误**：
- `conversation_message` 写成了错误表名，而真实表名应是 `conversation_messages`
- `agent_run` 的外键指向了不存在的表名

**建议**：
- 先统一写好每个模型的 `__tablename__`
- 所有 `ForeignKey("表名.字段")` 必须和真实表名完全一致

---

### 10.3 审计/Agent payload 字段类型选错

**常见问题**：
- 把结构化 payload 设计成 `String(255)`，后续一长就截断

**建议**：
- 审计与 Agent 运行的结构化数据优先用 `JSON`
- 如果暂时无法确定结构，也至少用 `Text`，不要用短字符串

---

### 10.4 工单 / 对话状态字段过度设计

**常见问题**：
- 一上来就搞很复杂的 Enum 和状态机，导致 Day 5 过重

**建议**：
- 先用字符串字段 + 文档约定值
- 等 API / Service 逻辑开始实现时，再逐步收敛为 Enum 或状态机常量

---

### 10.5 `down_revision` 链断裂

**常见原因**：
- 第二个迁移文件生成时没有正确链接到 Day 4 的 revision

**建议**：
- 生成迁移后立即检查文件头部：
  - `revision = ...`
  - `down_revision = 'f6c7458fff25'`
- 如果不对，要在提交前手动修正

---

## 11. 实施顺序建议

Day 5 推荐按这个顺序实现：

1. 先写 `conversation.py`
2. 再写 `conversation_message.py`
3. 再写 `ticket.py`
4. 再写 `audit_log.py`
5. 最后写 `agent_run.py`
6. 更新 `models/__init__.py`
7. 验证 `Base.metadata.tables.keys()`
8. 生成 Alembic 迁移脚本
9. 执行 `upgrade head`
10. 在 PostgreSQL 中确认全部 9 张表都存在

这样做的好处是：
- 先把核心对话链路搭起来（conversation → message）
- 再补工单和审计两个业务侧结构
- 最后补 Agent 执行记录，避免前置依赖不完整导致关系混乱
