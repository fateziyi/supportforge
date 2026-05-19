请将用户问题分类为以下类型之一：

- account_issue — 账号相关问题
- permission_issue — 权限配置问题
- billing_issue — 计费 / 付款问题
- product_usage — 产品使用指导
- bug_report — 缺陷 / 故障报告
- feature_request — 功能需求 / 建议
- knowledge_gap — 知识库无法覆盖的问题

输出 JSON，包含：
- category: 问题分类
- confidence: 分类置信度（0.0 ~ 1.0）
- reason: 分类理由