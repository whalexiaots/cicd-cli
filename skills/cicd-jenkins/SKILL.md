---
name: cicd-jenkins
version: 0.1.0
description: >-
  Jenkins 编译触发与状态监控：触发 VerifyBuild、轮询队列和编译状态、错误日志分析、构建报告。
  触发词：Jenkins、编译、构建、VB、VerifyBuild、trigger、编译状态、构建结果、编译失败。
metadata:
  requires:
    bins: ["python3"]
    packages: ["requests"]
---

# Jenkins 编译

> **前置条件**: 先阅读 [../cicd-shared/SKILL.md](../cicd-shared/SKILL.md) 了解认证和配置。

## Shortcuts（推荐优先使用）

| Shortcut | 说明 |
|----------|------|
| `+trigger` | 触发 Jenkins 编译 |
| `+poll` | 轮询编译状态（队列→编译→完成）|
| `+info` | 查看编译信息 |
| `+console` | 查看控制台输出（尾部 N 行）|

## 快速示例

```bash
# 触发编译（使用项目默认参数）
cicd-cli jenkins +trigger --change-id "552058 552059"

# 触发编译（指定 job）
cicd-cli jenkins +trigger --job VerifyBuild_for_8550 --change-id 552058

# 轮询编译状态
cicd-cli jenkins +poll --job VerifyBuild_for_8550 --queue-id 12345

# 查看编译信息
cicd-cli jenkins +info --job VerifyBuild_for_8550 --build 456

# 查看控制台输出最后 50 行
cicd-cli jenkins +console --job VerifyBuild_for_8550 --build 456 --tail 50
```

## 配置

```json
{
  "jenkins": {
    "host": "http://10.0.0.100:8080",
    "auth": { "username": "user", "api_token": "<TOKEN>" },
    "job_name": "VerifyBuild_for_8550",
    "default_params": {
      "PRODUCT": "Vex",
      "BRANCH": "Turbox-Snapdragon_Mid_2022.SPF.2.0",
      "BUILD_MODE": "FULL_BUILD"
    }
  }
}
```

## 关键约束

- **CRITICAL**: GERRIT_ID 多个用**空格**分隔（不是逗号！）
- **CRITICAL**: 轮询间隔不低于 30 秒（编译阶段），队列阶段不低于 10 秒
- **WARNING**: 构建超 120 分钟必须告警
- **WARNING**: 不同项目可能使用不同 Jenkins 服务器，注意配置切换
- 触发编译后返回 queue_id，用于后续轮询
