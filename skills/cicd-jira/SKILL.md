---
name: cicd-jira
version: 0.1.0
description: >-
  Jira Bug 全生命周期管理：创建 Bug、状态流转、评论更新、Resolve、搜索报告。
  触发词：Jira、Bug、issue、提Bug、Resolve、转票、评论、状态、搜索、JQL。
metadata:
  requires:
    bins: ["python3"]
    packages: ["requests"]
---

# Jira Bug 管理

> **前置条件**: 先阅读 [../cicd-shared/SKILL.md](../cicd-shared/SKILL.md) 了解认证和配置。

## Shortcuts（推荐优先使用）

| Shortcut | 说明 |
|----------|------|
| `+my-bugs` | 查看我的未关闭 Bug |
| `+create-bug` | 创建 Bug |
| `+resolve` | Resolve Issue |
| `+search` | JQL 搜索 |
| `+comment` | 添加评论 |
| `+transition` | 状态流转 |

## 快速示例

```bash
# 查看我的 Bug
cicd-cli jira +my-bugs
cicd-cli jira +my-bugs --project SILKY

# 创建 Bug
cicd-cli jira +create-bug --project SILKY --summary "Camera HAL 崩溃" --priority Critical

# Resolve
cicd-cli jira +resolve SILKY-123 --comment "[Root Cause]\\n内存泄漏"

# JQL 搜索
cicd-cli jira +search "project=SILKY AND status=Open ORDER BY priority DESC"

# 添加评论
cicd-cli jira +comment SILKY-123 --body "*[Current status]*\\n分析中"

# 状态流转（Open → In Progress）
cicd-cli jira +transition SILKY-123 --id 871
```

## 状态流转 ID 参考

| Transition | ID | 说明 |
|------------|-----|------|
| 开始进行 | 871 | Open → In Progress |
| Blocked | 901 | In Progress → Blocked |
| Resolve | 771 | In Progress → Resolved |

> 不同项目的 transition ID 可能不同，使用前先查询可用流转。

## 评论格式

Jira 使用 **Wiki 标记语法**（不是 Markdown！）:
- 加粗: `*text*`（单个星号）
- 标题: `h3. Title`
- 列表: `* item` 或 `# ordered item`
- 代码: `{code}...{code}`

## 关键约束

- **CRITICAL**: 拿到票第一步必须改状态 Open → In Progress
- **CRITICAL**: Jira 评论禁止出现明确人名，用 CL 号代替
- **WARNING**: Resolve 前必填 [Root Cause] [Solution] [Self Test]
- 评论模板字段需加粗且带方括号: `*[Current status]*`
