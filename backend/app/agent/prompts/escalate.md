如果问题满足以下任一条件，请建议转工单：

- 需要人工调查的复杂问题
- 需要后台系统操作处理
- 涉及权限或系统异常
- 知识库无法覆盖的内容
- 分类置信度过低（低于阈值）
- 用户明确要求人工客服

输出 JSON：
- should_escalate: 是否需要转工单（boolean）
- reason: 转工单的理由
- ticket_subject: 工单标题建议
- ticket_description: 工单描述建议