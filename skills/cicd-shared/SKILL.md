---
name: cicd-shared
version: 0.1.0
description: >-
  cicd-cli 共享基础 skill：配置初始化、认证管理、多项目切换、安全规则。
  被所有其他 cicd-* skill 依赖，必须最先读取。
  触发词：配置、认证、auth、config、project、凭证、登录、初始化。
metadata:
  requires:
    bins: ["python3"]
    packages: ["paramiko", "requests", "pycryptodome"]
---

# cicd-cli 共享规则

你是 AI Agent，通过 `cicd-cli` 命令操作 CI/CD 服务。下方是认证和通用规则。

## 配置初始化

```bash
# 初始化配置（交互式引导创建 services.json）
cicd-cli config init

# 查看当前配置
cicd-cli config show
```

配置文件位置: `~/.cicd-cli/config/services.json`

### 配置层级

```
services.json
├── gerrit:     { host, auth: { username, http_password } }
├── jenkins:    { host, auth: { username, api_token }, job_name }
├── jira:       { host, auth: { username, api_token } }
├── ssh:        { host, port, user, password, remote_dir }
├── ftp:        { host, port, user, password, local_dir }
├── elink:      { host, auth: { username, password, aes_key } }
├── ftp_servers: { chengdu: {...}, beijing1: {...} }
└── projects:
    ├── DoDo:   { ssh: {...}, jenkins: {...}, gerrit: {...}, elink: {...} }
    ├── Vex:    { ssh: {...}, jenkins: {...}, elink: {...} }
    └── ...
```

> **合并规则**: 项目级配置覆盖全局配置，未覆盖的字段回退到全局值。

## 多项目切换

```bash
cicd-cli project list          # 列出所有项目
cicd-cli project use DoDo      # 切换到 DoDo 项目
cicd-cli project show          # 显示当前项目配置
cicd-cli --project Vex <cmd>   # 临时指定项目（不影响默认值）
```

所有命令自动使用当前项目配置，也支持 `--project` 临时覆盖。

## 认证

```bash
cicd-cli auth status           # 查看各服务认证状态
cicd-cli auth login elink      # 登录易链（自动 AES 加密 + SSO 获取 JWT）
```

### 服务认证方式

| 服务 | 认证方式 | 凭证来源 |
|------|---------|---------|
| Gerrit | HTTP Password | services.json |
| Jenkins | API Token | services.json |
| Jira | PAT (API Token) | services.json |
| SSH | 密码/密钥 | services.json |
| FTP | 用户名/密码 | services.json |
| 易链 | SSO JWT Token | services.json + ~/.cicd-cli/secrets/elink.json |

### 易链认证

- 登录方式：AES-192-ECB 加密密码 → SSO 登录 → JWT Token
- Token 有效期：8 天（719999 秒）
- 自动缓存到 `~/.cicd-cli/secrets/elink.json`
- 使用前自动检查有效性，过期则重新登录

### 认证失败处理

1. 运行 `cicd-cli auth status` 检查哪些服务认证缺失
2. 编辑 `~/.cicd-cli/config/services.json` 填入正确凭证
3. 易链需额外运行 `cicd-cli auth login elink`

## 输出格式

```bash
--format json      # JSON 格式（默认）— AI Agent 友好
--format pretty    # 人类可读格式
--format table     # 表格格式
```

所有命令的 stdout 是数据（JSON），stderr 是进度/警告/错误。

## 安全规则

### 凭证保护
- **禁止** 在输出或日志中打印完整密码/Token
- Token 仅显示前 8 位 + `...`
- secrets 目录已在 .gitignore 中排除

### 路径安全
- 所有用户输入的路径参数需验证，防止路径遍历
- SSH/FTP 远程路径限制在 `remote_dir` 范围内

### CRITICAL 约束
- **不要**修改 services.json 中其他项目的配置
- **不要**在没有确认的情况下执行破坏性操作（删除、force push 等）
- **不要**将凭证信息写入 git 仓库
- 操作失败时提供明确的错误信息和修复建议

## 跨平台兼容

- 路径使用 `pathlib.Path`，自动适配 Windows/Linux/macOS
- SSH 使用 `paramiko`（纯 Python），无需系统 SSH 客户端
- 入口脚本提供 bash / cmd / PowerShell 三种格式

## 命令探索

```bash
cicd-cli --help                # 列出所有服务域
cicd-cli <service> --help      # 列出服务下所有命令
cicd-cli --version             # 查看版本
```
