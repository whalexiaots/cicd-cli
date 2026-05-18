# cicd-cli

CI/CD 命令行工具 — 为人类开发者和 AI Agent 设计。

## 特性

- **三层命令架构**: Shortcuts (+前缀) → Commands → Raw API
- **10 个服务域**: SSH / Gerrit / Jenkins / Jira / FTP / elink / Build / Review / Patch / Flash
- **跨平台**: Windows / macOS / Linux (Python 3.8+)
- **AI Agent 友好**: JSON 输出、SKILL.md 自动触发、AGENTS.md 集成指南
- **多项目支持**: services.json 全局 + 项目级配置覆盖

## 安装

### Option 1 — 从 npm 安装 (推荐)

```bash
npx @whalexiaots/cicd-cli@latest install
```

或全局安装：

```bash
npm install -g @whalexiaots/cicd-cli
cicd-cli config init
```

> 需要 Node.js >= 16 和 Python >= 3.8

### Option 2 — 从源码安装

```bash
git clone https://github.com/whalexiaots/cicd-cli.git
cd cicd-cli
make install
```

> `make install` 默认安装到 `~/.cicd-cli/`，自动安装 Python 依赖

### Option 3 — 手动安装

```bash
git clone https://github.com/whalexiaots/cicd-cli.git
cd cicd-cli
pip install -r requirements.txt
export PATH="$PWD/bin:$PATH"
```

### 初始化

```bash
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

---

## Supported AI Tools 安装指南

cicd-cli 支持以下 AI 工具集成。安装后 AI Agent 可自动识别并调用 cicd-cli 的 Skills。

### 通用前置步骤

```bash
# 方法 1: npm 安装 (推荐)
npx @whalexiaots/cicd-cli@latest install

# 方法 2: 从源码安装
git clone https://github.com/whalexiaots/cicd-cli.git
cd cicd-cli && make install

# 方法 3: 手动安装
git clone https://github.com/whalexiaots/cicd-cli.git ~/.cicd-cli/src
cd ~/.cicd-cli/src
pip install -r requirements.txt
# Linux/macOS:
echo 'export PATH="$HOME/.cicd-cli/src/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
# Windows (PowerShell):
# [Environment]::SetEnvironmentVariable("Path", "$env:USERPROFILE\.cicd-cli\src\bin;$env:Path", "User")

# 初始化配置
cicd-cli config init

# 验证安装
cicd-cli --version
```

---

### Claude Code

将 skills 目录链接到 Claude Code 的指令目录：

```bash
# 方法 1: 在项目 .claude/CLAUDE.md 中引用
cat >> .claude/CLAUDE.md << 'EOF'

## CI/CD 工具
使用 cicd-cli 执行 CI/CD 操作。Skills 文档位于 ~/.cicd-cli/src/skills/ 目录。
执行前先运行 `cicd-cli auth status` 检查认证状态。
EOF

# 方法 2: 全局 settings.json
# ~/.claude/settings.json 中添加 allowed commands:
# { "permissions": { "allow": ["cicd-cli"] } }
```

---

### GitHub Copilot (VS Code)

通过 `.github/copilot-instructions.md` 和 skills 机制加载：

```bash
# 1. 复制 skills 到工作区
mkdir -p .github/skills
cp -r ~/.cicd-cli/src/skills/cicd-* .github/skills/

# 2. 在 copilot-instructions.md 中注册
cat >> .github/copilot-instructions.md << 'EOF'

## CI/CD 工具集成
项目使用 cicd-cli 管理 CI/CD 流程。运行 `cicd-cli <service> +<action>` 执行操作。
详见各 skill 文档: .github/skills/cicd-*/SKILL.md
EOF

# 3. 在 .github/instructions/ 下创建指令文件（可选）
mkdir -p .github/instructions
cat > .github/instructions/cicd-cli.instructions.md << 'EOF'
---
applyTo: "**"
description: "cicd-cli CI/CD 工具使用规范"
---
使用 cicd-cli 执行远程编译、代码审查、补丁应用、刷机验证等操作。
所有命令输出 JSON 格式，可直接解析。
EOF
```

---

### GitHub Copilot CLI

```bash
# GitHub Copilot CLI 通过 shell alias 集成
# 在 ~/.bashrc 或 ~/.zshrc 中添加:
alias ci='cicd-cli'

# Copilot CLI 会自动发现 PATH 中的 cicd-cli 命令
# 使用 `gh copilot suggest "cicd-cli build +module xxx"` 获取建议
```

---

### Cursor

通过 `.cursorrules` 或 `.cursor/rules/` 加载：

```bash
# 方法 1: 项目级规则
cat > .cursorrules << 'EOF'
## CI/CD 工具
本项目使用 cicd-cli 管理 CI/CD。Skills 文档:
- ~/.cicd-cli/src/skills/cicd-shared/SKILL.md (通用配置)
- ~/.cicd-cli/src/skills/cicd-build/SKILL.md (远程编译)
- ~/.cicd-cli/src/skills/cicd-gerrit/SKILL.md (代码审查)
- ~/.cicd-cli/src/skills/cicd-flash/SKILL.md (刷机验证)

使用 `cicd-cli <service> +<shortcut>` 格式执行命令。
所有命令默认 JSON 输出。
EOF

# 方法 2: 全局规则目录
mkdir -p ~/.cursor/rules
cp ~/.cicd-cli/src/skills/cicd-shared/SKILL.md ~/.cursor/rules/cicd-shared.md
```

---

### Gemini CLI

Gemini CLI 自动读取 `AGENTS.md`：

```bash
# cicd-cli 自带 AGENTS.md，将其链接到项目根目录
ln -sf ~/.cicd-cli/src/AGENTS.md ./AGENTS.md

# 或直接复制
cp ~/.cicd-cli/src/AGENTS.md ./AGENTS.md
```

---

### Codex (OpenAI)

```bash
# Codex 通过 AGENTS.md 和项目指令加载
# 1. 链接 AGENTS.md
ln -sf ~/.cicd-cli/src/AGENTS.md ./AGENTS.md

# 2. 或在 codex.md/instructions 中引用
cat > codex.md << 'EOF'
## 工具
- cicd-cli: CI/CD 命令行工具，支持 ssh/gerrit/jenkins/jira/ftp/elink/build/review/patch/flash
- 用法: `cicd-cli <service> +<action> [flags]`
- Skills 文档: ~/.cicd-cli/src/skills/
EOF
```

---

### Windsurf

通过 `.windsurfrules` 加载：

```bash
cat > .windsurfrules << 'EOF'
## CI/CD 工具
使用 cicd-cli 执行 CI/CD 操作。

可用服务: ssh, gerrit, jenkins, jira, ftp, elink, build, review, patch, flash
命令格式: cicd-cli <service> +<shortcut> [--format json]

Skills 参考: ~/.cicd-cli/src/skills/cicd-*/SKILL.md
配置检查: cicd-cli auth status
EOF
```

---

### Cline / Roo Code

通过 `.clinerules` 或自定义指令加载：

```bash
# Cline
cat > .clinerules << 'EOF'
## CI/CD 工具
使用 cicd-cli 管理 CI/CD 流程。
- 命令格式: cicd-cli <service> +<action>
- 可用服务: ssh, gerrit, jenkins, jira, ftp, elink, build, review, patch, flash
- 配置: ~/.cicd-cli/config/services.json
- Skills: ~/.cicd-cli/src/skills/cicd-*/SKILL.md
EOF

# Roo Code
mkdir -p .roo/rules
cp .clinerules .roo/rules/cicd-cli.md
```

---

### OpenCode

```bash
# OpenCode 通过 AGENTS.md 自动发现
ln -sf ~/.cicd-cli/src/AGENTS.md ./AGENTS.md

# 或在 opencode 配置中注册命令
# ~/.config/opencode/config.json:
# { "tools": { "cicd-cli": { "command": "cicd-cli", "description": "CI/CD CLI" } } }
```

---

### OpenClaw

OpenClaw ACPX 运行时通过 skills 目录加载：

```bash
# 将 cicd-cli skills 安装到全局 skills 目录
mkdir -p ~/.agents/skills
cp -r ~/.cicd-cli/src/skills/cicd-* ~/.agents/skills/

# OpenClaw 自动扫描 ~/.agents/skills/ 下的 SKILL.md
# 无需额外配置，Agent 会按 description 中的触发词自动匹配
```

---

### Hermes

```bash
# Hermes 通过项目规则文件加载
cat > .hermes/rules.md << 'EOF'
## CI/CD 工具集成
使用 cicd-cli 执行 CI/CD 操作。
Skills 文档: ~/.cicd-cli/src/skills/
命令格式: cicd-cli <service> +<action> [flags]
EOF
```

---

### Mistral Vibe

```bash
# Mistral Vibe 通过 AGENTS.md 或项目配置加载
ln -sf ~/.cicd-cli/src/AGENTS.md ./AGENTS.md

# 或在 .vibe/instructions.md 中引用
mkdir -p .vibe
cat > .vibe/instructions.md << 'EOF'
使用 cicd-cli 管理 CI/CD: `cicd-cli <service> +<action>`
Skills: ~/.cicd-cli/src/skills/cicd-*/SKILL.md
EOF
```

---

### Kilo Code

```bash
# Kilo Code 兼容 Cline 规则格式
cat > .clinerules << 'EOF'
## CI/CD 工具
使用 cicd-cli 管理 CI/CD 流程。
命令: cicd-cli <service> +<action> [flags]
服务: ssh, gerrit, jenkins, jira, ftp, elink, build, review, patch, flash
Skills: ~/.cicd-cli/src/skills/cicd-*/SKILL.md
EOF
```

---

### Google Antigravity

```bash
# Antigravity 通过 AGENTS.md 和项目规则文件加载
ln -sf ~/.cicd-cli/src/AGENTS.md ./AGENTS.md

# 确保 cicd-cli 在 PATH 中可访问
which cicd-cli
```

---

## 验证安装

在任何 AI 工具中输入以下提示词测试集成是否正常：

```
请运行 cicd-cli auth status 检查所有服务的认证状态
```

如果 AI 能正确调用 cicd-cli 并返回 JSON 结果，说明集成成功。

---

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
