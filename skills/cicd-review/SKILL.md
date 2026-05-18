---
name: cicd-review
description: >-
  代码审查与规范检查：clang-format / checkpatch / shellcheck / flake8 等格式工具
  自动化检测 + AI 按清单做逻辑/安全/可维护性审查。
  Use when user mentions: 代码审查、审查代码、code review、格式检查、
  clang-format、checkpatch、审查通过、review patch、检查代码风格。
---

> 依赖: `cicd-ssh` · 配置: `projects.<name>.ssh` + `projects.<name>.repo`

# Code Review Skill

## Shortcuts

| 命令 | 说明 | 示例 |
|------|------|------|
| `+diff` | 获取最近变更 diff | `cicd-cli review +diff --commits 2` |
| `+files` | 列出变更文件 | `cicd-cli review +files` |
| `+format` | 自动格式检查 | `cicd-cli review +format` |
| `+commit-msg` | 检查 commit message | `cicd-cli review +commit-msg` |

## 自动检查工具映射

| 文件类型 | 工具 | 命令 |
|----------|------|------|
| C/C++ (.c/.h/.cpp) | clang-format | `clang-format --dry-run -Werror <file>` |
| C (kernel 路径) | checkpatch.pl | `scripts/checkpatch.pl --no-tree -f <file>` |
| Shell (.sh) | ShellCheck | `shellcheck <file>` |
| Python (.py) | flake8 | `flake8 <file>` |
| Java/Kotlin | google-java-format | `google-java-format --dry-run <file>` |

## AI 审查清单

执行 `+format` 仅做自动化工具检查。AI Agent 应额外按以下清单审查：

### A. 格式与风格
- 缩进一致（C: 8-Tab 或项目标准 4-space）
- 行宽 ≤80 列
- K&R 大括号风格
- 无尾部空白

### B. 逻辑与设计
- 函数单一职责、长度 ≤2 屏
- 错误路径资源释放（goto cleanup 模式）
- 控制流嵌套 ≤3 层

### C. 安全与健壮性
- Buffer 拷贝长度限制
- 指针使用前检查
- 无整数溢出/除零
- 资源 alloc/free 配对

### D. 可维护性
- 关键逻辑有注释
- Magic number 提取为常量
- 无循环依赖

### E. 修改原则
- 最小化修改范围
- 低耦合（wrapper/adapter）
- 无无关重构

### F. Commit Message 格式
```
<MODULE>: <SUBMODULE>: <summary>

- Change point 1
- Change point 2

IssueID: <JIRA-XXX>
```
MODULE ∈ {BSP, FW, TELE, SYSTEM, KERNEL, HAL, APPS}，标题 ≤72 字符。

## 工作流

1. `cicd-cli review +files` → 获取变更文件列表
2. `cicd-cli review +format` → 自动格式检查
3. `cicd-cli review +diff` → 获取完整 diff 供 AI 审查
4. `cicd-cli review +commit-msg` → 检查 commit message 格式
5. AI Agent 按清单输出审查报告
