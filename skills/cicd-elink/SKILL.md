---
name: cicd-elink
version: 0.1.0
description: >-
  易链代码管理平台操作：登录认证、项目查询、Gerrit Review -2 忽略申请。
  触发词：易链、elink、忽略、ignore、Review -2、checklog、cppcheck、项目列表、代码管理。
metadata:
  requires:
    bins: ["python3"]
    packages: ["requests"]
---

# 易链 (elink) 代码管理

> **前置条件**: 先阅读 [../cicd-shared/SKILL.md](../cicd-shared/SKILL.md) 了解认证和配置。

## Shortcuts（推荐优先使用）

| Shortcut | 说明 |
|----------|------|
| `+login` | 登录易链（浏览器 SSO 授权，自动回调获取 Token）|
| `+status` | 检查 Token 有效性 |
| `+project-list` | 查询易链项目列表 |
| `+ignore-review` | 一键忽略 Gerrit Review -2 |

## 快速示例

```bash
# 登录
cicd-cli elink +login

# 检查 Token 状态
cicd-cli elink +status

# 查询项目
cicd-cli elink +project-list
cicd-cli elink +project-list --name ProjectB

# 忽略 Review -2（默认忽略 checklog）
cicd-cli elink +ignore-review 552058

# 忽略特定检查
cicd-cli elink +ignore-review 552058 --accounts checklog cppcheck --reason "开源代码不改"

# 指定项目
cicd-cli elink +ignore-review 552058 --project-name MyProject --project-id 12345
```

## 配置

```json
{
  "elink": {
    "host": "elink.example.com",
    "protocol": "https",
    "auth": {
      "username": "<YOUR_USERNAME>",
      "password": "<可选，SSO 模式不需要>",
      "aes_key": "<可选，SSO 模式不需要>"
    },
    "module": 2
  },
  "projects": {
    "MyProject": {
      "elink": { "project_id": "12345", "project_name": "MyProject" }
    }
  }
}
```

## 已知项目 ID

在配置文件 `services.json` 中设置 `projects.<name>.elink.project_id`。
项目 ID 可通过 `cicd-cli elink +project-list` 查询。

## 忽略 Review -2 决策规则

### 可以直接忽略的情况：
- 修改 C/C++ 代码，cppcheck/pclint -2: **固定理由** `c代码忽略cppcheck 检查`
- 修改开源/第三方/vendor 代码
- checklog -2，但 commit message 符合规范（误报）
- XML/配置文件被静态分析误报
- copyright -2，文件无需版权头

### 需要先修改代码的情况：
- cppcheck/checkstyle 报出真实 bug
- commit message 格式确实不规范
- 明确的逻辑/安全问题

## 认证流程

### SSO 浏览器授权（推荐）
1. `cicd-cli elink +login` 启动本地回调服务器 (localhost:18632)
2. 自动打开浏览器到 `https://<host>/sso/token/login?redirect_uri=...`
3. 用户在浏览器中完成 SSO 认证
4. SSO 重定向到 localhost 回调，cicd-cli 自动捕获 Token
5. Token 缓存到 `~/.cicd-cli/secrets/elink.json`

### 账号密码登录（回退方式）
当 SSO 授权失败时（如无浏览器环境），自动回退：
1. AES-192-ECB (ZeroPadding) 加密密码
2. POST `/api/auth/token/login` (x-www-form-urlencoded)
3. 返回 JWT Token，缓存到 `~/.cicd-cli/secrets/elink.json`

## 关键约束

- **CRITICAL**: 忽略申请前必须先分析 -2 的具体原因（查 Gerrit comments/messages）
- **CRITICAL**: 真实 bug 不能忽略，必须先修复代码
- **WARNING**: Token 过期自动提示重新登录
- module 参数: 2=IoT智能硬件, 1=智能汽车
