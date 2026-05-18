---
name: cicd-gerrit
version: 0.1.0
description: >-
  Gerrit 代码审查：提交代码、Review 管理、Cherry-Pick、CL 依赖分析、Dashboard。
  触发词：Gerrit、代码审查、review、submit、cherry-pick、change、CL、push、rebase。
metadata:
  requires:
    bins: ["python3"]
    packages: ["requests"]
---

# Gerrit 代码审查

> **前置条件**: 先阅读 [../cicd-shared/SKILL.md](../cicd-shared/SKILL.md) 了解认证和配置。

## Shortcuts（推荐优先使用）

| Shortcut | 说明 |
|----------|------|
| `+dashboard` | 查看我的 Review 仪表板（is:open+owner:self）|
| `+query` | 自定义查询 changes |
| `+review` | 提交 Code Review 打分和评论 |
| `+cherry-pick` | Cherry-pick change 到目标分支 |
| `+detail` | 查看 change 详细信息 |

## 快速示例

```bash
# 查看我的未合入 changes
cicd-cli gerrit +dashboard

# 查询特定分支的 changes
cicd-cli gerrit +query "project:iot/vex+branch:dev+is:open"

# 打 Code-Review +2
cicd-cli gerrit +review 552058 --code-review 2 --message "LGTM"

# Cherry-pick 到另一个分支
cicd-cli gerrit +cherry-pick 552058 --branch release/v1.0

# 查看 change 详情
cicd-cli gerrit +detail 552058
```

## 配置

```json
{
  "gerrit": {
    "host": "https://gerrit.example.com",
    "port": 29418,
    "auth": {
      "method": "http_password",
      "username": "<YOUR_USERNAME>",
      "http_password": "<HTTP_PASSWORD>"
    }
  }
}
```

## Gerrit 查询语法

| 查询 | 说明 |
|------|------|
| `is:open+owner:self` | 我的未合入 changes |
| `is:open+reviewer:self` | 待我 review 的 changes |
| `project:iot/vex+branch:dev` | 指定项目和分支 |
| `change:552058` | 指定 change 编号 |
| `status:merged+after:2026-05-01` | 指定时间范围 |

## 关键约束

- **CRITICAL**: Review -2 的 change 不能直接 submit，需要先解决问题或提交忽略申请
- **CRITICAL**: Cherry-pick 前确认目标分支正确
- **WARNING**: 批量 review 操作需逐个确认
- Gerrit JSON 响应带 `)]}'` 前缀，客户端自动处理
