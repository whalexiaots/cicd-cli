# cicd-cli

CI/CD 命令行工具 — 为人类开发者和 AI Agent 设计。

## 特性

- **三层命令架构**: Shortcuts (+前缀) → Commands → Raw API
- **10 个服务域**: SSH / Gerrit / Jenkins / Jira / FTP / elink / Build / Review / Patch / Flash
- **跨平台**: Windows / macOS / Linux (Python 3.8+)
- **AI Agent 友好**: JSON 输出、SKILL.md 自动触发、AGENTS.md 集成指南
- **多项目支持**: services.json 全局 + 项目级配置覆盖

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化配置
cicd-cli config init

# 切换项目
cicd-cli project use <project_name>

# 检查认证
cicd-cli auth status
```

## 服务域

| 服务 | 说明 | 快捷命令示例 |
|------|------|------------|
| ssh | SSH 远程操作 | `cicd-cli ssh +exec "ls -la"` |
| gerrit | Gerrit 代码审查 | `cicd-cli gerrit +query --status open` |
| jenkins | Jenkins 编译 | `cicd-cli jenkins +trigger` |
| jira | Jira 问题跟踪 | `cicd-cli jira +my-bugs` |
| ftp | FTP 文件下载 | `cicd-cli ftp +download /path/to/file.zip` |
| elink | 易链代码管理 | `cicd-cli elink +status` |
| build | 远程编译 | `cicd-cli build +module frameworks/base` |
| review | 代码审查 | `cicd-cli review +format` |
| patch | 补丁应用 | `cicd-cli patch +cherry-pick refs/changes/xx/xxxxx/1 --repo path` |
| flash | 刷机验证 | `cicd-cli flash +fastboot --all` |

## 配置

配置文件位置: `~/.cicd-cli/config/services.json`

参考模板: [config/services.json.example](config/services.json.example)

## 开发

```bash
# 运行测试
python -m pytest tests/ -v

# 开发模式安装
pip install -e .
```

## 目录结构

```
cicd-cli/
├── bin/                    # 入口脚本 (bash/cmd/ps1)
├── core/                   # 核心框架 (cli/config/auth/output)
├── commands/               # 服务客户端 (每个服务一个文件)
├── shortcuts/              # 快捷命令处理器
├── skills/                 # AI Agent Skill 文档
├── config/                 # 配置模板
└── tests/                  # 测试
```

## 许可

Internal Use Only
