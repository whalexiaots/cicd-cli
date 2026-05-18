# cicd-cli — AI Agent 集成指南

## 概述

cicd-cli 是为**人类开发者**和 **AI Agent** 共同设计的 CI/CD 命令行工具。
参考 [lark-cli](https://github.com/larksuite/cli/) 的三层命令架构。

## 三层命令体系

```
Shortcuts (+前缀)  →  Commands (API 封装)  →  底层服务 API
     高层简洁            中层模块化              低层灵活
```

### 层级说明

| 层级 | 格式 | 适用场景 |
|------|------|----------|
| Shortcuts | `cicd-cli <service> +<action>` | 日常操作，AI Agent 优先使用 |
| Commands | `commands/<service>.py` 中的类方法 | Python 脚本集成 |
| Raw API | 各服务原生 REST/SSH 接口 | 特殊场景 |

## 服务域

| 服务 | 说明 | Shortcuts |
|------|------|-----------|
| ssh | SSH 远程操作 | +exec, +upload, +download |
| gerrit | Gerrit 代码审查 | +query, +review, +submit, +dashboard |
| jenkins | Jenkins 编译 | +trigger, +poll, +info, +console |
| jira | Jira 问题跟踪 | +search, +create, +transition, +my-bugs |
| ftp | FTP 文件下载 | +download, +list, +test |
| elink | 易链代码管理 | +login, +status, +project-list, +ignore-review |
| build | 远程编译 | +module, +kernel, +image, +nonhlos, +hlos, +all |
| review | 代码审查 | +diff, +files, +format, +commit-msg |
| patch | 补丁应用 | +cherry-pick, +apply, +am, +upload, +abort |
| flash | 刷机验证 | +download, +fastboot, +push, +reboot, +verify |

## AI Agent 使用规范

### 输出格式

所有命令默认输出 JSON，便于 Agent 解析：

```bash
cicd-cli gerrit +query --change-id I1234abc --format json
```

支持格式: `json` (默认) | `pretty` | `table`

### 项目切换

```bash
# 设置当前项目
cicd-cli project use <project_name>

# 临时指定项目
cicd-cli --project <name> build +module frameworks/base
```

### 典型 Agent 工作流

#### Bug 修复流程

```bash
1. cicd-cli jira +search --assignee me --status "In Progress"
2. cicd-cli gerrit +query --branch main --status open
3. cicd-cli patch +cherry-pick refs/changes/xx/xxxxx/1 --repo frameworks/base
4. cicd-cli build +module frameworks/base
5. cicd-cli flash +download --images boot.img system.img
6. cicd-cli flash +fastboot --all
7. cicd-cli flash +verify
8. cicd-cli gerrit +review --change-id Ixxxxx --score +1
```

#### 编译验证流程

```bash
1. cicd-cli build +hlos --clean
2. cicd-cli flash +download --images boot.img
3. cicd-cli flash +reboot --mode bootloader
4. cicd-cli flash +fastboot --partition boot --image ./artifacts/boot.img
5. cicd-cli flash +verify --version 20260427
```

## 配置

配置文件: `~/.cicd-cli/config/services.json`

```bash
cicd-cli config init   # 初始化配置
cicd-cli config show   # 查看当前配置
cicd-cli auth status   # 检查所有服务认证状态
```

## Skills 目录

每个 skill 对应 `skills/<name>/SKILL.md`，包含：
- 触发关键词（description 字段）
- Shortcuts 列表
- 决策表
- 异常处理
- 配置示例

AI Agent 通过读取 SKILL.md 自动识别何时调用哪个服务域。

## 跨平台

- Python 3.8+ (Windows/macOS/Linux)
- SSH 使用 paramiko（无需系统 ssh 命令）
- 路径使用 pathlib（跨平台兼容）
- 入口脚本: `bin/cicd-cli` (bash) / `bin/cicd-cli.cmd` (Windows)

## 安装

```bash
pip install -e .  # 开发模式安装
# 或
pip install paramiko requests pycryptodome  # 最小依赖
```

## 开发

```bash
# 运行测试
python -m pytest tests/ -v

# 添加新服务域
1. 创建 commands/<service>.py  (Client 类)
2. 创建 shortcuts/<service>_shortcuts.py  (handle_<service> 函数)
3. 在 core/cli.py 注册 handler
4. 创建 skills/cicd-<service>/SKILL.md
5. git commit
```
